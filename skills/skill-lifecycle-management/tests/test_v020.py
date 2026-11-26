import json, subprocess, sys, tempfile, unittest, datetime
from pathlib import Path
from test_slm import task, draft
from slm import Engine

class ActiveDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.e=Engine(self.tmp.name)
    def tearDown(self): self.e.db.close(); self.tmp.cleanup()
    def seed(self,n=3,**kw):
        for i in range(n): self.e.record(task(i,**kw))
    def proposal(self,**kw):
        g=self.e.recommendations('demo')[0]
        return self.e.propose('create',dict(draft=draft(**({"dependencies":[]} | kw)),project_id='demo',task_refs=[{'project_id':t['project_id'],'task_id':t['task_id']} for t in g['tasks']],pattern_id=g['pattern_id'],rationale='synthetic fixture'))
    def active(self,**kw):
        self.seed(); p=self.proposal(**kw); self.e.decide(p['id'],p['hash'],'approve'); self.e.apply(p['id']); return p
    def test_default_three_and_observe(self):
        for i in range(2): self.assertEqual(self.e.observe(task(i))['recommendations'],[])
        r=self.e.observe(task(2))['recommendations'][0]; self.assertEqual((r['count'],r['minimum'],r['action']),(3,3,'create')); self.assertEqual(self.e.listing(),[])
    def test_two_high_value(self):
        self.seed(2,reuse_value='high',value_evidence='synthetic observed recurring manual work'); self.assertEqual(self.e.recommendations('demo')[0]['minimum'],2)
        p=self.proposal(); self.assertEqual(p['status'],'pending')
    def test_high_value_requires_evidence(self):
        with self.assertRaises(ValueError): self.e.record(task(0,reuse_value='high'))
    def test_single_high_not_enough(self):
        self.e.record(task(0,reuse_value='high',value_evidence='synthetic')); self.e.record(task(1)); self.assertEqual(self.e.recommendations('demo'),[])
    def test_cross_project_requires_explicit_scope_and_flag(self):
        self.e.record(task(1,scope='general')); self.e.record(task(1,project_id='other',scope='general')); self.e.record(task(2,project_id='other',scope='general'))
        self.assertEqual(self.e.recommendations('demo'),[])
        r=self.e.recommendations('demo',True)[0]; self.assertEqual(r['count'],3); self.assertEqual(r['scope'],'general')
        refs=[{'project_id':t['project_id'],'task_id':t['task_id']} for t in r['tasks']]; d=dict(draft=draft(dependencies=[]),project_id='demo',task_refs=refs,rationale='fixture',pattern_id=r['pattern_id'])
        with self.assertRaises(ValueError): self.e.propose('create',d)
        d['cross_project_authorized']=True; self.assertEqual(self.e.propose('create',d)['status'],'pending')
    def test_cross_private_never_matches(self):
        self.e.record(task(1,scope='general')); self.e.record(task(2,project_id='other')); self.e.record(task(3,project_id='other',scope='general')); self.assertEqual(self.e.recommendations('demo',True),[])
    def test_shown_cooldown_new_evidence(self):
        self.seed(); r=self.e.recommendations('demo')[0]; self.e.recommendation_decide('demo',r['notice_id'],'shown'); self.assertEqual(self.e.recommendations('demo'),[])
        self.e.record(task(4)); self.assertEqual(self.e.recommendations('demo'),[])
        with self.e.db: self.e.db.execute('UPDATE recommendation_state SET updated=?',((datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=2)).isoformat(),))
        self.assertEqual(self.e.recommendations('demo')[0]['count'],4)
    def test_ignore_persistent(self):
        self.seed(); r=self.e.recommendations('demo')[0]; self.e.recommendation_decide('demo',r['notice_id'],'ignore'); self.e.record(task(4)); self.assertEqual(self.e.recommendations('demo'),[])
        self.e.recommendation_decide('demo',r['notice_id'],'reset'); self.assertEqual(len(self.e.recommendations('demo')),1)
    def test_reject_and_pending_suppress(self):
        self.seed(); p=self.proposal(); self.assertEqual(self.e.recommendations('demo'),[]); self.e.decide(p['id'],p['hash'],'reject'); self.assertEqual(self.e.recommendations('demo'),[])
    def test_reuse_and_optimize(self):
        self.active(); self.assertEqual(self.e.recommendations('demo')[0]['action'],'reuse')
        f=self.e.feedback(dict(name='minimal-change',version=1,case_id='fail',result='fail',source='synthetic',evidence='synthetic test'))
        r=self.e.recommendations('demo')[0]; self.assertEqual(r['action'],'optimize'); self.assertEqual(r['feedback_ids'],[f['id']]); self.assertEqual(self.e.skill_info('minimal-change')['active_version'],1)
    def test_dependencies_and_feedback_errors(self):
        self.active(dependencies=['python:sqlite3','python:slm_nonexistent_778812'])
        r=self.e.dependency_check('minimal-change',1); self.assertEqual(r['status'],'missing'); self.assertEqual([c['present'] for c in r['checks']],[True,False])
        out=Path(self.tmp.name)/'export'; self.e.export('minimal-change',1,out); self.assertIn('python:sqlite3',(out/'SKILL.md').read_text(encoding='utf-8')); self.assertTrue((out/'runtime-dependencies.json').is_file())
        f=dict(name='minimal-change',version=1,case_id='x',result='success',source='synthetic',evidence='fixture')
        with self.assertRaisesRegex(ValueError,'pass, fail or unknown'): self.e.feedback(f)
        f['result']='pass'; self.e.feedback(f)
        with self.assertRaisesRegex(ValueError,'case_id'): self.e.feedback(f)
    def test_new_proposal_requires_dependency_declaration(self):
        self.seed(); g=self.e.recommendations('demo')[0]
        missing=draft(); missing.pop('dependencies')
        with self.assertRaisesRegex(ValueError,'explicit dependencies required'):
            self.e.propose('create',dict(draft=missing,project_id='demo',task_ids=['0','1','2'],pattern_id=g['pattern_id'],rationale='fixture'))
    def test_legacy_deps_unknown(self):
        self.seed(); missing=draft(); missing.pop('dependencies')
        # Legacy stored version fixture: old records must remain readable, not silently become dependency-free.
        from slm import validate_draft, render, dump
        old=validate_draft(missing)
        with self.e.db:
            self.e.db.execute('INSERT INTO versions VALUES(?,?,?,?,?)',('minimal-change',1,dump(old),dump(render(old,1)),'legacy'))
            self.e.db.execute('INSERT INTO active VALUES(?,?)',('minimal-change',1))
        self.assertEqual(self.e.dependency_check('minimal-change',1)['status'],'unknown')
    def test_cross_process_cli_utf8(self):
        script=Path(__file__).resolve().parents[1]/'scripts/slm.py'; cmd=[sys.executable,str(script),'--home',self.tmp.name]
        for i in range(3):
            f=Path(self.tmp.name)/f'{i}.json'; f.write_text(json.dumps(task(i,summary='中文任务')),encoding='utf-8'); subprocess.run(cmd+['observe',str(f)],check=True,capture_output=True)
        raw=subprocess.check_output(cmd+['recommend','demo']).decode('utf-8'); self.assertIn('中文任务',raw); self.assertEqual(json.loads(raw)[0]['count'],3)
if __name__=='__main__': unittest.main()
