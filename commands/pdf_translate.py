import os
import re
import shutil
import time
import httpx
from datetime import datetime
from utils.console import console, show_error, show_message

PDF_TRANSLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "pdf_translate_process"
)

ISO_639_1_TO_3 = {
    "en": "eng",
    "id": "idn",
    "af": "afr",
    "ar": "ara",
    "bg": "bul",
    "bn": "ben",
    "ca": "cat",
    "cs": "ces",
    "da": "dan",
    "de": "deu",
    "el": "ell",
    "es": "spa",
    "et": "est",
    "fa": "fas",
    "fi": "fin",
    "fr": "fra",
    "gu": "guj",
    "he": "heb",
    "hi": "hin",
    "hr": "hrv",
    "hu": "hun",
    "it": "ita",
    "ja": "jpn",
    "kn": "kan",
    "ko": "kor",
    "lt": "lit",
    "lv": "lav",
    "mk": "mkd",
    "ml": "mal",
    "mr": "mar",
    "ne": "nep",
    "nl": "nld",
    "no": "nor",
    "pa": "pan",
    "pl": "pol",
    "pt": "por",
    "ro": "ron",
    "ru": "rus",
    "sk": "slk",
    "sl": "slv",
    "so": "som",
    "sq": "sqi",
    "sr": "srp",
    "sv": "swe",
    "sw": "swa",
    "ta": "tam",
    "te": "tel",
    "th": "tha",
    "tl": "tgl",
    "tr": "tur",
    "uk": "ukr",
    "ur": "urd",
    "vi": "vie",
    "zh-cn": "zho",
    "zh-tw": "zho",
}


def _to_iso_639_3(code_2: str) -> str:
    return ISO_639_1_TO_3.get(code_2.lower(), code_2)


def _detect_language(text: str) -> tuple[str, str]:
    from langdetect import detect, DetectorFactory, LangDetectException
    DetectorFactory.seed = 0
    try:
        lang_2 = detect(text)
        lang_3 = _to_iso_639_3(lang_2)
        return lang_2, lang_3
    except LangDetectException:
        return "unknown", "unknown"


def _translate_chunk(translator, chunk: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            return translator.translate(chunk)
        except Exception as e:
            if attempt < max_retries - 1:
                wait = (attempt + 1) * 2
                time.sleep(wait)
            else:
                raise
    return chunk


def _translate_text(text: str, target_lang_3: str, translator=None, progress=None, task=None) -> str:  # noqa: PLR0913
    from deep_translator import GoogleTranslator

    target_map = {"eng": "en", "idn": "id"}
    target = target_map.get(target_lang_3, target_lang_3)

    if translator is None:
        translator = GoogleTranslator(source="auto", target=target)

    max_chars = 2000
    if len(text) <= max_chars:
        result = _translate_chunk(translator, text)
        if task:
            progress.update(task, completed=len(text))
        return result

    chunks = []
    total_chunks = (len(text) + max_chars - 1) // max_chars
    for i in range(0, len(text), max_chars):
        chunk = text[i : i + max_chars]
        current_chunk = i // max_chars + 1
        pct = min(100, int((i / len(text)) * 100))
        if task:
            progress.update(
                task,
                description=f"Translating chunk {current_chunk}/{total_chunks} ({pct}%)",
            )
        try:
            translated = _translate_chunk(translator, chunk)
            chunks.append(translated)
        except Exception as e:
            show_message(
                f"Translation error chunk {current_chunk}/{total_chunks}: {e}",
                "yellow",
            )
            chunks.append(chunk)
        if task:
            progress.update(task, advance=len(chunk))
        if i + max_chars < len(text) and current_chunk % 10 == 0:
            time.sleep(0.2)

    if task:
        progress.update(
            task,
            description=f"Translated {total_chunks}/{total_chunks} (100%)",
        )
    return "\n".join(chunks)


def _extract_text_from_pdf(pdf_path: str) -> str:
    import fitz
    doc = fitz.open(pdf_path)
    pages_text = []
    for page in doc:
        pages_text.append(page.get_text())
    doc.close()
    return "\n".join(pages_text)


def _get_font_path() -> str | None:
    candidates = [
        "/System/Library/Fonts/Supplemental/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    font_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")
    os.makedirs(font_dir, exist_ok=True)
    font_path = os.path.join(font_dir, "DejaVuSans.ttf")
    if not os.path.exists(font_path):
        show_message("Downloading DejaVuSans font for PDF generation...", "cyan")
        url = "https://github.com/prawnpdf/prawn/raw/refs/heads/master/data/fonts/DejaVuSans.ttf"
        with httpx.Client(follow_redirects=True, timeout=30) as client:
            resp = client.get(url)
            resp.raise_for_status()
            with open(font_path, "wb") as f:
                f.write(resp.content)
    return font_path if os.path.exists(font_path) else None


def _create_pdf_from_text(text: str, output_path: str, title: str = ""):
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    font_path = _get_font_path()
    if font_path:
        pdf.add_font("CustomFont", "", font_path)
        pdf.set_font("CustomFont", "", 11)
    else:
        pdf.set_font("Helvetica", "", 11)
    pdf.set_auto_page_break(auto=True, margin=15)
    if title:
        if font_path:
            pdf.set_font("CustomFont", "", 14)
        else:
            pdf.set_font("Helvetica", "B", 14)
        pdf.multi_cell(0, 8, title)
        pdf.ln(4)
        if font_path:
            pdf.set_font("CustomFont", "", 11)
        else:
            pdf.set_font("Helvetica", "", 11)
    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            pdf.ln(4)
            continue
        try:
            pdf.multi_cell(0, 5.5, paragraph)
            pdf.ln(2)
        except Exception:
            safe = paragraph.encode("ascii", "replace").decode("ascii")
            pdf.multi_cell(0, 5.5, safe)
            pdf.ln(2)
    pdf.output(output_path)


def pdf_translate(
    source: str,
    target_langs: list[str],
    output_dir: str | None = None,
    keep_original: bool = True,
):
    try:
        import fitz  # noqa
    except ImportError:
        show_error("PyMuPDF required. Install: pip install pymupdf")
        return
    try:
        from langdetect import detect  # noqa
    except ImportError:
        show_error("langdetect required. Install: pip install langdetect")
        return
    try:
        from deep_translator import GoogleTranslator  # noqa
    except ImportError:
        show_error("deep-translator required. Install: pip install deep-translator")
        return
    try:
        from fpdf import FPDF  # noqa
    except ImportError:
        show_error("fpdf2 required. Install: pip install fpdf2")
        return

    valid_langs = [l.lower() for l in target_langs if l.lower() in ("eng", "idn")]
    if not valid_langs:
        show_error("At least one target language required: eng, idn")
        return

    is_url = source.startswith(("http://", "https://"))

    if is_url:
        show_message(f"Downloading PDF from: {source}", "cyan")
        temp_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".temp_pdf"
        )
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, "downloaded_pdf.pdf")
        with httpx.Client(follow_redirects=True, timeout=120) as client:
            resp = client.get(source)
            resp.raise_for_status()
            with open(temp_path, "wb") as f:
                f.write(resp.content)
        pdf_path = temp_path
        base_name = os.path.splitext(os.path.basename(source.split("?")[0]))[0]
        if not base_name or base_name == "":
            base_name = "journal"
    else:
        if not os.path.exists(source):
            show_error(f"File not found: {source}")
            return
        pdf_path = source
        base_name = os.path.splitext(os.path.basename(source))[0]

    show_message("Extracting text from PDF...", "cyan")
    text = _extract_text_from_pdf(pdf_path)
    if not text.strip():
        show_error("No text could be extracted. The PDF may be scanned or image-based.")
        if is_url and os.path.exists(pdf_path):
            os.remove(pdf_path)
        return

    show_message("Detecting original language...", "cyan")
    detected_2, detected_3 = _detect_language(text)
    show_message(
        f"Detected language: {detected_2} ({detected_3})",
        "green",
    )

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    sanitized_name = re.sub(r"[^\w\s-]", "", base_name)
    sanitized_name = re.sub(r"[-\s]+", "_", sanitized_name)[:60]

    if output_dir:
        batch_dir = os.path.join(output_dir, f"{timestamp}_{sanitized_name}")
    else:
        batch_dir = os.path.join(PDF_TRANSLATE_DIR, f"{timestamp}_{sanitized_name}")

    os.makedirs(batch_dir, exist_ok=True)

    if keep_original:
        orig_name = f"original_{detected_3}.pdf"
        orig_path = os.path.join(batch_dir, orig_name)
        shutil.copy2(pdf_path, orig_path)
        show_message(f"Saved original: {orig_path}", "green")

    from rich.progress import (
        Progress,
        BarColumn,
        TextColumn,
        TaskProgressColumn,
        TimeRemainingColumn,
        TimeElapsedColumn,
    )

    results = []

    for lang in valid_langs:
        if lang == "eng":
            target_label = "English"
        else:
            target_label = "Indonesian"

        if (detected_2 == "en" and lang == "eng") or (
            detected_2 == "id" and lang == "idn"
        ):
            show_message(
                f"Original already in {target_label}, copying as {lang}_{detected_3}.pdf",
                "yellow",
            )
            out_name = f"{lang}_{detected_3}.pdf"
            out_path = os.path.join(batch_dir, out_name)
            if keep_original:
                shutil.copy2(orig_path, out_path)
            else:
                shutil.copy2(pdf_path, out_path)
            results.append((lang, "skipped (same language)"))
            continue

        # Initialize translator outside progress to avoid hanging the bar
        show_message(f"Initializing {target_label} translator...", "cyan")
        from deep_translator import GoogleTranslator

        target_map = {"eng": "en", "idn": "id"}
        trg = target_map.get(lang, lang)
        try:
            translator = GoogleTranslator(source="auto", target=trg)
        except Exception as e:
            show_message(f"Failed to initialize translator: {e}", "red")
            results.append((lang, "failed"))
            continue

        total_chunks_est = (len(text) + 1999) // 2000
        show_message(
            f"Translating to {target_label}: ~{total_chunks_est} chunks, "
            f"estimated {total_chunks_est * 2}s...",
            "cyan",
        )

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Translating {len(text)} chars...", total=len(text)
            )
            progress.update(task, completed=0)

            try:
                translated = _translate_text(
                    text, lang, translator=translator, progress=progress, task=task
                )
            except Exception as e:
                show_message(f"Translation to {target_label} failed: {e}", "red")
                results.append((lang, "failed"))
                continue

        out_name = f"{lang}_{detected_3}.pdf"
        out_path = os.path.join(batch_dir, out_name)

        title = f"Translated from {detected_3} to {lang}"
        _create_pdf_from_text(translated, out_path, title=title)

        txt_path = os.path.join(batch_dir, f"{lang}_{detected_3}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(translated)

        show_message(f"Saved: {out_path}", "green")
        results.append((lang, "success"))

    if is_url and os.path.exists(pdf_path):
        os.remove(pdf_path)

    success_count = sum(1 for _, s in results if s == "success")
    show_message(
        f"\nDone. {success_count}/{len(valid_langs)} translations saved in: {batch_dir}",
        "bold green",
    )
