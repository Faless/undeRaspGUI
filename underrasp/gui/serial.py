from . import Gtk, GLib
from ..utils import utils
from datetime import datetime, timedelta

class SerialGUI:

    MAP = [
        ("power", "w", "watts", None),
        ("voltage", "v", "voltage", None),
        ("ampere", "a", "consumption", None),
        ("temperature", "c", "ard_temp", None),
        ("error", "e", "", None),
        ("status", "z", "", None),
        ("time", "t", "rtc_time", None),
        ("step", "d", "eeprom_time",
            lambda s: "n/a" if len(s) != 13 else "%s/%s/20%s %s:%s %s" % \
                    (s[0:2], s[2:4], s[4:6], s[6:8], s[8:10], s[10:13])),
        ("mode", "m", "", None),
    ]

    def __init__(self, builder, worker):
        self.builder = builder
        self.logger = self.get_obj("serial_logs_view")
        self.worker = worker
        self.connection = None
        self.refresh_ports()
        self.get_obj("serial_connect_btn").connect("toggled", self.connect_serial)
        self.get_obj("serial_commands_list").set_sensitive(False)
        self.get_obj("serial_refresh_btn").connect("button-release-event", self.refresh_release)
        # Timestamp editing signals
        self.get_obj("serial_eeprom_time_write").connect("button-release-event", self.open_time_dialog)
        self.get_obj("serial_rtc_time_write").connect("button-release-event", self.open_time_dialog)

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

    def update_time_dialog(self, eeprom):
        date = datetime.utcnow()
        self.get_obj("calendar").select_month(date.month-1, date.year)
        self.get_obj("calendar").select_day(date.day)
        self.get_obj("hours_value").set_value(date.hour)
        self.get_obj("minutes_value").set_value(date.minute)
        if eeprom:
            self.get_obj("sec_adjustment").set_upper(255)
            self.get_obj("sec_adjustment").set_lower(15)
            self.get_obj("seconds_value").set_value(15)
        else:
            self.get_obj("sec_adjustment").set_upper(59)
            self.get_obj("sec_adjustment").set_lower(0)
            self.get_obj("seconds_value").set_value(date.second)

    def open_time_dialog(self, widget, event):
        time_dialog = self.get_obj("time_dialog")
        name = Gtk.Buildable.get_name(widget)
        self.update_time_dialog(name == "serial_eeprom_time_write")
        time_dialog.show()
        response = time_dialog.run()
        time_dialog.hide()
        if response == Gtk.ResponseType.OK:
            hours = int(self.get_obj("hours_value").get_value())
            mins = int(self.get_obj("minutes_value").get_value())
            secs = int(self.get_obj("seconds_value").get_value())
            date = self.get_obj("calendar").get_date()
            dt = datetime(date[0], date[1]+1, date[2], hours, mins)
            if name == "serial_rtc_time_write":
                dt += timedelta(seconds=secs)
                self.worker.set_job(self.rtc_time_set, data=[dt], title="Sending data to RTC")
            else:
                self.worker.set_job(self.eeprom_time_set, data=[dt, secs], title="Sending data to EEPROM")

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
        print(time, step)
        pass

    def append_log(self, what):
        buf = self.logger.get_buffer()
        buf.insert(buf.get_end_iter(), "%s\n" % what)
        return False

    def get_obj(self, name):
        return self.builder.get_object(name)
