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
    pip install PyPDF2 sumy nltk tqdm langdetect
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

# Try to import langdetect for language detection
try:
    from langdetect import detect
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False
    logging.warning("langdetect not installed: language detection unavailable")

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
        # Check if PDF is encrypted
        if reader.is_encrypted:
            try:
                # Try with empty password
                reader.decrypt('')
            except:
                logging.error(f"Cannot decrypt PDF: {pdf_path}")
                return ''
        
        pages = [page.extract_text() or '' for page in reader.pages]
        combined = '\n'.join(pages)
        # Normalize whitespace
        return re.sub(r"\s+", ' ', combined).strip()
    except Exception as e:
        logging.error(f"Failed to extract text from {pdf_path}: {e}")
        return ''


def get_pdf_metadata(pdf_path: str) -> dict:
    """
    Extract metadata from PDF file.
    """
    metadata = {
        "title": "",
        "pages": 0
    }
    
    try:
        reader = PdfReader(pdf_path)
        if reader.is_encrypted:
            try:
                reader.decrypt('')
            except:
                return metadata
        
        metadata["pages"] = len(reader.pages)
        
        if reader.metadata:
            if reader.metadata.title:
                metadata["title"] = reader.metadata.title
    except Exception as e:
        logging.error(f"Failed to extract metadata from {pdf_path}: {e}")
    
    return metadata


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
    
    # Sort files naturally (so file10.pdf comes after file2.pdf, not before)
    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]
    
    return sorted(pdfs, key=natural_sort_key)


def sanitize_bookmark_title(title: str, max_length: int = 100) -> str:
    """
    Make sure bookmark title is valid and not too long.
    """
    # Remove or replace characters that might cause issues
    title = re.sub(r'[\\/*?:"<>|]', '-', title)
    
    # Limit length
    if len(title) > max_length:
        title = title[:max_length-3] + "..."
    
    return title


def get_tokenizer_for_language(text: str) -> Tokenizer:
    """
    Detect language and return appropriate tokenizer.
    """
    if not HAS_LANGDETECT or not text:
        return Tokenizer("english")
    
    try:
        lang = detect(text[:min(1000, len(text))])
        if lang == 'ko':
            return Tokenizer("korean")
        elif lang.startswith('zh'):
            return Tokenizer("chinese")
        elif lang == 'ja':
            return Tokenizer("japanese")
        else:
            return Tokenizer("english")
    except:
        return Tokenizer("english")


def summarize_text(text: str, num_sentences: int, max_chars: int) -> str:
    """
    Summarize text using TextRank algorithm.
    """
    if not text:
        return ""
        
    # Truncate text if necessary, but try to keep complete sentences
    if max_chars > 0 and len(text) > max_chars:
        truncated = text[:max_chars]
        # Try to end at a sentence boundary
        last_period = truncated.rfind('.')
        if last_period > max_chars * 0.8:  # Only if we didn't lose too much text
            truncated = truncated[:last_period+1]
        text = truncated
    
    tokenizer = get_tokenizer_for_language(text)
    
    try:
        parser = PlaintextParser.from_string(text, tokenizer)
        summarizer = TextRankSummarizer()
        sents = summarizer(parser.document, num_sentences)
        return ' '.join(str(s) for s in sents)
    except Exception as e:
        logging.error(f"Failed to summarize text: {e}")
        # Fallback to first 200 characters
        return text[:200] + "..."


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
    
    pdf_count = len(pdfs)
    logging.info(f"Starting to process {pdf_count} PDF files...")

    # Ensure output directory exists
    out_dir = os.path.dirname(args.output) or os.getcwd()
    os.makedirs(out_dir, exist_ok=True)

    # Process PDFs with progress bar
    entries = []
    merger = PdfMerger()
    current_page = 0
    
    for pdf_path in tqdm(pdfs, desc="Processing PDFs", unit="file"):
        try:
            # Extract filename for bookmark
            filename = os.path.basename(pdf_path)
            name_without_ext = os.path.splitext(filename)[0]
            
            # Get metadata and sanitize bookmark title
            metadata = get_pdf_metadata(pdf_path)
            
            # Use PDF title as bookmark if available, otherwise use filename
            bookmark_title = metadata["title"] or name_without_ext
            bookmark_title = sanitize_bookmark_title(bookmark_title)
            
            # Extract text for summary
            text = extract_text_from_pdf(pdf_path)
            summary = summarize_text(text, args.num_sentences, args.max_chars)
            
            # Append the PDF with bookmark
            merger.append(pdf_path, outline_item=bookmark_title)
            
            # Create entry for JSON index
            entries.append({
                "bookmark": bookmark_title,
                "page_number": current_page + 1, # 1-based page numbering
                "page_count": metadata["pages"],
                "summary": summary,
                "filename": os.path.basename(args.output)
            })
            
            # Update current page count for next file
            current_page += metadata["pages"]
            
        except Exception as e:
            logging.error(f"Error processing {pdf_path}: {e}")
    
    # Save the merged PDF
    try:
        merger.write(args.output)
        logging.info(f"Merged PDF with {pdf_count} files saved to: {args.output}")
    except Exception as e:
        logging.error(f"Failed to write merged PDF: {e}")
        sys.exit(1)
    finally:
        merger.close()

    # Create or update JSON index file
    idx_path = os.path.join(out_dir, 'summary_index.json')
    existing_entries = []
    
    if os.path.exists(idx_path):
        try:
            with open(idx_path, 'r', encoding='utf-8') as jf:
                data = json.load(jf)
                if isinstance(data, list):
                    existing_entries = data
                else:
                    logging.warning("Existing index file has incorrect format. Creating new index.")
        except Exception as e:
            logging.warning(f"Failed to read existing JSON index: {e}")
    
    # Add merged PDF filename to entries
    for entry in entries:
        entry["filename"] = os.path.basename(args.output)
    
    combined = existing_entries + entries
    
    with open(idx_path, 'w', encoding='utf-8') as jf:
        json.dump(combined, jf, ensure_ascii=False, indent=2)
    logging.info(f"JSON index with {len(entries)} entries updated at: {idx_path}")


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
