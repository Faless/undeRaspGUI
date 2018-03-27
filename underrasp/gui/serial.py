from . import Gtk, GLib
from .time_dialog import TimeDialog
from ..utils import utils
from datetime import datetime, timedelta


class SerialGUI:

    MAP = [
        ("power", "w", "watts", None),
        ("voltage", "v", "voltage", None),
        ("ampere", "a", "consumption", None),
        ("temperature", "c", "ard_temp", None),
        ("error", "e", "error", utils.error_filter),
        ("status", "z", "", None),
        ("time", "t", "rtc_time", None),
        ("step", "d", "eeprom_time", utils.step_filter),
        ("mode", "m", "mode", utils.mode_filter),
    ]

    def __init__(self, window, panel, worker):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("serial.xml")

        self.time_dialog = TimeDialog(window)
        self.logger = self.get_obj("serial_logs_view")
        self.worker = worker
        self.connection = None

        # Add Serial tab
        label = Gtk.Label()
        label.set_text("Serial")
        panel.append_page(self.get_obj("serial_panel"), label)

        self.refresh_ports()
        self.get_obj("serial_connect_btn").connect("toggled", self.connect_serial)
        self.get_obj("serial_commands_list").set_sensitive(False)
        self.get_obj("serial_refresh_btn").connect("button-release-event", self.refresh_release)

        # Timestamp editing signals
        self.get_obj("serial_eeprom_time_write").connect("button-release-event", self.open_time_dialog)
        self.get_obj("serial_rtc_time_write").connect("button-release-event", self.open_time_dialog)

        # Error reset
        self.get_obj("serial_error_write_btn").connect("button-release-event", self.reset_error_release)

        for (name, cmd, gui, func) in SerialGUI.MAP:
            if gui == "":
                continue
            self.get_obj("serial_%s_read_btn" % gui).connect("button-release-event", self.read_release)

    def refresh_release(self, widget, event):
        self.refresh_ports()

    def refresh_ports(self):
        # Comm ports
        btn = self.get_obj("serial_port_btn")
        ports = utils.get_ports_list()
        store = Gtk.ListStore(str, str)
        for p in ports:
            store.append(p)
        btn.set_model(store)
        btn.set_entry_text_column(0)
        if len(ports) > 0:
            btn.set_active(0)
            self.get_obj("serial_connect_btn").set_sensitive(True)
        else:
            btn.set_active(-1)
            self.get_obj("serial_connect_btn").set_sensitive(False)

    def connect_serial(self, widget):
        if widget.get_active():
            btn = self.get_obj("serial_port_btn")
            self.connection = utils.get_serial(btn.get_active_id())
            if not self.connection.is_open:
                self.connection = None
                widget.set_active(False)
                self.append_log("Connection failed!")
            else:
                self.get_obj("serial_commands_list").set_sensitive(True)
                self.append_log("Connected to port: %s" % self.connection.port)
                self.worker.set_job(self.do_connect, title="Connecting to the Arduino")
        else:
            if self.connection != None and self.connection.is_open:
                self.connection.close()
            self.append_log("Disconnected!")
            self.connection = None
            self.get_obj("serial_commands_list").set_sensitive(False)

    def do_connect(self):
        utils.read_all(self.connection)
        utils.write_line(self.connection, "?")
        lines = utils.read_all(self.connection)
        valid = False
        for line in lines:
            if line.strip() == "":
                continue
            self.worker.idle_add(self.append_log, " %s" % line)
            valid = True
        if valid:
            self.worker.idle_add(self.append_log, "Serial connection successful!")
            self.update_all()
        else:
            self.worker.idle_add(self.append_log, "Serial connection failed!")
            self.worker.idle_add(self.connection_failed)

    def connection_failed(self):
        self.get_obj("serial_connect_btn").set_active(False)
        self.get_obj("serial_commands_list").set_sensitive(False)

    def serial_set(self, cmd):
        utils.write_line(self.connection, cmd)
        out = utils.read_all(self.connection, .1)
        for line in out:
            if line != "":
                return True
        return False

    def serial_get(self, cmd):
        utils.write_line(self.connection, cmd)
        out = utils.read_all(self.connection, .1)
        for line in out:
            if line.startswith("CMD") and line.find(":") != -1:
                return line.split(":")[1].strip()
        return ""

    def update_all(self):
        utils.read_all(self.connection, 1)
        out = {}
        for (name, cmd, gui, func) in SerialGUI.MAP:
            if cmd == "":
                continue
            out[name] = self.serial_get(cmd)
        GLib.idle_add(self.update_gui, out)

    def update_gui(self, data):
        for (name, cmd, gui, func) in SerialGUI.MAP:
            if name not in data or gui == "":
                continue
            val = data[name] if func is None else func(data[name])
            self.get_obj("serial_%s_value" % gui).set_text(val)

    def open_time_dialog(self, widget, event):
        name = Gtk.Buildable.get_name(widget)
        self.time_dialog.update_time_dialog(name == "serial_eeprom_time_write")
        self.time_dialog.show()
        response = self.time_dialog.run()
        self.time_dialog.hide()
        if response == Gtk.ResponseType.OK:
            if name == "serial_rtc_time_write":
                dt = self.time_dialog.get_date_time()
                self.worker.set_job(self.rtc_time_set, data=[dt], title="Sending data to RTC")
            else:
                dt, step = self.time_dialog.get_time_step()
                self.worker.set_job(self.eeprom_time_set, data=[dt, step], title="Sending data to EEPROM")

    def rtc_time_set(self, time):
        cmd = "T%s" % time.strftime("%y%m%d%H%M%S")
        if(self.serial_set(cmd)):
            log = "Time set: %s" % cmd
        else:
            log = "Error setting time: %s" % cmd
        GLib.idle_add(self.append_log, log)
        out = {"time": self.serial_get("t")}
        GLib.idle_add(self.update_gui, out)

    def eeprom_time_set(self, time, step):
        cmd = "D%s%03d" % (time.strftime("%y%m%d%H%M"), int(step))
        if(self.serial_set(cmd)):
            log = "EEPROM Time set: %s" % cmd
        else:
            log = "Error setting EEPRTOM time: %s" % cmd
        GLib.idle_add(self.append_log, log)
        out = {"step": self.serial_get("d")}
        GLib.idle_add(self.update_gui, out)
        pass

    def read_release(self, widget, event):
        cur = Gtk.Buildable.get_name(widget).replace("serial_", "").replace("_read_btn", "")
        self.worker.set_job(self.read_value, data=[cur])

    def read_value(self, elem):
        for (name, cmd, gui, func) in SerialGUI.MAP:
            if elem != gui:
                continue
            val = self.serial_get(cmd)
            if val == "":
                GLib.idle_add(self.append_log, "Unable to read %s" % name)
            else:
                GLib.idle_add(self.update_gui, {name: val})
            break

    def reset_error_release(self, widget, event):
        self.worker.set_job(self.reset_error, title="Clearing error")

    def reset_error(self):
        if self.serial_set("E"):
            GLib.idle_add(self.append_log, "Cleared error")
        else:
            GLib.idle_add(self.append_log, "Unable to clear error")
        val = self.serial_get("e")
        GLib.idle_add(self.update_gui, {"error": val})

    def append_log(self, what):
        buf = self.logger.get_buffer()
        buf.insert(buf.get_end_iter(), "%s\n" % what)
        return False

    def get_obj(self, name):
        return self.builder.get_object(name)
