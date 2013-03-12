from ofxclient import Institution

inst = Institution(
        id = '3101',
        org = 'AMEX',
        url = 'https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do?request_type=nl_ofxdownload',
        username = 'genewilder',
        password = 'ihatecandy'
)

accounts = inst.accounts()
for a in accounts:
    # a StringIO wrapped string of the raw OFX download
    download  = a.download(days=5)
    print download.read()

    # an ofxparse.Statement object
    statement = a.statement(days=5)
    print statement.balance
