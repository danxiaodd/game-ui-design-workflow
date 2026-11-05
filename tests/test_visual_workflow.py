from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import workflow_state as state
from init_project import initialize
from validate_project import validate


class VisualWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.project=self.root/'visual-game'
        self.gdd=self.root/'existing-gdd.md'; self.gdd.write_text('Core rule: launch ducks.\n',encoding='utf-8')
        self.prompt=self.root/'prompt.md'; self.prompt.write_text('One representative game screen, approved palette.',encoding='utf-8')
        self.direction=self.root/'direction.md'; self.direction.write_text('Recommended direction with source references.',encoding='utf-8')
        self.png=self.root/'actual.png'; Image.new('RGBA',(32,32),(100,120,200,255)).save(self.png)
        state.initialize(self.project,[self.gdd])

    def direction_approved(self):
        state.record(self.project,'direction-v001','direction',self.direction,self.prompt)
        state.approve(self.project,'direction-v001','TEST FIXTURE user confirms direction V001')

    def test_existing_gdd_never_copied_or_modified(self):
        before=self.gdd.read_bytes()
        initialize(ROOT,'specs','visual-game',False,True,[self.gdd],self.root)
        self.assertEqual(self.gdd.read_bytes(),before)
        self.assertFalse((self.project/'gdd.md').exists())
        self.assertFalse((self.project/'prd.md').exists())
        self.assertFalse((self.project/'interaction.md').exists())
        self.assertEqual(state.load(self.project)['sources'][0]['path'],str(self.gdd))

    def test_direction_output_cannot_start_concept_until_user_approves(self):
        item=state.record(self.project,'direction-v001','direction',self.direction,self.prompt)
        self.assertEqual(item['status'],'review')
        with self.assertRaisesRegex(ValueError,'unapproved'):
            state.record(self.project,'concept-v001','concept',self.png,self.prompt,['direction-v001'])
        state.approve(self.project,'direction-v001','TEST FIXTURE explicit direction approval')
        self.assertEqual(state.record(self.project,'concept-v001','concept',self.png,self.prompt,['direction-v001'])['status'],'review')

    def test_unavailable_tool_stores_prompt_only(self):
        self.direction_approved()
        item=state.record(self.project,'concept-v001','concept',prompt=self.prompt,parents=['direction-v001'])
        self.assertEqual(item['status'],'pending-generation'); self.assertNotIn('path',item)
        with self.assertRaises(ValueError): state.approve(self.project,'concept-v001','yes')
        self.assertTrue((self.project/item['prompt']).is_file())
        self.assertEqual(validate(self.project,True).errors,[])

    def test_external_success_waits_for_transfer_without_faking_local_file(self):
        self.direction_approved()
        item=state.record(self.project,'concept-v001','concept',prompt=self.prompt,parents=['direction-v001'],result_ref='fixture-tool-result-1')
        self.assertEqual(item['status'],'pending-transfer'); self.assertNotIn('path',item)

    def test_concept_is_not_formal_page_approval(self):
        self.direction_approved()
        state.record(self.project,'concept-v001','concept',self.png,self.prompt,['direction-v001'])
        with self.assertRaises(ValueError): state.record(self.project,'home-v001','page',self.png,self.prompt,['concept-v001'])
        state.approve(self.project,'concept-v001','TEST FIXTURE user confirms concept')
        item=state.record(self.project,'home-v001','page',self.png,self.prompt,['concept-v001'])
        self.assertEqual(item['status'],'review')
        with self.assertRaises(ValueError): state.record(self.project,'button-v001','component',self.png,self.prompt,['home-v001'])

    def test_direct_page_and_independent_component_routes(self):
        item=state.record(self.project,'home-v001','page',self.png,self.prompt,direct_reason='TEST FIXTURE user requests home page only')
        self.assertEqual(item['status'],'review')
        state.record(self.project,'potion-v001','component',self.png,self.prompt,direct_reason='TEST FIXTURE independent potion asset')
        with self.assertRaises(ValueError): state.record(self.project,'invalid-v001','page',self.png,self.prompt)

    def test_resume_preserves_files_and_decisions(self):
        self.direction_approved(); saved=(self.project/'workflow-state.json').read_bytes()
        original=(self.project/'history/direction-v001/output.md').read_bytes()
        state.initialize(self.project,[self.gdd]); result=state.resume(self.project)
        self.assertEqual(saved,(self.project/'workflow-state.json').read_bytes())
        self.assertEqual(result['artifacts']['direction-v001'],'approved')
        with self.assertRaises(ValueError): state.record(self.project,'direction-v001','direction',self.direction)
        self.assertEqual(original,(self.project/'history/direction-v001/output.md').read_bytes())

    def test_modified_parent_or_prompt_blocks_downstream(self):
        self.direction_approved()
        state.record(self.project,'concept-v001','concept',self.png,self.prompt,['direction-v001'])
        (self.project/'history/direction-v001/prompt.md').write_text('Changed behind approved version',encoding='utf-8')
        self.assertEqual(state.resume(self.project)['artifacts']['concept-v001'],'stale-parent')
        with self.assertRaises(ValueError): state.approve(self.project,'concept-v001','yes')
        self.assertTrue(validate(self.project,True).errors)

    def test_source_change_requires_reread_and_marks_history_stale(self):
        self.direction_approved(); self.gdd.write_text('Changed game rules',encoding='utf-8')
        self.assertEqual(state.resume(self.project)['artifacts']['direction-v001'],'stale-source')
        with self.assertRaises(ValueError): state.record(self.project,'direction-v002','direction',self.direction)
        state.register_source(self.project,self.gdd,'TEST FIXTURE read updated core rules')
        self.assertFalse(state.approved(self.project,state.load(self.project),'direction-v001'))
        state.record(self.project,'direction-v002','direction',self.direction)

    def test_approval_requires_nonempty_evidence(self):
        state.record(self.project,'direction-v001','direction',self.direction)
        with self.assertRaises(ValueError): state.approve(self.project,'direction-v001',' ')

    def test_legacy_project_no_longer_requires_local_planning_triad(self):
        target=self.root/'factory-v2-shop'; shutil.copytree(ROOT/'examples/factory-v2-shop',target)
        for name in ('gdd.md','prd.md','interaction.md'): (target/name).unlink()
        self.assertEqual(validate(target,True).errors,[])

    def test_visual_only_workspace_name_can_be_user_selected(self):
        project=self.root/'ArtWorkflow'
        state.initialize(project,[self.gdd])
        self.assertEqual(validate(project,True).errors,[])

    def test_corrupt_parent_cycles_are_rejected_without_recursion(self):
        self.direction_approved()
        value=state.load(self.project)
        value['artifacts']['direction-v001']['parents']=['direction-v001']
        state.save(self.project,value)
        with self.assertRaisesRegex(ValueError,'cycle'): state.load(self.project)

    def test_revision_links_pending_task_without_inheriting_approval(self):
        self.direction_approved()
        state.record(self.project,'concept-v001','concept',prompt=self.prompt,parents=['direction-v001'])
        result=state.record(self.project,'concept-v002','concept',self.png,self.prompt,['direction-v001'],based_on='concept-v001')
        self.assertEqual(result['based_on'],'concept-v001'); self.assertEqual(result['status'],'review')


class PortableInstallTests(unittest.TestCase):
    def test_codex_install_runs_from_unrelated_working_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            project=Path(temp); unrelated=project/'other'; unrelated.mkdir()
            result=subprocess.run([sys.executable,str(ROOT/'scripts/install_skills.py'),'--project',str(project),'--agent','codex'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            installed=project/'.agents/skills'
            self.assertEqual(len(list(installed.glob('*/SKILL.md'))),10)
            runner=installed/'game-ui-workflow/scripts/run.py'
            result=subprocess.run([sys.executable,str(runner),'init_project','from-installed','--visual','--source',str(ROOT/'examples/factory-v2-shop/gdd.md'),'--workspace',str(project/'work')],cwd=unrelated,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertTrue((project/'work/from-installed/contracts/style-contract.yaml').is_file())
            self.assertFalse((project/'work/from-installed/gdd.md').exists())
            state_run=subprocess.run([sys.executable,str(runner),'workflow_state',str(project/'work/from-installed'),'resume'],cwd=unrelated,capture_output=True,text=True)
            self.assertEqual(state_run.returncode,0,state_run.stderr)
            self.assertEqual(json.loads(state_run.stdout)['sources_changed'],[])

    def test_repo_skills_are_discoverable_and_runners_match(self):
        for source in (ROOT/'skills').iterdir():
            if not (source/'SKILL.md').is_file(): continue
            self.assertTrue((ROOT/'.agents/skills'/source.name/'SKILL.md').is_file())
            self.assertEqual((source/'scripts/run.py').read_bytes(),(ROOT/'scripts/skill_runner.py').read_bytes())
