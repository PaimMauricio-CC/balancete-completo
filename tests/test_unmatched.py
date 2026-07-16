import unittest

import pandas as pd

from main import find_unmatched_records


class UnmatchedRecordsTests(unittest.TestCase):
    def test_keeps_zero_balance_betha_rows_and_tce_rows(self):
        betha = pd.DataFrame([
            {"Máscara Normalizada": "1.1", "Conta Corrente": "A", "Saldo_atual_Betha": 10.0},
            {"Máscara Normalizada": "2.2", "Conta Corrente": "B", "Saldo_atual_Betha": 0.0},
        ])
        tce = pd.DataFrame([
            {"Máscara Normalizada": "1.1", "Conta Corrente": "A", "Saldo_atual_TCE": 10.0},
            {"Máscara Normalizada": "3.3", "Conta Corrente": "C", "Saldo_atual_TCE": 0.0},
        ])

        unmatched_betha, unmatched_tce = find_unmatched_records(betha, tce)

        self.assertEqual(unmatched_betha["Conta Corrente"].tolist(), ["B"])
        self.assertEqual(unmatched_betha["Saldo_atual_Betha"].tolist(), [0.0])
        self.assertEqual(unmatched_tce["Conta Corrente"].tolist(), ["C"])


if __name__ == "__main__":
    unittest.main()
