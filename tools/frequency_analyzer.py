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
                print(
                    f"Warning: File size ({size_mb:.1f} MB) exceeds limit ({max_size_mb} MB)"
                )
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
            with bz2.open(xml_path, "rt", encoding="utf-8") as file:
                # Parse XML incrementally to handle large files
                context = ET.iterparse(file, events=("start", "end"))
                context = iter(context)
                event, root = next(context)

                current_title = ""
                current_text = ""
                in_page = False

                for event, elem in context:
                    if event == "start":
                        if elem.tag.endswith("page"):
                            in_page = True
                        elif elem.tag.endswith("title") and in_page:
                            current_title = ""
                        elif elem.tag.endswith("text") and in_page:
                            current_text = ""

                    elif event == "end":
                        if elem.tag.endswith("title") and in_page:
                            current_title = elem.text or ""
                        elif elem.tag.endswith("text") and in_page:
                            current_text = elem.text or ""
                        elif elem.tag.endswith("page") and in_page:
                            # Process this article
                            if current_text and not current_title.startswith(
                                ("File:", "Category:", "Template:", "Wikipedia:")
                            ):
                                cleaned = self.clean_text(current_text)
                                words = self.extract_words(cleaned)
                                self.word_counts.update(words)

                                articles_processed += 1
                                if articles_processed % 1000 == 0:
                                    print(
                                        f"  Processed {articles_processed:,} articles...",
                                        end="\r",
                                    )

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

    def download_opensubtitles(self, max_files: int = 100) -> str:
        """Download OpenSubtitles corpus for conversational English."""
        print("Downloading OpenSubtitles corpus...")

        # OpenSubtitles provides subtitle files - use a subset for efficiency
        # This is a sample URL - in practice you'd use their API or bulk downloads
        base_url = "https://object.pouta.csc.fi/OPUS-OpenSubtitles/v2018/mono/en.txt.gz"

        temp_fd, temp_path = tempfile.mkstemp(suffix=".txt.gz")
        os.close(temp_fd)

        try:
            print(f"Downloading OpenSubtitles from: {base_url}")
            urllib.request.urlretrieve(base_url, temp_path)

            size_mb = os.path.getsize(temp_path) / (1024 * 1024)
            print(f"Downloaded {size_mb:.1f} MB")

            return temp_path

        except Exception as e:
            print(f"OpenSubtitles download failed: {e}")
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return None

    def parse_opensubtitles(self, gz_path: str, max_lines: int = 100000) -> None:
        """Parse OpenSubtitles text file for conversational word frequencies."""
        print(f"Parsing OpenSubtitles (max {max_lines:,} lines)...")

        lines_processed = 0

        try:
            with gzip.open(gz_path, "rt", encoding="utf-8") as file:
                for line in file:
                    if lines_processed >= max_lines:
                        break

                    # Clean subtitle text (remove timestamps, formatting)
                    line = re.sub(r"\d{2}:\d{2}:\d{2}", "", line)  # Remove timestamps
                    line = re.sub(r"<[^>]+>", "", line)  # Remove HTML tags
                    line = re.sub(r"\[.*?\]", "", line)  # Remove [sound effects]

                    if line.strip():
                        cleaned = self.clean_text(line)
                        words = self.extract_words(cleaned)
                        self.word_counts.update(words)

                        lines_processed += 1
                        if lines_processed % 10000 == 0:
                            print(
                                f"  Processed {lines_processed:,} subtitle lines...",
                                end="\r",
                            )

        except Exception as e:
            print(f"\nError parsing OpenSubtitles: {e}")
            return

        print(f"\n  Processed {lines_processed:,} subtitle lines. Done!")

    def download_news_corpus(self) -> str:
        """Download news corpus for formal/journalistic English."""
        print("Downloading news corpus...")

        # WMT news datasets are freely available
        news_url = (
            "http://data.statmt.org/news-crawl/en/news.2023.en.shuffled.deduped.gz"
        )

        temp_fd, temp_path = tempfile.mkstemp(suffix=".news.gz")
        os.close(temp_fd)

        try:
            print(f"Downloading news data from: {news_url}")
            urllib.request.urlretrieve(news_url, temp_path)

            size_mb = os.path.getsize(temp_path) / (1024 * 1024)
            print(f"Downloaded {size_mb:.1f} MB")

            return temp_path

        except Exception as e:
            print(f"News corpus download failed: {e}")
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return None

    def parse_news_corpus(self, gz_path: str, max_lines: int = 50000) -> None:
        """Parse news corpus for journalistic word frequencies."""
        print(f"Parsing news corpus (max {max_lines:,} lines)...")

        lines_processed = 0

        try:
            with gzip.open(gz_path, "rt", encoding="utf-8") as file:
                for line in file:
                    if lines_processed >= max_lines:
                        break

                    if line.strip():
                        cleaned = self.clean_text(line)
                        words = self.extract_words(cleaned)
                        self.word_counts.update(words)

                        lines_processed += 1
                        if lines_processed % 5000 == 0:
                            print(
                                f"  Processed {lines_processed:,} news lines...",
                                end="\r",
                            )

        except Exception as e:
            print(f"\nError parsing news corpus: {e}")
            return

        print(f"\n  Processed {lines_processed:,} news lines. Done!")

    def process_multiple_corpora(
        self,
        wiki_articles: int = 5000,
        subtitle_lines: int = 100000,
        news_lines: int = 50000,
        use_real_data: bool = True,
    ) -> None:
        """Process multiple corpora for comprehensive frequency analysis."""
        print("Processing multiple corpora for comprehensive frequency analysis...")
        print("=" * 60)

        if not use_real_data:
            print("Using demo data instead of real corpora.")
            self._create_demo_data()
            return

        sources_used = []

        # 1. Wikipedia (formal/encyclopedic)
        if wiki_articles > 0:
            print("\n1. Processing Wikipedia (formal/encyclopedic text)...")
            dump_path = self.download_wikipedia_dump()
            if dump_path:
                try:
                    self.parse_wikipedia_xml(dump_path, wiki_articles)
                    sources_used.append("wikipedia")
                finally:
                    os.unlink(dump_path)
            else:
                print("Wikipedia processing failed, continuing with other sources...")

        # 2. OpenSubtitles (conversational)
        if subtitle_lines > 0:
            print("\n2. Processing OpenSubtitles (conversational text)...")
            subtitles_path = self.download_opensubtitles()
            if subtitles_path:
                try:
                    self.parse_opensubtitles(subtitles_path, subtitle_lines)
                    sources_used.append("opensubtitles")
                finally:
                    os.unlink(subtitles_path)
            else:
                print(
                    "OpenSubtitles processing failed, continuing with other sources..."
                )

        # 3. News corpus (journalistic)
        if news_lines > 0:
            print("\n3. Processing news corpus (journalistic text)...")
            news_path = self.download_news_corpus()
            if news_path:
                try:
                    self.parse_news_corpus(news_path, news_lines)
                    sources_used.append("news")
                finally:
                    os.unlink(news_path)
            else:
                print("News corpus processing failed, continuing with other sources...")

        # Fallback to demo if no sources worked
        if not sources_used:
            print("\nAll corpus downloads failed, using demo data...")
            self._create_demo_data()
            sources_used = ["demo"]

        # Store sources for metadata
        self._sources_used = sources_used

        print(f"\nCompleted processing. Sources used: {', '.join(sources_used)}")

    def process_wikipedia_sample(
        self, sample_size: int = 10000, use_real_data: bool = True
    ) -> None:
        """Process Wikipedia articles for word frequencies. (Legacy method - use process_multiple_corpora instead)"""
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
                self._sources_used = ["wikipedia"]
            finally:
                # Clean up downloaded file
                os.unlink(dump_path)
        else:
            print("Failed to download Wikipedia dump, using demo data...")
            self._create_demo_data()
            self._sources_used = ["demo"]

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

        # Store for metadata
        self._total_words = total_words

        # Create frequency mapping
        frequency_data = {}

        for rank, (word, count) in enumerate(sorted_words, 1):
            percentage = (count / total_words) * 100
            category_num, category_label = self.categorize_frequency(rank, total_unique)

            frequency_data[word] = {
                "percentage": round(percentage, 6),
                "category": category_num,
            }

        return frequency_data

    def save_results(self, data: Dict, output_file: str) -> None:
        """Save frequency data to JSON file."""
        output_path = Path(output_file)

        # Create metadata
        total_words = getattr(self, "_total_words", 0)
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
            "sources": getattr(self, "_sources_used", ["unknown"]),
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
        "--wiki-articles",
        "-w",
        type=int,
        default=3000,
        help="Number of Wikipedia articles to process (default: 3000)",
    )
    parser.add_argument(
        "--subtitle-lines",
        "-sub",
        type=int,
        default=50000,
        help="Number of subtitle lines to process (default: 50000)",
    )
    parser.add_argument(
        "--news-lines",
        "-news",
        type=int,
        default=25000,
        help="Number of news lines to process (default: 25000)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use demo data instead of downloading real corpora",
    )
    parser.add_argument(
        "--wikipedia-only",
        action="store_true",
        help="Use only Wikipedia (legacy mode)",
    )

    args = parser.parse_args()

    print("Frequency Analyzer - Generating word frequency data")
    print("=" * 60)

    analyzer = FrequencyAnalyzer(min_count=args.min_count)

    # Process data sources
    if args.wikipedia_only:
        # Legacy Wikipedia-only mode
        analyzer.process_wikipedia_sample(
            args.wiki_articles, use_real_data=not args.demo
        )
    else:
        # Multi-corpus mode for comprehensive coverage
        analyzer.process_multiple_corpora(
            wiki_articles=args.wiki_articles,
            subtitle_lines=args.subtitle_lines,
            news_lines=args.news_lines,
            use_real_data=not args.demo,
        )

    # Generate frequency mappings
    frequency_data = analyzer.generate_frequency_data()

    # Save results
    analyzer.save_results(frequency_data, args.output)

    print("\nDone! Use the frequency data in your dictionary by loading:")
    print(f"  {args.output}")


if __name__ == "__main__":
    main()
