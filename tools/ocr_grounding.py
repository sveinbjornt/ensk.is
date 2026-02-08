#!/usr/bin/env python3
"""
OCR Grounding tool.
Uses Tesseract to find bounding boxes for words on dictionary pages.
Supports parallel processing for all pages.
"""

import json
import os
import sys
import subprocess
import re
from multiprocessing import Pool, cpu_count

# Add project root to path
sys.path.insert(0, os.getcwd())

def run_tesseract(image_path):
    cmd = [
        "tesseract",
        image_path,
        "stdout",
        "-l", "eng",
        "--psm", "3", # Fully automatic page segmentation, but no OSD.
        "tsv"
    ]
    # Capture output. Tesseract can be noisy on stderr.
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # print(f"Error running tesseract on {image_path}: {result.stderr}")
        return None
    return result.stdout

def parse_tsv(tsv_data):
    lines = tsv_data.strip().split('\n')
    if not lines:
        return [], (0, 0)
        
    header = lines[0].split('\t')
    
    try:
        idx_level = header.index('level')
        idx_left = header.index('left')
        idx_top = header.index('top')
        idx_width = header.index('width')
        idx_height = header.index('height')
        idx_text = header.index('text')
    except ValueError:
        return [], (0, 0)

    # Find page dimensions from level 1 entry (page)
    page_width = 0
    page_height = 0
    
    rows = []
    for line in lines[1:]:
        parts = line.split('\t')
        if len(parts) < len(header):
            continue
        
        level = parts[idx_level]
        if level == '1': # Page level
            try:
                page_width = int(parts[idx_width])
                page_height = int(parts[idx_height])
            except ValueError:
                pass
            continue
            
        if level == '5': # Word level
            text = parts[idx_text].strip()
            if not text:
                continue
            
            try:
                rows.append({
                    'text': text,
                    'left': int(parts[idx_left]),
                    'top': int(parts[idx_top]),
                    'width': int(parts[idx_width]),
                    'height': int(parts[idx_height])
                })
            except ValueError:
                continue
            
    return rows, (page_width, page_height)

def clean_word(w):
    # Remove punctuation and lowercase
    return re.sub(r'[^\w]', '', w).lower()

def process_page_task(args):
    page_num, target_words = args
    
    image_path = f"static/img/pages/{page_num - 1:03d}.jpg"
    if not os.path.exists(image_path):
        return page_num, []

    tsv_output = run_tesseract(image_path)
    if not tsv_output:
        return page_num, []

    ocr_words, (pw, ph) = parse_tsv(tsv_output)
    
    if pw == 0 or ph == 0:
        return page_num, []

    grounding = []
    ocr_cursor = 0
    
    for word in target_words:
        cleaned_target = clean_word(word)
        found_idx = -1
        
        # Search forward from cursor
        for i in range(ocr_cursor, len(ocr_words)):
            ocr_w = ocr_words[i]
            cleaned_ocr = clean_word(ocr_w['text'])
            
            # Exact match (cleaned)
            if cleaned_ocr == cleaned_target:
                found_idx = i
                break
        
        if found_idx != -1:
            # Match found
            match = ocr_words[found_idx]
            
            # Normalize coordinates [ymin, xmin, ymax, xmax] to 0-1000
            xmin = int((match['left'] / pw) * 1000)
            ymin = int((match['top'] / ph) * 1000)
            xmax = int(((match['left'] + match['width']) / pw) * 1000)
            ymax = int(((match['top'] + match['height']) / ph) * 1000)
            
            grounding.append({
                "word": word,
                "bbox": [ymin, xmin, ymax, xmax]
            })
            
            # Advance cursor
            ocr_cursor = found_idx + 1
    
    return page_num, grounding

def main():
    if len(sys.argv) < 2:
        print("Usage: ocr_grounding.py <page_num|all> [save]")
        sys.exit(1)
    
    save_mode = len(sys.argv) > 2 and sys.argv[2] == "save"
    mode = sys.argv[1]

    # Load mapping once
    with open('data/word2page.json', 'r') as f:
        mapping = json.load(f)
    
    # Pre-group words by page
    words_by_page = {}
    for w, p in mapping.items():
        if p not in words_by_page:
            words_by_page[p] = []
        words_by_page[p].append(w)
    
    for p in words_by_page:
        words_by_page[p].sort(key=lambda s: s.lower())

    results = {}
    
    if mode == "all":
        tasks = []
        # Pages 1 to 707 (or max page in mapping)
        max_page = max(words_by_page.keys())
        print(f"Preparing tasks for {max_page} pages...")
        
        for p in range(1, max_page + 1):
            if p in words_by_page:
                tasks.append((p, words_by_page[p]))
        
        print(f"Processing {len(tasks)} pages using {cpu_count()} cores...")
        
        with Pool() as pool:
            for i, (page_num, grounding) in enumerate(pool.imap_unordered(process_page_task, tasks)):
                results[str(page_num)] = grounding
                if i % 50 == 0:
                    print(f"Progress: {i}/{len(tasks)} pages processed.")
        print("All pages processed.")
        
    else:
        # Single page
        try:
            page_num = int(mode)
        except ValueError:
            print("Invalid page number")
            sys.exit(1)
        
        print(f"Processing Page {page_num}...")
        target_words = words_by_page.get(page_num, [])
        if not target_words:
            print("No words found for this page in mapping.")
        
        _, results[str(page_num)] = process_page_task((page_num, target_words))
        print(f"Matched {len(results[str(page_num)])} / {len(target_words)} words.")

    if save_mode:
        grounding_file = 'data/word2page_coords.json'
        
        existing_data = {}
        if os.path.exists(grounding_file):
            try:
                with open(grounding_file, 'r') as f:
                    existing_data = json.load(f)
            except json.JSONDecodeError:
                pass
        
        existing_data.update(results)
        
        with open(grounding_file, 'w') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        print(f"Saved grounding data to {grounding_file}")
    else:
        if mode != "all":
             print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()