"""MacOS toolbar pet using PyObjC."""
import objc
from Cocoa import (
    NSStatusBar,
    NSVariableStatusItemLength,
    NSImage,
    NSView,
    NSRect,
    NSImageView,
    NSTimer,
    NSMenu,
    NSMenuItem,
    NSEvent,
)
from PyObjCTools import AppHelper

from src.pet_data_loader import get_current_pet, load_pet_data
import time
import random


class CustomView(NSView):
    def initWithFrame_(self, frame):
        self = objc.super(CustomView, self).initWithFrame_(frame)
        if self:
            self.setWantsLayer_(True)
            self.layer().setBackgroundColor_(objc.nil)
        return self

    def mouseDown_(self, event):
        status_item = getattr(self, "statusItem", None)
        if status_item:
            menu = status_item.menu()
            if menu:
                location = NSEvent.mouseLocation()
                menu.popUpMenuPositioningItem_atLocation_inView_(None, location, None)


class MacOSToolbarIcon:
    """Toolbar pet icon that walks, sits and sleeps."""

    def __init__(self, parent=None):
        self.parent = parent

        self.status_bar = NSStatusBar.systemStatusBar()
        self.status_item = self.status_bar.statusItemWithLength_(NSVariableStatusItemLength)

        frame = NSRect((0, -12), (96, 48))
        self.custom_view = CustomView.alloc().initWithFrame_(frame)
        self.custom_view.statusItem = self.status_item

        self.gif_image_view = NSImageView.alloc().initWithFrame_(NSRect((0, -12), (44, 44)))
        self.custom_view.addSubview_(self.gif_image_view)
        self.status_item.setView_(self.custom_view)

        self.add_menu()

        self.direction = 1
        self.current_x = 0

        self.state = "walking"
        self.state_start_time = time.time()

        self.start_walk()

        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.05, self, objc.selector(self.update_, signature=b"v@:@"), None, True
        )

    def add_menu(self):
        menu = NSMenu.alloc().init()
        close_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Return to Desktop", "closeToolbarPet:", ""
        )
        close_item.setTarget_(self)
        menu.addItem_(close_item)
        self.status_item.setMenu_(menu)

    def closeToolbarPet_(self, _sender):
        if self.timer:
            self.timer.invalidate()
        self.status_bar.removeStatusItem_(self.status_item)
        if self.parent:
            self.parent.end_toolbar_pet()

    # State helpers -----------------------------------------------------
    def start_walk(self):
        self.state = "walking"
        self.state_start_time = time.time()
        k, c = get_current_pet()
        action = "walk_right" if self.direction == 1 else "walk_left"
        gif_path = load_pet_data(k, c, action)
        gif_image = NSImage.alloc().initByReferencingFile_(gif_path)
        self.gif_image_view.setImage_(gif_image)
        self.gif_image_view.setAnimates_(True)
        print("toolbar pet: start walking")

    def start_sit(self):
        self.state = "sitting"
        self.state_start_time = time.time()
        k, c = get_current_pet()
        gif_path = load_pet_data(k, c, "sit")
        gif_image = NSImage.alloc().initByReferencingFile_(gif_path)
        self.gif_image_view.setImage_(gif_image)
        self.gif_image_view.setAnimates_(True)
        print("toolbar pet: start sitting")

    def start_sleep(self):
        self.state = "sleeping"
        self.state_start_time = time.time()
        k, c = get_current_pet()
        gif_path = load_pet_data(k, c, "sleep")
        gif_image = NSImage.alloc().initByReferencingFile_(gif_path)
        self.gif_image_view.setImage_(gif_image)
        self.gif_image_view.setAnimates_(True)
        print("toolbar pet: start sleeping")

    # Animation update --------------------------------------------------
    def update_(self, _timer):
        now = time.time()
        k, c = get_current_pet()

        if self.state == "walking":
            step_size = 1
            self.current_x += self.direction * step_size

            if self.current_x <= -10:
                self.direction = 1
                gif_path = load_pet_data(k, c, "walk_right")
                gif_image = NSImage.alloc().initByReferencingFile_(gif_path)
                self.gif_image_view.setImage_(gif_image)
                self.gif_image_view.setAnimates_(True)
            elif self.current_x >= 58:
                self.direction = -1
                gif_path = load_pet_data(k, c, "walk_left")
                gif_image = NSImage.alloc().initByReferencingFile_(gif_path)
                self.gif_image_view.setImage_(gif_image)
                self.gif_image_view.setAnimates_(True)

            self.gif_image_view.setFrame_(NSRect((self.current_x, -12), (44, 44)))

            if now - self.state_start_time >= 10:
                if random.random() <= 0.6:
                    self.start_sit()
                else:
                    self.state_start_time = now

        elif self.state == "sitting":
            if now - self.state_start_time >= 10:
                if random.random() <= 0.5:
                    self.start_sleep()
                else:
                    self.start_walk()

        elif self.state == "sleeping":
            if now - self.state_start_time >= 20:
                self.start_sit()


if __name__ == "__main__":
    from Cocoa import NSApplication
    app = NSApplication.sharedApplication()
    icon = MacOSToolbarIcon()
    AppHelper.runEventLoop()