#!/usr/bin/env python3
"""
PDF 파일들을 병합하고, 각 PDF에 자동으로 북마크를 추가하며,
텍스트를 추출하여 sumy를 이용한 정교한 요약 및 메타데이터 인덱스(JSON, 요약 텍스트)를 생성하는 스크립트입니다.
"""

import os
import json
import re
import logging
import argparse
from PyPDF2 import PdfMerger, PdfReader

import nltk
nltk.download('punkt')
nltk.download('punkt_tab')

def setup_logging():
    """로그 설정: 로그 레벨과 포맷을 지정합니다."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


def extract_text_from_pdf(pdf_path: str, max_pages: int = 2) -> str:
    """
    PDF의 처음 몇 페이지에서 텍스트를 추출합니다.
    
    Args:
        pdf_path (str): PDF 파일 경로.
        max_pages (int): 추출할 최대 페이지 수.
        
    Returns:
        str: 추출된 텍스트 (여러 공백은 하나의 공백으로 정리됨).
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages[:max_pages]:
            page_text = page.extract_text() or ""
            text += page_text
        # 여러 공백을 하나로 정리
        return re.sub(r"\s+", " ", text.strip())
    except Exception as e:
        logging.error(f"Failed to extract text from {pdf_path}: {e}")
        return ""


def generate_summary(text: str, sentence_count: int = 3) -> str:
    """
    sumy 라이브러리의 LexRankSummarizer를 사용하여 입력 텍스트에서 요약을 생성합니다.
    텍스트의 길이가 충분하지 않거나 요약이 생성되지 않으면 기본적으로 처음 300자를 반환합니다.
    
    Args:
        text (str): 요약할 텍스트.
        sentence_count (int): 반환할 요약 문장의 수. 기본값은 3.
    
    Returns:
        str: 생성된 요약 텍스트.
    """
    try:
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.summarizers.lex_rank import LexRankSummarizer

        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LexRankSummarizer()
        summary = summarizer(parser.document, sentence_count)
        summary_text = " ".join(str(sentence) for sentence in summary)
        return summary_text if summary_text.strip() else text[:300]
    except Exception as e:
        logging.error(f"Summary generation failed using sumy: {e}. Falling back to basic extraction.")
        return text[:300]


def merge_pdfs_with_bookmarks(input_dir: str, output_path: str, max_pages: int = 2, recursive: bool = False, summary_sentence_count: int = 3) -> None:
    """
    입력 디렉토리 내의 PDF 파일들을 병합하여, 각 PDF에 북마크를 추가하고,
    sumy를 이용해 정교한 요약 및 메타데이터(JSON, 텍스트 요약)를 생성합니다.
    
    Args:
        input_dir (str): PDF 파일들이 위치한 폴더 경로.
        output_path (str): 병합된 PDF 파일의 출력 경로.
        max_pages (int): 요약 생성을 위해 텍스트 추출 시 읽을 최대 페이지 수.
        recursive (bool): 하위 디렉토리까지 재귀적으로 탐색할지 여부.
        summary_sentence_count (int): 요약에 사용할 문장 수.
    """
    merger = PdfMerger()

    # 대소문자 구분 없이 PDF 파일 수집 (재귀적 검색 옵션 제공)
    pdf_files = []
    if recursive:
        for root, _, files in os.walk(input_dir):
            for f in files:
                if f.lower().endswith(".pdf"):
                    pdf_files.append(os.path.join(root, f))
        pdf_files = sorted(pdf_files)
    else:
        pdf_files = sorted(
            [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
        )

    if not pdf_files:
        logging.warning("No PDF files found in the specified input directory.")
        return

    # 출력 디렉토리 및 메타데이터 파일 경로 설정 (output 폴더 내)
    output_dir = os.path.dirname(output_path)
    index_json_path = os.path.join(output_dir, "summary_index.json")
    summary_path = os.path.join(output_dir, "summary.txt")

    # 기존 인덱스 데이터 로드 (존재할 경우)
    existing_json = []
    if os.path.exists(index_json_path):
        try:
            with open(index_json_path, "r", encoding="utf-8") as jf:
                existing_json = json.load(jf)
        except Exception as e:
            logging.error(f"Failed to load existing JSON index from {index_json_path}: {e}")

    existing_filenames = {item.get("filename") for item in existing_json}
    summary_lines = []

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        if filename in existing_filenames:
            logging.info(f"Skipped (duplicate): {filename}")
            continue

        bookmark_title = os.path.splitext(filename)[0]
        try:
            merger.append(pdf_path, outline_item=bookmark_title)
            logging.info(f"Added: {filename} with bookmark '{bookmark_title}'")
        except Exception as e:
            logging.error(f"Error adding {filename} to merger: {e}")
            continue

        extracted_text = extract_text_from_pdf(pdf_path, max_pages)
        refined_summary = generate_summary(extracted_text, summary_sentence_count)
        summary_lines.append(f"{bookmark_title}\n- {refined_summary}\n")

        # 메타데이터 JSON 업데이트 (파일 이름, 북마크, 요약 포함)
        existing_json.append({
            "filename": filename,
            "bookmark": bookmark_title,
            "summary": refined_summary
        })

    os.makedirs(output_dir, exist_ok=True)

    # 요약 텍스트 파일에 요약 내용 추가
    try:
        with open(summary_path, "a", encoding="utf-8") as summary_file:
            summary_file.write("\n".join(summary_lines) + "\n")
        logging.info(f"Summary updated: {summary_path}")
    except Exception as e:
        logging.error(f"Failed to update summary.txt: {e}")

    # JSON 인덱스 파일 업데이트
    try:
        with open(index_json_path, "w", encoding="utf-8") as json_file:
            json.dump(existing_json, json_file, indent=2, ensure_ascii=False)
        logging.info(f"Index JSON updated: {index_json_path}")
    except Exception as e:
        logging.error(f"Failed to write JSON index: {e}")

    # 병합된 PDF 저장
    try:
        with open(output_path, "wb") as fout:
            merger.write(fout)
        logging.info(f"Merged PDF saved to: {output_path}")
    except Exception as e:
        logging.error(f"Failed to write merged PDF to {output_path}: {e}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge PDFs with bookmarks, enhanced summaries (using sumy), and metadata."
    )
    parser.add_argument("--input", required=True, help="Path to folder with PDF files")
    parser.add_argument("--output", default="merged_output.pdf", help="Output PDF filename")
    parser.add_argument("--pages", type=int, default=2, help="Max number of pages to extract text for summaries")
    parser.add_argument("--recursive", action="store_true", help="Recursively search for PDF files in subdirectories")
    parser.add_argument("--summary_sentences", type=int, default=3, help="Number of sentences for summary (default: 3)")
    return parser.parse_args()


def main():
    setup_logging()
    args = parse_arguments()

    # 출력 파일 경로가 절대 경로가 아니면 output 폴더 내에 저장
    if not os.path.isabs(args.output):
        args.output = os.path.join("output", args.output)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    merge_pdfs_with_bookmarks(
        args.input,
        args.output,
        max_pages=args.pages,
        recursive=args.recursive,
        summary_sentence_count=args.summary_sentences
    )


if __name__ == "__main__":
    main()
