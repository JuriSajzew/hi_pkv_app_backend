from django.test import TestCase
import pdfplumber
import PyPDF2

# Create your tests here.


class PdfExtractTestCase(TestCase):
    def test_pdf_text_extraction(self):
        # Pfad zur PDF-Datei
        file_path = r'C:\developer\React_Native\pkv_app_backend\documents\dummy.pdf'
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            extracted_text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                extracted_text += page.extract_text()

        print(extracted_text)

        # Setze den Pfad zu deiner PDF-Datei
        # Ersetze dies mit dem tatsächlichen Pfad zu deiner Datei
        # file_path = r'C:\developer\React_Native\pkv_app_backend\documents\dummy.pdf'
#
        # Öffne die PDF und extrahiere den Text
        # with pdfplumber.open(file_path) as pdf:
        #    extracted_text = ""
        #    for page in pdf.pages:
        #        page_text = page.extract_text()
        #        extracted_text += page_text
#
        # Drucke den extrahierten Text zur Überprüfung
        # print(extracted_text)
#
        # Füge eine einfache Überprüfung hinzu, um sicherzustellen, dass Text extrahiert wurde
        # self.assertTrue(len(extracted_text) > 0,
        #                "Kein Text aus der PDF extrahiert.")
