import keyring
from keyrings.alt.file import PlaintextKeyring
import os
import os.path
import tempfile
import unittest
from test.test_support import EnvironmentVarGuard

import ofxclient.config
from ofxclient.config import OfxConfig
from ofxclient import Institution, CreditCardAccount


class OfxConfigTests(unittest.TestCase):

    def setUp(self):
        keyring.set_keyring(PlaintextKeyring())

        self.env = EnvironmentVarGuard()
        self.temp_file = tempfile.NamedTemporaryFile()

        test_path = os.path.dirname(os.path.realpath(__file__))
        self.env['XDG_DATA_HOME'] = test_path
        self.env['XDG_CONFIG_HOME'] = test_path

    def tearDown(self):
        self.temp_file.close()

    def testFileCreated(self):
        file_name = self.temp_file.name
        self.temp_file.close()

        self.assertFalse(os.path.exists(file_name))

        c = OfxConfig(file_name=file_name)  # noqa
        self.assertTrue(os.path.exists(file_name))

        os.remove(file_name)

    def testAddAccount(self):
        c = OfxConfig(file_name=self.temp_file.name)

        i = Institution(
                id='1',
                org='org',
                url='url',
                username='user',
                password='pass'
        )
        a = CreditCardAccount(institution=i, number='12345')

        c.add_account(a)
        self.assertEqual(len(c.accounts()), 1)
        self.assertEqual(c.account(a.local_id()).local_id(), a.local_id())

    def testLoadFromFile(self):
        c = OfxConfig(file_name=self.temp_file.name)
        i = Institution(
                id='1',
                org='org',
                url='url',
                username='user',
                password='pass'
        )
        a = CreditCardAccount(institution=i, number='12345')
        c.add_account(a)
        c.save()

        c = OfxConfig(file_name=self.temp_file.name)
        got = c.account(a.local_id())
        self.assertEqual(len(c.accounts()), 1)
        self.assertEqual(got.local_id(), a.local_id())
        self.assertEqual(got.number, a.number)
        self.assertEqual(got.institution.local_id(), a.institution.local_id())
        self.assertEqual(got.institution.id, a.institution.id)
        self.assertEqual(got.institution.org, a.institution.org)
        self.assertEqual(got.institution.url, a.institution.url)
        self.assertEqual(got.institution.username, a.institution.username)
        self.assertEqual(got.institution.password, a.institution.password)

    def testFieldsSecured(self):
        if not ofxclient.config.KEYRING_AVAILABLE:
            return

        # always skip these for now
        return

        c = OfxConfig(file_name=self.temp_file.name)

        i = Institution(
                id='1',
                org='org',
                url='url',
                username='user',
                password='pass'
        )
        a = CreditCardAccount(institution=i, number='12345')
        c.add_account(a)

        self.assertTrue(
            c.parser.is_secure_option(a.local_id(), 'institution.username')
        )
        self.assertTrue(
            c.parser.is_secure_option(a.local_id(), 'institution.password')
        )

    def testFieldsRemainUnsecure(self):
        if not ofxclient.config.KEYRING_AVAILABLE:
            return

        # always skip these for now
        return

        c = OfxConfig(file_name=self.temp_file.name)
        i = Institution(
                id='1',
                org='org',
                url='url',
                username='user',
                password='pass'
        )
        a = CreditCardAccount(institution=i, number='12345')
        c.add_account(a)

        # pretend the user put their password in there in the clear on purpose
        c.parser.remove_option(a.local_id(), 'institution.password')
        c.parser.set(a.local_id(), 'institution.password', 'pass')
        c.save()

        c = OfxConfig(file_name=self.temp_file.name)
        self.assertTrue(
            c.parser.is_secure_option(a.local_id(), 'institution.username')
        )
        self.assertFalse(
            c.parser.is_secure_option(a.local_id(), 'institution.password')
        )

    def testResecuredAfterEncryptAccount(self):
        if not ofxclient.config.KEYRING_AVAILABLE:
            return

        # always skip these for now
        return

        c = OfxConfig(file_name=self.temp_file.name)
        i = Institution(
                id='1',
                org='org',
                url='url',
                username='user',
                password='pass'
        )
        a1 = CreditCardAccount(institution=i, number='12345')
        c.add_account(a1)
        a2 = CreditCardAccount(institution=i, number='67890')
        c.add_account(a2)

        # pretend the user put their password in there in the clear on purpose
        # to fix something... and then wants it to be resecured later on
        c.parser.remove_option(a1.local_id(), 'institution.password')
        c.parser.set(a1.local_id(), 'institution.password', 'pass')
        c.save()

        c = OfxConfig(file_name=self.temp_file.name)
        self.assertEqual(len(c.accounts()), 2)
        self.assertEqual(len(c.encrypted_accounts()), 1)
        self.assertEqual(len(c.unencrypted_accounts()), 1)
        self.assertTrue(
            c.parser.is_secure_option(a1.local_id(), 'institution.username')
        )
        self.assertFalse(
            c.parser.is_secure_option(a1.local_id(), 'institution.password')
        )

        c.encrypt_account(a1.local_id())
        self.assertEqual(len(c.accounts()), 2)
        self.assertEqual(len(c.encrypted_accounts()), 2)
        self.assertEqual(len(c.unencrypted_accounts()), 0)
        self.assertTrue(
            c.parser.is_secure_option(a1.local_id(), 'institution.username')
        )
        self.assertTrue(
            c.parser.is_secure_option(a1.local_id(), 'institution.password')
        )
