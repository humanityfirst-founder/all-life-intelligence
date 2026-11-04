"""Prüft die neuen Exportfunktionen, einschliesslich CSV-Sicherheit und Quellenstatus."""
from pathlib import Path
import csv
import json
import sys
from tempfile import TemporaryDirectory
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import review_export, agent, sourcecheck


def fixture():
    return {
        'application': 'ALL-LIFE INTELLIGENCE – Agentensystem v0.9',
        'created_utc': '2026-10-27T12:38:27+00:00',
        'quality_check_version':'1.2',
        'study_protocol_gate':{'flags':[
            {'role':'A1','code':'NONINFERIORITY_NOT_ESTABLISHED',
            'issue':'Nichtsignifikanz beweist keine Nichtunterlegenheit.','action':'CI prüfen.'},
            {'role':'KOORDINATOR','code':'NONINFERIORITY_NOT_ESTABLISHED',
            'issue':'Nichtsignifikanz beweist keine Nichtunterlegenheit.','action':'CI prüfen.'}
        ]},
        'source_checks':{'checker_version':'1.2','checked_at_utc':'2026-10-27T13:13:49+00:00',
            'sources':[{'id':'S01','status':'HTML_ABGERUFEN_TEXTAUSZUG','url':sourcecheck.ALLOWED_PAGES['S01']},
                       {'id':'S02','status':'ORIGINAL_QUELLE_NICHT_PRUEFBAR','url':sourcecheck.ALLOWED_PAGES['S02']}],
            'claims':[{'role':'A1','source_id':'S01','status':'THEMATISCH_PASSENDE_STELLE_KEIN_BELEG',
                        'statement':'NIST hat die vier Risikomanagement-Funktionen.','passage':'GOVERN MAP MEASURE MANAGE','warning':'Kein Beweis'},
                       {'role':'A6','source_id':'S02','status':'ORIGINAL_QUELLE_NICHT_PRUEFBAR',
                        'statement':'=SUM(1,1)','passage':'<script>unsafe</script>','warning':'Offen'}]}}

class ReviewExportTests(unittest.TestCase):
    def test_summary_does_not_claim_verification(self):
        obj=review_export.build_overview(fixture())
        self.assertEqual(obj['sources_retrieved'],1)
        self.assertEqual(obj['claim_source_pairs'],2)
        self.assertEqual(obj['candidate_passages'],1)
        self.assertEqual(obj['flags_total'],2)
        self.assertEqual(obj['content_verified_automatically'],0)
        self.assertFalse(obj['manual_approval'])

    def test_missing_online_check_not_silently_accepted(self):
        with self.assertRaises(ValueError):
            review_export.build_overview({'application':'demo'})

    def test_csv_formula_injection_blocked(self):
        for expression in ['=HYPERLINK("x")','  +SUM(1,2)','-2+2','@INDIRECT("x")','\t=2+2','\r+2']:
            with self.subTest(expression=expression):
                self.assertTrue(review_export.safe_for_spreadsheet(expression).startswith("'"))

    def test_html_escapes_untrusted_model_text(self):
        result=review_export.make_html(review_export.build_overview(fixture()),fixture())
        self.assertNotIn('<script>unsafe</script>',result)
        self.assertIn('NICHT_ZUR', agent.study_protocol_gate({'A1':''})['release_status'])

    def test_csv_has_open_manual_columns_and_valid_utf8(self):
        with TemporaryDirectory() as d:
            hp,cp=review_export.write_exports(fixture(),Path(d))
            self.assertTrue(hp.is_file())
            with cp.open(encoding='utf-8-sig',newline='') as f:
                rows=list(csv.reader(f,delimiter=';'))
            self.assertEqual(len(rows),3)
            self.assertEqual(rows[1][-4],'OFFEN')
            self.assertTrue(rows[2][4].startswith("'=SUM"))
            self.assertIn('GOVERN MAP MEASURE MANAGE',cp.read_text(encoding='utf-8-sig'))
            obj=json.loads((Path(d)/'qualitaetskennzahlen.json').read_text(encoding='utf-8'))
            self.assertEqual(obj['content_verified_automatically'],0)

    def test_previous_manual_csv_is_archived_before_rewrite(self):
        with TemporaryDirectory() as d:
            target=Path(d)
            _,cp=review_export.write_exports(fixture(),target)
            cp.write_text('already human annotated',encoding='utf-8')
            review_export.write_exports(fixture(),target)
            old=list((target/'archiv').glob('PRUEFLISTE_vor_erneuter_Pruefung_*.csv'))
            self.assertEqual(len(old),1)
            self.assertEqual(old[0].read_text(encoding='utf-8'),'already human annotated')

    def test_fingerprint_stable_for_same_statement(self):
        with TemporaryDirectory() as d:
            target=Path(d)
            _,cp=review_export.write_exports(fixture(),target)
            first=list(csv.reader(cp.open(encoding='utf-8-sig',newline=''),delimiter=';'))[1][0]
            _,cp=review_export.write_exports(fixture(),target)
            second=list(csv.reader(cp.open(encoding='utf-8-sig',newline=''),delimiter=';'))[1][0]
            self.assertEqual(first,second)

    def test_sourcecheck_integration_generates_dashboard_automatically(self):
        from unittest.mock import patch
        with TemporaryDirectory() as d:
            dest=Path(d)
            report=agent.research(agent.DEFAULT_QUESTION,['A1','A2'],'demo','gpt-5-mini')
            agent.save_report(report,dest)
            fake={'checked_at_utc':'2026-10-27T13:15:00+00:00',
                  'checker_version':'1.2',
                  'sources':[{'id':'S01','status':'HTML_ABGERUFEN_TEXTAUSZUG','url':sourcecheck.ALLOWED_PAGES['S01']}],
                  'claims':[{'role':'A1','source_id':'S01','status':'THEMATISCH_PASSENDE_STELLE_KEIN_BELEG',
                             'statement':'GOVERN MAP MEASURE MANAGE','passage':'GOVERN MAP MEASURE MANAGE','warning':'Offen'}],
                  '_source_blocks':{'S01':{'status':'HTML_ABGERUFEN_TEXTAUSZUG','blocks':['GOVERN MAP MEASURE MANAGE']}}}
            with patch.object(sourcecheck,'check_report',return_value=fake):
                self.assertEqual(sourcecheck.run(dest/'letzter_bericht.json',confirm=False,open_report=False),0)
            self.assertTrue((dest/'PRUEFLISTE.csv').exists())
            self.assertTrue((dest/'QUALITAETSBILANZ.html').exists())
            self.assertTrue((dest/'qualitaetskennzahlen.json').exists())

    def test_no_network_in_report_generator(self):
        # Die Offline-Bilanz darf allein mit den strukturierten Prüfdaten arbeiten.
        with TemporaryDirectory() as d:
            p=Path(d)/'letzter_bericht.json'
            p.write_text(json.dumps(fixture()),encoding='utf-8')
            self.assertEqual(review_export.cli(['--report',str(p)]),0)
            self.assertTrue((Path(d)/'QUALITAETSBILANZ.html').exists())

if __name__=='__main__': unittest.main()
