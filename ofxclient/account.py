import security
from ofxparse import OfxParser
from ofxparse.ofxparse import InvestmentAccount as OfxInvestmentAccount
from request import Builder
from institution import Institution
from settings import Settings
import StringIO, hashlib, time, datetime

class Account:
    def __init__(self, institution=None, routing_number=None, account_type=None, broker_id=None, number=None, description=None, guid=None ):
        if guid is None and number is None:
            raise Exception("must provide either a guid or a number")

        self.institution = institution
        self.number = number or security.get_password( guid )
        self.guid = guid or account_number_hash(number)
        self.routing_number = routing_number
        self.account_type = account_type
        self.broker_id = broker_id

        default_desc = institution.description + ' ****' + self.number[-4:]
        self.description = description or default_desc

        self._statements = {}

    @staticmethod
    def list():
        return [ Account.from_config(s) for s in Settings.accounts() ]

    @staticmethod
    def list_from_institution( institution ):
        return [ x for x in Account.list() if x.institution == institution ]

    @staticmethod
    def query_from_institution( institution ):
        builder = Builder( institution )
        query = builder.acctQuery()
        resp = builder.doQuery( query )
        resp_handle = StringIO.StringIO(resp)
        accounts = []
        for a in OfxParser.parse(resp_handle).accounts:
            accounts.append( Account.from_ofxparser(institution,a) )
        return accounts

    @staticmethod
    def from_ofxparser(institution,ofx):
        return Account(
            institution = institution,
            number = ofx.number,
            description = ofx.desc if hasattr(ofx,'desc') else '',
            routing_number = ofx.routing_number,
            account_type = ofx.account_type,
            broker_id = ofx.brokerid if hasattr(ofx,'brokerid') else '',
        )

    @staticmethod
    def from_config(c):
        institution = Institution.from_config(Settings.banks(c['institution']))
        return Account(
            institution = institution,
            guid = c['guid'],
            description = c['description'],
            routing_number = c['routing_number'],
            account_type = c['account_type'],
            broker_id = c['broker_id']
        )


    @staticmethod
    def from_id(guid):
        return Account.from_config( Settings.accounts(guid) )
    
    def save(self):
        # always save the original account number in the keystore
        security.set_password( self.guid, self.number or '' )
        struct = {
            'guid': self.guid,
            'institution': self.institution.guid(),
            'description': self.description,
            'routing_number': self.routing_number,
            'account_type': self.account_type,
            'broker_id': self.broker_id
        } 

        config = Settings.config()
        new_accounts = []
        for a in Settings.accounts():
            if a['guid'] != self.guid:
                new_accounts.append(a)
        new_accounts.append(struct)

        config['accounts'] = new_accounts
        Settings.config_save(config)

    def delete(self):
        # remove the account number from the security store
        security.set_password( self.guid, None )

        config = Settings.config()
        new_accounts = []
        for a in Settings.accounts():
            if a['guid'] != self.guid:
                new_accounts.append(a)
        config['accounts'] = new_accounts
        Settings.config_save(config)

    def is_bank_account(self):
        return 1 if self.type() == 'bank' else 0

    def is_brokerage_account(self):
        return 1 if self.type() == 'brokerage' else 0

    def is_credit_card_account(self):
        return 1 if self.type() == 'credit' else 0
        
    def type(self):
        if self.broker_id != '':
            return 'brokerage' 
        if self.routing_number != '':
            return 'bank'
        if self.account_type != '':
            return 'bank'
        return 'credit'

    def download(self,days=60):
        days_ago = datetime.datetime.now() - datetime.timedelta( days=days )
        from_date = time.strftime("%Y%m%d",days_ago.timetuple())
        builder = Builder(self.institution) 
        query = None
        if self.is_brokerage_account():
            query = builder.invstQuery(self.broker_id,self.number,from_date)
        elif self.is_bank_account():
            query = builder.baQuery(self.number,from_date,self.account_type,self.routing_number)
        elif self.is_credit_card_account():
            query = builder.ccQuery(self.number,from_date)
            
        if query is None:
            return 
        response = builder.doQuery(query)
        return StringIO.StringIO(response)

    def statement(self,days=60):
        days_ago = datetime.datetime.now() - datetime.timedelta( days=days )
        from_date = time.strftime("%Y%m%d",days_ago.timetuple())
        if not from_date in self._statements:
            data = self.download(days=days)
            ofx = OfxParser.parse( data )
            self._statements[from_date] = ofx.account.statement

        return self._statements[from_date]

    def transactions(self,days=60):
        return self.statement(days=days).transactions

    def __repr__(self):
        return str({
            'type': self.type(),
            'number': '******',
            'guid': self.guid,
            'routing_number': self.routing_number,
            'description': self.description,
            'broker_id': self.broker_id,
            'institution.description': self.institution.description,
            'account_type': self.account_type,
        })

def account_number_hash(clear):
    return hashlib.sha256( "account %s" % clear ).hexdigest()
