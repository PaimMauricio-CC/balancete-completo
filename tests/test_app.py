from io import BytesIO
import unittest

from app import app
from tests.xml_samples import reference_files


class IncomeReportRouteTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_income_report_upload_renders_consolidated_values(self):
        uploads = [
            (BytesIO(content), name)
            for name, content in reference_files()
        ]
        response = self.client.post(
            "/",
            data={"conferidor_type": "informe", "xmlFiles": uploads},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("R$ 36.426,60".encode(), response.data)
        self.assertIn("R$ 1.313,60".encode(), response.data)
        self.assertIn("R$ 3.543,24".encode(), response.data)
        self.assertIn("123.456.789-09".encode(), response.data)

    def test_income_report_requires_xml(self):
        response = self.client.post(
            "/",
            data={"conferidor_type": "informe"},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Selecione ao menos um XML eSocial".encode(), response.data)


if __name__ == "__main__":
    unittest.main()
