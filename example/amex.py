# Example on how to use the ofxclient library without the
# web interface.  It's admittedly clunky but doable -- it's
# free so get over it >=)
import ofxclient
from pprint import pprint

# http://www.ofxhome.com/index.php/institution/view/424
# note this is NOT the FI Id. It's the ofxhome ID.
ofxhome_id    = '424'
your_username = 'genewilder'
your_password = 'ihatecandy'

# yeah I know, you can't pass the 'pass' in
# the constructor.. I'm lame and maybe I'll fix 
# it later
institution = ofxclient.Institution(
    id = ofxhome_id,
    username = your_username
)
institution.password = your_password

# You HAVE to call save() but only just once. Calling save
# repeatedly won't hurt anything.
# Note that ffter calling this, you would never need to specify the
# institution.password again as it will be loaded from the keychain
#
# save() triggers saving of cache information (see ~/.ofxclient) as well
# as a config file (see ~/.ofxclient.conf)
institution.save()

accounts = institution.accounts()

# returns an ofxparse.Statement object
# see an the ofx.account.statement portion of their docs:
# https://github.com/jseutter/ofxparse/blob/master/README
statement = accounts[0].statement(days=5)

# get the balance
print "balance: %s" % statement.balance

# and get the transactions too if you want
pprint(statement.transactions)
