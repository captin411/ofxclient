import sys, os
sys.path.append('..')

from ofxclient import Institution, Settings, Account
import unittest
import getpass

class InstitutionTestCase(unittest.TestCase):

    def testIdOnly(self):
        i = Institution('623')
        self.assertEquals(i.id,'623')
        self.assertEquals(i.description,'Scottrade, Inc.')

    def testDescriptionOverride(self):
        i = Institution('623',description='test desc')
        self.assertEquals(i.description,'test desc')

    def testRequireID(self):
        with self.assertRaises(Exception):
            i = Institution()

    def testFromConfig1(self):
        i = Institution.from_config({
            'id': '623',
            'username': 'bob',
            'description': 'my account' 
        })
        self.assertEquals(i.id,'623')
        self.assertEquals(i.username,'bob')
        self.assertEquals(i.description,'my account')

    def testFromConfig2(self):
        i = Institution.from_config({
            'id': '623',
            'username': 'bob',
        })
        self.assertEquals(i.id,'623')
        self.assertEquals(i.username,'bob')
        self.assertEquals(i.description,'Scottrade, Inc.')

    def testFromConfig3(self):
        i = Institution.from_config({
            'id': '623',
        })
        self.assertEquals(i.id,'623')
        self.assertEquals(i.username,None)
        self.assertEquals(i.description,'Scottrade, Inc.')

    def testList(self):
        settings = Settings.banks()
        institutions = Institution.list()
        self.assertEquals( len(settings), len(institutions) )

    def testSort(self):
        institutions = [
            Institution('625'),
            Institution('483'),
            Institution('624'),
        ]
        self.assertEquals( [ x.id for x in sorted(institutions) ], ['624','625','483'] )

def testfile_name(filename):
    path = 'testfiles/' + filename
    if ('tests' in os.listdir('.')):
        path = 'tests/' + path
    return path

def testfile(filename):
    return file(testfile_name(filename))

if __name__ == '__main__':
    unittest.main()
