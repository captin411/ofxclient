from account import Account, BankAccount, BrokerageAccount, CreditCardAccount
from ConfigParser import ConfigParser
from institution import Institution
from ofxhome import OFXHome
from util import combined_download
import os
import os.path
import client
import sys

CONF_PATH           = os.path.expanduser('~/ofxclient.ini')
AUTO_OPEN_DOWNLOADS = 1
DOWNLOAD_DAYS       = 30

def run():
    main_menu()

def main_menu():
    while 1:

        menu_title("Main\nEdit %s to\nchange descriptions or ofx options" % CONF_PATH)

        accounts = configured_accounts()
        for idx,account in enumerate(accounts):
            menu_item(idx,account.long_description())

        menu_item('A', 'Add an account')
        if accounts:
            menu_item('D', 'Download all combined')
        
        menu_item('Q', 'Quit')

        choice = prompt().lower()
        if   choice == 'a':
            add_account_menu()
        elif choice == 'd':
            if not accounts:
                print "no accounts on file"
            else:
                ofxdata  = combined_download(accounts,days=DOWNLOAD_DAYS)
                wrote    = write_and_handle_download(ofxdata,'combined_download.ofx')
                print "wrote: %s" % wrote
        elif choice in ['q','']:
            return
        elif int(choice) < len(accounts):
            account = accounts[int(choice)]
            view_account_menu(account)

def add_account_menu():
    menu_title("Add account")
    while 1:
        query = prompt('enter part of a bank name eg. express> ')
        if query.lower() in ['']:
            return

        found = OFXHome.search(query)
        if not found:
            error("No banks found")
            continue
        
        while 1:
            for idx,bank in enumerate(found):
                menu_item(idx,bank['name'])
            choice = prompt().lower()
            if choice in ['q','']:
                return
            elif int(choice) < len(found):
                bank = OFXHome.lookup(found[int(choice)]['id'])
                if login_test_menu(bank):
                    return

def view_account_menu(account):
    while 1:
        menu_title(account.long_description())

        institution = account.institution
        client      = institution.client()

        print "Overview:"
        print "  Name:           %s" % account.description
        print "  Account Number: %s" % account.number_masked()
        print "  Institution:    %s" % institution.description
        print "  Main Type:      %s" % str(type(account))
        if hasattr(account,'routing_number'):
            print "  Routing Number: %s" % account.routing_number
            print "  Sub Type:       %s" % account.account_type
        if hasattr(account,'broker_id'):
            print "  Broker ID:      %s" % account.broker_id

        print "Nerdy Info:"
        print "  Download Up To:        %s days" % DOWNLOAD_DAYS
        print "  Username:              %s" % institution.username
        print "  Local Account ID:      %s" % account.local_id()
        print "  Local Institution ID:  %s" % institution.local_id()
        print "  FI Id:                 %s" % institution.id
        print "  FI Org:                %s" % institution.org
        print "  FI Url:                %s" % institution.url
        if institution.broker_id:
            print "  FI Broker Id:          %s" % institution.broker_id
        print "  Client Id:             %s" % client.id
        print "  App Ver:               %s" % client.app_version
        print "  App Id:                %s" % client.app_id
        print "  OFX Ver:               %s" % client.ofx_version
        print "  Config File:           %s" % CONF_PATH
        
        menu_item('D', 'Download')
        choice = prompt().lower()
        if choice == 'd':
            out = account.download(days=DOWNLOAD_DAYS)
            wrote = write_and_handle_download(out,"%s.ofx" % account.local_id())
            print "wrote: %s" % wrote
        return

def login_test_menu(bank_info):
    while 1:
        username = ''
        while not username:
            username = prompt('username> ')

        password = ''
        while not password:
            password = prompt('password> ')

        i = Institution(
                id = bank_info['fid'],
                org = bank_info['org'],
                url = bank_info['url'],
                broker_id = bank_info['brokerid'],
                username = username,
                password = password
        )
        try:
            i.authenticate()
        except Exception, e:
            print "authentication failed: %s" % e
            continue

        accounts = i.accounts()
        for a in accounts:
            save_account(a)
        return 1

def load_account(sid):
    conf = config_load()
    data = unflatten_dict( dict( conf.items(sid) ) )
    return Account.deserialize(data)

def save_account(a):
    conf       = config_load()

    data       = flatten_dict( a.serialize() )
    section_id = data['local_id']

    if not conf.has_section(section_id):
        conf.add_section(section_id)

    for key in sorted(data):
        conf.set(section_id,key,data[key])

    config_save(conf)

def write_and_handle_download(ofx_data,name):
    outfile = open(name,'w')
    outfile.write( ofx_data.read() )
    outfile.close()
    if AUTO_OPEN_DOWNLOADS:
        open_with_ofx_handler(name)
    return os.path.abspath(name)

def config_load():
    # ensure the file exists
    with file(CONF_PATH,'a'):
        os.utime(CONF_PATH,None)

    conf = ConfigParser()
    conf.readfp(open(CONF_PATH))
    return conf

def config_save(conf):
    with file(CONF_PATH,'w') as fp:
        conf.write(fp)

def configured_accounts():
    accounts = []
    conf = config_load()
    for section in conf.sections():
        accounts.append( load_account(section)  )
    return accounts

def prompt(text='choice> '):
    got = raw_input(text)
    return got

def error(text=''):
    print "!! %s" % text

def menu_item(key,description):
    print "(%s) %s" % (key, description)

def menu_title(name):
    print "+----------------------------------"
    print "%s" % name
    print "+----------------------------------"

def open_with_ofx_handler(filename):
    import platform
    sysname = platform.system()
    if sysname == 'Darwin':
        os.system("/usr/bin/open '%s'" % filename)
    elif sysname == 'Windows':
        os.startfile(filename)
    else: 
        # linux
        os.system("xdg-open '%s'" % filename)

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


if __name__ == '__main__':
    run()

