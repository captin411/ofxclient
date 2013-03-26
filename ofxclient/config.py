from __future__ import with_statement
from ofxclient.account import Account
from ConfigParser import ConfigParser
import os
import os.path

try:
    import keyring
    KEYRING_AVAILABLE = True
except:
    KEYRING_AVAILABLE = False

try:
    DEFAULT_CONFIG = os.path.expanduser(os.path.join('~', 'ofxclient.ini'))
except:
    DEFAULT_CONFIG = None


class SecurableConfigParser(ConfigParser):
    """:py:class:`ConfigParser.ConfigParser` subclass that knows how to store
    options marked as secure into the OS specific
    keyring/keychain.

    To mark an option as secure, the caller must call
    'set_secure' at least one time for the particular
    option and from then on it will be seen as secure
    and will be stored / retrieved from the keychain.

    Example::

      from ofxclient.config import SecurableConfigParser

      # password will not be saved in the config file

      c = SecurableConfigParser()
      c.add_section('Info')
      c.set('Info','username','bill')
      c.set_secure('Info','password','s3cre7')
      with open('config.ini','w') as fp:
        c.write(fp)
    """

    _secure_placeholder = '%{secured}'

    def __init__(self, keyring_name='ofxclient',
                 keyring_available=KEYRING_AVAILABLE, **kwargs):
        ConfigParser.__init__(self)
        self.keyring_name = keyring_name
        self.keyring_available = keyring_available
        self._unsaved = {}
        self.keyring_name = keyring_name

    def is_secure_option(self, section, option):
        """Test an option to see if it is secured or not.

        :param section: section id
        :type section: string
        :param option: option name
        :type option: string
        :rtype: boolean
        otherwise.
        """
        if not self.has_section(section):
            return False
        if not self.has_option(section, option):
            return False
        if ConfigParser.get(self, section, option) == self._secure_placeholder:
            return True
        return False

    def has_secure_option(self, section, option):
        """See is_secure_option"""
        return self.is_secure_option(section, option)

    def items(self, section):
        """Get all items for a section. Subclassed, to ensure secure
        items come back with the unencrypted data.

        :param section: section id
        :type section: string
        """
        items = []
        for k, v in ConfigParser.items(self, section):
            if self.is_secure_option(section, k):
                v = self.get(section, k)
            items.append((k, v))
        return items

    def secure_items(self, section):
        """Like items() but only return secure items.

        :param section: section id
        :type section: string
        """
        return [x
                for x in self.items(section)
                if self.is_secure_option(section, x[0])]

    def set(self, section, option, value):
        """Set an option value. Knows how to set options properly marked
        as secure."""
        if self.is_secure_option(section, option):
            self.set_secure(section, option, value)
        else:
            ConfigParser.set(self, section, option, value)

    def set_secure(self, section, option, value):
        """Set an option and mark it as secure.

        Any subsequent uses of 'set' or 'get' will also
        now know that this option is secure as well.
        """
        if self.keyring_available:
            s_option = "%s%s" % (section, option)
            self._unsaved[s_option] = ('set', value)
            value = self._secure_placeholder
        ConfigParser.set(self, section, option, value)

    def get(self, section, option, *args):
        """Get option value from section. If an option is secure,
        populates the plain text."""
        if self.is_secure_option(section, option) and self.keyring_available:
            s_option = "%s%s" % (section, option)
            if self._unsaved.get(s_option, [''])[0] == 'set':
                return self._unsaved[s_option][1]
            else:
                return keyring.get_password(self.keyring_name, s_option)
        return ConfigParser.get(self, section, option, *args)

    def remove_option(self, section, option):
        """Removes the option from ConfigParser as well as
        the secure storage backend
        """
        if self.is_secure_option(section, option) and self.keyring_available:
            s_option = "%s%s" % (section, option)
            self._unsaved[s_option] = ('delete', None)
        ConfigParser.remove_option(self, section, option)

    def write(self, *args):
        """See ConfigParser.write().  Also writes secure items to keystore."""
        ConfigParser.write(self, *args)
        if self.keyring_available:
            for key, thing in self._unsaved.items():
                action = thing[0]
                value = thing[1]
                if action == 'set':
                    keyring.set_password(self.keyring_name, key, value)
                elif action == 'delete':
                    try:
                        keyring.delete_password(self.keyring_name, key)
                    except:
                        pass
        self._unsaved = {}


class OfxConfig(object):
    """Default config file handler for other tools to use.

    This can read and write from the default config which is
    $USERS_HOME/ofxclient.ini

    :param file_name: absolute path to a config file (optional)
    :type file_name: string or None

    Example usage::

      from ofxclient.config import OfxConfig
      from ofxclient import Account

      a = Account()

      c = OfxConfig(file_name='/tmp/new.ini')
      c.add_account(a)
      c.save()

      account_list = c.accounts()
      one_account  = c.account( a.local_id() )
    """

    def __init__(self, file_name=None):

        self.secured_field_names = [
            'institution.username',
            'institution.password'
        ]

        f = file_name or DEFAULT_CONFIG
        if f is None:
            raise ValueError('file_name is required')
        self._load(f)

    def reload(self):
        """Reload the config file from disk"""
        return self._load()

    def accounts(self):
        """List of confgured :py:class:`ofxclient.Account` objects"""
        return [self._section_to_account(s)
                for s in self.parser.sections()]

    def encrypted_accounts(self):
        return [a
                for a in self.accounts()
                if self.is_encrypted_account(a.local_id())]

    def unencrypted_accounts(self):
        return [a
                for a in self.accounts()
                if not self.is_encrypted_account(a.local_id())]

    def account(self, id):
        """Get :py:class:`ofxclient.Account` by section id"""
        if self.parser.has_section(id):
            return self._section_to_account(id)
        return None

    def add_account(self, account):
        """Add Account to config (does not save)"""
        serialized = account.serialize()
        section_items = flatten_dict(serialized)
        section_id = section_items['local_id']

        if not self.parser.has_section(section_id):
            self.parser.add_section(section_id)

        for key in sorted(section_items):
            self.parser.set(section_id, key, section_items[key])

        self.encrypt_account(id=section_id)

        return self

    def encrypt_account(self, id):
        """Make sure that certain fields are encrypted."""
        for key in self.secured_field_names:
            value = self.parser.get(id, key)
            self.parser.set_secure(id, key, value)
        return self

    def is_encrypted_account(self, id):
        """Are all fields for the account id encrypted?"""
        for key in self.secured_field_names:
            if not self.parser.is_secure_option(id, key):
                return False
        return True

    def remove_account(self, id):
        """Add Account from config (does not save)"""
        if self.parser.has_section(id):
            self.parser.remove_section(id)
            return True
        return False

    def save(self):
        """Save changes to config file"""
        with open(self.file_name, 'w') as fp:
            self.parser.write(fp)
        return self

    def _load(self, file_name=None):
        self.parser = None

        file_name = file_name or self.file_name

        if not os.path.exists(file_name):
            with open(file_name, 'a'):
                os.utime(file_name, None)

        self.file_name = file_name

        conf = SecurableConfigParser()
        conf.readfp(open(self.file_name))
        self.parser = conf

        return self

    def _section_to_account(self, section):
        section_items = dict(self.parser.items(section))
        serialized = unflatten_dict(section_items)
        return Account.deserialize(serialized)


def unflatten_dict(dict, prefix=None, separator='.'):
    ret = {}
    for k, v in dict.items():
        key_parts = k.split(separator)

        if len(key_parts) == 1:
            ret[k] = v
        else:
            first = key_parts[0]
            rest = key_parts[1:]
            temp = ret.setdefault(first, {})
            for idx, part in enumerate(rest):
                if (idx+1) == len(rest):
                    temp[part] = v
                else:
                    temp = temp.setdefault(part, {})
    return ret


def flatten_dict(dict, prefix=None, separator='.'):
    ret = {}
    for k, v in dict.items():
        if prefix:
            flat_key = separator.join([prefix, k])
        else:
            flat_key = k
        if isinstance(v, dict):
            deflated = flatten_dict(v, prefix=flat_key)
            for dk, dv in deflated.items():
                ret[dk] = dv
        else:
            ret[flat_key] = v
    return ret
