import pdfplumber


def extract_pdf_text(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:  # Überprüfe, ob Text extrahiert wurde
                text += page_text
            else:
                print(f"Kein Text auf Seite {pdf.pages.index(page) + 1}")
    return text
