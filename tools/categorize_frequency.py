
import json

def categorize_words(input_path, output_path):
    """
    Reads word frequency data, re-categorizes it based on a 6-tier taxonomy,
    and writes the result to a new file.
    """
    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {input_path}")
        return

    words_data = data.get("words", {})
    if not words_data:
        print("No 'words' key found in the JSON data.")
        return

    # Sort words by percentage, descending
    # Items are (word, {details})
    sorted_words = sorted(
        words_data.items(),
        key=lambda item: item[1].get("percentage", 0),
        reverse=True
    )

    total_word_count = len(sorted_words)
    
    # Define the 6-tier taxonomy based on percentile cutoffs
    taxonomy = {
        "very_frequent": (0, 0.01),      # Top 1%
        "frequent": (0.01, 0.05),        # Next 4% (1-5%)
        "common": (0.05, 0.20),          # Next 15% (5-20%)
        "uncommon": (0.20, 0.50),        # Next 30% (20-50%)
        "rare": (0.50, 0.80),            # Next 30% (50-80%)
        "very_rare": (0.80, 1.0)         # Bottom 20% (80-100%)
    }

    new_words_data = {}
    for i, (word, details) in enumerate(sorted_words):
        percentile = i / total_word_count
        category_name = "unknown"
        for name, (start, end) in taxonomy.items():
            if start <= percentile < end:
                category_name = name
                break
        
        new_details = details.copy()
        new_details["category_name"] = category_name
        # Assign a numeric category for easier sorting/filtering if needed
        new_details["category_id"] = list(taxonomy.keys()).index(category_name)
        new_words_data[word] = new_details

    # Update metadata to reflect the new taxonomy
    new_metadata = data.get("metadata", {}).copy()
    new_metadata["categories"] = {
        i: name for i, name in enumerate(taxonomy.keys())
    }
    
    new_data = {
        "metadata": new_metadata,
        "words": new_words_data
    }

    # Write to the output file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
        print(f"Successfully categorized {total_word_count} words.")
        print(f"Output written to {output_path}")
    except IOError as e:
        print(f"Error writing to file {output_path}: {e}")

if __name__ == "__main__":
    # Note: Using absolute paths for clarity in this context
    input_file = "/Users/sveinbjorn/Projects/ensk.is/data/freq/word_frequencies.json"
    output_file = "/Users/sveinbjorn/Projects/ensk.is/data/freq/word_frequencies_categorized.json"
    categorize_words(input_file, output_file)
