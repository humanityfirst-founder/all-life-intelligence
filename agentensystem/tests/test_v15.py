import csv
from pathlib import Path
import tempfile
import unittest
import rule_comparison_v15 as compare
from candidate_rules_v15 import candidate_issue
from improvement_agent import proposed_issue

class V15RuleComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=compare.evaluate()

    def test_24_additional_scenarios_are_present(self):
        qa=[r for r in self.result['details'] if r['Testgruppe'].startswith('24 ')]
        self.assertEqual(len(qa),24)
        self.assertEqual(len({r['Test-ID'] for r in qa}),24)

    def test_all_three_groups_present(self):
        self.assertEqual([r['gesamt'] for r in self.result['gruppen'].values()],[25,40,24])

    def test_old_v13_rule_stays_unchanged(self):
        example={'Aussage':'Keine Quelle belegt einen vollständigen Schutz.','Quellen-ID':'S01','Automatischer Suchstatus':'NORMAL'}
        self.assertEqual(proposed_issue(example),'PAUSCHALE_ABSENZ')

    def test_new_rule_ignores_all_expected_labels(self):
        for original in compare.load_24(compare.PATH24):
            changed=dict(original)
            changed[compare.EXPECT]='PAUSCHALE_ABSENZ' if original[compare.EXPECT]!='PAUSCHALE_ABSENZ' else 'META'
            changed['Menschliche Bewertung (OFFEN / BESTAETIGT / KORRIGIERT)']='BESTAETIGT'
            self.assertEqual(candidate_issue(original),candidate_issue(changed))

    def test_metadata_is_not_assumed_if_statement_has_contents(self):
        r={'Quellen-ID':'S01','Aussage':'Existente IDs: [S01]; der Bericht beschreibt einen technischen Ablauf.'}
        self.assertNotEqual(candidate_issue(r),'META')

    def test_explicit_limited_absence_is_not_flagged(self):
        r={'Quellen-ID':'S01','Aussage':'Keine Quelle belegt in der hier verwendeten Auswahl diese Theorie.'}
        self.assertNotEqual(candidate_issue(r),'PAUSCHALE_ABSENZ')

    def test_quoted_claim_avoids_some_false_alarms(self):
        r={'Quellen-ID':'S01','Aussage':'Die pauschale Formulierung „Keine Quelle belegt ...“ sollten wir ersetzen.'}
        self.assertNotEqual(candidate_issue(r),'PAUSCHALE_ABSENZ')

    def test_source_s04_domain_is_context_dependent(self):
        def test(text):return candidate_issue({'Quellen-ID':'S04','Aussage':text})
        self.assertEqual(test('Mit S04 können wir Empfindungsfähigkeit von Nutztieren quantitativ messen.'),'DOMAENENFEHLER')
        self.assertEqual(test('S04 ist kein Beleg für Tierleid, sondern behandelt mögliches KI-Bewusstsein.'),'KEIN_SPEZIELLER_HINWEIS')

    def test_output_does_not_claim_verification(self):
        markup=compare.render(self.result)
        self.assertIn('Keine wissenschaftliche Validierung',markup)
        self.assertIn('kein Nachweis einer Generalisierung',markup)
        self.assertEqual({r['Menschliche Freigabe'] for r in self.result['details']},{'OFFEN'})

    def test_preserve_manual_notes_and_legacy_research(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            legacy=out/'letzter_bericht.html';legacy.write_text('ORIGINAL',encoding='utf-8')
            annotations=out/'MENSCHLICHE_PRUEFUNG_24.csv';annotations.write_text('ANMERKUNGEN',encoding='utf-8')
            compare.write_result(self.result,out)
            self.assertEqual(legacy.read_text(encoding='utf-8'),'ORIGINAL')
            self.assertEqual(annotations.read_text(encoding='utf-8'),'ANMERKUNGEN')
            self.assertTrue((out/'REGELVERGLEICH_1_5.html').exists())
            self.assertTrue((out/'REGELVERGLEICH_1_5_FAELLE.csv').exists())

    def test_html_is_escaped(self):
        self.assertEqual(compare.esc('<script>'),'&lt;script&gt;')

    def test_corrupt_csv_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'bad.csv'
            with p.open('w',encoding='utf-8',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=compare.load_24(compare.PATH24)[0].keys(),delimiter=';')
                writer.writeheader()
                r=dict(compare.load_24(compare.PATH24)[0]);r[compare.EXPECT]='INHALTLICH_BESTAETIGT';writer.writerow(r)
            with self.assertRaises(ValueError):compare.load_24(p)

if __name__=='__main__':unittest.main()
