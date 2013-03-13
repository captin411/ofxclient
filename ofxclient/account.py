from ofxparse import OfxParser, AccountType
from request  import Builder
import datetime
import StringIO
import time
import hashlib

class Account(object):
    """Base class for accounts at an institution

    It provides basic methods for retrieving transactions
    that are common to all different types of accounts.

    Subclasses only need to implement the download_query method
    which is expected to take an 'as_of' parameter representing
    an effective lower date boundary in 'YYYYMMDD' format.  The
    return value of this function is expected to be a prepared
    query as returned by the ofxclient.request.Builder

    See these subclasses for more details:
    BankAccount
    CreditCardAccount
    BrokerageAccount
    """
    def __init__(self, number, institution ):
        self.institution = institution
        self.number      = number

    def local_id(self):
        """A unique identifier useful when trying to dedupe or otherwise 
        distinguish one account instance from another.
        """
        return hashlib.sha256("%s%s" % (
                self.institution.local_id(),
                self.number ))

    def builder(self):
        return Builder(self.institution) 

    def download(self,days=60):
        """Return a StringIO wrapped string with the raw OFX response"""
        days_ago  = datetime.datetime.now() - datetime.timedelta( days=days )
        as_of     = time.strftime("%Y%m%d",days_ago.timetuple())
        query     = self.download_query( as_of = as_of )
        response  = self.builder().doQuery(query)
        return StringIO.StringIO(response)

    def download_parsed(self,days=60):
        """Return the downloaded OFX response parsed by ofxparse.OfxParser"""
        return OfxParser.parse( self.download(days=days) )

    def statement(self,days=60):
        """Return the ofxparse.Statement for this account"""
        parsed = self.download_parsed(days=days)
        return parsed.account.statement

    def transactions(self,days=60):
        """Return a list of ofxparse.Transaction objects"""
        return self.statement(days=days).transactions

    @staticmethod
    def from_ofxparse( data, institution ):
        """Factory method to return an ofxclient.Account subclass from an ofxparse.Account result"""
        if data.type == AccountType.Bank:
            return BankAccount(
                    institution=institution,
                    number=data.account_id,
                    routing_number=data.routing_number,
                    account_type=data.account_type)
        elif data.type == AccountType.CreditCard:
            return CreditCardAccount( 
                    institution=institution,
                    number=data.account_id )
        elif data.type == AccountType.Investment:
            return BrokerageAccount(
                    institution=institution,
                    number=data.account_id,
                    broker_id=data.brokerid)
        raise ValueError("unknown account type: %s" % data.type)


class BrokerageAccount(Account):
    """Implementation representing a brokerage/investment account"""
    def __init__(self, broker_id, **kwargs):
        super( BrokerageAccount, self ).__init__(**kwargs)
        self.broker_id = broker_id

    def download_query(self,as_of):
        """formulate the specific query needed for download"""
        b = self.builder()
        q = b.invstQuery(self.broker_id,self.number,as_of)
        return q

class BankAccount(Account):
    """Implementation representing a checking or savings account"""
    def __init__(self, routing_number, account_type, **kwargs):
        super( BankAccount, self ).__init__(**kwargs)
        self.routing_number = routing_number
        self.account_type   = account_type

    def download_query(self,as_of):
        """formulate the specific query needed for download"""
        b = self.builder()
        q = b.baQuery(self.number,as_of,self.account_type,self.routing_number)
        return q

class CreditCardAccount(Account):
    """Implementation representing a credit card account"""
    def __init__(self, **kwargs):
        super( CreditCardAccount, self ).__init__(**kwargs)

    def download_query(self,as_of):
        """formulate the specific query needed for download"""
        b = self.builder()
        q = b.ccQuery(self.number,as_of)
        return q
