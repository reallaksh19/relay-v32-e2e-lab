import pathlib, sys, tempfile, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT/'src'))
from csv_auditor.parser import read_rows

class R01InputAcceptance(unittest.TestCase):
    def csv(self,text):
        with tempfile.TemporaryDirectory() as tmp:
            path=pathlib.Path(tmp)/'a.csv'; path.write_text(text,encoding='utf-8')
            return read_rows(path)
    def test_valid(self): self.assertEqual({'A': {'value':'10'},'B': {'value':'20'}}, self.csv('id,value\nA,10\nB,20\n'))
    def test_duplicate_id(self):
        with self.assertRaises(ValueError): self.csv('id,value\nA,10\nA,20\n')
    def test_empty_id(self):
        with self.assertRaises(ValueError): self.csv('id,value\n,10\n')
    def test_missing_header(self):
        with self.assertRaises(ValueError): self.csv('name,value\nA,10\n')
