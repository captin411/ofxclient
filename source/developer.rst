Developer Guide
===============

Module List
-----------

.. autosummary::
   :toctree:
   :nosignatures:

   ofxclient.Account
   ofxclient.BankAccount
   ofxclient.BrokerageAccount
   ofxclient.CreditCardAccount
   ofxclient.Institution
   ofxclient.OfxConfig
   ofxclient.Client
   ofxclient.config.SecurableConfigParser

Config File
-----------


Location
^^^^^^^^

Look for a file named::

  ofxclient.ini

The config file, as created the the ``ofxclient`` CLI exists in your home folder or documents folder.  This is OS dependent.

Items
^^^^^

The *ini* format consists of a section header, followed by a number of option = value pairs, each on new lines.

Section Header
""""""""""""""

:section header: This is the account local_id. See :py:class:`ofxclient.Account` object. Don't change this.

Account Options
"""""""""""""""

:account_type: The OFX account type at the protocol level. Don't change this - it is not part of the "description". *May not be present.*
:broker_id: The OFX broker id at the protocol level. Don't change this. *May not be present.*
:description: Human readable description of the account. Very safe to edit.
:local_id: This is the account local_id. See :py:class:`ofxclient.Account` object. Don't change this.
:number: The account number. Don't change this.
:routing_number: The OFX routing number / bank id. Don't change this. *May not be present.*

Institution Options
"""""""""""""""""""

:institution.client_args.app_id: The emulated desktop app. 'QWIN' means quicken and you probably should not touch this.
:institution.client_args.app_version: The emulated version of the desktop app. '2200' is Quickens way of meaning 'version 2013'.  It's possible you may need to bump this up by '100' (for each year) since Quicken discontinues two year old products.
:institution.client_args.id: The unique client ID.  You probably don't need to change this.  It is only pertinent if the OFX protocol version by your bank has to be '103' or higher.
:institution.client_args.ofx_version: The OFX protocol version. '102' is usually ok for most banks.  Some require '103'.  It is rare but you may need to tweak this.
:institution.local_id:  This is the institution local_id. See :py:class:`ofxclient.Institution` object. Don't change this.
:institution.description:  Human readable description of the bank. Very safe to edit.
:institution.id:  The FI Id assigned to the bank. Typically don't need to change this.
:institution.org:  The FI Org assigned to the bank. Typically don't need to change this.
:institution.url:  This FI Url assigned to the bank. Typically don't need to change this.
:institution.broker_id:  The FI broker id assigned to the bank.  Typically don't need to change this.
:institution.username:  Your username is securely stored so this is a placeholder.  If you username and password changed and things are breaking, set this to your username as a string to *unsecure* it.
:institution.password:  Your password is securely stored so this is a placeholder.  If you username and password changed and things are breaking, set this to your password as a string to *unsecure* it.

Example
^^^^^^^

Here is an example entry from the ``ofxclient.ini``::

  [f0a14074d33cdf83b4a099bc322dbe2fe19680ca1719425b33de5022]
  account_type = CHECKING
  description = Checking
  institution.broker_id = 
  institution.client_args.app_id = QWIN
  institution.client_args.app_version = 2200
  institution.client_args.id = 4fa6f700154f49839b869492f99c883f
  institution.client_args.ofx_version = 102
  institution.description = WF
  institution.id = 3000
  institution.local_id = e51fb78f88580a1c2e3bb65bd59495384383e58abda8796c9bf06dcf
  institution.org = WF
  institution.password = %{secured}
  institution.url = https://ofxdc.wellsfargo.com/ofx/process.ofx
  institution.username = %{secured}
  local_id = f0a14074d33cdf83b4a099bc322dbe2fe19680ca1719425b33de5022
  number = ******
  routing_number = ******

