from io import BytesIO
import unittest

from app import app
from tests.xml_samples import reference_files


class IncomeReportRouteTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_home_exposes_three_top_level_sections_and_drop_support(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn('value="contabil"'.encode(), response.data)
        self.assertIn('value="folha"'.encode(), response.data)
        self.assertIn('value="esocial"'.encode(), response.data)
        self.assertIn("new DataTransfer()".encode(), response.data)

    def test_income_report_upload_renders_consolidated_values(self):
        uploads = [
            (BytesIO(content), name)
            for name, content in reference_files()
        ]
        response = self.client.post(
            "/",
            data={"conferidor_type": "esocial", "xmlFiles": uploads},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("R$ 36.426,60".encode(), response.data)
        self.assertIn("R$ 1.313,60".encode(), response.data)
        self.assertIn("R$ 3.543,24".encode(), response.data)
        self.assertIn("123.456.789-09".encode(), response.data)
        self.assertIn("Baixar resumo PDF".encode(), response.data)

        pdf_response = self.client.get("/download/Relatorio_eSocial.pdf")
        self.assertEqual(pdf_response.status_code, 200)
        self.assertTrue(pdf_response.data.startswith(b"%PDF"))
        pdf_response.close()

    def test_income_report_requires_xml(self):
        response = self.client.post(
            "/",
            data={"conferidor_type": "esocial"},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Selecione ao menos um XML eSocial".encode(), response.data)


if __name__ == "__main__":
    unittest.main()
