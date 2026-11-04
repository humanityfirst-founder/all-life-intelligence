import csv
import tempfile
import unittest
from pathlib import Path
from auto_qa_v17 import analyse_cases


class OfflineQualityGateTests(unittest.TestCase):
    def _write(self, folder, rows):
        p=Path(folder)/'checks.csv'
        with p.open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=['Test-ID','Szenario-Erwartung','KI-Kontextkategorie','Menschliche Freigabe'],delimiter=';')
            writer.writeheader()
            writer.writerows(rows)
        return p

    def test_counts_pending_separately_from_wrong(self):
        with tempfile.TemporaryDirectory() as folder:
            p=self._write(folder,[
              {'Test-ID':'a','Szenario-Erwartung':'META','KI-Kontextkategorie':'META','Menschliche Freigabe':'OFFEN'},
              {'Test-ID':'b','Szenario-Erwartung':'METHODE','KI-Kontextkategorie':'PAUSCHALE_ABSENZ','Menschliche Freigabe':'OFFEN'},
              {'Test-ID':'c','Szenario-Erwartung':'META','KI-Kontextkategorie':'UNKLAR','Menschliche Freigabe':'OFFEN'},
            ])
            actual=analyse_cases(p)
            self.assertEqual(actual['cases_evaluated'],2)
            self.assertEqual(actual['matches_with_internal_labels'],1)
            self.assertEqual(actual['differences_from_internal_labels'],1)
            self.assertEqual(actual['cases_pending'],1)
            self.assertEqual(actual['human_confirmations_reported'],0)

    def test_duplicate_id_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            p=self._write(folder,[
              {'Test-ID':'x','Szenario-Erwartung':'META','KI-Kontextkategorie':'META','Menschliche Freigabe':'OFFEN'},
              {'Test-ID':'x','Szenario-Erwartung':'META','KI-Kontextkategorie':'META','Menschliche Freigabe':'OFFEN'},
            ])
            with self.assertRaises(ValueError): analyse_cases(p)

    def test_missing_header_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'checks.csv'
            p.write_text('Test-ID;KI-Kontextkategorie\nA;META\n',encoding='utf-8')
            with self.assertRaises(ValueError): analyse_cases(p)

    def test_human_confirmation_not_assumed(self):
        with tempfile.TemporaryDirectory() as folder:
            p=self._write(folder,[
              {'Test-ID':'a','Szenario-Erwartung':'META','KI-Kontextkategorie':'META','Menschliche Freigabe':'OFFEN'},
              {'Test-ID':'b','Szenario-Erwartung':'META','KI-Kontextkategorie':'META','Menschliche Freigabe':'BESTAETIGT'},
            ])
            actual=analyse_cases(p)
            self.assertEqual(actual['human_confirmations_reported'],1)
