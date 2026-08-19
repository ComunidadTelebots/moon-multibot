import unittest,webapp_sublot_22 as f
from webapp_sublot_22_manifest import FEATURES
class Sublot22Tests(unittest.TestCase):pass
def make(api):
 def test(self):self.assertTrue(callable(getattr(f,api)))
 return test
for x in FEATURES:setattr(Sublot22Tests,x['test'].rsplit('.',1)[-1],make(x['api']))
