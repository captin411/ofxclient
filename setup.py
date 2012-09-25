from setuptools import setup, find_packages, Command
import re, os, tempfile

class DMGCommand(Command):
    """Command to build a DMG"""
    description = "Build an OSX DMG"
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):

        py2app = self.get_finalized_command('py2app')
        py2app.run()

        short_app_name = py2app.get_appname()
        app_path  = py2app.appdir
        dist_path = os.path.dirname(app_path)
        app_name  = os.path.basename(app_path)

        tmp_path = tempfile.mkdtemp()

        dmg_src = "%s/%s" % (tmp_path,short_app_name)
        self.mkpath(dmg_src)
        os.symlink('/Applications',"%s/Applications" % dmg_src)

        src_path = "%s/%s" % (dmg_src,app_name)
        self.mkpath(src_path)
        self.copy_tree(app_path,src_path)

        version = self.distribution.get_version()

        os.system("hdiutil create -srcfolder %s %s/%s-%s.dmg" % (dmg_src,dist_path,short_app_name,version))
       
        print "%s %s %s" % (app_path, src_path, tmp_path)


 #'app_dir': '/Users/dbartle/Documents/ofxc/dist/',
 #'app_files': ['/Users/dbartle/Documents/ofxc/dist/ofxclient.app'],
 #'appdir': '/Users/dbartle/Documents/ofxc/dist/ofxclient.app',
        


        pass

VERSIONFILE="ofxclient/version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

setup(name='ofxclient',
      app=["osx/OFXClient.py"],
      options={
        'py2app': {
            'iconfile': 'osx/image128.icns',
            'resources': 'osx/image128.png, ofxclient/webapp/html',
            'excludes': 'pygments',
            'plist': {
                'LSBackgroundOnly': True
            }
        }
      },
      version=verstr,
      description="OFX client for dowloading transactions from banks",
      long_description=open("./README.md", "r").read(),
      classifiers=[
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          "Natural Language :: English",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Topic :: Software Development :: Libraries :: Python Modules",
          "Topic :: Utilities",
          "License :: OSI Approved :: MIT License",
          ],
      keywords='ofx, Open Financial Exchange, download transactions',
      author='David Bartle',
      author_email='captindave@gmail.com',
      url='https://github.com/captin411/ofxclient',
      license='MIT License',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      cmdclass={'dmg':DMGCommand},
      entry_points={
          'console_scripts': [
              'ofxclientd = ofxclient.server:cmdline'
          ]
      },
      install_requires=[
          "ofxhome",
          "ofxparse>0.8",
          "simplejson",
          "BeautifulSoup>=3.0",
          "cherrypy",
          "mako",
          "keyring"
      ],
      test_suite='tests',
      )
