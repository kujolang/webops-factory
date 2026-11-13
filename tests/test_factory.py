import sys, tempfile, unittest, shutil, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from siteops import *
from factory import verify
import factory
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
class ContractTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.site=self.base/'site';shutil.copytree(ROOT/'examples/studio-site',self.site)
    def tearDown(self):self.tmp.cleanup()
    def edits(self):
        values=read(ROOT/'examples/studio.json')['fixtureValues'];return [{'findingId':f['id'],'value':values[f['file']+':'+f['kind']],'reason':'Fixture repair'} for f in audit(self.site)]
    def test_example_has_five_findings(self):self.assertEqual(len(audit(self.site)),5)
    def test_repairs_clear_supported_checks(self):apply(self.site,audit(self.site),self.edits());self.assertEqual(audit(self.site),[])
    def test_source_snapshot_is_independent(self):
        snapshot=self.base/'snapshot';manifest=intake(self.site,snapshot);apply(snapshot,audit(snapshot),self.edits());self.assertEqual(len(audit(self.site)),5);self.assertEqual(len(manifest),5)
    def test_path_escape(self):
        for value in ['../private','/tmp/file','a/../../private']:
            with self.assertRaises(ValueError):confined(self.site,value)
    def test_symlinks_rejected(self):
        (self.site/'secret.html').symlink_to('/etc/passwd')
        with self.assertRaises(ValueError):intake(self.site,self.base/'out')
    def test_script_rejected(self):
        with (self.site/'index.html').open('a') as f:f.write('<script>alert(1)</script>')
        with self.assertRaises(ValueError):intake(self.site,self.base/'out')
    def test_svg_active_content_rejected(self):
        with (self.site/"workshop.svg").open("a") as f:f.write("<script>alert(1)</script>")
        with self.assertRaises(ValueError):intake(self.site,self.base/"out")
    def test_comment_title_is_not_a_title(self):
        p=self.site/"index.html";p.write_text(p.read_text().replace("<title></title>","<!-- <title>Fake title</title> -->"))
        self.assertTrue(any(f["kind"]=="title" for f in audit(self.site)))
        apply(self.site,audit(self.site),self.edits());self.assertEqual(audit(self.site),[])
    def test_event_handler_rejected(self):
        with (self.site/'index.html').open('a') as f:f.write('<img src="x" onerror="alert(1)">')
        with self.assertRaises(ValueError):intake(self.site,self.base/'out')
    def test_hidden_secrets_not_ingested(self):
        (self.site/'.env').write_text('secret');intake(self.site,self.base/'out');self.assertFalse((self.base/'out/.env').exists())
    def test_invented_finding_rejected(self):
        with self.assertRaises(ValueError):apply(self.site,audit(self.site),[{'findingId':'invented','value':'x','reason':'x'}])
    def test_remote_link_rejected(self):
        edits=self.edits();f=next(f for f in audit(self.site) if f['kind']=='broken_link');e=next(e for e in edits if e['findingId']==f['id']);e['value']='https://example.com'
        before=sha(self.site/'index.html')
        with self.assertRaises(ValueError):apply(self.site,audit(self.site),edits)
        self.assertEqual(sha(self.site/'index.html'),before)
    def test_markup_rejected(self):
        edits=self.edits();edits[0]['value']='<script>x</script>'
        with self.assertRaises(ValueError):apply(self.site,audit(self.site),edits)
    def test_changed_source_rejected(self):
        findings=audit(self.site);edits=self.edits();p=self.site/'index.html';p.write_text(' '+p.read_text())
        with self.assertRaises(ValueError):apply(self.site,findings,edits)
    def test_duplicate_edit_rejected(self):
        e=self.edits()[0]
        with self.assertRaises(ValueError):apply(self.site,audit(self.site),[e,e])
    def test_recorded_example_import_is_verified_and_repeatable(self):
        with patch.object(factory,'RUNS',self.base/'runs'):
            self.assertEqual(factory.import_example(),0)
            self.assertEqual(factory.import_example(),0)
            run=next((self.base/'runs').iterdir());self.assertTrue(verify(run)['ok'])
            (run/'candidate/index.html').write_text('tampered')
            with self.assertRaises(ValueError):factory.import_example()
    def test_package_detects_drift(self):
        p=self.base/'file.txt';p.write_text('good');write(self.base/'package.json',{'schema':'kujo.webops-factory.package/v1','files':[{'path':'file.txt','sha256':sha(p)}]});self.assertTrue(verify(self.base)['ok']);p.write_text('changed')
        with self.assertRaises(ValueError):verify(self.base)
if __name__=='__main__':unittest.main()
