#!/usr/bin/env python3
"""
PDF 병합 및 요약 생성 스크립트

기능:
 1. PDF 병합 및 북마크 추가
 2. 텍스트 추출 및 요약 메타데이터 생성 (JSON, summary.txt)

옵션:
 --input             PDF 폴더 경로 (필수)
 --output            출력 PDF 파일 경로 (기본: output/merged.pdf)
 --recursive         하위 디렉토리 재귀 탐색
 --summary_length    요약 텍스트 길이 (문자 수, 기본: 300)
 --verbose           디버그 로그 활성화
"""

import os
import sys
import json
import re
import logging
import argparse
from PyPDF2 import PdfMerger, PdfReader
import nltk

# NLTK punkt tokenizer 설치
nltk.download('punkt', quiet=True)

# 진행 상태 표시 (tqdm 사용 가능)
try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda iterable, **kwargs: iterable


def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF 전체에서 텍스트를 추출합니다."""
    try:
        reader = PdfReader(pdf_path)
        texts = [page.extract_text() or '' for page in reader.pages]
        combined = "\n".join(texts)
        return re.sub(r"\s+", " ", combined).strip()
    except Exception as e:
        logging.error(f"텍스트 추출 실패 ({pdf_path}): {e}")
        return ''


def find_pdfs(input_dir: str, recursive: bool) -> list:
    """PDF 파일 목록을 반환합니다."""
    pdfs = []
    if recursive:
        for root, _, files in os.walk(input_dir):
            for name in files:
                if name.lower().endswith('.pdf'):
                    pdfs.append(os.path.join(root, name))
    else:
        for name in os.listdir(input_dir):
            if name.lower().endswith('.pdf'):
                pdfs.append(os.path.join(input_dir, name))
    return sorted(pdfs)


def merge_and_process(args):
    """PDF 병합, 북마크 추가, 요약/메타데이터 생성"""
    if not os.path.isdir(args.input):
        logging.error(f"입력 폴더가 없습니다: {args.input}")
        sys.exit(1)

    pdfs = find_pdfs(args.input, args.recursive)
    total = len(pdfs)
    if total == 0:
        logging.warning("PDF 파일을 찾을 수 없습니다.")
        return
    logging.info(f"총 {total}개 PDF 파일 처리 시작")

    out_dir = os.path.dirname(args.output) or os.getcwd()
    os.makedirs(out_dir, exist_ok=True)

    # 병합 및 북마크 추가
    merger = PdfMerger()
    for pdf in tqdm(pdfs, desc="Merging PDFs"):
        title = os.path.splitext(os.path.basename(pdf))[0]
        merger.append(pdf, outline_item=title)
    try:
        merger.write(args.output)
        logging.info(f"병합 완료: {args.output}")
    except Exception as e:
        logging.error(f"PDF 병합 실패: {e}")
        return
    finally:
        merger.close()

    # 텍스트 추출 및 요약 생성
    summary = {}
    for pdf in tqdm(pdfs, desc="Generating summaries"):
        text = extract_text_from_pdf(pdf)
        summary[os.path.basename(pdf)] = text[:args.summary_length]

    # JSON 인덱스 저장
    idx_path = os.path.join(out_dir, 'summary_index.json')
    try:
        with open(idx_path, 'w', encoding='utf-8') as jf:
            json.dump(summary, jf, ensure_ascii=False, indent=2)
        logging.info(f"Summary index saved: {idx_path}")
    except Exception as e:
        logging.error(f"Summary index 저장 실패: {e}")

    # 요약 텍스트 파일 저장
    txt_path = os.path.join(out_dir, 'summary.txt')
    try:
        with open(txt_path, 'w', encoding='utf-8') as sf:
            for name, snippet in summary.items():
                base = os.path.splitext(name)[0]
                sf.write(f"{base}\n- {snippet}\n\n")
        logging.info(f"Summary text saved: {txt_path}")
    except Exception as e:
        logging.error(f"Summary text 저장 실패: {e}")


def parse_args():
    parser = argparse.ArgumentParser(description="Merge PDFs and generate summaries")
    parser.add_argument('--input', required=True, help='PDF 폴더 경로')
    parser.add_argument('--output', default='output/merged.pdf', help='출력 PDF 경로')
    parser.add_argument('--recursive', action='store_true', help='하위 디렉토리 재귀 탐색')
    parser.add_argument('--summary_length', type=int, default=300, help='요약 길이 (문자 수)')
    parser.add_argument('--verbose', action='store_true', help='디버그 로그 출력')
    return parser.parse_args()


def main():
    args = parse_args()
    setup_logging(args.verbose)
    # 기본 출력 디렉토리 설정
    if not os.path.dirname(args.output):
        args.output = os.path.join('output', args.output)
    merge_and_process(args)


if __name__ == '__main__':
    main()
