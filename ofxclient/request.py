import uuid, httplib, time, urllib2
import logging

class Builder:
    def __init__(self, institution ):
        self.institution = institution
        # 'On April 30, of each year, Quicken discontinues its support for
        # any of its versions more than 2 years old.'
        # http://microsoftmoneyoffline.wordpress.com/appid-appver/
        # 1800 == Quicken Windows 2010
        # 2100 == Quicken Windows 2012
        # 2200 == Quicken Windows 2013
        self.app_id = 'QWIN'
        self.app_ver = '2200'
        self.cookie = 3

    def _cookie(self):
        self.cookie += 1
        return str(self.cookie)

    """Generate signon message"""
    def _signOn(self,username=None,password=None):
        i = self.institution
        bank = i.dsn
        u = username or i.username
        p = password or i.password
        fidata = [ _field("ORG",bank['org']) ]
        if bank.has_key("fid"):
            fidata += [ _field("FID",bank["fid"]) ]
        return _tag("SIGNONMSGSRQV1",
                    _tag("SONRQ",
                         _field("DTCLIENT",_date()),
                         _field("USERID",u),
                         _field("USERPASS",p),
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

    def authQuery(self, username=None, password=None):
        u = username or self.institution.username
        p = password or self.institution.password
        return str.join("\r\n",[self._header(), _tag("OFX", self._signOn(username=u,password=p))])

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
        logging.info('Builder.doQuery')
        # N.B. urllib doesn't honor user Content-type, use urllib2
        i = self.institution
        bank = i.dsn
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
