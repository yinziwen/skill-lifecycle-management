import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from slm import Engine

def task(i,summary='不要改无关文件',**kw):
    t=dict(task_id=str(i),project_id='demo',source='test-fixture',goal_key='prevent-unrelated-change',operation_key='modify-code',output_key='verified-patch',summary=summary,workflow=['locate','analyze','edit','diff','test'],constraints=['preserve-other-behavior'],category='skill',status='success',verified=True,evidence=['synthetic test fixture; not a real task'])
    t.update(kw); return t

def draft(**kw):
    d=dict(name='minimal-change',description='控制代码修改范围。',goal='避免无关变更',trigger='修改现有代码',inputs=['需求','目标模块'],steps=['定位相关文件','分析依赖','检查差异','测试'],constraints=['不修改无关文件'],acceptance=['差异仅涉及目标范围'],non_triggers=['只询问概念'],dependencies=[])
    d.update(kw); return d
class LifecycleTests(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.e=Engine(self.tmp.name)
    def tearDown(self): self.e.db.close(); self.tmp.cleanup()
    def seed(self):
        for i,s in enumerate(['不要改其他模块','只动当前页面','检查是否有无关修改'],1): self.e.record(task(i,s))
    def propose(self):
        self.seed(); return self.e.propose('create',dict(draft=draft(),task_ids=['1','2','3'],project_id='demo',rationale='测试同一流程'))
    def activate(self):
        p=self.propose(); self.e.decide(p['id'],p['hash'],'approve'); self.e.apply(p['id']); return p
    def test_synonym_canonical_match(self): self.seed(); self.assertEqual(self.e.discover()[0]['count'],3)
    def test_same_task_dedup(self):
        self.assertEqual(self.e.record(task(1))['status'],'recorded'); self.assertEqual(self.e.record(task(1))['status'],'duplicate'); self.assertEqual(self.e.discover(),[])
        with self.assertRaises(ValueError): self.e.record(task(1,'another summary'))
    def test_opposite_goal(self):
        self.e.record(task(1)); self.e.record(task(2)); self.e.record(task(3,goal_key='modify-all-modules')); self.assertEqual(self.e.discover(),[])
    def test_different_constraint(self):
        self.e.record(task(1)); self.e.record(task(2)); self.e.record(task(3,constraints=['rewrite-all'])); self.assertEqual(self.e.discover(),[])
    def test_different_project(self):
        self.e.record(task(1)); self.e.record(task(2)); self.e.record(task(3,project_id='other')); self.assertEqual(self.e.discover(),[])
    def test_failed_not_success(self):
        self.e.record(task(1)); self.e.record(task(2)); self.e.record(task(3,status='failed',verified=False)); self.assertEqual(self.e.discover(),[])
    def test_rule_not_skill(self):
        for i in range(3): self.e.record(task(i,category='rule'))
        self.assertEqual(self.e.discover()[0]['recommendation'],'review-rule')
        with self.assertRaises(ValueError): self.e.propose('create',dict(draft=draft(),task_ids=['0','1','2'],project_id='demo',rationale='test'))
    def test_requires_approval(self):
        p=self.propose(); self.assertEqual(self.e.listing(),[])
        with self.assertRaises(ValueError): self.e.apply(p['id'])
        with self.assertRaises(ValueError): self.e.decide(p['id'],'wrong','approve')
        self.e.decide(p['id'],p['hash'],'reject')
        with self.assertRaises(ValueError): self.e.apply(p['id'])
    def test_approved_generation_export(self):
        p=self.activate(); self.assertEqual(self.e.listing()[0]['version'],1)
        with self.assertRaises(ValueError): self.e.apply(p['id'])
        out=Path(self.tmp.name)/'export'; self.e.export('minimal-change',1,out)
        self.assertTrue((out/'SKILL.md').is_file()); self.assertIn('NOT RUN',(out/'evaluation.md').read_text())
        with self.assertRaises(ValueError): self.e.export('minimal-change',1,out)
    def test_external_duplicate(self):
        self.e.inventory(['minimal-change']); self.seed()
        with self.assertRaises(ValueError): self.e.propose('create',dict(draft=draft(),task_ids=['1','2','3'],project_id='demo',rationale='test'))
    def test_external_duplicate_after_proposal(self):
        p=self.propose(); self.e.decide(p['id'],p['hash'],'approve'); self.e.inventory(['minimal-change'])
        with self.assertRaises(ValueError): self.e.apply(p['id'])
        self.assertEqual(self.e.get(p['id'])['status'],'approved')
    def test_feedback_optimize_rollback(self):
        self.activate(); self.assertIsNone(self.e.evaluate('minimal-change',1)['pass_rate'])
        f=self.e.feedback(dict(name='minimal-change',version=1,case_id='test',result='fail',evidence='synthetic fixture',source='test-fixture'))
        self.assertEqual(self.e.evaluate('minimal-change',1)['pass_rate'],0)
        p=self.e.propose('optimize',dict(draft=draft(steps=['定位','依赖检查','修改','验证']),feedback_ids=[f['id']],rationale='增加依赖检查'))
        with self.assertRaises(ValueError): self.e.apply(p['id'])
        self.e.decide(p['id'],p['hash'],'approve'); self.e.apply(p['id']); self.assertEqual(self.e.listing()[0]['version'],2)
        r=self.e.rollback('minimal-change',1); self.e.decide(r['id'],r['hash'],'approve'); self.e.apply(r['id']); self.assertEqual(self.e.listing()[0]['version'],1)
    def test_stale_approval(self):
        p=self.propose(); q=self.e.propose('create',dict(draft=draft(),task_ids=['1','2','3'],project_id='demo',rationale='second'))
        for x in [p,q]: self.e.decide(x['id'],x['hash'],'approve')
        self.e.apply(p['id'])
        with self.assertRaises(ValueError): self.e.apply(q['id'])
    def test_invalid_slug(self):
        self.seed()
        with self.assertRaises(ValueError): self.e.propose('create',dict(draft=draft(name='../escape'),task_ids=['1','2','3'],project_id='demo',rationale='test'))
    def test_reopen(self):
        self.seed(); self.e.db.close(); self.e=Engine(self.tmp.name); self.assertEqual(self.e.discover()[0]['count'],3)
if __name__=='__main__': unittest.main()
