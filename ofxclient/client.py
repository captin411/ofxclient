from __future__ import absolute_import
from __future__ import unicode_literals
try:
    # python 3
    from http.client import HTTPSConnection
except ImportError:
    # python 2
    from httplib import HTTPSConnection
import logging
import time
try:
    # python 3
    from urllib.parse import splittype, splithost
except ImportError:
    # python 2
    from urllib import splittype, splithost
import uuid

DEFAULT_APP_ID = 'QWIN'
DEFAULT_APP_VERSION = '2200'
DEFAULT_OFX_VERSION = '102'

LINE_ENDING = "\r\n"


def ofx_uid():
    return str(uuid.uuid4().hex)


class Client:
    """This communicates with the banks via the OFX protocol

    :param institution: institution to connect to
    :type institution: :py:class:`ofxclient.Institution`
    :param id: client id (optional need for OFX version >= 103)
    :type id: string
    :param app_id: OFX app id
    :type app_id: string
    :param app_version: OFX app version
    :type app_version: string
    :param ofx_version: OFX spec version
    :type ofx_version: string
    """

    def __init__(
        self,
        institution,
        id=ofx_uid(),
        app_id=DEFAULT_APP_ID,
        app_version=DEFAULT_APP_VERSION,
        ofx_version=DEFAULT_OFX_VERSION
    ):
        self.institution = institution
        self.id = id
        self.app_id = app_id
        self.app_version = app_version
        self.ofx_version = ofx_version
        self.cookie = 3

    def authenticated_query(
        self,
        with_message=None,
        username=None,
        password=None
    ):
        """Authenticated query

        If you pass a 'with_messages' array those queries will be passed along
        otherwise this will just be an authentication probe query only.
        """
        u = username or self.institution.username
        p = password or self.institution.password

        contents = ['OFX', self._signOn(username=u, password=p)]
        if with_message:
            contents.append(with_message)
        return LINE_ENDING.join([self.header(), _tag(*contents)])

    def bank_account_query(self, number, date, account_type, bank_id):
        """Bank account statement request"""
        return self.authenticated_query(
            self._bareq(number, date, account_type, bank_id)
        )

    def credit_card_account_query(self, number, date):
        """CC Statement request"""
        return self.authenticated_query(self._ccreq(number, date))

    def brokerage_account_query(self, number, date, broker_id):
        return self.authenticated_query(
            self._invstreq(broker_id, number, date))

    def account_list_query(self, date='19700101000000'):
        return self.authenticated_query(self._acctreq(date))

    def post(self, query):
        i = self.institution
        logging.debug('posting data to %s' % i.url)
        logging.debug('---- request ----')
        logging.debug(query)
        garbage, path = splittype(i.url)
        host, selector = splithost(path)
        h = HTTPSConnection(host, timeout=60)
        h.request('POST', selector, query,
                  {
                      "Content-type": "application/x-ofx",
                      "Accept": "*/*, application/x-ofx",
                      "User-Agent": "httpclient" # This is necessary for TD Bank.
                  })
                      
                  })
        res = h.getresponse()
        response = res.read().decode('ascii', 'ignore')
        logging.debug('---- response ----')
        logging.debug(res.__dict__)
        logging.debug(response)
        res.close()

        return response

    def next_cookie(self):
        self.cookie += 1
        return str(self.cookie)

    def header(self):
        parts = [
            "OFXHEADER:100",
            "DATA:OFXSGML",
            "VERSION:%d" % int(self.ofx_version),
            "SECURITY:NONE",
            "ENCODING:USASCII",
            "CHARSET:1252",
            "COMPRESSION:NONE",
            "OLDFILEUID:NONE",
            "NEWFILEUID:"+ofx_uid(),
            ""
        ]
        return LINE_ENDING.join(parts)

    """Generate signon message"""
    def _signOn(self, username=None, password=None):
        i = self.institution
        u = username or i.username
        p = password or i.password
        fidata = [_field("ORG", i.org)]
        if i.id:
            fidata.append(_field("FID", i.id))

        client_uid = ''
        if str(self.ofx_version) == '103':
            client_uid = _field('CLIENTUID', self.id)

        return _tag("SIGNONMSGSRQV1",
                    _tag("SONRQ",
                         _field("DTCLIENT", now()),
                         _field("USERID", u),
                         _field("USERPASS", p),
                         _field("LANGUAGE", "ENG"),
                         _tag("FI", *fidata),
                         _field("APPID", self.app_id),
                         _field("APPVER", self.app_version),
                         client_uid
                         ))

    def _acctreq(self, dtstart):
        req = _tag("ACCTINFORQ", _field("DTACCTUP", dtstart))
        return self._message("SIGNUP", "ACCTINFO", req)

# this is from _ccreq below and reading page 176 of the latest OFX doc.
    def _bareq(self, acctid, dtstart, accttype, bankid):
        req = _tag("STMTRQ",
                   _tag("BANKACCTFROM",
                        _field("BANKID", bankid),
                        _field("ACCTID", acctid),
                        _field("ACCTTYPE", accttype)),
                   _tag("INCTRAN",
                        _field("DTSTART", dtstart),
                        _field("INCLUDE", "Y")))
        return self._message("BANK", "STMT", req)

    def _ccreq(self, acctid, dtstart):
        req = _tag("CCSTMTRQ",
                   _tag("CCACCTFROM", _field("ACCTID", acctid)),
                   _tag("INCTRAN",
                        _field("DTSTART", dtstart),
                        _field("INCLUDE", "Y")))
        return self._message("CREDITCARD", "CCSTMT", req)

    def _invstreq(self, brokerid, acctid, dtstart):
        req = _tag("INVSTMTRQ",
                   _tag("INVACCTFROM",
                        _field("BROKERID", brokerid),
                        _field("ACCTID", acctid)),
                   _tag("INCTRAN",
                        _field("DTSTART", dtstart),
                        _field("INCLUDE", "Y")),
                   _field("INCOO", "Y"),
                   _tag("INCPOS",
                        _field("DTASOF", now()),
                        _field("INCLUDE", "Y")),
                   _field("INCBAL", "Y"))
        return self._message("INVSTMT", "INVSTMT", req)

    def _message(self, msgType, trnType, request):
        return _tag(msgType+"MSGSRQV1",
                    _tag(trnType+"TRNRQ",
                         _field("TRNUID", ofx_uid()),
                         _field("CLTCOOKIE", self.next_cookie()),
                         request))


def _field(tag, value):
    return "<"+tag+">"+value


def _tag(tag, *contents):
    return LINE_ENDING.join(['<'+tag+'>']+list(contents)+['</'+tag+'>'])


def now():
    return time.strftime("%Y%m%d%H%M%S", time.localtime())
