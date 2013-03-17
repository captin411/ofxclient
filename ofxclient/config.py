from ofxclient.account import Account
from ConfigParser import ConfigParser
import os.path

try:
    import keyring
    KEYRING_AVAILABLE = 1
except ImportError:
    KEYRING_AVAILABLE = 0

DEFAULT_CONFIG = os.path.expanduser('~/ofxclient.ini')

class SecurableConfigParser(ConfigParser):

    keyring_name  = ''

    _secure_placeholder = '%{secured}'
    _unsaved            = {}

    def __init__(self, keyring_name='ofxclient', **kwargs):
        ConfigParser.__init__(self)
        self.keyring_name = keyring_name

    def is_secure_option(self,section,option):
        if not self.has_section(section):
            return False
        if not self.has_option(section,option):
            return False
        if ConfigParser.get(self,section,option) == self._secure_placeholder:
            return True
        return False

    def has_secure_option(self,section,option):
        return self.is_secure_option(section,option)

    def items(self, section):
        items = []
        for k,v in ConfigParser.items(self,section):
            if self.is_secure_option(section,k):
                v = self.get(section,k)
            items.append( (k,v) )
        return items

    def secure_items(self, section):
        return [ x for x in self.items(section) if self.is_secure_option(section,x[0]) ]

    def set(self, section, option, value):
        if self.is_secure_option(section,option):
            self.set_secure(section, option, value)
        ConfigParser.set(self,section,option,value)

    def set_secure(self, section, option, value):
        if KEYRING_AVAILABLE:
            s_option = "%s%s" % (section,option)
            self._unsaved[s_option] = ('set',value)
            value    = self._secure_placeholder
        ConfigParser.set(self,section,option,value)

    def get(self, section, option,*args):
        if self.is_secure_option(section,option):
            s_option = "%s%s" % (section,option)
            if self._unsaved.get(s_option,[''])[0] == 'set':
                return self._unsaved[s_option][1]
            else:
                return keyring.get_password( self.keyring_name, s_option )
        return ConfigParser.get(self,section,option,*args)

    def remove_option(self, section, option):
        ConfigParser.remove_option(self,section,option)
        s_option = "%s%s" % (section,option)
        self._unsaved[s_option] = ('delete',None)

    def write(self,*args):
        ConfigParser.write(self,*args)
        if KEYRING_AVAILABLE:
            for key,thing in self._unsaved.items():
                action = thing[0]
                value  = thing[1]
                if action == 'set':
                    keyring.set_password( self.keyring_name, key, value )
                elif action == 'delete':
                    try:
                        keyring.delete_password( self.keyring_name, key )
                    except:
                        pass
        self._unsaved = {}

class OfxConfig(object):

    file_name = DEFAULT_CONFIG
    parser    = None
    accounts  = []

    def __init__(self, file_name=None):
        self.load(file_name)

    def load(self,file_name=None):
        file_name = file_name or self.file_name

        # make sure the file exists
        with file(file_name,'a'):
            os.utime(file_name,None)

        conf = SecurableConfigParser()
        conf.readfp(open(file_name))
        self.parser = conf

        # just in case we passed a new file_name in
        self.file_name = file_name
        return self

    def reload(self):
        return self.load()

    def accounts(self):
        return [ self.section_to_account(s) for s in self.parser.sections() ]

    def add_account(self,account):
        serialized    = account.serialize()
        section_items = flatten_dict( serialized )
        section_id    = section_items['local_id']

        if not self.parser.has_section(section_id):
            self.parser.add_section(section_id)

        for key in sorted(section_items):
            value = section_items[key]
            if key in ['institution.username','institution.password']:
                self.parser.set_secure(section_id,key,value)
            else:
                self.parser.set(section_id,key,value)

        return self

    def section_to_account(self,section):
        section_items = dict(self.parser.items(section))
        serialized    = unflatten_dict( section_items )
        return Account.deserialize(serialized)

    def save(self):
        with file(self.file_name,'w') as fp:
            self.parser.write(fp)
        return self

def unflatten_dict(dict,prefix=None,separator='.'):
    ret = {}
    for k,v in dict.items():
        key_parts = k.split(separator)

        if len(key_parts) == 1:
            ret[k] = v
        else:
            first = key_parts[0]
            rest  = key_parts[1:]
            temp = ret.setdefault(first,{})
            for idx,part in enumerate(rest):
                if (idx+1) == len(rest):
                    temp[part] = v
                else:
                    temp = temp.setdefault(part,{})
    return ret

def flatten_dict(dict,prefix=None,separator='.'):
    ret = {}
    for k,v in dict.items():
        if prefix:
            flat_key = separator.join([prefix,k])
        else:
            flat_key = k
        if type(v) == type({}):
            deflated = flatten_dict(v,prefix=flat_key)
            for dk,dv in deflated.items():
                ret[dk]=dv
        else:
            ret[flat_key]=v
    return ret
