import urllib
from datetime import datetime
from xml.dom.minidom import parseString

API_URL='http://www.ofxhome.com/api.php'

class API:

    @staticmethod
    def lookup(id):
        return Institution(_xml_request({ 'lookup': id }))

    @staticmethod
    def all():
        return search() 

    @staticmethod
    def search(name=None):
        if name is None:
            params = { 'all': 'yes' }
        else:
            params = { 'search': name }
        return InstitutionList(_xml_request(params))

def _attr(node,name):
    return node.getAttribute(name)

def _text(parent,name):
    rc = []
    for node in parent.getElementsByTagName(name)[0].childNodes:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def _xml_request(params=None):
    encoded = urllib.urlencode(params)
    xml = urllib.urlopen("%s?%s" % (API_URL,encoded)).read()
    return xml

#---------------------------------------------
class InstitutionList:
    def __init__(self,xml):
        self.xml = xml
        self.xml_parsed = parseString(self.xml)

    @staticmethod
    def from_file(file):
        return InstitutionList(open(file,'r').read())

    def list(self):
        root = self.xml_parsed.documentElement
        data = []
        for node in root.getElementsByTagName('institutionid'):
            yield { 'name': _attr(node,'name'), 'id': _attr(node,'id') }

    def __iter__(self):
        return self.list()

    def __str__(self):
        return self.xml
#---------------------------------------------
class Institution:
    def __init__(self,xml):
        self.xml = xml
        self.xml_parsed = parseString(self.xml)

    @staticmethod
    def from_file(file):
        return Institution(open(file,'r').read())

    def dict(self):
        dom = self.xml_parsed
        root = dom.documentElement
        data = {
            'id': _attr(root,'id'),
            'name': _text(root,'name'),
            'fid': _text(root,'fid'),
            'org': _text(root,'org'),
            'url': _text(root,'url'),
            'brokerid': _text(root,'brokerid'),
            'ofxfail': _text(root,'ofxfail'),
            'sslfail': _text(root,'sslfail'),
            'lastofxvalidation': datetime.strptime(_text(root,'lastofxvalidation'),"%Y-%m-%d %H:%M:%S"),
            'lastsslvalidation': datetime.strptime(_text(root,'lastsslvalidation'),"%Y-%m-%d %H:%M:%S"),
        }
        return data

    def __repr__(self):
        return str(self.dict())

    def __str__(self):
        return self.xml

