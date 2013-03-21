Users Guide
===========

Running
-------

Open up the `terminal on OS X <http://www.ehow.com/how_6762372_open-terminal-apple.html>`_, or the `command prompt on Windows
<http://windows.microsoft.com/en-US/windows-vista/Open-a-Command-Prompt-window>`_.

1. Run the program::

    ofxclient

2. Follow the prompts at the main menu::

    +----------------------------------
    Main
    Edit ofxclient.ini to
    change descriptions or ofx options
    +----------------------------------
    (A) Add an account
    (Q) Quit
    choice>

Adding Accounts
---------------

1. Hitting `A` on the main menu will allow you to search for an bank name::

    choice> A
    +----------------------------------
    Add account
    +----------------------------------
    enter part of a bank name eg. express>

2. Then you can search for a part of a bank name::

    enter part of a bank name eg. express> wells
    (0) Wells Fargo
    (1) Wells Fargo Advantage Funds
    (2) Wells Fargo Advisor
    (3) Wells Fargo Advisors
    (4) Wells Fargo Bank
    (5) Wells Fargo Bank 2013
    (6) Wells Fargo Investments, LLC
    (7) Wells Fargo Trust-Investment Mgt

3. Enter the number of your choice and then enter the username and password for the bank::

    choice> 0
    username> happy
    password> times

4. All accounts at that bank are configured automatically and stored in the config file::

    +----------------------------------
    Main
    Edit ofxclient.ini to
    change descriptions or ofx options
    +----------------------------------
    (0) WF: Checking
    (A) Add an account
    (D) Download all combined
    (Q) Quit
    choice> q

Advanced configuration
----------------------

Sometimes, financial institutions have specific low level tweaks to *application ids*, *version numbers*, or *ofx protocol versions*.  In most cases you
will not have to mess with these values.

If you run into problems, take a look at the forums at `ofxhome.com <http://ofxhome.com>`_.  Often times others will have run into issues and have posted
specific configuration settings that have worked for them.

Note:

You are probably only interested in the ``institution.client_args.*`` settings but feel free to also mess
around with the ``description`` and ``institution.description`` settings.  Those control the name of the
account in the applications.  Do not ever modify the ``local_id`` options.

You will need to edit the $HOME/ofxclient.ini file.  Here is an example excerpt from that file::

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
