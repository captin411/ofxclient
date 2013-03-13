import StringIO
import hashlib
from account import Account
from ofxparse import OfxParser
from BeautifulSoup import BeautifulStoneSoup
from request import Builder

class Institution(object):
    """Represents an institution or bank

    This is where you specify all connection details needed
    for the specific institution.

    For help obtaining the id, org, and url; please see the
    ofxhome python module and/or the http://ofxhome.com website.
    """
    def __init__(self, id, org, url, username, password, description=None ):
        self.id = id
        self.org = org
        self.url = url
        self.username = username
        self.password = password
        self.description = description or self.default_description()

    def local_id(self):
        """A unique identifier useful when trying to dedupe or otherwise 
        distinguish one institution instance from another.
        """
        return hashlib.sha256("%s%s" % (
                self.id,
                self.username ))

    def default_description(self):
        """Get the default institution description"""
        return self.org

    def authenticate(self,username=None,password=None):
        """Test the authentication credentials

        Raises a ValueError if there is a problem authenticating
        with the human readable reason given by the institution.
        """

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
        """Return a list of ofxclient.Account objects for this institution

        These objects let you download statements, transactions, positions,
        and perform balance checks.
        """
        builder = Builder( self )
        query   = builder.acctQuery()
        resp    = builder.doQuery(query)
        resp_handle = StringIO.StringIO(resp)

        accounts = []

        for a in OfxParser.parse(resp_handle).accounts:
            accounts.append( Account.from_ofxparse(a,institution=self) )
        return accounts
