from __future__ import absolute_import
from __future__ import unicode_literals
try:
    # python 3
    from io import StringIO
except ImportError:
    # python 2
    from StringIO import StringIO

from ofxclient.client import Client


def combined_download(accounts, days=60):
    """Download OFX files and combine them into one

    It expects an 'accounts' list of ofxclient.Account objects
    as well as an optional 'days' specifier which defaults to 60
    """

    client = Client(institution=None)

    out_file = StringIO()
    out_file.write(client.header())
    out_file.write('<OFX>')
    for a in accounts:
        ofx = a.download(days=days).read()
        stripped = ofx.partition('<OFX>')[2].partition('</OFX>')[0]
        out_file.write(stripped)

    out_file.write("</OFX>")
    out_file.seek(0)

    return out_file
