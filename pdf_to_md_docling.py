import os
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import ImageRefMode

from cleanup_md import clean_text


INPUT_FOLDER = Path("./my_pdfs")
OUTPUT_FOLDER = Path("./output_md_docling")
IMAGE_RESOLUTION_SCALE = 2.0


def build_converter() -> DocumentConverter:
    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
        }
    )


def convert_pdf(converter: DocumentConverter, pdf_path: Path, output_dir: Path) -> None:
    pdf_name = pdf_path.stem
    final_dir = (output_dir / pdf_name).resolve()
    md_existing = final_dir / f"{pdf_name}.md"
    if md_existing.exists():
        print(f"--- Skipping {pdf_path.name} (already converted) ---")
        return
    final_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n--- Converting {pdf_path.name} ---")
    result = converter.convert(str(pdf_path.resolve()))
    doc = result.document

    md_filename = f"{pdf_name}.md"
    artifacts_rel = Path(f"{pdf_name}_artifacts")
    cwd = Path.cwd()
    try:
        os.chdir(final_dir)
        doc.save_as_markdown(
            md_filename,
            artifacts_dir=artifacts_rel,
            image_mode=ImageRefMode.REFERENCED,
        )
    finally:
        os.chdir(cwd)
    md_path = final_dir / md_filename
    raw = md_path.read_text(encoding="utf-8")
    cleaned = clean_text(raw)
    md_path.write_text(cleaned, encoding="utf-8")
    print(f"  saved markdown -> {md_path}")
    print(f"  pages: {len(doc.pages)}, pictures: {len(doc.pictures)}, tables: {len(doc.tables)}")
    print(f"  cleanup: {len(raw.splitlines())} -> {len(cleaned.splitlines())} lines")


def main() -> None:
    INPUT_FOLDER.mkdir(exist_ok=True)
    OUTPUT_FOLDER.mkdir(exist_ok=True)

    pdfs = sorted(p for p in INPUT_FOLDER.iterdir() if p.suffix.lower() == ".pdf")
    if not pdfs:
        print(f"No PDFs found in {INPUT_FOLDER}")
        return

    print(f"Found {len(pdfs)} PDF(s). Output -> {OUTPUT_FOLDER}")
    print("First run will download docling models (a few hundred MB).")

    converter = build_converter()
    for pdf in pdfs:
        try:
            convert_pdf(converter, pdf, OUTPUT_FOLDER)
        except Exception as e:
            print(f"  ERROR while processing {pdf.name}: {e}")

    print(f"\nDone. See {OUTPUT_FOLDER}")


if __name__ == "__main__":
    main()
