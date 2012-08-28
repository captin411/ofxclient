import StringIO
import os.path
import security
from BeautifulSoup import BeautifulStoneSoup
from ofxhome import OFXHome
from ofxhome import Institution as OFXHomeInstitution
from settings import Settings
from request import Builder
from exceptions import LoginException
import hashlib
import logging

class Institution:
    def __init__(self, id, username=None, description=None):
        dsn = bank_config(id)

        self.id = id
        self.username = username
        self.dsn = dsn
        self.description = description or dsn['name']
        self.password = security.get_password( self.keyring_id() )

    @staticmethod
    def from_config(c):
        return Institution(c.get('id'),username=c.get('username'),description=c.get('description'))

    @staticmethod
    def from_id(id):
        return Institution.from_config( Settings.banks(id) )

    def keyring_id(self):
        return "%s%s" % (self.id,self.username)

    def guid(self):
        return hashlib.sha256(self.keyring_id()).hexdigest()

    @staticmethod
    def list():
        return [ Institution.from_config(s) for s in Settings.banks() ]

    @staticmethod
    def search(query):
        results = OFXHome.search(query)
        return [ Institution(r['id']) for r in results ]

    def save(self):
        # always save the password
        security.set_password(
            self.keyring_id(),
            self.password or ''
        )

        config = Settings.config()
        new_banks = []
        for s in Settings.banks():
            i = Institution.from_config(s)
            if i != self:
                new_banks.append(s)
        new_banks.append({
            'id': self.id,
            'username': self.username,
            'description': self.description,
            'guid': self.guid()
        })

        config['banks'] = new_banks
        Settings.config_save(config)

    def auth_test(self,username=None,password=None):
        u = username or self.username
        if not u:
            raise LoginException("missing username",bank=self)
        p = password or self.password
        if not u:
            raise LoginException("missing password",bank=self)

        builder = Builder(self)
        query = builder.authQuery(username=u,password=p)
        res = builder.doQuery(query)
        ofx = BeautifulStoneSoup(res)

        try:
            sonrs = ofx.find('sonrs')
            code = int(sonrs.find('code').contents[0].strip())
        except:
            raise LoginException("parse error: %s" % res,bank=self)

        try:
            status = sonrs.find('message').contents[0].strip()
        except Exception:
            status = ''

        if code == 0:
            return 1

        security.set_password(
            self.keyring_id(),
            ''
        )
        raise LoginException(status,code=code,bank=self)

    def accounts(self):
        local = self.local_accounts()
        if len(local):
            return local
        else:
            return self.cache_remote_accounts()

    def remote_accounts(self):
        return Account.query_from_institution( self )

    def cache_remote_accounts(self):
        accounts = self.remote_accounts()
        for a in accounts:
            a.save()
        return accounts

    def local_accounts(self):
        return Account.list_from_institution( self )

    def __eq__(self, b):
        return self.guid() == b.guid()

    def __ne__(self, b):
        return self.guid() != b.guid()

    def __cmp__(self, b):
        if self.description == b.description:
            return 0
        elif self.description > b.description:
            return 1
        return -1

    def __repr__(self):
        return repr({
            'id': self.id,
            'description': self.description,
            'username': self.username,
            'guid': self.guid()
        })

bank_config_cache = {}
def bank_config(guid):
    if bank_config_cache.has_key(guid):
        return bank_config_cache[guid]
    path = os.path.join( Settings.fi_cache(), '%s.xml' % guid )
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        logging.info("uncached bank config %s" % guid)
        institution = OFXHome.lookup(guid)
        file = open(path,'w')
        file.write(institution.xml)
        file.close()
    logging.info("parsing file %s" % path)
    bank_config_cache[guid] = OFXHomeInstitution.from_file(path).__dict__
    return bank_config_cache[guid]

from account import Account
