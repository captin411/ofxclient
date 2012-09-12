import objc
from Foundation import *
from AppKit import *
from PyObjCTools import AppHelper
import ofxclient.server, webbrowser, ofxclient

class MyApp(NSApplication):

    def finishLaunching(self):
        # Make statusbar item
        statusbar = NSStatusBar.systemStatusBar()
        self.statusitem = statusbar.statusItemWithLength_(NSVariableStatusItemLength)
        self.icon = NSImage.alloc().initByReferencingFile_('/Users/dbartle/Documents/image128.png')
        self.icon.setScalesWhenResized_(True)
        self.icon.setSize_((16, 16))
        self.statusitem.setImage_(self.icon)

        #make the menu
        self.menubarMenu = NSMenu.alloc().init()


        accounts = [ i.__json__() for i in ofxclient.Account.list() ]
        if accounts:
            self.accountsMain = NSMenuItem.alloc().init()
            self.accountsMain.setTitle_('Downloads')

            self.accountsSubMenu = NSMenu.alloc().init()
            for a in accounts:
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(a['long_description'],'download:','')
                item.setRepresentedObject_(a['guid'])
                self.accountsSubMenu.addItem_(item)
            self.accountsMain.setSubmenu_(self.accountsSubMenu)

            self.menubarMenu.addItem_(self.accountsMain)

        self.menuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('View Web Application', 'open:', '')
        self.menubarMenu.addItem_(self.menuItem)

        self.quit = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'terminate:', '')
        self.menubarMenu.addItem_(self.quit)

        #add menu to statusitem
        self.statusitem.setMenu_(self.menubarMenu)
        self.statusitem.setToolTip_('OFX Client')

        t = NSThread.alloc().initWithTarget_selector_object_(self,self.runServer, None)
        t.start()

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


