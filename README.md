Overview
=========

Simple ofxclient command line utility and OFX client libraries for development.

Full Documentation
==================

http://captin411.github.io/ofxclient/

Quick Start
===========

> $ ofxclient --download combined.ofx --open --verbose

Security Notes
==============

Initial Setup
-------------

When using the command line tool, initial account setup uses a third party website.
The website http://ofxhome.com will be consulted in order to determine information about
banks.  For example, the API url that your bank wants to use for their OFX communication.

You will be transmitting the name of your bank to a third party over an insecure channel.

Your password and username are not transmitted during the "search" phase.

The username and password will be transmitted to the URL for your bank as provided by
ofxhome.com.  You will be shown the URL that will be used.  If the URL does not look
appropriate, or otherwise appears to be tampered with, then do not submit your username
and password during the setup phase.

Bank Information Storage
------------------------
A configuration file `$HOME/ofxclient.ini` is used to store the information about the banks
that you want to download transactions from.

Your username and password are stored encrypted however your account number, routing number,
bank name, and account type are not encrypted and are visible to anyone with access to this
file on your local computer.

For full details on the config file, see: http://captin411.github.io/ofxclient/
