import os.path
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
    html_path = "%s/webapp/html" % os.path.dirname(__file__)
    security_realm = 'Bank Statement Downloader'
    _json = None

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
        if Settings._json:
            return Settings._json;
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

        Settings._json = conf
        return conf

    @staticmethod
    def config_save(config):
        conf = open(CONFFILE,'w')
        conf.write( json.dumps(config, sort_keys=False, indent=4) )
        conf.close()
        Settings._json = None
        return Settings.config()

    @staticmethod
    def banks(only_guid=None):
        conf = Settings.config()
        banks = conf['banks']
        if only_guid is not None:
            for b in banks:
                if b.get('guid') == only_guid:
                    return b
        else:
            return banks

    @staticmethod
    def accounts(only_guid=None):
        conf = Settings.config()
        accounts = conf['accounts']
        if only_guid is not None:
            for a in accounts:
                if a.get('guid') == only_guid:
                    return a
        else:
            return accounts
