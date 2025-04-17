#!/usr/bin/env python3
"""
main.py

This script merges PDF files, adds bookmarks, extracts text from each PDF, and generates TextRank summaries (metadata).

Features:
 1. Merge all PDF files in a directory into a single PDF and add bookmarks for each file.
 2. Extract text from each individual PDF to generate summary metadata:
    - Accumulate a JSON index file (filename, bookmark, summary).

Usage:
    python main.py --input <pdf_folder> [options]

Dependencies:
    pip install PyPDF2 sumy nltk tqdm
    # For Korean morphological analysis (optional):
    # pip install konlpy

Options:
    --input            Path to the directory containing PDF files (required)
    --output           Output path for the merged PDF (default: output/merged.pdf)
    --recursive        Recursively search subdirectories
    --num_sentences    Number of sentences for the summary (default: 3)
    --max_chars        Maximum characters for summary input (default: 3000)
    --verbose          Enable detailed logging
"""

import os
import sys
import json
import re
import logging
import argparse
from PyPDF2 import PdfMerger, PdfReader
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
import nltk

# Download NLTK punkt tokenizer quietly
nltk.download('punkt', quiet=True)

# Optional progress bar loader
try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable


def setup_logging(verbose: bool):
    """
    Configure logging level and format based on verbosity flag.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file and return it as a single string.
    """
    try:
        reader = PdfReader(pdf_path)
        pages = [page.extract_text() or '' for page in reader.pages]
        combined = '\n'.join(pages)
        # Normalize whitespace
        return re.sub(r"\s+", ' ', combined).strip()
    except Exception as e:
        logging.error(f"Failed to extract text from {pdf_path}: {e}")
        return ''


def find_pdfs(input_dir: str, recursive: bool) -> list:
    """
    Find all PDF files in the given directory. Optionally search subdirectories.
    """
    pdfs = []
    if recursive:
        for root, _, files in os.walk(input_dir):
            for f in files:
                if f.lower().endswith('.pdf'):
                    pdfs.append(os.path.join(root, f))
    else:
        for f in os.listdir(input_dir):
            if f.lower().endswith('.pdf'):
                pdfs.append(os.path.join(input_dir, f))
    return sorted(pdfs)


def merge_and_process(args):
    """
    Merge all found PDFs into one file, add bookmarks, and generate TextRank summaries for each.
    """
    # Validate input directory
    if not os.path.isdir(args.input):
        logging.error(f"Input directory not found: {args.input}")
        sys.exit(1)

    pdfs = find_pdfs(args.input, args.recursive)
    if not pdfs:
        logging.warning("No PDF files found to process.")
        return
    logging.info(f"Starting to process {len(pdfs)} PDF files...")

    # Ensure output directory exists
    out_dir = os.path.dirname(args.output) or os.getcwd()
    os.makedirs(out_dir, exist_ok=True)

    # Prepare bookmark titles from filenames
    bookmarks = [os.path.splitext(os.path.basename(p))[0] for p in pdfs]

    # Merge PDFs and add bookmarks
    merger = PdfMerger()
    for p, bm in zip(pdfs, bookmarks):
        merger.append(p, outline_item=bm)
    try:
        merger.write(args.output)
        logging.info(f"Merged PDF saved to: {args.output}")
    finally:
        merger.close()

    # Initialize TextRank summarizer
    summarizer = TextRankSummarizer()
    try:
        # Try to use Korean tokenizer if konlpy is installed
        tokenizer = Tokenizer("korean")
    except Exception:
        logging.warning("konlpy not installed: using English tokenizer instead.")
        tokenizer = Tokenizer("english")

    # Generate summary entries for each PDF
    entries = []
    for pdf, bm in zip(pdfs, bookmarks):
        text = extract_text_from_pdf(pdf)
        # Truncate text if it exceeds max_chars
        if args.max_chars > 0 and len(text) > args.max_chars:
            text = text[:args.max_chars]
        if text:
            try:
                parser = PlaintextParser.from_string(text, tokenizer)
                sents = summarizer(parser.document, args.num_sentences)
                summary_text = ' '.join(str(s) for s in sents)
            except Exception as e:
                logging.error(f"Failed to summarize {pdf}: {e}")
                # Fallback to first 200 characters
                summary_text = text[:200]
        else:
            summary_text = ''
        entries.append({
            "filename": os.path.basename(args.output),
            "bookmark": bm,
            "summary": summary_text
        })

    # Append entries to JSON index file
    idx_path = os.path.join(out_dir, 'summary_index.json')
    if os.path.exists(idx_path):
        try:
            with open(idx_path, 'r', encoding='utf-8') as jf:
                existing = json.load(jf)
            combined = existing + entries if isinstance(existing, list) else existing
        except Exception as e:
            logging.warning(f"Failed to read existing JSON index: {e}")
            combined = entries
    else:
        combined = entries

    with open(idx_path, 'w', encoding='utf-8') as jf:
        json.dump(combined, jf, ensure_ascii=False, indent=2)
    logging.info(f"JSON index file updated at: {idx_path}")


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Merge PDFs and summarize individual files.")
    parser.add_argument('--input', required=True, help='Directory of PDF files')
    parser.add_argument('--output', default='output/merged.pdf', help='Path for merged PDF output')
    parser.add_argument('--recursive', action='store_true', help='Search subdirectories recursively')
    parser.add_argument('--num_sentences', type=int, default=3, help='Number of sentences in summary')
    parser.add_argument('--max_chars', type=int, default=3000, help='Maximum characters of text for summarization')
    parser.add_argument('--verbose', action='store_true', help='Enable detailed logging')
    return parser.parse_args()


def main():
    args = parse_args()
    setup_logging(args.verbose)
    # Ensure output path includes directory
    if not os.path.dirname(args.output):
        args.output = os.path.join('output', args.output)
    merge_and_process(args)


if __name__ == '__main__':
    main()
