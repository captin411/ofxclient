import StringIO
from account import Account
from ofxparse import OfxParser
from BeautifulSoup import BeautifulStoneSoup
from request import Builder
import logging

class Institution:
    def __init__(self, id, org, url, username, password ):
        self.id = id
        self.org = org
        self.url = url
        self.username = username
        self.password = password

    def authenticate(self,username=None,password=None):
        u = username or self.username
        p = password or self.password

        builder = Builder(self)
        query = builder.authQuery(username=u,password=p)
        res = builder.doQuery(query)
        ofx = BeautifulStoneSoup(res)

        sonrs = ofx.find('sonrs')
        code = int(sonrs.find('code').contents[0].strip())

        try:
            status = sonrs.find('message').contents[0].strip()
        except Exception:
            status = ''

        if code == 0:
            return 1

        raise ValueError(status)

    def accounts(self):
        builder = Builder( self )
        query   = builder.acctQuery()
        resp    = builder.doQuery(query)
        resp_handle = StringIO.StringIO(resp)

        accounts = []

        for a in OfxParser.parse(resp_handle).accounts:
            accounts.append( Account.from_ofxparse(a,institution=self) )
        return accounts
