import unittest
import webapp_sublot_21 as f
from webapp_sublot_21_manifest import FEATURES
class Sublot21Tests(unittest.TestCase): pass
def make_test(api):
 def test(self): self.assertTrue(callable(getattr(f,api)))
 return test
for feature in FEATURES: setattr(Sublot21Tests,feature['test'].rsplit('.',1)[-1],make_test(feature['api']))
