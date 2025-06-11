import PyPDF2
import openpyxl

def extract_text_from_pdf(pdf_path, password=None):
    """
    Extracts text from all pages of a PDF.
    Supports encrypted PDFs (if password is provided).
    
    Args:
        pdf_path (str): Path to the PDF file.
        password (str): Optional password for encrypted PDFs.

    Returns:
        str: Concatenated text from all pages.
    """
    full_text = ""

    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)

        # Handle encryption
        if reader.is_encrypted:
            if not password:
                raise ValueError("🔐 PDF is encrypted but no password was provided.")
            try:
                reader.decrypt(password)
            except Exception as e:
                raise ValueError(f"🔒 Failed to decrypt PDF: {e}")

        # Extract text page-by-page
        for i, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            except Exception as e:
                print(f"⚠️ Warning: Failed to extract text from page {i}: {e}")

    return full_text.strip()


def save_text_to_excel(text, output_path):
    """
    Saves each line of extracted text into a new row in Excel column A.

    Args:
        text (str): Full extracted text (line-separated).
        output_path (str): Destination .xlsx file path.
    """
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Extracted PDF Text"

    for i, line in enumerate(text.splitlines(), start=1):
        sheet.cell(row=i, column=1).value = line.strip()

    workbook.save(output_path)
    print(f"✅ Data written to Excel: {output_path}")
