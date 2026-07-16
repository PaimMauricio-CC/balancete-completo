import unittest

from services.esocial import parse_income_report
from services.pdf_report import build_audit_pdf, build_esocial_pdf
from tests.xml_samples import reference_files


class PdfReportTests(unittest.TestCase):
    def test_esocial_report_is_a_pdf_with_chart_and_table_content(self):
        report = parse_income_report(reference_files())
        content = build_esocial_pdf(report)
        self.assertTrue(content.startswith(b"%PDF"))
        self.assertGreater(len(content), 3000)

    def test_generic_audit_report_supports_zero_value_chart(self):
        content = build_audit_pdf(
            title="Auditoria de teste",
            subtitle="Resumo",
            metrics=[("Somente Betha", 0), ("Somente TCE", 0)],
            chart_items=[("Betha", 0), ("TCE", 0)],
            chart_title="Distribuição",
        )
        self.assertTrue(content.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
