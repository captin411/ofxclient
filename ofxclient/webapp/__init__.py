import cherrypy, ofxclient, os.path
from mako.template import Template
from mako.lookup import TemplateLookup
try:
    import json
except ImportError:
    import simplejson as json


current_dir = os.path.abspath( os.path.dirname(__file__) )
html_dir    = "%s/html" % current_dir
if not os.path.exists(html_dir):
    html_dir = '%s/html' % os.path.abspath(os.getcwd())

lookup = TemplateLookup(directories=[html_dir])
def _t(name,**kwargs):
    return lookup.get_template(name).render(**kwargs)

class REST(object):

    @cherrypy.expose
    def add_bank(self,id=None,username=None,password=None):

        cherrypy.response.headers['Content-Type'] = 'application/json'
        cherrypy.response.status = 200

        result = {
            'status': 'ok',
            'message': ''
        }
        if id and username and password:
            i = ofxclient.Institution(id,username=username)
            i.password = password
            try:
                i.auth_test()
                i.save()
            except Exception as e:
                result['status'] = 'error'
                result['message'] = 'unable to log into bank with those credentials'
        else:
            result['status'] = 'error'
            result['message'] = 'id, username, and password are all required'

        ret = json.dumps(result)
        cherrypy.response.body = ret
        if result['status'] == 'error':
            cherrypy.response.status = 400
        return ret

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
        if q:
            institutions = sorted(ofxclient.Institution.search(q))
        else:
            institutions = []
        return _t('search.html',institutions=institutions,q=q)

    @cherrypy.expose
    def delete_account(self,id=None):
        try:
            a = ofxclient.Account.from_id(id)
            a.delete()
        except:
            pass
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def delete_bank(self,id=None):
        try:
            i = ofxclient.Institution.from_id(id)
            i.delete()
        except:
            pass
        raise cherrypy.HTTPRedirect("/")

    rest = REST()
