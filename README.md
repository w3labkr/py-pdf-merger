# PDF Merge & Summary Script

A command-line tool to merge multiple PDF files into one and generate text summaries with metadata.

## Features

- **Merge PDFs**: Combines all PDF files in a directory into a single PDF, adding bookmarks for each file.
- **Text Extraction**: Extracts text from each PDF.
- **Summary Generation**: Creates a JSON index (`summary_index.json`) mapping filenames to text snippets and a plain text summary (`summary.txt`).
- **Recursive Search**: Optionally include PDFs in subdirectories.
- **Configurable Summary Length**: Control the number of characters in each summary snippet.
- **Verbose Logging**: Enable debug-level logs for detailed progress.

## Requirements

- Python 3.7+
- [PyPDF2](https://pypi.org/project/PyPDF2/)
- [nltk](https://pypi.org/project/nltk/)
- Optional: [tqdm](https://pypi.org/project/tqdm/) for a progress bar

> Note: The script will attempt to download the NLTK 'punkt' tokenizer if not already available.

## Getting Started

1. Clone this repository or copy `pdf_merge_summary.py` into your project.
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install PyPDF2 nltk tqdm
   ```

## Usage

Basic execution:

```shell
python pdf_merge_summary.py --input ./my_pdfs --output my_merged.pdf
```

Example with options:

```shell
python pdf_merge_summary.py \
  --input ./reports \
  --output final_report.pdf \
  --recursive \
  --summary_length 200 \
  --verbose
```

## Development Environment Setup

### Check Python Versions

```bash
pyenv versions
```

### Install Python 3.12.9

```bash
pyenv install -l | grep 3.12
pyenv install 3.12.9
```

### Create and Activate Virtual Environment

```bash
pyenv virtualenv 3.12.9 py-pdf-merger-3.12.9
pyenv activate py-pdf-merger-3.12.9
# Optional: pin the local version for the project
pyenv local py-pdf-merger-3.12.9
```

### VSCode Configuration

- Press `Cmd + Shift + P` and select **Python: Select Interpreter**, then choose `py-pdf-merger-3.12.9`.

### Deactivate and Remove Virtual Environment

```bash
pyenv deactivate
pyenv uninstall py-pdf-merger-3.12.9
```

### Install Required Packages and Freeze Requirements

```bash
pip install PyPDF2 nltk tqdm
pip freeze > requirements.txt
```

## Output Files

- **Merged PDF**: The combined PDF with bookmarks (as specified by `--output`).
- **summary_index.json**: JSON file mapping each original PDF filename to its text snippet.
- **summary.txt**: Plain text file containing filenames and their snippets.

## License

MIT License
