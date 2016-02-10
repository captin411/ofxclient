import unittest

from ofxclient import Account
from ofxclient import BankAccount
from ofxclient import BrokerageAccount
from ofxclient import CreditCardAccount
from ofxclient import Institution


class OfxAccountTests(unittest.TestCase):

    def setUp(self):
        institution = Institution(
                id='1',
                org='Example',
                url='http://example.com',
                username='username',
                password='password'
        )
        self.institution = institution

    def testNumberRequired(self):
        a = {'institution': self.institution}
        self.assertRaises(TypeError, Account, **a)

    def testInstitutionRequired(self):
        a = {'number': '12345'}
        self.assertRaises(TypeError, Account, **a)

    def testMasked(self):
        account = Account(
                number='12345',
                institution=self.institution
        )
        self.assertEqual(account.number_masked(), '***2345')
        account.number = '1234'
        self.assertEqual(account.number_masked(), '***1234')
        account.number = '123'
        self.assertEqual(account.number_masked(), '***123')
        account.number = '12'
        self.assertEqual(account.number_masked(), '***12')
        account.number = '1'
        self.assertEqual(account.number_masked(), '***1')

    def testDescription(self):
        account = Account(
                number='12345',
                institution=self.institution
        )
        self.assertEqual(
                account.description,
                '***2345',
                'kwarg is not required and defaults')

        account = Account(
                number='12345',
                institution=self.institution,
                description=None
        )
        self.assertEqual(account.description, '***2345', 'None defaults')

        account = Account(
                number='12345',
                institution=self.institution,
                description=''
        )
        self.assertEqual(
                account.description,
                '***2345',
                'empty string desc defaults')

        account = Account(
                number='12345',
                institution=self.institution,
                description='0'
        )
        self.assertEqual(account.description, '0', '0 string is preserved')

        account = Account(
                number='12345',
                institution=self.institution,
                description='passed'
        )
        self.assertEqual(account.description, 'passed')

    def testNoInstitution(self):
        account = Account(
                number='12345',
                institution=None
        )
