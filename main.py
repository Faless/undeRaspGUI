#!/usr/bin/python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GLib
gi.require_version('WebKit2', '4.0')
from gi.repository import WebKit2
from datetime import datetime
import threading
import time
import matplotlib
matplotlib.use("agg")
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3 as NavigationToolbar
from plotter import plotter
from utils import utils

class BrowserGUI:

    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("browser.xml")
        self.window = self.builder.get_object("browser_window")
        self.webview = WebKit2.WebView()
        self.builder.get_object("browser_content").add_with_viewport(self.webview)
        self.window.show_all()

    def load_uri(self, uri):
        self.webview.load_uri(uri)

    def destroy(self):
        self.window.destroy()


class PlotterGUI:

    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("plotter.xml")
        self.window = self.builder.get_object("plotter_window")

        cdt = plotter.get_dict_from_file("data/test.txt")
        plt = plotter.get_plot_from_dict(cdt)
        plt.draw()

        self.canvas = FigureCanvas(plt.gcf())
        self.canvas.set_size_request(750, 550)
        self.builder.get_object("plotter_plot_scrollable").add_with_viewport(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas, self.window)
        self.builder.get_object("plotter_toolbar_scrollable").add_with_viewport(self.toolbar)
        self.window.show_all()

    def destroy(self):
        self.window.destroy()

class Worker:

    @staticmethod
    def _worker(gui):
        while not gui.stop_thread:
            if gui.job != None:
                gui.job()
                gui.job = None
                GLib.idle_add(gui.wait_dialog.hide)
            time.sleep(0.05)

    def __init__(self, builder):

        self.builder = builder
        self.wait_dialog = self.builder.get_object("wait_dialog")

        # This is the job funciton, will be executed by the worker if not None
        self.job = None
        self.stop_thread = False

        # Init the worker
        self.thread = threading.Thread(target=Worker._worker, args=(self,))
        self.thread.daemon = True
        self.thread.start()

    def set_job(self, func, title=""):
        assert(self.job is None)
        if title == "":
            title = "Running command..."
        self.builder.get_object("wait_label").set_label(title)
        self.wait_dialog.show_all()
        self.job = func


class SerialGUI:

    def __init__(self, builder, logger, worker):
        self.builder = builder
        self.logger = logger
        self.worker = worker
        self.connection = None
        self.refresh_ports()
        self.builder.get_object("serial_connect_btn").connect("toggled", self.connect_serial)
        self.builder.get_object("serial_commands_list").set_sensitive(False)
        self.builder.get_object("serial_refresh_btn").connect("button-release-event", self.refresh_release)

    def refresh_release(self, widget, event):
        self.refresh_ports()

    def refresh_ports(self):
        # Comm ports
        btn = self.builder.get_object("serial_port_btn")
        ports = utils.get_ports_list()
        port_store = Gtk.ListStore(str, str)
        for p in ports:
            port_store.append(p)
        btn.set_model(port_store)
        btn.set_entry_text_column(0)
        if len(ports) > 0:
            btn.set_active(0)
            self.builder.get_object("serial_connect_btn").set_sensitive(True)
        else:
            btn.set_active(-1)
            self.builder.get_object("serial_connect_btn").set_sensitive(False)

    def connect_serial(self, widget):
        if widget.get_active():
            btn = self.builder.get_object("serial_port_btn")
            self.connection = utils.get_serial(btn.get_active_id())
            if not self.connection.is_open:
                self.connection = None
                widget.set_active(False)
                self.append_log("Connection failed!")
            else:
                self.builder.get_object("serial_commands_list").set_sensitive(True)
                self.append_log("Connected to port: %s" % self.connection.port)
        else:
            if self.connection != None and self.connection.is_open:
                self.connection.close()
            self.append_log("Disconnected!")
            self.connection = None
            self.builder.get_object("serial_commands_list").set_sensitive(False)

    def append_log(self, what):
        buf = self.logger.get_buffer()
        buf.insert(buf.get_end_iter(), "%s\n" % what)
        return False


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
        self.worker = Worker(self.builder)

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

    def read_value():
        pass

if __name__ == "__main__":
    # Calling GObject.threads_init() is not needed for PyGObject 3.10.2+
    GObject.threads_init()
    gui = UnderRaspWaterGUI()
    Gtk.main()
