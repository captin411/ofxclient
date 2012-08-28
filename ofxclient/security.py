import keyring
from settings import Settings

REALM = Settings.security_realm

cache = {}
def set_password(username,password):
    if username in cache:
        del cache[username]
    return keyring.set_password( REALM, username, password )

def get_password(username):
    if username not in cache:
        cache[username] = keyring.get_password( REALM, username )
    return cache[username]


