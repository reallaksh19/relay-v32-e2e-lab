import pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from csv_auditor.compare import diff
class R02CompareAcceptance(unittest.TestCase):
    def test_three_change_classes(self):
        self.assertEqual({'added':['D'],'removed':['C'],'modified':['B']},diff({'A':{'value':'10'},'B':{'value':'20'},'C':{'value':'30'}},{'D':{'value':'40'},'B':{'value':'25'},'A':{'value':'10'}}))
    def test_no_change(self): self.assertEqual({'added':[],'removed':[],'modified':[]},diff({'A':{'value':'1'}},{'A':{'value':'1'}}))
    def test_stable_sorting(self): self.assertEqual(['A','Z'],diff({},{'Z':{},'A':{}})['added'])
