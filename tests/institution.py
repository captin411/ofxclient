import unittest
from ofxclient import Client
from ofxclient import Institution

class OfxInstitutionTests(unittest.TestCase):

    def testClientDefaultsPreserved(self):
        i = Institution(
                id='1',
                org='org',
                url='http://example.com',
                username='username',
                password='password'
        )

        c  = Client(institution=i)
        ic = i.client()

        self.assertEqual( c.id, ic.id )
        self.assertEqual( c.app_id, ic.app_id )
        self.assertEqual( c.app_version, ic.app_version )
        self.assertEqual( c.ofx_version, ic.ofx_version )

    def testClientSomeOverride(self):
        i = Institution(
                id='1',
                org='org',
                url='http://example.com',
                username='username',
                password='password',
                client_args = {
                    'app_id': 'capp_id',
                }
        )

        c  = Client(institution=i)
        ic = i.client()
        self.assertEqual( ic.app_id, 'capp_id', 'overridden app_id')
        self.assertNotEqual( ic.app_id, c.app_id, 'overridden app_id')
        self.assertEqual( ic.id, c.id, 'default id')
        self.assertEqual( ic.app_version, c.app_version, 'default app version')
        self.assertEqual( ic.ofx_version, c.ofx_version, 'default ofx version')

    def testClientAllOverride(self):
        i = Institution(
                id='1',
                org='org',
                url='http://example.com',
                username='username',
                password='password',
                client_args = {
                    'id': 'cid',
                    'app_id': 'capp_id',
                    'app_version': 'capp_version',
                    'ofx_version': 'cofx_version'
                }
        )

        c = i.client()
        self.assertEqual( c.id, 'cid' )
        self.assertEqual( c.app_id, 'capp_id' )
        self.assertEqual( c.app_version, 'capp_version' )
        self.assertEqual( c.ofx_version, 'cofx_version' )

    def testRequiredParams(self):
        self.assertRaises(TypeError,Institution.__init__)

        a = { 'id': '1' }
        self.assertRaises(TypeError,Institution,**a)

        a = { 'id': '1', 'org': 'org' }
        self.assertRaises(TypeError,Institution,**a)

        a = { 'id': '1', 'org': 'org', 'url': 'url' }
        self.assertRaises(TypeError,Institution,**a)

        a = { 'id': '1', 'org': 'org', 'url': 'url', 'username': 'username' }
        self.assertRaises(TypeError,Institution,**a)
