from ofxparse import OfxParser, AccountType
from request import Builder
import StringIO, time, datetime

class Account(object):
    def __init__(self, number, institution):
        self.institution = institution
        self.number      = number

    def builder(self):
        return Builder(self.institution) 

    def download(self,days=60):
        days_ago  = datetime.datetime.now() - datetime.timedelta( days=days )
        as_of     = time.strftime("%Y%m%d",days_ago.timetuple())
        query     = self.download_query( as_of = as_of )
        response  = self.builder().doQuery(query)
        return StringIO.StringIO(response)

    def download_parsed(self,days=60):
        return OfxParser.parse( self.download(days=days) )

    def statement(self,days=60):
        parsed = self.download_parsed(days=days)
        return parsed.account.statement

    def transactions(self,days=60):
        return self.statement(days=days).transactions

    @staticmethod
    def from_ofxparse( data, institution ):
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

    def __init__(self, broker_id, **kwargs):
        super( BrokerageAccount, self ).__init__(**kwargs)
        self.broker_id = broker_id

    def download_query(self,as_of):
        b = self.builder()
        q = b.invstQuery(self.broker_id,self.number,as_of)
        return q

class BankAccount(Account):

    def __init__(self, routing_number, account_type, **kwargs):
        super( BankAccount, self ).__init__(**kwargs)
        self.routing_number = routing_number
        self.account_type   = account_type

    def download_query(self,as_of):
        b = self.builder()
        q = b.baQuery(self.number,as_of,self.account_type,self.routing_number)
        return q

class CreditCardAccount(Account):
    def __init__(self, **kwargs):
        super( CreditCardAccount, self ).__init__(**kwargs)

    def download_query(self,as_of):
        b = self.builder()
        q = b.ccQuery(self.number,as_of)
        return q
