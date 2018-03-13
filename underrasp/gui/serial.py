from . import Gtk, GLib
from ..utils import utils

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
        store = Gtk.ListStore(str, str)
        for p in ports:
            store.append(p)
        btn.set_model(store)
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
                self.worker.set_job(self.do_connect, "Connecting to the Arduino")
        else:
            if self.connection != None and self.connection.is_open:
                self.connection.close()
            self.append_log("Disconnected!")
            self.connection = None
            self.builder.get_object("serial_commands_list").set_sensitive(False)

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

    def serial_get(self, cmd):
        utils.write_line(self.connection, cmd)
        out = utils.read_all(self.connection, .1)
        for line in out:
            if line.startswith("CMD") and line.find(":") != -1:
                return line.split(":")[1].strip()
        return ""

    def get_update_dict(self):
        return {
            "power": "",
            "voltage": "",
            "ampere": "",
            "temperature": "",
            "error": "",
            "status": "",
            "time": "",
            "step": "",
            "mode": "",
        }

    def update_all(self):
        utils.read_all(self.connection, 1)
        out = self.get_update_dict()
        out['power'] = self.serial_get("w")
        out['voltage'] = self.serial_get("v")
        out['ampere'] = self.serial_get("a")
        out['temperature'] = self.serial_get("c")
        out['error'] = self.serial_get("e")
        out['status'] = self.serial_get("z")
        out['time'] = self.serial_get("t")
        out['step'] = self.serial_get("d")
        out['mode'] = self.serial_get("m")
        GLib.idle_add(self.update_gui, out)

    def update_gui(self, data):
        for k in data:
            v = data[k]
            if v == "":
                continue
            obj = ""
            if k == "ampere":
                obj = "serial_consumption_value"
            elif k == "voltage":
                obj = "serial_voltage_value"
            elif k == "power":
                obj = "serial_watts_value"
            elif k == "temperature":
                obj = "serial_ard_temp_value"
            elif k == "time":
                obj = "serial_rtc_time_value"
            elif k == "step":
                obj = "serial_eeprom_time_value"

            if obj != "":
                print(obj)
                self.builder.get_object(obj).set_text(v)

    def append_log(self, what):
        buf = self.logger.get_buffer()
        buf.insert(buf.get_end_iter(), "%s\n" % what)
        return False
