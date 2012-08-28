import keyring, time, base64
from settings import Settings
try:
    import json
except ImportError:
    import simplejson as json

REALM = Settings.security_realm
JSON_KEY = 'OFXCredentials'
CACHE_TIME = 15

def store(struct):
    str = base64.b64encode(json.dumps(struct))
    return keyring.set_password(REALM,JSON_KEY,str)

def retrieve():
    str = keyring.get_password(REALM,JSON_KEY)
    if str is None:
        return {}
    else:
        return json.loads(base64.b64decode(str))

cache = None
def set_password(username,password):
    global cache
    cache = None
    data = retrieve()
    data[username] = password
    return store(data)

def get_password(username):
    global cache
    now = time.time()
    if not cache or cache['expires'] < now:
        cache = {
            'expires': now+CACHE_TIME,
            'data': retrieve()
        }
    return cache.get('data',{}).get(username)


