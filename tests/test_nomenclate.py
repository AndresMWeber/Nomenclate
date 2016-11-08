# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from imp import reload

import unittest
import nomenclate.core.nomenclature as nm
reload(nm)


class TestNomenclate(unittest.TestCase):
    def setUp(self):
        self.fixture = nm.Nomenclate()

    def tearDown(self):
        del self.fixture

    def format_options(self):
        self.assertEqual(self.fixture.format_options,
                         {'format_archive': '{side}_{name}_{space}_{purpose}_{decorator}_{childType}_{type}', 'format_model_topgrp': '{side}_{location}_{name}{decorator}_lod{var}_{type}', 'format_lee': '{type}_{childType}_{space}_{purpose}_{name}_{side}', 'format': '{side}_{location}_{name}{decorator}{var}_{childType}_{purpose}_{type}', 'format_rig_topgrp': '{name}{decorator}_lod{var}_{type}', 'format_curve': '{side}_{location}_{name}_{decorator}{var}_curve_{type}', 'format_shader': '{}', 'format_joint': '{side}_{location}_{name}{decorator}J{var}_{childType}_{purpose}_{type}', 'format_deformer': '{side}_{location}_{name}_{decorator}{var}_deform_{type}'})
    
    def test(self):
        self.failUnlessEqual(range(1, 10), range(1, 10))