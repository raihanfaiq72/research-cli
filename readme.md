# Academic Research Assistant CLI

A modern command-line research assistant for discovering, analyzing, and organizing scholarly literature from legal Open Access sources.

Designed for graduate students, researchers, and software engineering practitioners who need a fast and reproducible workflow for literature review, paper discovery, citation analysis, and research trend exploration.

---

## Features

### Literature Discovery

* Search papers by keyword
* Search by DOI
* Search by author
* Search by institution
* Filter by publication year range
* Rank results by relevance and citation count

### Academic Metadata

Retrieve:

* Title
* Authors
* Journal
* Publisher
* DOI
* Publication Year
* Citation Count
* Abstract
* Open Access Status

### PDF Translation

Translate research papers from any language to English or Indonesian:

```bash
research pdf-translate https://example.com/paper.pdf --to eng,idn
```

Auto-detects original language, extracts text, translates, and saves original + translated PDFs in organized batch folders.

### Open Access PDF Finder

Discover legally available PDFs from:

* OpenAlex
* Unpaywall
* CORE
* arXiv
* Europe PMC
* Institutional Repositories
* Publisher Open Access Sources

### Citation Analysis

Analyze:

* Citation counts
* Influential citations
* Reference counts
* Related papers

### Research Trend Analysis

Visualize publication trends over time:

```text
2019 ████
2020 ███████
2021 ██████████
2022 █████████████
2023 ███████████████
2024 ██████████████████
```

### Reading List Management

* Save papers
* Remove papers
* Export collections
* Organize literature review workflow

### Export Formats

* CSV
* BibTeX
* Markdown

---

## Example Usage

Search papers:

```bash
research search "microservices architecture"
```

Filter by publication year:

```bash
research search "digital agriculture" --year 2020-2026
```

Retrieve paper details:

```bash
research doi 10.xxxx/xxxxx
```

View abstract:

```bash
research abstract 10.xxxx/xxxxx
```

Find Open Access PDF:

```bash
research pdf 10.xxxx/xxxxx
```

Translate PDF (URL or local file):

```bash
research pdf-translate https://example.com/paper.pdf --to eng
research pdf-translate paper.pdf --to eng,idn
```

Find related research:

```bash
research related 10.xxxx/xxxxx
```

Analyze publication trends:

```bash
research trend "software architecture"
```

Save a paper:

```bash
research save 5
```

Export reading list:

```bash
research export bibtex
```

---

## Architecture

The application follows a modular architecture:

```text
CLI Layer
    │
    ▼
Command Layer
    │
    ▼
Service Layer
    │
    ├── OpenAlex
    ├── Crossref
    ├── Unpaywall
    ├── CORE
    ├── Semantic Scholar
    ├── arXiv
    └── Europe PMC
```

---

## Technology Stack

* Python 3.12+
* Typer
* Rich
* Requests / HTTPX
* Pydantic
* Pandas
* PyMuPDF
* langdetect
* deep-translator
* fpdf2
* OpenAlex API
* Crossref API
* Unpaywall API
* Semantic Scholar API
* CORE API

---

## Research Motivation

This project was developed to support academic research workflows, particularly for graduate-level literature reviews in:

* Software Engineering
* Software Architecture
* Microservices
* API-First Development
* Domain-Driven Design
* Digital Agriculture
* Information Systems Integration

The objective is to provide a reproducible, command-line based alternative for discovering and organizing scholarly literature from legal Open Access sources.

---

## License

MIT License

---

## Disclaimer

This project only uses publicly available metadata and legally accessible Open Access resources.

No copyrighted content is bypassed, downloaded, or distributed without permission from the content owner.
