from ofxparse import OfxParser, AccountType
import datetime
from io import BytesIO
import time
import hashlib


class Account(object):
    """Base class for accounts at an institution

    :param number: The account number
    :type number: string
    :param institution: The bank this belongs to
    :type institution: :py:class:`ofxclient.Institution` object
    :param description: optional account description
    :type description: string or None

    This class is almost never never instantiated on it's own. Instead,
    sub-classes are instantiated.

    In most cases these subclasses are either being deserialized from a
    config file entry, a serialization hash, or returned by the
    :py:meth:`ofxclient.Institution.accounts` method.

    Example from a saved config entry::

      from ofxclient.config import OfxConfig
      account = OfxConfig().account('local_id() string')

    Example of deserialization::

      from ofxclient import BankAccount
      # assume 'inst' is an Institution()
      a1    = BankAccount(number='asdf',institution=inst)
      data1 = a1.serialize()
      a2    = Account.deserialize(data1)

    Example by querying the bank directly::

      from ofxclient import Institution
      # assume an Institution() is configured with
      # a username/password etc
      accounts = institution.accounts()

    .. seealso::

       :py:class:`ofxclient.BankAccount`
       :py:class:`ofxclient.BrokerageAccount`
       :py:class:`ofxclient.CreditCardAccount`

    """
    def __init__(self, number, institution, description=None):
        self.institution = institution
        self.number = number
        self.description = description or self._default_description()

    def local_id(self):
        """Locally generated unique account identifier.

        :rtype: string
        """
        return hashlib.sha256(("%s%s" % (
            self.institution.local_id(),
            self.number)).encode()).hexdigest()

    def number_masked(self):
        """Masked version of the account number for privacy.

        :rtype: string
        """
        return "***%s" % self.number[-4:]

    def long_description(self):
        """Long description of the account (includes institution description).

        :rtype: string
        """
        return "%s: %s" % (self.institution.description, self.description)

    def _default_description(self):
        return self.number_masked()

    def download(self, days=60):
        """Downloaded OFX response for the given time range

        :param days: Number of days to look back at
        :type days: integer
        :rtype: :py:class:`BytesIO`

        """
        days_ago = datetime.datetime.now() - datetime.timedelta(days=days)
        as_of = time.strftime("%Y%m%d", days_ago.timetuple())
        query = self._download_query(as_of=as_of)
        response = self.institution.client().post(query)
        return BytesIO(response)

    def download_parsed(self, days=60):
        """Downloaded OFX response parsed by :py:meth:`OfxParser.parse`

        :param days: Number of days to look back at
        :type days: integer
        :rtype: :py:class:`ofxparser.Ofx`
        """
        return OfxParser.parse(self.download(days=days))

    def statement(self, days=60):
        """Download the :py:class:`ofxparse.Statement` given the time range

        :param days: Number of days to look back at
        :type days: integer
        :rtype: :py:class:`ofxparser.Statement`
        """
        parsed = self.download_parsed(days=days)
        return parsed.account.statement

    def transactions(self, days=60):
        """Download a a list of :py:class:`ofxparse.Transaction` objects

        :param days: Number of days to look back at
        :type days: integer
        :rtype: list of :py:class:`ofxparser.Transaction` objects
        """
        return self.statement(days=days).transactions

    def serialize(self):
        """Serialize predictably for use in configuration storage.

        Output look like this::

          {
            'local_id':       'string',
            'number':         'account num',
            'description':    'descr',
            'broker_id':      'may be missing - type dependent',
            'routing_number': 'may be missing - type dependent,
            'account_type':   'may be missing - type dependent,
            'institution': {
                # ... see :py:meth:`ofxclient.Institution.serialize`
            }
          }

        :rtype: nested dictionary
        """
        data = {
            'local_id': self.local_id(),
            'institution': self.institution.serialize(),
            'number': self.number,
            'description': self.description
        }
        if hasattr(self, 'broker_id'):
            data['broker_id'] = self.broker_id
        elif hasattr(self, 'routing_number'):
            data['routing_number'] = self.routing_number
            data['account_type'] = self.account_type

        return data

    @staticmethod
    def deserialize(raw):
        """Instantiate :py:class:`ofxclient.Account` subclass from dictionary

        :param raw: serilized Account
        :param type: dict as  given by :py:meth:`~ofxclient.Account.serialize`
        :rtype: subclass of :py:class:`ofxclient.Account`
        """
        from ofxclient.institution import Institution
        institution = Institution.deserialize(raw['institution'])

        del raw['institution']
        del raw['local_id']

        if 'broker_id' in raw:
            a = BrokerageAccount(institution=institution, **raw)
        elif 'routing_number' in raw:
            a = BankAccount(institution=institution, **raw)
        else:
            a = CreditCardAccount(institution=institution, **raw)
        return a

    @staticmethod
    def from_ofxparse(data, institution):
        """Instantiate :py:class:`ofxclient.Account` subclass from ofxparse
        module

        :param data: an ofxparse account
        :type data: An :py:class:`ofxparse.Account` object
        :param institution: The parent institution of the account
        :type institution: :py:class:`ofxclient.Institution` object
        """

        description = data.desc if hasattr(data, 'desc') else None
        if data.type == AccountType.Bank:
            return BankAccount(
                institution=institution,
                number=data.account_id,
                routing_number=data.routing_number,
                account_type=data.account_type,
                description=description)
        elif data.type == AccountType.CreditCard:
            return CreditCardAccount(
                institution=institution,
                number=data.account_id,
                description=description)
        elif data.type == AccountType.Investment:
            return BrokerageAccount(
                institution=institution,
                number=data.account_id,
                broker_id=data.brokerid,
                description=description)
        raise ValueError("unknown account type: %s" % data.type)


class BrokerageAccount(Account):
    """:py:class:`ofxclient.Account` subclass for brokerage/investment accounts

    In addition to the parameters it's superclass requires, the following
    parameters are needed.

    :param broker_id: Broker ID of the account
    :type broker_id: string

    .. seealso::

       :py:class:`ofxclient.Account`
    """
    def __init__(self, broker_id, **kwargs):
        super(BrokerageAccount, self).__init__(**kwargs)
        self.broker_id = broker_id

    def _download_query(self, as_of):
        """Formulate the specific query needed for download

        Not intended to be called by developers directly.

        :param as_of: Date in 'YYYYMMDD' format
        :type as_of: string
        """
        c = self.institution.client()
        q = c.brokerage_account_query(
            number=self.number, date=as_of, broker_id=self.broker_id)
        return q


class BankAccount(Account):
    """:py:class:`ofxclient.Account` subclass for a checking/savings account

    In addition to the parameters it's superclass requires, the following
    parameters are needed.

    :param routing_number: Routing number or account number of the account
    :type routing_number: string
    :param account_type: Account type per OFX spec can be empty but not None
    :type account_type: string

    .. seealso::

       :py:class:`ofxclient.Account`
    """
    def __init__(self, routing_number, account_type, **kwargs):
        super(BankAccount, self).__init__(**kwargs)
        self.routing_number = routing_number
        self.account_type = account_type

    def _download_query(self, as_of):
        """Formulate the specific query needed for download

        Not intended to be called by developers directly.

        :param as_of: Date in 'YYYYMMDD' format
        :type as_of: string
        """
        c = self.institution.client()
        q = c.bank_account_query(
            number=self.number,
            date=as_of,
            account_type=self.account_type,
            bank_id=self.routing_number)
        return q


class CreditCardAccount(Account):
    """:py:class:`ofxclient.Account` subclass for a credit card account

    No additional parameters to the constructor are needed.

    .. seealso::

       :py:class:`ofxclient.Account`
    """
    def __init__(self, **kwargs):
        super(CreditCardAccount, self).__init__(**kwargs)

    def _download_query(self, as_of):
        """Formulate the specific query needed for download

        Not intended to be called by developers directly.

        :param as_of: Date in 'YYYYMMDD' format
        :type as_of: string
        """
        c = self.institution.client()
        q = c.credit_card_account_query(number=self.number, date=as_of)
        return q
