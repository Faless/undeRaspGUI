from . import Gtk, GObject, GLib
from datetime import datetime
import time
from .worker import Worker
from .serial import SerialGUI
from .plotter import PlotterGUI
from .browser import BrowserGUI

class UnderRaspWaterGUI:

    def __init__(self):

        # The plotter GUI
        self.plotter = None

        # The browser GUI
        self.browser = None

        # Parse the XML file
        self.builder = Gtk.Builder()
        self.builder.add_from_file("main.xml")

        # Start worker
        self.worker = Worker(self.builder, GLib.idle_add)

        # Setup window and close event handling
        self.window = self.builder.get_object("window")
        self.window.connect("delete-event", self.on_quit)

        # Setup logger
        self.logger = self.builder.get_object("serial_logs_view")

        # Setupdialogs 
        self.time_dialog = self.builder.get_object("time_dialog")

        # Timestamp editing signals
        self.builder.get_object("serial_eeprom_time_write").connect("button-release-event", self.open_time_dialog)
        self.builder.get_object("serial_rtc_time_write").connect("button-release-event", self.open_time_dialog)

        # Sensor data signals
        self.builder.get_object("net_read_sensors_btn").connect("button-release-event", self.read_sensors_data)

        # Sensor data signals
        self.builder.get_object("net_browse_images_btn").connect("button-release-event", self.open_browser)

        # Setup SerialGUI
        self.serialgui = SerialGUI(self.builder, self.logger, self.worker)

        # Show window
        self.window.show_all()

    def on_quit(self, a, b):
        self.worker.stop_thread = True
        self.worker.thread.join()
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
                self.worker.set_job(self.thread_test_job, "Sending data to RTC")
            else:
                self.worker.set_job(self.thread_test_job, "Sending data to EEPROM")

    def read_sensors_data(self, widget, event):
        if self.plotter is not None:
            self.plotter.destroy()
        self.plotter = PlotterGUI()

    def open_browser(self, widget, event):
        if self.browser is not None:
            self.browser.destroy()
        self.browser = BrowserGUI()
        self.browser.load_uri("http://www.esa.int/")

    def update_time_dialog(self):
        date = datetime.utcnow()
        self.builder.get_object("hours_value").set_value(date.hour)
        self.builder.get_object("minutes_value").set_value(date.minute)
        self.builder.get_object("seconds_value").set_value(date.second)

    def thread_test_job(self):
        for i in range(0,10):
            time.sleep(0.2)
        GLib.idle_add(self.append_log, "Job finished!")

    @staticmethod
    def run():
        # Calling GObject.threads_init() is not needed for PyGObject 3.10.2+
        GObject.threads_init()
        Gtk.main()
