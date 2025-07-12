#!/usr/bin/env python3
"""
Frequency Analyzer - Generate word frequency data from open sources

Creates a JSON file mapping words to frequency percentiles and categories.
Uses Wikipedia and optionally other open data sources.

Usage:
    python frequency_analyzer.py [--output freq.json] [--min-count 5]
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Tuple
import urllib.request
import gzip
import xml.etree.ElementTree as ET
import bz2
import tempfile
import os


class FrequencyAnalyzer:
    def __init__(self, min_count: int = 5):
        self.min_count = min_count
        self.word_counts = Counter()

    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove markup, normalize whitespace
        text = re.sub(r"\[\[.*?\]\]", "", text)  # Remove wiki links
        text = re.sub(r"\{\{.*?\}\}", "", text)  # Remove templates
        text = re.sub(r"<.*?>", "", text)  # Remove HTML
        text = re.sub(r"[^\w\s]", " ", text)  # Keep only words and spaces
        text = re.sub(r"\s+", " ", text)  # Normalize whitespace
        return text.lower().strip()

    def extract_words(self, text: str):
        """Extract words from cleaned text."""
        words = text.split()
        # Filter: 2+ chars, alphabetic only, not all caps
        return [w for w in words if len(w) >= 2 and w.isalpha() and not w.isupper()]

    def download_wikipedia_dump(self, max_size_mb: int = 1000) -> str:
        """Download a recent Wikipedia dump file. Returns path to downloaded file."""
        print("Downloading Wikipedia dump...")
        
        # Use a smaller, manageable dump for testing
        dump_url = "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles1.xml-p1p41242.bz2"
        
        # Create temp file
        temp_fd, temp_path = tempfile.mkstemp(suffix=".xml.bz2")
        os.close(temp_fd)
        
        try:
            print(f"Downloading from: {dump_url}")
            urllib.request.urlretrieve(dump_url, temp_path)
            
            # Check file size
            size_mb = os.path.getsize(temp_path) / (1024 * 1024)
            print(f"Downloaded {size_mb:.1f} MB")
            
            if size_mb > max_size_mb:
                print(f"Warning: File size ({size_mb:.1f} MB) exceeds limit ({max_size_mb} MB)")
                os.unlink(temp_path)
                return None
                
            return temp_path
            
        except Exception as e:
            print(f"Download failed: {e}")
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return None
    
    def parse_wikipedia_xml(self, xml_path: str, max_articles: int = 10000) -> None:
        """Parse Wikipedia XML dump and extract article text."""
        print(f"Parsing Wikipedia XML (max {max_articles:,} articles)...")
        
        articles_processed = 0
        
        try:
            # Open compressed XML file
            with bz2.open(xml_path, 'rt', encoding='utf-8') as file:
                # Parse XML incrementally to handle large files
                context = ET.iterparse(file, events=('start', 'end'))
                context = iter(context)
                event, root = next(context)
                
                current_title = ""
                current_text = ""
                in_page = False
                
                for event, elem in context:
                    if event == 'start':
                        if elem.tag.endswith('page'):
                            in_page = True
                        elif elem.tag.endswith('title') and in_page:
                            current_title = ""
                        elif elem.tag.endswith('text') and in_page:
                            current_text = ""
                    
                    elif event == 'end':
                        if elem.tag.endswith('title') and in_page:
                            current_title = elem.text or ""
                        elif elem.tag.endswith('text') and in_page:
                            current_text = elem.text or ""
                        elif elem.tag.endswith('page') and in_page:
                            # Process this article
                            if current_text and not current_title.startswith(('File:', 'Category:', 'Template:', 'Wikipedia:')):
                                cleaned = self.clean_text(current_text)
                                words = self.extract_words(cleaned)
                                self.word_counts.update(words)
                                
                                articles_processed += 1
                                if articles_processed % 1000 == 0:
                                    print(f"  Processed {articles_processed:,} articles...", end="\r")
                                
                                if articles_processed >= max_articles:
                                    break
                            
                            # Reset for next article
                            current_title = ""
                            current_text = ""
                            in_page = False
                        
                        # Clear processed elements to save memory
                        elem.clear()
                        
                    if articles_processed >= max_articles:
                        break
                        
        except Exception as e:
            print(f"\nError parsing XML: {e}")
            if articles_processed == 0:
                print("Falling back to demo data...")
                self._create_demo_data()
                return
        
        print(f"\n  Processed {articles_processed:,} articles. Done!")
    
    def process_wikipedia_sample(self, sample_size: int = 10000, use_real_data: bool = True) -> None:
        """Process Wikipedia articles for word frequencies."""
        print(f"Processing Wikipedia sample ({sample_size:,} articles)...")
        
        if not use_real_data:
            print("Using demo data instead of real Wikipedia dump.")
            self._create_demo_data()
            return
        
        # Download and process real Wikipedia data
        dump_path = self.download_wikipedia_dump()
        
        if dump_path:
            try:
                self.parse_wikipedia_xml(dump_path, sample_size)
            finally:
                # Clean up downloaded file
                os.unlink(dump_path)
        else:
            print("Failed to download Wikipedia dump, using demo data...")
            self._create_demo_data()

    def _create_demo_data(self) -> None:
        """Create demo frequency data for testing."""
        print("Creating demo frequency data...")

        # Simulate realistic English word frequencies
        common_words = ["the", "be", "to", "of", "and", "a", "in", "that", "have", "it"]
        frequent_words = [
            "for",
            "not",
            "on",
            "with",
            "he",
            "as",
            "you",
            "do",
            "at",
            "this",
        ]
        average_words = [
            "from",
            "they",
            "we",
            "say",
            "her",
            "she",
            "or",
            "an",
            "will",
            "my",
        ]
        rare_words = [
            "about",
            "out",
            "many",
            "time",
            "very",
            "when",
            "come",
            "here",
            "how",
            "just",
        ]
        very_rare_words = [
            "serendipity",
            "perspicacious",
            "ephemeral",
            "quintessential",
            "ubiquitous",
        ]

        # Assign realistic frequencies
        for word in common_words:
            self.word_counts[word] = 10000
        for word in frequent_words:
            self.word_counts[word] = 5000
        for word in average_words:
            self.word_counts[word] = 1000
        for word in rare_words:
            self.word_counts[word] = 100
        for word in very_rare_words:
            self.word_counts[word] = 10

    def categorize_frequency(
        self, rank: int, total_unique_words: int
    ) -> Tuple[int, str]:
        """Convert rank to 0-4 scale with labels. Most words will be very_rare (4)."""
        percentile = rank / total_unique_words

        if percentile <= 0.01:
            return 0, "very_frequent"
        elif percentile <= 0.05:
            return 1, "frequent"
        elif percentile <= 0.20:
            return 2, "average"
        elif percentile <= 0.50:
            return 3, "rare"
        else:
            return 4, "very_rare"

    def generate_frequency_data(self) -> Dict[str, Dict]:
        """Generate final frequency mapping."""
        print("Generating frequency data...")

        # Filter by minimum count
        filtered_counts = {
            word: count
            for word, count in self.word_counts.items()
            if count >= self.min_count
        }

        # Sort by frequency (most frequent first)
        sorted_words = sorted(filtered_counts.items(), key=lambda x: x[1], reverse=True)

        total_words = sum(filtered_counts.values())
        total_unique = len(filtered_counts)

        print(f"Total words processed: {total_words:,}")
        print(f"Unique words (min count {self.min_count}): {total_unique:,}")

        # Create frequency mapping
        frequency_data = {}

        for rank, (word, count) in enumerate(sorted_words, 1):
            percentage = (count / total_words) * 100
            category_num, category_label = self.categorize_frequency(rank, total_unique)

            frequency_data[word] = {
                "count": count,
                "percentage": round(percentage, 6),
                "rank": rank,
                "category": category_num,
                "category_label": category_label,
            }

        return frequency_data

    def save_results(self, data: Dict, output_file: str) -> None:
        """Save frequency data to JSON file."""
        output_path = Path(output_file)

        # Create metadata
        total_words = sum(item["count"] for item in data.values())
        metadata = {
            "total_words_processed": total_words,
            "unique_words": len(data),
            "min_count_threshold": self.min_count,
            "categories": {
                0: "very_frequent (top 1%)",
                1: "frequent (top 5%)",
                2: "average (top 20%)",
                3: "rare (top 50%)",
                4: "very_rare (bottom 50%)",
            },
            "sources": ["wikipedia_sample"],
            "note": "Frequency percentages are relative to this corpus",
        }

        output_data = {"metadata": metadata, "words": data}

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"Frequency data saved to: {output_path}")
        print(f"Total unique words: {len(data):,}")

        # Show sample of each category
        by_category = {}
        for word, info in data.items():
            cat = info["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(word)

        print("\nSample words by category:")
        for cat in sorted(by_category.keys()):
            sample = by_category[cat][:5]
            cat_label = metadata["categories"][cat]
            print(f"  {cat} ({cat_label}): {', '.join(sample)}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate word frequency data from open sources"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="word_frequencies.json",
        help="Output JSON file (default: word_frequencies.json)",
    )
    parser.add_argument(
        "--min-count",
        "-m",
        type=int,
        default=5,
        help="Minimum word count to include (default: 5)",
    )
    parser.add_argument(
        "--sample-size",
        "-s",
        type=int,
        default=10000,
        help="Number of Wikipedia articles to process (default: 10000)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use demo data instead of downloading real Wikipedia dump",
    )

    args = parser.parse_args()

    print("Frequency Analyzer - Generating word frequency data")
    print("=" * 60)

    analyzer = FrequencyAnalyzer(min_count=args.min_count)

    # Process data sources
    analyzer.process_wikipedia_sample(args.sample_size, use_real_data=not args.demo)

    # Generate frequency mappings
    frequency_data = analyzer.generate_frequency_data()

    # Save results
    analyzer.save_results(frequency_data, args.output)

    print(f"\nDone! Use the frequency data in your dictionary by loading:")
    print(f"  {args.output}")


if __name__ == "__main__":
    main()
