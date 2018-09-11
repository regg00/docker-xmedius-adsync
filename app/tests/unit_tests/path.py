#////////////////////////////////////////////////////////////////////////////
# Copyright (c) 2012 Sagemcom Canada Permission to use this work
# for any purpose must be obtained in writing from Sagemcom Canada
# 5252 de Maisonneuve Blvd. West, suite 400, Montreal, Quebec H4A 3S5
#////////////////////////////////////////////////////////////////////////////

import os
import sys

root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.append(root_path)
sys.path.append(os.path.join(root_path, 'third_party', 'mock-1.0b1'))
sys.path.append(os.path.join(root_path, 'third_party', 'python-ldap-2.4.10.win32-py2.7'))
sys.path.append(os.path.join(root_path, 'third_party', 'PyYAML-3.10.win32-py2.7'))
