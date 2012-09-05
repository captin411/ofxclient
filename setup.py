from setuptools import setup, find_packages

setup(name='ofxclient',
      version='0.8.1',
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
      scripts=['scripts/ofxclientd'],
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
      entry_points="""
      """,
      )
