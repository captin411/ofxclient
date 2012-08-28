import cherrypy, ofxclient, os.path
from mako.template import Template
from mako.lookup import TemplateLookup

current_dir = os.path.abspath( os.path.dirname(__file__) )
html_dir    = "%s/html" % current_dir

lookup = TemplateLookup(directories=[html_dir])
def _t(name,**kwargs):
    return lookup.get_template(name).render(**kwargs)

class Root(object):
    @cherrypy.expose
    def index(self):
        banks = sorted(ofxclient.Institution.list())
        return _t('index.html',banks=banks)

    @cherrypy.expose
    def download(self,account_id,filename_arbitrary,days=60):
        account = ofxclient.Account.from_id(account_id)
        cherrypy.response.headers['Content-Type'] = 'application/vnd.intu.QFX'
        cherrypy.lib.caching.expires(secs=0,force=True)
        return account.download(days=int(days)).read()

    @cherrypy.expose
    def search(self,q=None,**kwargs):
        institutions = sorted(ofxclient.Institution.search(q))
        return _t('search.html',institutions=institutions)

    @cherrypy.expose
    def add_bank(self,id=None,username=None,password=None,**kwargs):
        if id and username and password:
            i = ofxclient.Institution(id,username=username)
            i.password = password
            try:
                i.auth_test()
            except Exception as e:
                return _t('add_bank.html',i=i,error=e)
            i.save()
            raise cherrypy.HTTPRedirect("/")
        else:
            i = ofxclient.Institution(id)
            return _t('add_bank.html',i=i)

