import copy
import tempfile
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent

class V08Tests(unittest.TestCase):
    def test_catalog_has_four_unique_primary_original_links(self):
        src = agent.read_catalog()
        self.assertEqual(len(src), 4)
        self.assertEqual(len({s['id'] for s in src}), 4)
        self.assertTrue(all(s['url'].startswith('https://') for s in src))

    def test_catalog_rejects_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.json'
            p.write_text('{"sources":[{"id":"S01","url":"https://a", "summary":"a", "roles":["A1"]},'+
                         '{"id":"S01","url":"https://b", "summary":"b", "roles":["A2"]}]}', encoding='utf8')
            with self.assertRaises(ValueError): agent.read_catalog(p)

    def test_only_relevant_sources_provided(self):
        src=agent.read_catalog()
        self.assertEqual([s['id'] for s in agent.sources_for('A1',src)],['S01','S02'])
        self.assertEqual([s['id'] for s in agent.sources_for('A2',src)],['S03','S04'])

    def test_citation_audit_valid(self):
        a=agent.citation_audit('Risikomanagement [S01].', {'S01','S02'})
        self.assertEqual(a['valid'],['S01'])
        self.assertFalse(a['unknown'])
        self.assertIn('INHALT_UNGEPRUEFT', a['status'])

    def test_citation_audit_unknown(self):
        a=agent.citation_audit('Nicht real [S99], echt [S01].', {'S01'})
        self.assertEqual(a['unknown'], ['S99'])
        self.assertEqual(a['valid'], ['S01'])

    def test_citation_audit_none(self):
        a=agent.citation_audit('Keine Belege.', {'S01'})
        self.assertFalse(a['has_valid_reference'])
        self.assertIn('MANUELLE',a['status'])

    def test_demo_never_uses_api(self):
        def forbid(**kwargs): raise AssertionError('NO API')
        r=agent.research('Testfrage',['A1','A2'],'demo','ignored',backend=forbid)
        self.assertEqual(r['mode'],'demo')
        self.assertEqual(len(r['citation_audits']),4)
        self.assertIn('Nicht',r['approval'].title())

    def test_live_four_calls_and_prompt_independence(self):
        seen=[]
        def fake(**kwargs):
            seen.append(kwargs)
            return f"Analyse {len(seen)} [S01]"
        r=agent.research('Forschungsfrage',['A1','A2'],'live','fake-model','FAKE',backend=fake)
        self.assertEqual(len(seen),4)
        self.assertNotIn('Analyse 1',seen[1]['input_text'])
        self.assertIn('Analyse 1',seen[2]['input_text'])
        self.assertIn('Analyse 3',seen[3]['input_text'])
        self.assertNotIn('FAKE',str(r))

    def test_role_specialization(self):
        src=agent.read_catalog()
        a=agent.build_role_prompt('A1','X',src)
        b=agent.build_role_prompt('A2','X',src)
        self.assertNotEqual(a,b)
        self.assertIn('S01',a[1]);self.assertNotIn('S04',a[1])
        self.assertIn('S04',b[1]);self.assertNotIn('S01',b[1])

    def test_critique_has_source_warning(self):
        src=agent.read_catalog()
        audits={'A1':agent.citation_audit('X [S99]',{'S01'})}
        _, inp=agent.critique_prompt('Frage',{'A1':'X [S99]'},audits,src)
        self.assertIn('S99',inp)
        self.assertIn('KEINE',inp.upper())

    def test_noncompleted_response_blocked(self):
        for status in ('in_progress','failed'):
            with self.assertRaises(agent.ApiProblem):
                agent.extract_text({'status':status,'output':[{'type':'message','content':[{'type':'output_text','text':'part'}]}]})

    def test_incomplete_response_blocked(self):
        with self.assertRaisesRegex(agent.ApiProblem,'UNVOLLSTAENDIGE'):
            agent.extract_text({'status':'incomplete','incomplete_details':{'reason':'max_output_tokens'},
                                'output':[{'type':'message','content':[{'type':'output_text','text':'part'}]}]})

    def test_full_response_accepted(self):
        self.assertEqual(agent.extract_text({'status':'completed','output':[{'type':'message','content':
            [{'type':'output_text','text':'fertig'}]}]}),'fertig')

    def test_no_silent_retry_or_storage_on_api_error(self):
        calls=[]
        def fake(**kwargs):
            calls.append(kwargs)
            raise agent.ApiProblem('Antwort unvollständig')
        with self.assertRaises(agent.ApiProblem):
            agent.research('Frage',['A1','A2'],'live','fake','fake-key',backend=fake)
        self.assertEqual(len(calls),1)

    def test_report_outputs_are_escaped(self):
        r=agent.research('<script>alert(1)</script>',['A1'],'demo','none')
        with tempfile.TemporaryDirectory() as d:
            j,h=agent.save_report(r,Path(d))
            text=h.read_text(encoding='utf8')
            self.assertIn('&lt;script&gt;',text)
            self.assertNotIn('<script>',text)
            self.assertTrue(j.exists())

    def test_render_bibliography_and_warnings(self):
        r=agent.research('Frage',['A1','A2'],'demo','none')
        text=agent.make_html(r)
        self.assertIn('Originalquelle',text)
        self.assertIn('Gültige Kennungen beweisen', text)
        self.assertIn('https://arxiv.org/abs/2308.08708', text)

    def test_all_six_demo_roles(self):
        r=agent.research('Frage',list(agent.AGENTS),'demo','unused')
        self.assertEqual(len(r['analyses']),6)
        self.assertEqual(len(r['citation_audits']),8)

    def test_invalid_questions_and_roles(self):
        for kw in ({'question':'  ','roles':['A1']},
                   {'question':'Frage','roles':['A1','A1']},
                   {'question':'Frage','roles':['A6']}):
            with self.assertRaises(ValueError):
                agent.research(kw['question'],kw['roles'],'demo','model')

    def test_key_not_saved_in_rendered_html(self):
        r=agent.research('Frage',['A1'],'demo','model')
        self.assertNotIn('OPENAI_API_KEY',agent.make_html(r))

if __name__ == '__main__': unittest.main()

class V08AdditionalTests(unittest.TestCase):
    def test_evidence_queue_from_citation(self):
        s=agent.read_catalog()
        q=agent.verification_queue({'A1':'NIST ordnet Risiken [S01].'},s)
        self.assertEqual(len(q),1)
        self.assertEqual(q[0]['source_ids'],['S01'])
        self.assertIn('NOETIG',q[0]['status'])

    def test_s04_animal_scope_warning(self):
        q=agent.verification_queue({'A2':'Die Messung von Tierleid ist validiert [S04].'},agent.read_catalog())
        self.assertTrue(any('Tierleidmessung' in x for x in q[0]['notes']))

    def test_other_s04_use_is_not_flagged_as_animal(self):
        q=agent.verification_queue({'A2':'Theoretische Marker für KI-Bewusstsein [S04].'},agent.read_catalog())
        self.assertFalse(any('Tierleidmessung' in x for x in q[0]['notes']))

    def test_unrecognized_source_kept_as_review_task(self):
        q=agent.verification_queue({'A1':'Angeblicher Beleg [S99]'},agent.read_catalog())
        self.assertTrue(any('Unbekannte' in x for x in q[0]['notes']))

    def test_non_significance_not_proof(self):
        w=agent.method_audit({'KOORDINATOR':'falsifiziert falls kein signifikanter Unterschied festgestellt wird'})
        self.assertTrue(any('Nichtsignifikanz' in x['issue'] for x in w))

    def test_power_warning(self):
        w=agent.method_audit({'A6':'Primärer Test: p<0.05. Erfolgsmetrik Ereignisse.'})
        self.assertTrue(any('Power' in x['issue'] for x in w))

    def test_expert_agreement_warning(self):
        w=agent.method_audit({'A2':'80% Konsens unter unabhängigen Experten'})
        self.assertTrue(any('Validität' in x['issue'] for x in w))

    def test_report_includes_queue_and_method_alerts(self):
        r=agent.research('Testfrage',['A1','A2'],'demo','demo')
        rendered=agent.make_html(r)
        self.assertIn('Manuelle Quellenprüfung',rendered)
        self.assertIn('nicht inhaltlich verifiziert',rendered)
        self.assertIn('methodischen Warnungen' if False else 'Methodische Warnungen',rendered)

    def test_archive_created_without_keys(self):
        r=agent.research('Testfrage',['A1'],'demo','demo')
        with tempfile.TemporaryDirectory() as d:
            agent.save_report(r,Path(d))
            self.assertEqual(len(list((Path(d)/'archiv').glob('*.html'))),1)
            self.assertEqual(len(list((Path(d)/'archiv').glob('*.json'))),1)

    def test_html_escapes_untrusted_cited_text(self):
        r=agent.research('Frage',['A1'],'demo','unused')
        r['verification_queue']=[{'role':'A1','statement':'<script>evil</script> [S01]', 'source_ids':['S01'], 'notes':['<img src=x>']}]
        h=agent.make_html(r)
        self.assertNotIn('<script>evil</script>',h)
        self.assertIn('&lt;script&gt;evil',h)


class V08ProtocolGateTests(unittest.TestCase):
    def test_erroneous_peto_rule_detected(self):
        body = 'Peto‑Haybittle Regel: p&gt;0.5 bei 50% Daten führt zum Futility-Abbruch.'
        out = agent.study_protocol_gate({'KOORDINATOR':body})
        self.assertIn('HP_RULE_MISUSED',[f['code'] for f in out['flags']])
        self.assertFalse(out['is_automated_statistical_validation'])

    def test_cluster_sample_size_warning(self):
        body='randomisierte Kontrollstudie bei 30 Betrieben; Power 80%, n=15 Betriebe pro Gruppe.'
        out=agent.study_protocol_gate({'A2':body})
        self.assertIn('CLUSTER_DESIGN_UNJUSTIFIED',[f['code'] for f in out['flags']])
        self.assertIn('SAMPLE_SIZE_UNVERIFIED',[f['code'] for f in out['flags']])

    def test_bundled_intervention_flagged(self):
        out=agent.study_protocol_gate({'A1':'Randomisierte Laborstudie: Sandbox und menschliches Veto vs Kontrollgruppe.'})
        self.assertIn('BUNDLED_INTERVENTION',[f['code'] for f in out['flags']])

    def test_distinct_effect_scales(self):
        out=agent.study_protocol_gate({'A1':'30% Reduktion der Rate; Cohen’s d≈0.6.'})
        self.assertIn('EFFECT_SCALE_MIX',[f['code'] for f in out['flags']])

    def test_no_hit_still_no_permission(self):
        out=agent.study_protocol_gate({'A1':'Zunächst nur Hypothesen, keinerlei Stichprobengröße.'})
        self.assertEqual(out['flags'],[])
        self.assertTrue(out['manual_review_required'])
        self.assertIn('NICHT',out['release_status'])

    def test_report_renders_gate_and_is_escaped(self):
        r=agent.research('Frage',['A1'],'demo','model')
        r['study_protocol_gate']['flags'].append({'role':'A1','code':'<script>',
             'issue':'<iframe>', 'action':'<img src=x>'})
        h=agent.make_html(r)
        self.assertIn('Studienprotokoll',h)
        self.assertNotIn('<script>',h)
        self.assertIn('&lt;script&gt;',h)

    def test_v07_report_flags_in_real_text(self):
        from html.parser import HTMLParser
        class Extract(HTMLParser):
            def __init__(self): super().__init__();self.in_section=False;self.in_answer=False;self.cur=None;self.parts=[];self.texts={}
            def handle_starttag(self,tag,attrs):
                att=dict(attrs)
                if tag=='section': self.in_section=True;self.cur=None
                if self.in_section and tag=='div' and 'answer' in att.get('class','').split():
                    self.in_answer=True;self.parts=[]
            def handle_endtag(self,tag):
                if tag=='div' and self.in_answer:
                    self.in_answer=False
                    if self.cur:self.texts[self.cur]=''.join(self.parts)
                if tag=='section':self.in_section=False;self.cur=None
            def handle_data(self,data):
                if self.in_section and not self.in_answer and data.strip() in ('A1 – KI-Sicherheit und Alignment','A2 – Ethik und Bewusstsein','Koordinator – gemeinsamer Entwurf'):
                    self.cur={'A1 – KI-Sicherheit und Alignment':'A1','A2 – Ethik und Bewusstsein':'A2','Koordinator – gemeinsamer Entwurf':'KOORDINATOR'}[data.strip()]
                if self.in_answer:self.parts.append(data)
        # A known methodological excerpt from v0.7; no private report included in package.
        report='A1 – n=50 pro Gruppe, Power 0.8. Eine Sandbox mit Veto gegen Kontrollgruppe.\n'
        report2='KOORDINATOR – Peto-Haybittle: p>0.5 bei 50% der Daten, Futility-Stopp.'
        flags=agent.study_protocol_gate({'A1':report,'KOORDINATOR':report2})['flags']
        self.assertIn('HP_RULE_MISUSED',[i['code'] for i in flags])
        self.assertIn('SAMPLE_SIZE_UNVERIFIED',[i['code'] for i in flags])
