# PDF Merge & Summary Script

A command-line tool that merges multiple PDF files into one and generates TextRank-based summary metadata for each individual PDF.

## Features

- **Merge PDFs**: Combine all PDF files in a specified directory into a single PDF and add bookmarks for each original file.
- **Text Extraction**: Extract text content from each PDF file.
- **Summary Metadata Generation**: Perform TextRank summarization on each individual PDF and append the results to a JSON index file (`summary_index.json`).
- **Recursive Search**: Use the `--recursive` option to include PDFs in subdirectories.
- **Configurable Summary Length**: Control the number of sentences in each summary with `--num_sentences` and limit input text length with `--max_chars` (sentence boundaries are considered).
- **Verbose Logging**: Enable debug-level logging with the `--verbose` flag.
- **Language Detection**: Automatically detect the language of the text and use an appropriate tokenizer (requires `langdetect`).
- **Natural Sorting**: PDF files are sorted naturally (e.g., `file2.pdf` comes before `file10.pdf`).

## Requirements

- Python 3.7+
- [PyPDF2](https://pypi.org/project/PyPDF2/)
- [sumy](https://pypi.org/project/sumy/)
- [nltk](https://pypi.org/project/nltk/)
- [langdetect](https://pypi.org/project/langdetect/) (optional, for language detection)
- Optional: [tqdm](https://pypi.org/project/tqdm/) for progress bars
- Recommended for Korean processing: [konlpy](https://pypi.org/project/konlpy/)

> The script will automatically download the NLTK 'punkt' tokenizer if it is not already available.

## Installation

```bash
# Using pyenv to manage Python versions
git clone https://github.com/w3labkr/py-pdf-merger.git
cd py-pdf-merger
pyenv install 3.12.9
pyenv virtualenv 3.12.9 pdf-merge-summary
pyenv local pdf-merge-summary

# Install dependencies and freeze
pip install PyPDF2 sumy nltk tqdm langdetect konlpy
pip freeze > requirements.txt
```

## Usage

Basic usage:

```bash
python main.py --input ./pdf_folder --output merged.pdf
```

With options:

```bash
python main.py \
  --input ./reports \
  --output final_report.pdf \
  --recursive \
  --num_sentences 3 \
  --max_chars 3000 \
  --verbose
```

## Command-Line Options

| Option             | Description                                                   | Default            |
| ------------------ | ------------------------------------------------------------- | ------------------ |
| `--input`          | Path to the directory containing PDF files (required)         | —                  |
| `--output`         | Output path for the merged PDF                                | `output/merged.pdf`|
| `--recursive`      | Include PDFs in subdirectories                                | `False`            |
| `--num_sentences`  | Number of sentences to include in each summary                | `3`                |
| `--max_chars`      | Maximum number of characters to read for summarization (0 = no limit) | `3000`             |
| `--verbose`        | Enable detailed debug logging                                 | `False`            |

## Output

- **Merged PDF**: The combined PDF file written to the path specified by `--output`.
- **summary_index.json**: A cumulative JSON array of summary metadata objects.

### Additional Notes

- **Encrypted PDFs**: The script attempts to decrypt encrypted PDFs using an empty password. If decryption fails, the file will be skipped.
- **Natural Sorting**: PDF files are sorted naturally (e.g., `file2.pdf` comes before `file10.pdf`).
- **Fallback for Summarization**: If summarization fails, the script falls back to the first 200 characters of the text.

## License

This software license under the [MIT License](LICENSE).
