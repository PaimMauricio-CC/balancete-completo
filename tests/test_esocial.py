from decimal import Decimal
import unittest

from services.esocial import ESocialError, parse_income_report
from tests.xml_samples import esocial_xml, reference_files


class ESocialParserTests(unittest.TestCase):
    def test_consolidates_sample_xmls_to_reference_totals(self):
        report = parse_income_report(reference_files())

        self.assertEqual(report.worker_cpf_formatted, "123.456.789-09")
        self.assertEqual(report.employer_registration_formatted, "CNPJ raiz 12.345.678")
        self.assertEqual(len(report.months), 6)
        self.assertEqual(report.months[0].period_label, "Jan/2026")
        self.assertEqual(report.months[-1].period_label, "Jun/2026")
        self.assertEqual(report.totals["taxable_income"], Decimal("36426.60"))
        self.assertEqual(report.totals["inss"], Decimal("1313.60"))
        self.assertEqual(report.totals["irrf"], Decimal("3543.24"))
        self.assertEqual(report.totals["thirteenth_salary"], Decimal("0.00"))

    def test_deduplicates_same_receipt(self):
        first = reference_files()[0]
        report = parse_income_report([first, first])
        self.assertEqual(len(report.months), 1)
        self.assertEqual(report.source_count, 1)

    def test_rejects_non_esocial_xml(self):
        with self.assertRaisesRegex(ESocialError, "evento não suportado"):
            parse_income_report([("outro.xml", b"<root />")])

    def test_sums_multiple_consolidated_groups_and_keeps_gross_thirteenth(self):
        extra = """<consolidApurMen><CRMen>188901</CRMen><vlrRendTrib>25.00</vlrRendTrib><vlrRendTrib13>300.00</vlrRendTrib13><vlrPrevOficial>2.50</vlrPrevOficial><vlrPrevOficial13>20.00</vlrPrevOficial13><vlrCRMen>1.25</vlrCRMen></consolidApurMen>"""
        report = parse_income_report([("evento.xml", esocial_xml(extra_consolidated=extra))])
        self.assertEqual(report.totals["taxable_income"], Decimal("1025.00"))
        self.assertEqual(report.totals["thirteenth_salary"], Decimal("300.00"))


if __name__ == "__main__":
    unittest.main()
