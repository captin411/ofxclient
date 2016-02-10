from setuptools import setup, find_packages
import os
import re

VERSIONFILE = "ofxclient/version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

setup(name='ofxclient',
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
      packages=find_packages(exclude=[
          'ez_setup', 'example', 'tests', 'external']),
      include_package_data=True,
      zip_safe=False,
      entry_points={
          'console_scripts': [
              'ofxclient = ofxclient.cli:run'
          ]
      },
      install_requires=[
          "argparse",
          "keyring",
          "ofxhome",
          "ofxparse>0.8",
          "beautifulsoup4",
      ],
      test_suite='tests',
      )
