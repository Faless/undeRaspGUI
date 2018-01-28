#!/usr/bin/python
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GLib
from datetime import datetime
import threading
import time

class UnderRaspWaterGUI:

    @staticmethod
    def _worker(gui):
        while not gui.stop_thread:
            if gui.job != None:
                gui.job()
                gui.job = None
                GLib.idle_add(gui.wait_dialog.hide)
            time.sleep(0.05)

    def __init__(self):

        # This is the job funciton, will be executed by the worker if not None
        self.job = None
        self.stop_thread = False

        # Parse the XML file
        self.builder = Gtk.Builder()
        self.builder.add_from_file("main.xml")

        # Setup window and close event handling
        self.window = self.builder.get_object("window")
        self.window.connect("delete-event", self.on_quit)

        # Setup logger
        self.logger = self.builder.get_object("logs_view")

        # Setupdialogs 
        self.wait_dialog = self.builder.get_object("wait_dialog")
        self.time_dialog = self.builder.get_object("time_dialog")

        # Timestamp editing signals
        self.builder.get_object("eeprom_time_write").connect("button-release-event", self.open_time_dialog)
        self.builder.get_object("rtc_time_write").connect("button-release-event", self.open_time_dialog)

        # Show window
        self.window.show_all()

        # Init the worker
        self.thread = threading.Thread(target=UnderRaspWaterGUI._worker, args=(self,))
        self.thread.daemon = True
        self.thread.start()

    def on_quit(self, a, b):
        self.stop_thread = True
        self.thread.join()
        Gtk.main_quit(a, b)

    def append_log(self, what):
        buf = self.logger.get_buffer()
        buf.insert(buf.get_end_iter(), "%s\n" % what)
        return False

    def open_time_dialog(self, widget, event):
        self.update_time_dialog()
        name = Gtk.Buildable.get_name(widget)
        self.time_dialog.show()
        response = self.time_dialog.run()
        self.time_dialog.hide()
        if response == Gtk.ResponseType.OK:
            if name == "rtc_time_write":
                self.set_job(self.thread_test_job, "Sending data to RTC")
            else:
                self.set_job(self.thread_test_job, "Sending data to EEPROM")

    def update_time_dialog(self):
        date = datetime.utcnow()
        self.builder.get_object("hours_value").set_value(date.hour)
        self.builder.get_object("minutes_value").set_value(date.minute)
        self.builder.get_object("seconds_value").set_value(date.second)

    def thread_test_job(self):
        for i in range(0,10):
            time.sleep(0.2)
        GLib.idle_add(self.append_log, "Job finished!")

    def set_job(self, func, title=""):
        assert(self.job is None)
        if title == "":
            title = "Running command..."
        self.builder.get_object("wait_label").set_label(title)
        self.wait_dialog.show_all()
        self.job = func

    def read_value():
        pass

if __name__ == "__main__":
    # Calling GObject.threads_init() is not needed for PyGObject 3.10.2+
    GObject.threads_init()
    gui = UnderRaspWaterGUI()
    Gtk.main()
