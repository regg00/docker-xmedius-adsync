#////////////////////////////////////////////////////////////////////////////
# Copyright (c) 2012 Sagemcom Canada Permission to use this work
# for any purpose must be obtained in writing from Sagemcom Canada
# 5252 de Maisonneuve Blvd. West, suite 400, Montreal, Quebec H4A 3S5
#////////////////////////////////////////////////////////////////////////////

import glob
import unittest
import os
import path


test_dir = os.path.dirname(__file__)
if(test_dir):
    test_path = test_dir + '/test_*.py'
else:
    test_path = 'test_*.py'
base_test_string = glob.glob(test_path)
module_strings = [str[0:len(str) - 3] for str in base_test_string]

suites = [unittest.defaultTestLoader.loadTestsFromName(str.replace(os.sep, '.')) for str in module_strings]
testSuite = unittest.TestSuite(suites)
text_runner = unittest.TextTestRunner().run(testSuite)
