from ofxhome import API
from ofxhome import Institution as APIInstitution
import os, os.path, uuid, httplib, time, urllib2
from ofxparse import OfxParser
from ofxparse.ofxparse import InvestmentAccount as OfxInvestmentAccount
import StringIO
import hashlib
try:
    import json
except ImportError:
    import simplejson as json

CONFFILE = os.path.expanduser('~/.pyofxclient.conf')

CONFFILE_DEFAULT = {
    'cache_folder': '~/.pyofxclient',
    'ofx_folder': '~/.pyofxclient/downloads',
    'banks': [],
    'accounts': [],
}

class Settings:
    @staticmethod
    def fi_cache():
        return Settings.ensure_path( os.path.join(Settings.cache(),'fi') )

    @staticmethod
    def cache():
        conf = Settings.config()
        return Settings.ensure_path( os.path.expanduser(conf['cache_folder']) )

    @staticmethod
    def ensure_path(path):
        if not os.path.exists(path):
            os.makedirs(path)
        return path
    
    @staticmethod
    def config():
        if not os.path.exists( CONFFILE ) or os.path.getsize(CONFFILE) == 0:
            Settings.config_save(CONFFILE_DEFAULT)
        conf = json.loads( open(CONFFILE,'r').read() )

        should_write = False
        for k in CONFFILE_DEFAULT.keys():
            if not conf.has_key(k):
                should_write = True
                conf[k] = CONFFILE_DEFAULT[k]
        if should_write:
            Settings.config_save(conf)

        return conf

    @staticmethod
    def config_save(config):
        conf = open(CONFFILE,'w')
        conf.write( json.dumps(config, sort_keys=True, indent=4) )
        conf.close()
        return Settings.config()

    @staticmethod
    def banks(only_guid=None):
        conf = Settings.config()
        banks = conf['banks']
        if only_guid is not None:
            for b in banks:
                if b['guid'] == only_guid:
                    return b
        else:
            return banks

    @staticmethod
    def accounts(only_hash=None):
        conf = Settings.config()
        accounts = conf['accounts']
        if only_hash is not None:
            for a in accounts:
                if a['account_hash'] == only_hash:
                    return a
        else:
            return accounts
        

class Institution:
    def __init__(self, guid, username=None, password=None ):
        self.guid   = guid
        self.bank   = self.bank_config(guid)
        self.username = username
        self.password = password
        self._accounts = None
        self._rb = RequestBuilder(self);
        pass

    def accounts(self):
        if self._accounts is None:
            response = self._rb.doQuery( self._rb.acctQuery() )
            accounts = []
            for a in OfxParser.parse( StringIO.StringIO(response)).accounts:
                accounts.append( Account(self,ofx_account=a) )
            self._accounts = accounts
        return self._accounts

    def bank_config(self,guid):
        path = self.config_path()
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            institution = API.lookup(self.guid)
            file = open(path,'w')
            file.write(str(institution))
            file.close()
        return APIInstitution.from_file(path).dict()

    def config_path(self):
        return os.path.join( Settings.fi_cache(), '%s.xml' % self.guid )

class Account:
    def __init__(self, institution, ofx_account=None):
        self.institution = institution
        self._rb = RequestBuilder(self.institution);
        self._statements = {}
        if ofx_account is not None:
            self.number = ofx_account.number
            self.hashed_number = Account.hash(ofx_account.number)
            self.routing_number = ofx_account.routing_number
            self.account_type = ofx_account.account_type
            self.type = ofx_account.type
            if isinstance(ofx_account, OfxInvestmentAccount):
                self.brokerid = ofx_account.brokerid
            else:
                self.brokerid = ''

    def statement(self,as_of=time.time()-60*86400):
        from_date = time.strftime("%Y%m%d",time.localtime(as_of))
        if not from_date in self._statements:
            query = None
            if self.brokerid:
                query = self._rb.invstQuery(self.brokerid,self.number, from_date)
            elif self.account_type != '':
                query = self._rb.baQuery(self.number,from_date,self.account_type,self.routing_number)
            elif self.account_type == '':
                query = self._rb.ccQuery(self.number,from_date)
                
            if query is None:
                return 

            response = self._rb.doQuery(query)
            ofx = OfxParser.parse( StringIO.StringIO(response))
            self._statements[from_date] = ofx.account.statement

        return self._statements[from_date]

    def transactions(self,as_of=time.time()-60*86400):
        return self.statement(as_of).transactions

    def __repr__(self):
        return str({
            'account': self.number,
            'account_hash': self.hashed_number,
            'routing_number': self.routing_number,
            'bank': self.institution.bank['name'],
            'account_type': self.account_type,
            'type': self.type,
        })

    @staticmethod
    def load_by_hash(hash,institution):
        accounts = institution.accounts()
        for a in accounts:
            if hash == Account.hash(a.number):
                return Account(institution,ofx_account=a)

    @staticmethod
    def hash(clear):
        return hashlib.sha256().hexdigest()
        
         

class RequestBuilder:
    def __init__(self, institution ):
        self.institution = institution
        self.app_id = 'QWIN'
        self.app_ver = '1800'
        self.cookie = 3

    def _cookie(self):
        self.cookie += 1
        return str(self.cookie)

    """Generate signon message"""
    def _signOn(self):
        i = self.institution
        bank = i.bank 
        fidata = [ _field("ORG",bank['org']) ]
        if bank.has_key("fid"):
            fidata += [ _field("FID",bank["fid"]) ]
        return _tag("SIGNONMSGSRQV1",
                    _tag("SONRQ",
                         _field("DTCLIENT",_date()),
                         _field("USERID",i.username),
                         _field("USERPASS",i.password),
                         _field("LANGUAGE","ENG"),
                         _tag("FI", *fidata),
                         _field("APPID",self.app_id),
                         _field("APPVER",self.app_ver),
                         ))

    def _acctreq(self, dtstart):
        req = _tag("ACCTINFORQ",_field("DTACCTUP",dtstart))
        return self._message("SIGNUP","ACCTINFO",req)

# this is from _ccreq below and reading page 176 of the latest OFX doc.
    def _bareq(self, acctid, dtstart, accttype, bankid):
        req = _tag("STMTRQ",
               _tag("BANKACCTFROM",
                   _field("BANKID",bankid),
                    _field("ACCTID",acctid),
                _field("ACCTTYPE",accttype)),
               _tag("INCTRAN",
                   _field("DTSTART",dtstart),
                _field("INCLUDE","Y")))
        return self._message("BANK","STMT",req)
    
    def _ccreq(self, acctid, dtstart):
        req = _tag("CCSTMTRQ",
                   _tag("CCACCTFROM",_field("ACCTID",acctid)),
                   _tag("INCTRAN",
                        _field("DTSTART",dtstart),
                        _field("INCLUDE","Y")))
        return self._message("CREDITCARD","CCSTMT",req)

    def _invstreq(self, brokerid, acctid, dtstart):
        req = _tag("INVSTMTRQ",
                   _tag("INVACCTFROM",
                      _field("BROKERID", brokerid),
                      _field("ACCTID",acctid)),
                   _tag("INCTRAN",
                        _field("DTSTART",dtstart),
                        _field("INCLUDE","Y")),
                   _field("INCOO","Y"),
                   _tag("INCPOS",
                        _field("DTASOF", _date()),
                        _field("INCLUDE","Y")),
                   _field("INCBAL","Y"))
        return self._message("INVSTMT","INVSTMT",req)

    def _message(self,msgType,trnType,request):
        return _tag(msgType+"MSGSRQV1",
                    _tag(trnType+"TRNRQ",
                         _field("TRNUID",_genuuid()),
                         _field("CLTCOOKIE",self._cookie()),
                         request))
    
    def _header(self):
        return str.join("\r\n",[ "OFXHEADER:100",
                           "DATA:OFXSGML",
                           "VERSION:102",
                           "SECURITY:NONE",
                           "ENCODING:USASCII",
                           "CHARSET:1252",
                           "COMPRESSION:NONE",
                           "OLDFILEUID:NONE",
                           "NEWFILEUID:"+_genuuid(),
                           ""])

    def baQuery(self, acctid, dtstart, accttype, bankid):
        """Bank account statement request"""
        return str.join("\r\n",[self._header(),
                       _tag("OFX",
                                self._signOn(),
                                self._bareq(acctid, dtstart, accttype, bankid))])
                        
    def ccQuery(self, acctid, dtstart):
        """CC Statement request"""
        return str.join("\r\n",[self._header(),
                          _tag("OFX",
                               self._signOn(),
                               self._ccreq(acctid, dtstart))])

    def acctQuery(self,dtstart='19700101000000'):
        return str.join("\r\n",[self._header(),
                          _tag("OFX",
                               self._signOn(),
                               self._acctreq(dtstart))])

    def invstQuery(self, brokerid, acctid, dtstart):
        return str.join("\r\n",[self._header(),
                          _tag("OFX",
                               self._signOn(),
                               self._invstreq(brokerid, acctid,dtstart))])

    def doQuery(self,query):
        # N.B. urllib doesn't honor user Content-type, use urllib2
        i = self.institution
        bank = i.bank 
        garbage, path = urllib2.splittype(bank['url'])
        host, selector = urllib2.splithost(path)
        h = httplib.HTTPSConnection(host)
        h.request('POST', selector, query, 
                  { "Content-type": "application/x-ofx",
                    "Accept": "*/*, application/x-ofx"
                  })
        res = h.getresponse()
        response = res.read()
        res.close()

        return response
        
def _field(tag,value):
    return "<"+tag+">"+value

def _tag(tag,*contents):
    return str.join("\r\n",["<"+tag+">"]+list(contents)+["</"+tag+">"])

def _date():
    return time.strftime("%Y%m%d%H%M%S",time.localtime())

def _genuuid():
    return uuid.uuid4().hex
