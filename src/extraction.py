import PyPDF2
import openpyxl

def extract_pdf_text(pdf_path, password=None):
    """
    Extracts text from all pages of a (possibly encrypted) PDF file.
    Returns the full text as a string.
    """
    pdf_text = ""
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # Handle encrypted files
        if pdf_reader.is_encrypted:
            if password:
                try:
                    pdf_reader.decrypt(password)
                except Exception as e:
                    raise Exception("🔒 Failed to decrypt PDF: " + str(e))
            else:
                raise Exception("🔐 PDF is encrypted but no password was provided.")

        # Loop through all pages
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                pdf_text += text + "\n"

    return pdf_text

def write_to_excel(data, excel_path):
    """
    Writes extracted PDF text to an Excel file.
    Each line becomes a row in column A of the Excel sheet.
    """
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "PDF Data"

    lines = data.strip().split("\n")
    for i, line in enumerate(lines, start=1):
        sheet[f"A{i}"] = line

    workbook.save(excel_path)
    print(f"✅ Data written to Excel: {excel_path}")

