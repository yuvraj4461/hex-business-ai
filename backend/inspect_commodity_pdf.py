from pathlib import Path

import pymupdf


DATA_DIR = (
    Path(__file__).parent
    / "data"
)


# Find all PDFs inside the data folder.
pdf_files = list(
    DATA_DIR.glob("*.pdf")
)


print("PDF files found:")

for pdf in pdf_files:
    print(" -", pdf.name)


if not pdf_files:
    raise FileNotFoundError(
        f"No PDF files found in: {DATA_DIR}"
    )


# Prefer a World Bank / CMO PDF.
preferred = [
    pdf
    for pdf in pdf_files
    if (
        "CMO" in pdf.name.upper()
        or "WORLD_BANK" in pdf.name.upper()
    )
]


if preferred:
    PDF_PATH = preferred[0]
else:
    PDF_PATH = pdf_files[0]


print(
    "\nUsing PDF:",
    PDF_PATH.name,
)


document = pymupdf.open(
    PDF_PATH
)


print(
    "Number of pages:",
    len(document),
)


for page_number, page in enumerate(
    document
):

    print(
        f"\n===== PAGE {page_number + 1} =====\n"
    )

    text = page.get_text()

    print(
        text[:5000]
    )