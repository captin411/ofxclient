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
from ofxclient.client import DEFAULT_OFX_VERSION

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
    parser.add_argument('--download-days', default=DOWNLOAD_DAYS, type=int, help='number of days to download (default: %s)' % DOWNLOAD_DAYS)
    parser.add_argument('--ofx-version', default=DEFAULT_OFX_VERSION, type=int, help='ofx version to use for new accounts (default: %s)' % DEFAULT_OFX_VERSION)
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
                ofxdata = a.download(days=args.download_days)
            else:
                ofxdata = combined_download(accounts, days=args.download_days)
            args.download.write(ofxdata.read().encode())
            if args.open:
                open_with_ofx_handler(args.download.name)
            sys.exit(0)
        else:
            print("no accounts configured")

    main_menu(args)


def main_menu(args):
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
            add_account_menu(args)
        elif choice == 'd':
            if not accounts:
                print("no accounts on file")
            else:
                ofxdata = combined_download(accounts, days=args.download_days)
                wrote = write_and_handle_download(
                    ofxdata,
                    'combined_download.ofx'
                )
                print("wrote: %s" % wrote)
        elif choice in ['q', '']:
            return
        elif int(choice) < len(accounts):
            account = accounts[int(choice)]
            view_account_menu(account, args)


def add_account_menu(args):
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
                if login_check_menu(bank, args):
                    return


def view_account_menu(account, args):
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
        print("  Download Up To:        %s days" % args.download_days)
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
        print("  User-Agent header:     %s" % client.user_agent)
        print("  Accept header:         %s" % client.accept)
        print("  Config File:           %s" % GlobalConfig.file_name)

        menu_item('D', 'Download')
        choice = prompt().lower()
        if choice == 'd':
            out = account.download(days=args.download_days)
            wrote = write_and_handle_download(out,
                                              "%s.ofx" % account.local_id())
            print("wrote: %s" % wrote)
        return


def login_check_menu(bank_info, args):
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
        prompt_text = 'password> '
        if os.name == 'nt' and sys.version_info < (3, 0):
            prompt_text = prompt_text.encode('utf8')
        while not password:
            password = getpass.getpass(prompt=prompt_text)

        i = Institution(
            id=bank_info['fid'],
            org=bank_info['org'],
            url=bank_info['url'],
            broker_id=bank_info['brokerid'],
            description=bank_info['name'],
            username=username,
            password=password,
            client_args=client_args_for_bank(bank_info, args.ofx_version)
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


def client_args_for_bank(bank_info, ofx_version):
    """
    Return the client arguments to use for a particular Institution, as found
    from ofxhome. This provides us with an extension point to override or
    augment ofxhome data for specific institutions, such as those that
    require specific User-Agent headers (or no User-Agent header).

    :param bank_info: OFXHome bank information for the institution, as returned
      by ``OFXHome.lookup()``
    :type bank_info: dict
    :param ofx_version: OFX Version argument specified on command line
    :type ofx_version: str
    :return: Client arguments for a specific institution
    :rtype: dict
    """
    client_args = {'ofx_version': str(ofx_version)}
    if 'ofx.discovercard.com' in bank_info['url']:
        # Discover needs no User-Agent and no Accept headers
        client_args['user_agent'] = False
        client_args['accept'] = False
    if 'www.accountonline.com' in bank_info['url']:
        # Citi needs no User-Agent header
        client_args['user_agent'] = False
    if 'ofx.schwab.com' in bank_info['url']:
        # Schwab requires no User-Agent header
        client_args['user_agent'] = False
    return client_args

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
