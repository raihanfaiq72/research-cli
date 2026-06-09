# Academic Research Assistant CLI

CLI asisten riset akademik untuk mahasiswa S2 Ilmu Komputer IPB — fokus pada Rekayasa Perangkat Lunak, Software Architecture, Microservices, API-First Development, Digital Agriculture.

Menggunakan **7 sumber Open Access legal**: OpenAlex, Crossref, Unpaywall, CORE, Semantic Scholar, arXiv, Europe PMC.

---

## Daftar Isi

- [Install](#install)
- [Konfigurasi](#konfigurasi)
- [Workflow Cepat](#workflow-cepat)
- [Daftar Perintah](#daftar-perintah)
  - [search](#search--cari-paper)
  - [doi](#doi--detail-paper)
  - [abstract](#abstract--ambil-abstrak)
  - [pdf](#pdf--cari-url-pdf)
  - [download](#download--unduh-pdf)
  - [pdf-translate](#pdf-translate--terjemahkan-pdf)
  - [related](#related--paper-terkait)
  - [trend](#trend--tren-publikasi)
  - [save](#save--simpan-ke-reading-list)
  - [reading-list](#reading-list--lihat-reading-list)
  - [remove](#remove--hapus-dari-reading-list)
  - [export](#export--ke-csv-bibtex-markdown)
- [Sumber Data](#sumber-data)
- [Tips & Troubleshooting](#tips--troubleshooting)

---

## Install

```bash
cd research-cli
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Konfigurasi

Salin `.env.example` ke `.env`:

```bash
cp .env.example .env
```

Isi API key yang diperlukan (opsional — sebagian besar API gratis tanpa key):

| Variabel | Wajib? | Untuk |
|----------|--------|-------|
| `UNPAYWALL_EMAIL` | Opsional | Unpaywall — cari PDF OA |
| `CORE_API_KEY` | Opsional | CORE — cari PDF OA |
| `REQUEST_TIMEOUT` | Opsional | Timeout HTTP (default: 30) |
| `CACHE_ENABLED` | Opsional | Cache hasil query (default: true) |
| `CACHE_TTL` | Opsional | Durasi cache dalam detik (default: 3600) |

> **Catatan:** OpenAlex, Crossref, Semantic Scholar, arXiv, dan Europe PMC **gratis tanpa API key**.

---

## Workflow Cepat

Workflow lengkap: **Cari → Lihat → Simpan → Export**

```bash
# 1. Cari paper
python3 main.py search "microservices architecture" --limit 5

# 2. Lihat detail paper berdasarkan DOI
python3 main.py doi 10.1109/ms.2016.64

# 3. Simpan ke reading list (dari hasil search terakhir)
python3 main.py save 1,2,3

# 4. Lihat reading list
python3 main.py reading-list

# 5. Export ke BibTeX untuk referensi skripsi
python3 main.py export bibtex --output references.bib
```

---

## Daftar Perintah

### `search` — Cari Paper

Mencari paper dari 3 sumber sekaligus: **OpenAlex**, **Semantic Scholar**, **Crossref**. Hasil otomatis di-deduplikasi berdasarkan DOI dan judul.

```bash
# Cari berdasarkan keyword
python3 main.py search "microservices architecture"

# Filter tahun
python3 main.py search "digital agriculture" --year 2020-2026

# Batasi jumlah hasil
python3 main.py search "software architecture" --limit 10

# Urutkan berdasarkan sitasi terbanyak
python3 main.py search "api-first development" --sort citations

# Urutkan berdasarkan tahun terbaru
python3 main.py search "microservices" --sort year

# Kombinasi semua opsi
python3 main.py search "code smell detection" --year 2020-2026 --limit 15 --sort citations
```

**Options:**
| Opsi | Alias | Default | Deskripsi |
|------|-------|---------|-----------|
| `--year` | `-y` | — | Filter rentang tahun, format: `2020-2026` |
| `--limit` | `-l` | `20` | Jumlah hasil maksimal |
| `--sort` | `-s` | `relevance` | Urutan: `relevance`, `citations`, `year` |

**Output:**
```
┏━━┳━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━┓
┃ # ┃ Year ┃ Title                                ┃ Citat… ┃ OA ┃
┡━━╇━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━┩
│ 1 │ 2016 │ Microservices Architecture Enables   │    724 │ ✗ │
│   │      │ DevOps: Migration to a...            │        │   │
│ 2 │ 2025 │ Microservices Architecture           │    249 │ ✗ │
│ 3 │ 2018 │ Contextual understanding of          │    194 │ ✓ │
│   │      │ microservice architecture...         │        │   │
└──┴──────┴──────────────────────────────────────┴────────┴──┘
```

Kolom **OA** (Open Access): ✓ = gratis, ✗ = berbayar/paywall.

---

### `doi` — Detail Paper

Menampilkan metadata lengkap paper berdasarkan DOI. Mencari dari 4 sumber secara bergantian (OpenAlex → Semantic Scholar → Crossref → Europe PMC).

```bash
python3 main.py doi 10.1016/j.njas.2019.100315
```

**Output:**
```
╭────────────────────────── Paper Details ──────────────────────────╮
│                                                                    │
│  Title: A review of social science on digital agriculture...       │
│  Authors: Laurens Klerkx, Emma Jakku, Pierre Labarthe              │
│  Year: 2019                                                        │
│  Journal: NJAS - Wageningen Journal of Life Sciences               │
│  Publisher: Elsevier BV                                            │
│  DOI: https://doi.org/10.1016/j.njas.2019.100315                   │
│  Citations: 1150                                                   │
│  Open Access: Yes                                                  │
│  PDF URL: https://doi.org/10.1016/j.njas.2019.100315               │
│  Source: openalex                                                  │
│                                                                    │
│  Abstract:                                                         │
│  While there is a lot of literature from a natural or technical    │
│  sciences perspective...                                           │
╰────────────────────────────────────────────────────────────────────╯
```

---

### `abstract` — Ambil Abstrak

Menampilkan abstrak paper secara terpisah (full text, tidak dipotong).

```bash
python3 main.py abstract 10.1016/j.njas.2019.100315
```

Mencari dari: OpenAlex → Europe PMC → Semantic Scholar.

---

### `pdf` — Cari URL PDF

Mencari URL PDF Open Access legal dari 4 sumber: Unpaywall, CORE, OpenAlex, arXiv.

```bash
python3 main.py pdf 10.1016/j.njas.2019.100315
```

**Output jika ditemukan:**
```
PDF Sources Found:

  [OpenAlex] https://doi.org/10.1016/j.njas.2019.100315

  (detail paper ditampilkan)
```

**Output jika tidak ditemukan (paywall):**
```
Error: No open access PDF found for DOI '10.1109/ms.2016.64'.
Try checking the paper's repository or contact the authors.
```

---

### `download` — Unduh PDF

Mencari PDF lalu mengunduhnya ke folder lokal.

```bash
# Download ke folder default (downloads/)
python3 main.py download 10.1016/j.njas.2019.100315

# Download ke folder kustom
python3 main.py download 10.1016/j.njas.2019.100315 --output ./pdfs
```

**Alur download:**
1. Cari PDF di arXiv (preprint)
2. Cari PDF di Unpaywall, CORE, OpenAlex
3. Verifikasi URL benar-benar mengarah ke file PDF (cek `content-type`)
4. Download dengan **Rich progress bar**

**Progress bar:**
```
Downloading A_review_of_social_science_on_digital_agriculture_smart_farming_and_agriculture_4_0.pdf
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.2 MB/1.2 MB • 2.3 MB/s • 0:00:01 ✓
PDF saved: downloads/A_review_of_social_science...pdf (1204.5 KB)
```

**Catatan penting:**
- Hanya bekerja untuk paper **Open Access** (✓)
- Paper **paywall** (✗) seperti IEEE, Springer, Elsevier tidak bisa diunduh
- Coba cari preprint di arXiv jika paper asli berbayar
- File disimpan di folder `downloads/` dengan nama dari judul paper

---

### `pdf-translate` — Terjemahkan PDF

Menerjemahkan paper PDF ke bahasa Inggris (`eng`) dan/atau Indonesia (`idn`). Mendukung input dari **URL** maupun **file lokal**. Bahasa asal paper otomatis terdeteksi (mendukung berbagai bahasa).

**Alur kerja:**
1. Ambil PDF (dari URL atau file lokal)
2. Ekstrak teks dari PDF
3. Deteksi bahasa asal secara otomatis
4. Terjemahkan ke bahasa target
5. Simpan original dan hasil terjemahan sebagai PDF + TXT

```bash
# Terjemahkan dari URL ke Inggris
python3 main.py pdf-translate https://example.com/paper.pdf --to eng

# Terjemahkan dari URL ke Indonesia
python3 main.py pdf-translate https://example.com/paper.pdf --to idn

# Terjemahkan ke Inggris dan Indonesia sekaligus
python3 main.py pdf-translate https://example.com/paper.pdf --to eng,idn

# Terjemahkan file lokal
python3 main.py pdf-translate ./paper.pdf --to eng

# Output ke folder kustom
python3 main.py pdf-translate https://example.com/paper.pdf --to eng,idn --output ./my_translations
```

**Options:**
| Opsi | Alias | Default | Deskripsi |
|------|-------|---------|-----------|
| `--to` | `-t` | `eng` | Bahasa target: `eng`, `idn`, atau `eng,idn` |
| `--output` | `-o` | — | Direktori output kustom (default: `pdf_translate_process/`) |

**Struktur Output:**

Setiap batch terjemahan disimpan di folder dengan format `YYYY-MM-DD_HH-MM-SS_nama_file/`:

```
pdf_translate_process/
└── 2026-06-09_14-30-00_journal/
    ├── original_eng.pdf      # Original (jika bahasa Inggris)
    ├── en_spa.pdf            # Terjemahan Inggris (dari Spanish)
    ├── idn_spa.pdf           # Terjemahan Indonesia (dari Spanish)
    ├── en_spa.txt            # Teks terjemahan Inggris
    └── idn_spa.txt           # Teks terjemahan Indonesia
```

> **Catatan:** Terjemahan menggunakan **Google Translate** (via `deep-translator`). Koneksi internet diperlukan. Untuk PDF hasil scan / image-based tidak bisa diekstrak.

---

### `related` — Paper Terkait

Menampilkan paper yang terkait berdasarkan DOI. Menggunakan OpenAlex dan Semantic Scholar.

```bash
# 10 paper terkait (default)
python3 main.py related 10.1016/j.njas.2019.100315

# 15 paper terkait
python3 main.py related 10.1016/j.njas.2019.100315 --limit 15
```

Berguna untuk:
- Menemukan paper tambahan untuk literature review
- Eksplorasi topik penelitian
- Menemukan sitasi yang relevan

---

### `trend` — Tren Publikasi

Menampilkan visualisasi jumlah publikasi per tahun untuk suatu topik. Data dari OpenAlex.

```bash
python3 main.py trend "microservices"
python3 main.py trend "digital agriculture" --start 2020 --end 2026
```

**Output:**
```
╭───────── Research Trend: "microservices" ─────────╮
│                                                     │
│    2020 ███████████ 2578                            │
│    2021 █████████████ 3092                          │
│    2022 █████████████████ 3976                      │
│    2023 █████████████████████████ 5795              │
│    2024 ██████████████████████████████ 6850         │
│                                                     │
╰─────────────────────────────────────────────────────╯
```

**Options:**
| Opsi | Alias | Default | Deskripsi |
|------|-------|---------|-----------|
| `--start` | `-s` | `2019` | Tahun awal |
| `--end` | `-e` | `2026` | Tahun akhir |

---

### `save` — Simpan ke Reading List

Menyimpan paper dari hasil `search` terakhir ke reading list.

```bash
# Cari dulu
python3 main.py search "software architecture" --limit 10

#Simpan berdasarkan nomor urut di tabel hasil search
python3 main.py save 1,2,3

# Simpan nomor 1 sampai 5
python3 main.py save 1,2,3,4,5
```

> **Data disimpan secara persisten** di `data/reading_list.json` — tidak hilang meski CLI ditutup.

---

### `reading-list` — Lihat Reading List

Menampilkan semua paper yang sudah disimpan.

```bash
python3 main.py reading-list
```

Format tabel sama seperti `search`. Paper ditampilkan dengan nomor urut yang bisa digunakan untuk `remove`.

---

### `remove` — Hapus dari Reading List

```bash
python3 main.py remove 1,2
```

Akan meminta konfirmasi sebelum menghapus (`y/n`).

---

### `export` — ke CSV / BibTeX / Markdown

Mengexport semua paper di reading list ke format yang bisa digunakan untuk skripsi / tesis.

```bash
# CSV (bisa dibuka di Excel/Google Sheets)
python3 main.py export csv
python3 main.py export csv --output papers.csv

# BibTeX (untuk LaTeX / Zotero / Mendeley)
python3 main.py export bibtex --output references.bib

# Markdown (bisa langsung di-paste ke laporan)
python3 main.py export markdown --output papers.md
```

**Contoh output BibTeX:**
```bibtex
@article{klerkx2019areviewof,
  title = {A review of social science on digital agriculture...},
  author = {Laurens Klerkx and Emma Jakku and Pierre Labarthe},
  year = {2019},
  journal = {NJAS - Wageningen Journal of Life Sciences},
  publisher = {Elsevier BV},
  doi = {https://doi.org/10.1016/j.njas.2019.100315},
  abstract = {While there is a lot of literature...}
}
```

---

## Sumber Data

| Sumber | API Key | Rate Limit | Biaya |
|--------|---------|------------|-------|
| **OpenAlex** | Tidak perlu | ~100 rb/hari | Gratis |
| **Crossref** | Tidak perlu | 50/detik | Gratis |
| **Semantic Scholar** | Tidak perlu | 100/detik | Gratis |
| **Unpaywall** | Email (daftar) | 100 rb/hari | Gratis |
| **CORE** | API key (daftar) | 500/hari | Gratis |
| **arXiv** | Tidak perlu | Tanpa batas | Gratis |
| **Europe PMC** | Tidak perlu | Tanpa batas | Gratis |

---

## Tips & Troubleshooting

### "No search results available" saat `save`

Hasil search disimpan di `data/last_search.json`. Pastikan sudah menjalankan `search` sebelum `save`:

```bash
python3 main.py search "microservices" --limit 5   # ✅ dulu
python3 main.py save 1,2                            # ✅ baru ini
```

### Paper tidak bisa didownload (paywall)

Paper dari IEEE, Springer, Elsevier biasanya **berbayar**. Solusi:

1. **Akses institusi** — login via perpustakaan IPB
2. **Cari preprint** di arXiv, ResearchGate, atau repository penulis
3. **Coba cari judul yang sama** dengan keyword yang lebih spesifik
4. **Gunakan `related`** untuk menemukan paper OA yang mirip

```bash
# Cari preprint di sumber gratis
python3 main.py search "paper title" --sort year

# Cari paper terkait yang mungkin OA
python3 main.py related 10.1109/ms.2016.64
```

### API timeout / error

```bash
# Periksa koneksi internet
curl -s --max-time 5 https://api.openalex.org

# Perbesar timeout di .env
REQUEST_TIMEOUT=60
```

### Cache

Hasil pencarian di-cache 1 jam di folder `.cache/`. Untuk force refresh:

```bash
rm -rf .cache/
```

### Ingin output lebih cepat

Gunakan `--limit` kecil dulu untuk tes, baru perbesar untuk hasil lengkap:

```bash
python3 main.py search "microservices" --limit 5   # cepet
python3 main.py search "microservices" --limit 50  # lengkap
```
