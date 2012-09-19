import objc
from Foundation import *
from AppKit import *
from PyObjCTools import AppHelper
import ofxclient.server, webbrowser, ofxclient, os, ofxclient.settings, time

class MyApp(NSApplication):

    def finishLaunching(self):
        # Make statusbar item
        statusbar = NSStatusBar.systemStatusBar()
        self.statusitem = statusbar.statusItemWithLength_(NSVariableStatusItemLength)
        self.icon = NSImage.alloc().initByReferencingFile_('image128.png')
        self.icon.setScalesWhenResized_(True)
        self.icon.setSize_((16, 16))
        self.statusitem.setImage_(self.icon)
        self.statusitem.setHighlightMode_(True)

        #add menu to statusitem
        self.statusitem.setToolTip_('OFX Client')
        self.updateMenu()

        t = NSThread.alloc().initWithTarget_selector_object_(self,self.runServer, None)
        t.start()

        c = NSThread.alloc().initWithTarget_selector_object_(self,self.configWatcher, None)
        c.start()

    def configWatcher(self):
        lastRefresh = None
        while 1:
            modifiedOn = os.stat(ofxclient.settings.CONFFILE).st_mtime
            if lastRefresh is None or modifiedOn > lastRefresh:
                lastRefresh = modifiedOn
                self.updateMenu()
            time.sleep(1)


    def updateMenu(self):
        self.statusitem.setMenu_(None)
        self.statusitem.setMenu_(self.makeMenu())

    def makeMenu(self):
        #make the menu
        menubarMenu = NSMenu.alloc().init()

        unsorted = [ i.__json__() for i in ofxclient.Account.list() ]
        accounts = sorted(unsorted,key=lambda a: str(a['long_description']).lower())

        accountsMain = NSMenuItem.alloc().init()
        accountsMain.setTitle_('Download')
        if not accounts:
            accountsMain.setEnabled_(False)

            error = NSMenuItem.alloc().init()
            error.setTitle_('No Accounts Configured')
            error.setEnabled_(False)
            menubarMenu.addItem_(error)
            menubarMenu.addItem_(NSMenuItem.separatorItem())


        if accounts:
            accountsSubMenu = NSMenu.alloc().init()
            for a in accounts:
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(a['long_description'],'download:','')
                item.setRepresentedObject_(a['guid'])
                accountsSubMenu.addItem_(item)
            accountsMain.setSubmenu_(accountsSubMenu)

        menubarMenu.addItem_(accountsMain)

        menubarMenu.addItem_(NSMenuItem.separatorItem())

        menuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Configure...', 'open:', '')
        menubarMenu.addItem_(menuItem)

        menubarMenu.addItem_(NSMenuItem.separatorItem())

        quit = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'terminate:', '')
        menubarMenu.addItem_(quit)
        return menubarMenu


    def runServer(self):
        pool = NSAutoreleasePool.alloc().init()
        ofxclient.server.server(open_browser=False)
        pool.release()

    def download_(self, sender):
        guid = sender._.representedObject
        webbrowser.open('http://localhost:8080/download/%s/transactions.ofx?days=10' % guid)

    def open_(self, notification):
        webbrowser.open('http://localhost:8080', new=1, autoraise=True)


if __name__ == "__main__":
    app = MyApp.sharedApplication()
    AppHelper.runEventLoop()


