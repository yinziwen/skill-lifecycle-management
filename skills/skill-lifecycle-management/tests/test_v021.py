"""D8/D9 regression; synthetic fixtures, not host semantic/behavior tests."""
import json, subprocess, sys, tempfile, unittest, zipfile
from pathlib import Path
from test_slm import task, draft
from slm import Engine, dump, digest, validate_draft

class FixTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.e=Engine(self.tmp.name)
    def tearDown(self):
        self.e.db.close(); self.tmp.cleanup()
    def active(self, deps=None):
        for i in range(3): self.e.record(task(i))
        p=self.e.propose('create',dict(draft=draft(dependencies=deps or []),task_ids=['0','1','2'],project_id='demo',rationale='fixture'))
        self.e.decide(p['id'],p['hash'],'approve'); self.e.apply(p['id'])
        return self.e.feedback(dict(name='minimal-change',version=1,case_id='fixture',result='fail',evidence='synthetic',source='test'))
    def opt(self,f,d):
        return self.e.propose('optimize',dict(draft=d,feedback_ids=[f['id']],rationale='fixture'))
    def test_t30_switch_session(self):
        self.e.record(task(1,session_id='a')); r=self.e.record(task(1,session_id='b'))
        self.assertEqual(r['status'],'duplicate'); self.assertTrue(r['session_linked'])
        self.assertEqual(self.e.task_sessions('demo','1')['session_ids'],['a','b'])
        self.assertEqual(self.e.tasks()[0]['session_id'],'a')
    def test_t31_three_sessions_one_task(self):
        for s in ['a','b','c','c',None]: self.e.record(task(1,session_id=s))
        self.assertEqual(len(self.e.tasks()),1); self.assertEqual(self.e.recommendations('demo'),[])
        self.assertEqual(self.e.task_sessions('demo','1')['session_ids'],['a','b','c'])
    def test_t32_three_distinct_tasks(self):
        for i in range(3):
            for s in ['a','b']: self.e.record(task(i,session_id=s))
        self.assertEqual(self.e.recommendations('demo')[0]['count'],3)
    def test_t33_concurrent_cli(self):
        script=Path(__file__).resolve().parents[1]/'scripts/slm.py'
        processes=[]
        for i in range(6):
            p=Path(self.tmp.name)/f'{i}.json'; p.write_text(json.dumps(task(1,session_id=f's{i}')),encoding='utf-8')
            processes.append(subprocess.Popen([sys.executable,str(script),'--home',self.tmp.name,'record',str(p)],stdout=subprocess.PIPE,stderr=subprocess.PIPE))
        results=[]
        for p in processes:
            out,err=p.communicate(timeout=30); self.assertEqual(p.returncode,0,err.decode()); results.append(json.loads(out))
        self.assertEqual(sum(r['status']=='recorded' for r in results),1)
        self.assertEqual(len(self.e.tasks()),1); self.assertEqual(len(self.e.task_sessions('demo','1')['session_ids']),6)
        out=subprocess.check_output([sys.executable,str(script),'--home',self.tmp.name,'task-sessions','demo','1']); self.assertEqual(len(json.loads(out)['session_ids']),6)
    def test_t34_project_isolation(self):
        self.e.record(task(1,session_id='a')); self.e.record(task(1,project_id='other',session_id='b'))
        self.assertEqual(self.e.task_sessions('demo','1')['session_ids'],['a']); self.assertEqual(self.e.task_sessions('other','1')['session_ids'],['b'])
    def test_t35_missing_opt_dependencies(self):
        f=self.active(['python:sqlite3']); d=draft(); d.pop('dependencies')
        with self.assertRaisesRegex(ValueError,'explicit dependencies'): self.opt(f,d)
        d['dependencies_declared']=True
        with self.assertRaisesRegex(ValueError,'explicit dependencies'): self.opt(f,d)
        self.assertEqual(self.e.skill_info('minimal-change')['active_version'],1)
    def test_t36_explicit_same_dependencies(self):
        f=self.active(['python:sqlite3']); p=self.opt(f,draft(dependencies=['python:sqlite3']))
        self.assertEqual(p['status'],'pending'); self.e.decide(p['id'],p['hash'],'approve'); self.e.apply(p['id'])
        self.assertEqual(self.e.dependency_check('minimal-change',2)['status'],'declared-dependencies-present')
    def test_t37_missing_runtime_dependency_draft_only(self):
        f=self.active(); p=self.opt(f,draft(dependencies=['python:slm_no_such_module_021']))
        self.e.decide(p['id'],p['hash'],'approve'); r=self.e.apply(p['id'])
        self.assertEqual(r['status'],'registered-local-draft'); self.assertFalse(r['installed'])
        self.assertEqual(self.e.dependency_check('minimal-change',2)['status'],'missing')
    def test_t38_tamper_after_approval(self):
        f=self.active(); p=self.opt(f,draft(dependencies=[])); self.e.decide(p['id'],p['hash'],'approve')
        payload=p['payload']; payload['draft']['dependencies']=['python:sqlite3']
        with self.e.db: self.e.db.execute('UPDATE proposals SET payload=? WHERE id=?',(dump(payload),p['id']))
        with self.assertRaisesRegex(ValueError,'content changed'): self.e.apply(p['id'])
        self.assertEqual(self.e.get(p['id'])['status'],'approved'); self.assertEqual(self.e.skill_info('minimal-change')['active_version'],1)
    def test_t39_legacy_approved_invalid_draft_transaction_rollback(self):
        f=self.active(); p=self.opt(f,draft(dependencies=[])); payload=p['payload']; payload['draft']['dependencies_declared']=False
        h=digest({'kind':'optimize','name':p['name'],'payload':payload})
        with self.e.db: self.e.db.execute('UPDATE proposals SET payload=?,hash=?,status=? WHERE id=?',(dump(payload),h,'approved',p['id']))
        with self.assertRaisesRegex(ValueError,'explicit dependencies'): self.e.apply(p['id'])
        self.assertEqual(self.e.get(p['id'])['status'],'approved'); self.assertEqual(len(self.e.skill_info('minimal-change')['versions']),1)
    def test_changed_task_content_still_rejected(self):
        self.e.record(task(1,session_id='a'))
        with self.assertRaisesRegex(ValueError,'different content'): self.e.record(task(1,summary='different',session_id='b'))
        self.assertEqual(self.e.task_sessions('demo','1')['session_ids'],['a'])
    def test_session_absent_then_present(self):
        self.e.record(task(1)); self.e.record(task(1,session_id='b')); self.assertEqual(self.e.task_sessions('demo','1')['session_ids'],['b'])
    def test_migration_legacy_schema(self):
        self.e.record(task(1,session_id='original')); self.e.record(task(2)); original=self.e.tasks()
        with self.e.db: self.e.db.execute('DROP TABLE task_sessions')
        self.e.db.close(); self.e=Engine(self.tmp.name)
        self.assertEqual(self.e.tasks(),original); self.assertEqual(self.e.task_sessions('demo','1')['session_ids'],['original']); self.assertEqual(self.e.task_sessions('demo','2')['session_ids'],[])
        self.e.record(task(1,session_id='new')); self.assertEqual(self.e.task_sessions('demo','1')['session_ids'],['new','original'])
    def test_legacy_create_route_no_bypass(self):
        for i in range(3): self.e.record(task(i))
        d=draft(); d.pop('dependencies')
        with self.assertRaisesRegex(ValueError,'explicit dependencies'): self.e.propose('create',dict(draft=d,task_ids=['0','1','2'],project_id='demo',rationale='fixture'))
    def test_bad_declarations(self):
        f=self.active()
        for d in [draft(dependencies=None),draft(dependencies=[] ,dependencies_declared=False),draft(dependencies=['invalid'])]:
            with self.assertRaises(ValueError): self.opt(f,d)
    def test_tamper_before_approval(self):
        f=self.active(); p=self.opt(f,draft(dependencies=[])); payload=p['payload']; payload['draft']['dependencies']=['command:git']
        with self.e.db: self.e.db.execute('UPDATE proposals SET payload=? WHERE id=?',(dump(payload),p['id']))
        with self.assertRaisesRegex(ValueError,'content changed'): self.e.decide(p['id'],p['hash'],'approve')
        self.assertEqual(self.e.get(p['id'])['status'],'pending')
    def test_explicit_empty_opt_dependencies(self):
        f=self.active(['python:sqlite3']); p=self.opt(f,draft(dependencies=[])); self.e.decide(p['id'],p['hash'],'approve'); self.e.apply(p['id'])
        self.assertEqual(self.e.skill_info('minimal-change')['versions'][-1]['draft']['dependencies'],[])
    def test_legacy_pending_requires_fresh_proposal(self):
        f=self.active(); p=self.opt(f,draft(dependencies=[])); payload=p['payload']; payload['draft']['dependencies_declared']=False
        h=digest({'kind':'optimize','name':p['name'],'payload':payload})
        with self.e.db: self.e.db.execute('UPDATE proposals SET payload=?,hash=? WHERE id=?',(dump(payload),h,p['id']))
        with self.assertRaisesRegex(ValueError,'explicit dependencies'): self.e.decide(p['id'],h,'approve')
        self.e.decide(p['id'],h,'reject'); self.assertEqual(self.e.get(p['id'])['status'],'rejected')
