from setuptools import setup, find_packages
import re

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
