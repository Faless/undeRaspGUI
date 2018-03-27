from . import Gtk, GObject, GLib
import time
from .worker import Worker
from .serial import SerialGUI
from .plotter import PlotterGUI
from .browser import BrowserGUI
from .network import NetworkGUI


class UnderRaspWaterGUI:

    def __init__(self):

        # The plotter GUI
        self.plotter = None

        # The browser GUI
        self.browser = None

        # Parse the XML file
        self.builder = Gtk.Builder()
        self.builder.add_from_file("main.xml")
        self.window = self.builder.get_object("window")

        # Start serial worker
        self.serial_worker = Worker(self.builder, GLib.idle_add)

        # Sensor data signals
        #self.builder.get_object("net_read_sensors_btn").connect("button-release-event", self.read_sensors_data)

        # Sensor data signals
        #self.builder.get_object("net_browse_images_btn").connect("button-release-event", self.open_browser)

        tabs = self.builder.get_object("tabs")

        # Setup NetworkGUI
        self.networkgui = NetworkGUI(self.window, tabs)

        # Setup SerialGUI
        self.serialgui = SerialGUI(self.window, tabs, self.serial_worker)

        # Setup window and close event handling
        self.window.connect("delete-event", self.on_quit)

        # Show window
        self.window.show_all()

    def on_quit(self, a, b):
        self.serial_worker.stop_wait()
        Gtk.main_quit(a, b)

    def read_sensors_data(self, widget, event):
        if self.plotter is not None:
            self.plotter.destroy()
        self.plotter = PlotterGUI()

    def open_browser(self, widget, event):
        if self.browser is not None:
            self.browser.destroy()
        self.browser = BrowserGUI()
        self.browser.load_uri("http://www.esa.int/")

    @staticmethod
    def run():
        # Calling GObject.threads_init() is not needed for PyGObject 3.10.2+
        GObject.threads_init()
        Gtk.main()
