try:
    from configparser import ConfigParser, NoOptionError
except ImportError:
    from ConfigParser import ConfigParser, NoOptionError
import unittest

from ofxclient.config import SecurableConfigParser


def makeConfig(keyring_available=True, **kwargs):
    conf = None
    conf = SecurableConfigParser(keyring_available=keyring_available, **kwargs)
    conf.add_section('section1')
    conf.add_section('section2')
    conf.set('section1', 'username', 'USERNAME')
    conf.set_secure('section1', 'password', 'PASSWORD')
    conf.set('section2', 'question', 'answer')
    conf.set_secure('section2', 'ssn', '111-11-1111')
    return conf


class IdentifySecureOptionTests(unittest.TestCase):

    def testIsSecureOption(self):
        c = makeConfig()
        self.assertTrue(c.is_secure_option('section1', 'password'))
        self.assertTrue(c.is_secure_option('section2', 'ssn'))
        self.assertFalse(c.is_secure_option('section1', 'username'))
        self.assertFalse(c.is_secure_option('section2', 'question'))

    def testStaysSecure(self):
        c = makeConfig()
        self.assertTrue(c.is_secure_option('section1', 'password'))
        c.set('section1', 'password', 'MYPASS')
        self.assertTrue(c.is_secure_option('section1', 'password'))

    def testStaysUnsecure(self):
        c = makeConfig()
        self.assertFalse(c.is_secure_option('section1', 'username'))
        c.set('section1', 'username', 'MYUSER')
        self.assertFalse(c.is_secure_option('section1', 'username'))

    def testSetThenSetSecureTurnsSecure(self):
        c = makeConfig()
        c.set('section1', 'foo', 'bar')
        self.assertFalse(c.is_secure_option('section1', 'foo'))
        c.set_secure('section1', 'foo', 'bar')
        self.assertTrue(c.is_secure_option('section1', 'foo'))
        c.set('section1', 'foo', 'bar')
        self.assertTrue(c.is_secure_option('section1', 'foo'))

    def testItemsHavePasswords(self):
        c = makeConfig()
        items = sorted(c.items('section1'))
        self.assertEqual(
                items,
                [('password', 'PASSWORD'), ('username', 'USERNAME')]
        )
        self.assertEqual(len(items), 2)

    def testSecureItems(self):
        c = makeConfig()
        items = sorted(c.secure_items('section1'))
        self.assertEqual(items, [('password', 'PASSWORD')])
        self.assertEqual(len(items), 1)
        c.remove_option('section1', 'password')
        items = sorted(c.secure_items('section1'))
        self.assertEqual(len(items), 0)

    def testGet(self):
        c = makeConfig()
        self.assertEqual(c.get('section1', 'password'), 'PASSWORD')
        self.assertNotEqual(
                ConfigParser.get(c, 'section1', 'password'),
                'PASSWORD'
        )
        self.assertEqual(c.get('section1', 'username'), 'USERNAME')
        c.remove_option('section1', 'password')
        self.assertRaises(NoOptionError, c.get, 'section1', 'password')

    def testUnsavedOptions(self):
        c = makeConfig()
        s_option = "%s%s" % ('section1', 'foo2')

        c.set('section1', 'foo2', 'bar2')
        self.assertFalse(s_option in c._unsaved)

        c.remove_option('section1', 'foo2')
        self.assertFalse(s_option in c._unsaved)

        c.set_secure('section1', 'foo2', 'bar2')
        self.assertTrue(s_option in c._unsaved)
        self.assertTrue(c._unsaved[s_option][0] == 'set')
        self.assertTrue(c._unsaved[s_option][1] == 'bar2')

        c.remove_option('section1', 'foo2')
        self.assertTrue(s_option in c._unsaved)
        self.assertTrue(c._unsaved[s_option][0] == 'delete')
        self.assertTrue(c._unsaved[s_option][1] is None)

    def testKeyringOffSet(self):
        c = makeConfig(keyring_available=False)
        self.assertFalse(c.is_secure_option('section1', 'username'))
        self.assertFalse(c.is_secure_option('section1', 'password'))

        self.assertEqual(c._unsaved, {})

        c.set_secure('section1', 'password', 'PASSWORD')
        self.assertFalse(c.is_secure_option('section1', 'password'))

        self.assertEqual(c.get('section1', 'password'), 'PASSWORD')
        self.assertEqual(c.get('section1', 'username'), 'USERNAME')

        c.remove_option('section1', 'password')
        self.assertFalse(c.is_secure_option('section1', 'password'))
        self.assertEqual(c._unsaved, {})

    pass
