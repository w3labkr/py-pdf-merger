#!/usr/bin/env python3
"""
pdf_merge_summary.py

A script to merge PDF files, add bookmarks, extract text, and generate summary metadata.

Features:
 1. Merge PDF files in a directory into a single PDF with bookmarks for each file.
 2. Extract text from each PDF and generate summary metadata:
    - JSON index mapping filenames to text snippets.
    - Plain text summary file.

Usage:
    python pdf_merge_summary.py --input <pdf_folder> [options]

Options:
    --input            Path to directory containing PDF files (required).
    --output           Path for the merged PDF (default: output/merged.pdf).
    --recursive        Recursively include PDFs from subdirectories.
    --summary_length   Number of characters to include in each summary snippet (default: 300).
    --verbose          Enable detailed debug logging.
"""

import os
import sys
import json
import re
import logging
import argparse
from PyPDF2 import PdfMerger, PdfReader
import nltk

# Ensure the NLTK punkt tokenizer is available
nltk.download('punkt', quiet=True)

# Optional progress bar
try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        """Fallback progress indicator: returns the original iterable."""
        return iterable


def setup_logging(verbose: bool):
    """
    Configure logging level and format.

    Args:
        verbose (bool): If True, set level to DEBUG; otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract and normalize text content from a PDF file.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: The extracted text with whitespace normalized, or an empty string on error.
    """
    try:
        reader = PdfReader(pdf_path)
        pages = [page.extract_text() or '' for page in reader.pages]
        combined = '\n'.join(pages)
        # Collapse multiple whitespace characters into a single space
        return re.sub(r"\s+", ' ', combined).strip()
    except Exception as e:
        logging.error(f"Failed to extract text from {pdf_path}: {e}")
        return ''


def find_pdfs(input_dir: str, recursive: bool) -> list:
    """
    Discover PDF files in a directory, optionally recursively.

    Args:
        input_dir (str): Directory to search.
        recursive (bool): If True, include subdirectories.

    Returns:
        list: Sorted list of full file paths to PDFs.
    """
    pdfs = []
    if recursive:
        for root, _, files in os.walk(input_dir):
            for fname in files:
                if fname.lower().endswith('.pdf'):
                    pdfs.append(os.path.join(root, fname))
    else:
        for fname in os.listdir(input_dir):
            if fname.lower().endswith('.pdf'):
                pdfs.append(os.path.join(input_dir, fname))
    return sorted(pdfs)


def merge_and_process(args):
    """
    Merge PDFs, add bookmarks, and generate summary metadata.

    Args:
        args: Parsed command-line arguments with attributes:
            input (str): PDF directory.
            output (str): Merged PDF path.
            recursive (bool): Recurse into subdirectories.
            summary_length (int): Number of characters per summary.
            verbose (bool): Enable debug logging.

    Side Effects:
        Creates the merged PDF, a JSON index, and a summary.txt file in the output directory.
    """
    # Validate input directory
    if not os.path.isdir(args.input):
        logging.error(f"Input directory not found: {args.input}")
        sys.exit(1)

    # Discover PDF files
    pdfs = find_pdfs(args.input, args.recursive)
    total = len(pdfs)
    if total == 0:
        logging.warning("No PDF files found to process.")
        return
    logging.info(f"Processing {total} PDF files...")

    # Prepare output directory
    out_dir = os.path.dirname(args.output) or os.getcwd()
    os.makedirs(out_dir, exist_ok=True)

    # Merge files and add bookmarks
    merger = PdfMerger()
    for pdf in tqdm(pdfs, desc="Merging PDFs"):
        bookmark = os.path.splitext(os.path.basename(pdf))[0]
        merger.append(pdf, outline_item=bookmark)
    try:
        merger.write(args.output)
        logging.info(f"Merged PDF saved to: {args.output}")
    except Exception as e:
        logging.error(f"Error writing merged PDF: {e}")
        return
    finally:
        merger.close()

    # Generate summaries
    summary = {}
    for pdf in tqdm(pdfs, desc="Extracting summaries"):
        text = extract_text_from_pdf(pdf)
        summary[os.path.basename(pdf)] = text[:args.summary_length]

    # Write JSON index
    idx_path = os.path.join(out_dir, 'summary_index.json')
    try:
        with open(idx_path, 'w', encoding='utf-8') as jf:
            json.dump(summary, jf, ensure_ascii=False, indent=2)
        logging.info(f"JSON index saved to: {idx_path}")
    except Exception as e:
        logging.error(f"Error saving JSON index: {e}")

    # Write summary text file
    txt_path = os.path.join(out_dir, 'summary.txt')
    try:
        with open(txt_path, 'w', encoding='utf-8') as sf:
            for fname, snippet in summary.items():
                base = os.path.splitext(fname)[0]
                sf.write(f"{base}\n- {snippet}\n\n")
        logging.info(f"Summary text saved to: {txt_path}")
    except Exception as e:
        logging.error(f"Error saving summary text: {e}")


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Contains parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Merge PDFs and generate text summaries."
    )
    parser.add_argument(
        '--input', required=True,
        help='Path to directory containing PDF files.'
    )
    parser.add_argument(
        '--output', default='output/merged.pdf',
        help='File path for the merged PDF output.'
    )
    parser.add_argument(
        '--recursive', action='store_true',
        help='Include PDF files in subdirectories.'
    )
    parser.add_argument(
        '--summary_length', type=int, default=300,
        help='Number of characters to include in each summary snippet.'
    )
    parser.add_argument(
        '--verbose', action='store_true',
        help='Enable debug-level logging.'
    )
    return parser.parse_args()


def main():
    """
    Main entry point: parse arguments, configure logging, and run merge process.
    """
    args = parse_args()
    setup_logging(args.verbose)

    # Ensure output directory exists if only filename is provided
    if not os.path.dirname(args.output):
        args.output = os.path.join('output', args.output)

    merge_and_process(args)


if __name__ == '__main__':
    main()
