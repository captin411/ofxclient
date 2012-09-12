import objc
from Foundation import *
from AppKit import *
from PyObjCTools import AppHelper
import ofxclient.server, webbrowser

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

        self.menuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('View Accounts', 'open:', '')
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

    def open_(self, notification):
        webbrowser.open('http://localhost:8080', new=1, autoraise=True)


if __name__ == "__main__":
    app = MyApp.sharedApplication()
    AppHelper.runEventLoop()


