# py-pdf-merger

Python script to merge PDF files, auto-insert bookmarks, generate metadata index, extract text, and summarize content

## 사용 방법

기본 실행

```shell
python main.py --input ./my_pdfs --output my_merged.pdf
```

실행 예제

```shell
python main.py --input ./data/개인정보포털/법령자료 --output 개인정보포털-법령자료-2024.pdf
python main.py --input ./data/개인정보포털/행정규칙 --output 개인정보포털-행정규칙-2024.pdf
python main.py --input ./data/개인정보포털/안내서 --output 개인정보포털-안내서-2024.pdf
python main.py --input ./data/개인정보포털/판례보기 --output 개인정보포털-판례보기-2024.pdf
python main.py --input ./data/공개SW포털 --output 공개SW포털-오픈소스SW-2025.pdf
python main.py --input ./data/한국저작권위원회 --output 한국저작권위원회-저작권-2024.pdf
```

## 개발 환경 설정

파이썬 버전 확인

```shell
pyenv versions
```

파이썬 설치

```shell
pyenv install -l | grep 3.12
pyenv install 3.12.9
```

가상환경 생성 및 활성화

```shell
pyenv virtualenv 3.12.9 py-pdf-merger-3.12.9
pyenv activate py-pdf-merger-3.12.9
pyenv shell py-pdf-merger-3.12.9
```

VSCODE 설정

- Cmd + Shift + P -> Python interpreter 변경

가상환경 버전 고정

```shell
pyenv local py-pdf-merger-3.12.9
```

가상환경 종료 및 삭제

```shell
pyenv deactivate py-pdf-merger-3.12.9
pyenv uninstall py-pdf-merger-3.12.9
```

필수 패키지 설치

```shell
(py-pdf-merger-3.12.9) pip install PyPDF2
(py-pdf-merger-3.12.9) pip freeze > requirements.txt
```
