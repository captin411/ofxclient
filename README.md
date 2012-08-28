ofxclient
=========

Python OFX client libraries and basic web application

installing
==========

python setup.py

quick start
===========

This distribution comes with a small web application so that you can add your banks, accounts and credentials.

Run this command in the terminal or command prompt

> ofxclient

security
========
One thing that I hate about a lot of these financial tools is the lack of protection of things like passwords and account numbers.  You may not realize it
but some of these OFX files have your full credit card number as the account number.  This is actually necessary to have on file so that you can tell the
bank which account you want to download the transactions from using OFX.

To help combat this, I'm using the keyring module which attempts to use your OS's native keychain.  On OSX this is the Keychain.  Don't be suprised if you
are asked for your keychain password.  This is completely normal.

Passwords are stored in the keychain and are looked up by the bank/username combination

Your account numbers are hashed locally in the configuration file.  Whenever the full account number is needed, it is looked up in the keychain as needed.


FAQ
========
Q: Quicken exists and does this already. Why did you do this?
A: I don't use Quicken or GnuCash.  I use budgeting software (You Need A Budget) that does not have direct connect capabilities (intentionally).  Other
people are still using Microsoft Money which is no longer supported.  This helps those of us in this situation.
