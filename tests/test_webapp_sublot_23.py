import unittest,webapp_sublot_23 as f
from webapp_sublot_23_manifest import FEATURES
class Sublot23Tests(unittest.TestCase):pass
def make(api):
 def test(self):self.assertTrue(callable(getattr(f,api)))
 return test
for x in FEATURES:setattr(Sublot23Tests,x['test'].rsplit('.',1)[-1],make(x['api']))
