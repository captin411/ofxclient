from account import BankAccount, BrokerageAccount, CreditCardAccount
from ConfigParser import ConfigParser
from institution import Institution
from ofxhome import OFXHome
from util import combined_download
import os
import os.path
import request
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
                inst     = accounts[0].institution
                ofxdata  = combined_download(accounts,days=DOWNLOAD_DAYS,request_settings=inst.request_settings)
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
        print "Overview:"
        print "  Name:           %s" % account.description
        print "  Account Number: %s" % account.number_masked()
        print "  Institution:    %s" % account.institution.description
        print "  Main Type:      %s" % str(type(account))
        if hasattr(account,'routing_number'):
            print "  Routing Number: %s" % account.routing_number
            print "  Sub Type:       %s" % account.account_type
        if hasattr(account,'broker_id'):
            print "  Broker ID:      %s" % account.broker_id

        print "Nerdy Info:"
        print "  Download Up To:        %s days" % DOWNLOAD_DAYS
        print "  Username:              %s" % account.institution.username
        print "  Local Account ID:      %s" % account.local_id()
        print "  Local Institution ID:  %s" % account.institution.local_id()
        print "  FI Id:                 %s" % account.institution.id
        print "  FI Org:                %s" % account.institution.org
        print "  FI Url:                %s" % account.institution.url
        if account.institution.broker_id:
            print "  FI Broker Id:          %s" % account.institution.broker_id
        print "  App Ver:               %s" % account.institution.request_settings['app_version']
        print "  App Id:                %s" % account.institution.request_settings['app_id']
        print "  OFX Ver:               %s" % account.institution.request_settings['ofx_version']
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
                password = password,
                request_settings = {
                    'app_id':      request.DEFAULT_APP_ID,
                    'app_version': request.DEFAULT_APP_VERSION,
                    'ofx_version': request.DEFAULT_OFX_VERSION,
                }
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
    i = Institution(
        id = conf.get(sid,'institution_id'),
        org = conf.get(sid,'institution_org'),
        url = conf.get(sid,'institution_url'),
        description = conf.get(sid,'institution_description'),
        username = conf.get(sid,'institution_username'),
        password = conf.get(sid,'institution_password'),
        request_settings = {
            'app_id': conf.get(sid,'request_app_id'),
            'app_version': conf.get(sid,'request_app_version'),
            'ofx_version': conf.get(sid,'request_ofx_version'),
        }
    )
    if conf.has_option(sid,'institution_broker_id'):
        i.broker_id = conf.get(sid,'institution_broker_id'),

    if   conf.has_option(sid,'account_broker_id'):
        a = BrokerageAccount(
            institution = i,
            number = conf.get(sid,'account_number'),
            broker_id = conf.get(sid,'broker_id'),
            description = conf.get(sid,'account_description'),
        )
    elif conf.has_option(sid,'account_routing_number'):
        a = BankAccount(
            institution = i,
            number = conf.get(sid,'account_number'),
            routing_number = conf.get(sid,'account_routing_number'),
            account_type = conf.get(sid,'account_account_type'),
            description = conf.get(sid,'account_description'),
        )
    else:
        a = CreditCardAccount(
            institution = i,
            number = conf.get(sid,'account_number'),
            description = conf.get(sid,'account_description'),
        )

    return a

def save_account(a):
    conf = config_load()
    section_id = a.local_id()
    data = {
      'account_local_id': a.local_id(),
      'account_description': a.description,
      'account_number':   a.number,
      'institution_id':   a.institution.id,
      'institution_broker_id': a.institution.broker_id,
      'institution_description':   a.institution.description,
      'institution_org':  a.institution.org,
      'institution_url':  a.institution.url,
      'institution_local_id': a.institution.local_id(),
      'institution_username': a.institution.username,
      'institution_password': a.institution.password,
      'request_app_id':       a.institution.request_settings['app_id'],
      'request_app_version':  a.institution.request_settings['app_version'],
      'request_ofx_version':  a.institution.request_settings['ofx_version'],
    }
    if hasattr(a,'broker_id'):
        data['account_broker_id'] = a.broker_id

    if hasattr(a,'routing_number'):
        data['account_routing_number'] = a.routing_number
        data['account_account_type']   = a.account_type

    if not conf.has_section(section_id):
        conf.add_section(section_id)

    for key,value in data.items():
        conf.set(section_id,key,value)
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

if __name__ == '__main__':
    run()

