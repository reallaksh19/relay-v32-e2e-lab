import json, pathlib, subprocess, sys, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class R03CLIAcceptance(unittest.TestCase):
    def invoke(self,before,after):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp);(p/'a.csv').write_text(before);(p/'b.csv').write_text(after)
            return subprocess.run([sys.executable,'-m','csv_auditor.cli',str(p/'a.csv'),str(p/'b.csv')],capture_output=True,text=True,env={**__import__('os').environ,'PYTHONPATH':str(ROOT/'src')})
    def test_end_to_end(self):
        r=self.invoke('id,value\nA,10\nB,20\nC,30\n','id,value\nA,10\nB,25\nD,40\n');self.assertEqual(0,r.returncode,r.stderr);self.assertEqual({'added':['D'],'removed':['C'],'modified':['B']},json.loads(r.stdout))
    def test_invalid_fails_closed(self):
        r=self.invoke('id,value\nA,10\nA,20\n','id,value\nA,10\n');self.assertNotEqual(0,r.returncode);self.assertFalse(r.stdout.strip().startswith('{'));self.assertIn('CSV_ERROR:',r.stderr);self.assertNotIn('Traceback',r.stderr)
