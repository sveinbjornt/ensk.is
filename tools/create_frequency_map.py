
import json

def create_frequency_map(input_path, output_path):
    """
    Reads categorized word frequency data and creates a simple
    JSON map of word -> category_id.
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
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

    # Create a simple map of word to its category ID
    frequency_map = {
        word: details.get("category_id")
        for word, details in words_data.items()
        if "category_id" in details
    }

    # Write the simple map to the output file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(frequency_map, f, indent=2, ensure_ascii=False)
        print(f"Successfully created frequency map for {len(frequency_map)} words.")
        print(f"Output written to {output_path}")
    except IOError as e:
        print(f"Error writing to file {output_path}: {e}")

if __name__ == "__main__":
    input_file = "/Users/sveinbjorn/Projects/ensk.is/data/freq/word_frequencies_categorized.json"
    output_file = "/Users/sveinbjorn/Projects/ensk.is/data/freq/word_frequency_map.json"
    create_frequency_map(input_file, output_file)
