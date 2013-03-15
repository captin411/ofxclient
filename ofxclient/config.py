from account import Account
from ConfigParser import ConfigParser
import os.path

DEFAULT_CONFIG = os.path.expanduser('~/ofxclient.ini')

class OfxConfig(object):

    file_name = DEFAULT_CONFIG
    parser    = None

    def __init__(self, file_name=None):
        self.load(file_name)

    def load(self,file_name=None):
        file_name = file_name or self.file_name

        # make sure the file exists
        with file(file_name,'a'):
            os.utime(file_name,None)

        conf = ConfigParser()
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

        if not conf.has_section(section_id):
            self.parser.add_section(section_id)

        for key in sorted(section_items):
            value = section_items[key]
            self.parser.set(section_id,key,value)

        return self

    def save(self):
        with file(self.file_name,'w') as fp:
            self.parser.write(fp)
        return self

    def section_to_account(self,section):
        section_items = self.parser.items(section)
        serialized    = unflatten_dict( dict(section_items) )
        return Account.deserialize(serialized)



    pass

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

