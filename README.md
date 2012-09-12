Overview
=========

Python OFX client libraries and basic web application

I will put all easy to install files here for those who don't feel like typing and stuff:

https://github.com/captin411/ofxclient/downloads


Installing
==========

OSX
---

> sudo easy_install ofxclient

Windows
-------

> easy_install  --find-links https://github.com/captin411/ofxparse/downloads ofxclient

Note: Make sure %PYTHON_HOME%\Scripts is added to your %PATH% otherwise the 'ofxclientd' command will not be found on your path.

Source
------

> get source from https://github.com/captin411/ofxclient

> unpack it

> sudo python setup.py install

Quick Start
===========

This distribution comes with a small web application so that you can add your banks, accounts and credentials.

Run this command in the terminal or command prompt

> ofxclientd

If you need to, you can override the port that is bound to (8080)

> ofxclientd -p 8080

And if you don't want the webbrowser opened on start

> ofxclientd -b

Daemonizing on OSX or Linux
> nohup ofxclient -b &

Screen Shots
============

Searching for a bank
--------------------
http://cl.ly/image/1u0r3E2z2G0j
http://cl.ly/image/1J2K391G2104

Adding a bank
--------------------
http://cl.ly/image/1T294228380a

Your list of banks
--------------------
http://cl.ly/image/0a3Y1q3W3V1P
