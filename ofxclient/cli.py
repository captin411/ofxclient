from __future__ import absolute_import
from __future__ import unicode_literals
import argparse
import getpass
import io
import logging
import os
import os.path
import sys

from ofxhome import OFXHome

from ofxclient.account import BankAccount, BrokerageAccount, CreditCardAccount
from ofxclient.config import OfxConfig
from ofxclient.institution import Institution
from ofxclient.util import combined_download

AUTO_OPEN_DOWNLOADS = 1
DOWNLOAD_DAYS = 30

GlobalConfig = None


def run():
    global GlobalConfig

    parser = argparse.ArgumentParser(prog='ofxclient')
    parser.add_argument('-a', '--account')
    parser.add_argument('-d', '--download', type=argparse.FileType('wb', 0))
    parser.add_argument('-o', '--open', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-c', '--config', help='config file path')
    args = parser.parse_args()

    if args.config:
        GlobalConfig = OfxConfig(file_name=args.config)
    else:
        GlobalConfig = OfxConfig()

    accounts = GlobalConfig.accounts()
    account_ids = [a.local_id() for a in accounts]

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if args.download:
        if accounts:
            if args.account:
                a = GlobalConfig.account(args.account)
                ofxdata = a.download(days=DOWNLOAD_DAYS)
            else:
                ofxdata = combined_download(accounts, days=DOWNLOAD_DAYS)
            args.download.write(ofxdata.read())
            if args.open:
                open_with_ofx_handler(args.download.name)
            sys.exit(0)
        else:
            print("no accounts configured")

    main_menu()


def main_menu():
    while 1:
        menu_title("Main\nEdit %s to\nchange descriptions or ofx options" %
                   GlobalConfig.file_name)

        accounts = GlobalConfig.accounts()
        for idx, account in enumerate(accounts):
            menu_item(idx, account.long_description())

        menu_item('A', 'Add an account')
        if accounts:
            menu_item('D', 'Download all combined')

        menu_item('Q', 'Quit')

        choice = prompt().lower()
        if choice == 'a':
            add_account_menu()
        elif choice == 'd':
            if not accounts:
                print("no accounts on file")
            else:
                ofxdata = combined_download(accounts, days=DOWNLOAD_DAYS)
                wrote = write_and_handle_download(
                    ofxdata,
                    'combined_download.ofx'
                )
                print("wrote: %s" % wrote)
        elif choice in ['q', '']:
            return
        elif int(choice) < len(accounts):
            account = accounts[int(choice)]
            view_account_menu(account)


def add_account_menu():
    menu_title("Add account")
    while 1:
        print('------')
        print('Notice')
        print('------')
        print('You are about to search for bank connection information')
        print('on a third party website.  This means you are trusting')
        print('http://ofxhome.com and their security policies.')
        print('')
        print('You will be sending your bank name to this website.')
        print('------')
        query = prompt('bank name eg. "express" (enter to exit)> ')
        if query.lower() in ['']:
            return

        found = OFXHome.search(query)
        if not found:
            error("No banks found")
            continue

        while 1:
            for idx, bank in enumerate(found):
                menu_item(idx, bank['name'])
            choice = prompt().lower()
            if choice in ['q', '']:
                return
            elif int(choice) < len(found):
                bank = OFXHome.lookup(found[int(choice)]['id'])
                if login_check_menu(bank):
                    return


def view_account_menu(account):
    while 1:
        menu_title(account.long_description())

        institution = account.institution
        client = institution.client()

        print("Overview:")
        print("  Name:           %s" % account.description)
        print("  Account Number: %s" % account.number_masked())
        print("  Institution:    %s" % institution.description)
        print("  Main Type:      %s" % str(type(account)))
        if hasattr(account, 'routing_number'):
            print("  Routing Number: %s" % account.routing_number)
            print("  Sub Type:       %s" % account.account_type)
        if hasattr(account, 'broker_id'):
            print("  Broker ID:      %s" % account.broker_id)

        print("Nerdy Info:")
        print("  Download Up To:        %s days" % DOWNLOAD_DAYS)
        print("  Username:              %s" % institution.username)
        print("  Local Account ID:      %s" % account.local_id())
        print("  Local Institution ID:  %s" % institution.local_id())
        print("  FI Id:                 %s" % institution.id)
        print("  FI Org:                %s" % institution.org)
        print("  FI Url:                %s" % institution.url)
        if institution.broker_id:
            print("  FI Broker Id:          %s" % institution.broker_id)
        print("  Client Id:             %s" % client.id)
        print("  App Ver:               %s" % client.app_version)
        print("  App Id:                %s" % client.app_id)
        print("  OFX Ver:               %s" % client.ofx_version)
        print("  Config File:           %s" % GlobalConfig.file_name)

        menu_item('D', 'Download')
        choice = prompt().lower()
        if choice == 'd':
            out = account.download(days=DOWNLOAD_DAYS)
            wrote = write_and_handle_download(out,
                                              "%s.ofx" % account.local_id())
            print("wrote: %s" % wrote)
        return


def login_check_menu(bank_info):
    print('------')
    print('Notice')
    print('------')
    print('You are about to test to make sure your username and password')
    print('are correct.  This means you will be sending it to the URL below.')
    print('If the URL does not appear to belong to your bank then you should')
    print('exit this program by hitting CTRL-C.')
    print('  bank name: %s' % (bank_info['name']))
    print('  bank url:  %s' % (bank_info['url']))
    print('------')
    while 1:
        username = ''
        while not username:
            username = prompt('username> ')

        password = ''
        while not password:
            password = getpass.getpass('password> ')

        i = Institution(
            id=bank_info['fid'],
            org=bank_info['org'],
            url=bank_info['url'],
            broker_id=bank_info['brokerid'],
            description=bank_info['name'],
            username=username,
            password=password
        )
        try:
            i.authenticate()
        except Exception as e:
            print("authentication failed: %s" % e)
            continue

        accounts = i.accounts()
        for a in accounts:
            GlobalConfig.add_account(a)
        GlobalConfig.save()
        return 1


def write_and_handle_download(ofx_data, name):
    outfile = io.open(name, 'w')
    outfile.write(ofx_data.read())
    outfile.close()
    if AUTO_OPEN_DOWNLOADS:
        open_with_ofx_handler(name)
    return os.path.abspath(name)


def prompt(text='choice> '):
    try:
        # python 2
        got = raw_input(text)
    except NameError:
        # python 3
        got = input(text)
    return got


def error(text=''):
    print("!! %s" % text)


def menu_item(key, description):
    print("(%s) %s" % (key, description))


def menu_title(name):
    print("+----------------------------------")
    print("%s" % name)
    print("+----------------------------------")


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
