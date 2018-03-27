from . import Gtk, GLib
from .time_dialog import TimeDialog
from ..utils.network import NetworkListener, NetworkPinger
from ..utils import utils
from datetime import datetime, timedelta
from ..config import Config


class NetworkGUI:

    def __init__(self, window, panel):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("network.xml")

        window.connect("delete-event", self.on_quit)

        self.logger = self.get_obj("net_logs_view")
        self.listener = NetworkListener(Config.PORT,
                self.received, self.connection_changed, GLib.idle_add)
        self.pinger = NetworkPinger()

        # Add Serial tab
        label = Gtk.Label()
        label.set_text("Network")
        panel.append_page(self.get_obj("net_panel"), label)

    def get_data_dict(self):
        return {
            'voltage': '',
            'time': '',
            'disk_space': '',
            'serial': '',
            'data_hash': '',
            'data_points': ''
        }

    def update_ui(self, data):
        for k in data:
            self.get_obj("%s_value" % k).set_text(data[k])

    def append_log(self, what):
        buf = self.logger.get_buffer()
        buf.insert(buf.get_end_iter(), "%s\n" % what)
        return False

    def get_obj(self, name):
        return self.builder.get_object(name)

    def on_quit(self, a, b):
        self.listener.stop_wait()
        self.pinger.stop_wait()

    def connection_changed(self, connected):
        txt = 'Not connected'
        if connected:
            txt = 'Connected'
        self.get_obj('status_value').set_text(txt)

    def received(self, pkt):
        data = ''
        ip = pkt[1][0]
        port = pkt[1][1]
        try:
            data = pkt[0].decode('utf8').strip()
        except:
            self.append_log("Invalid packet received from %s:%d" % (ip, port))
            return
        self.append_log("From %s:%d" % (ip, port))
        self.append_log("%s\n" % data)

        sp = data.split('\n')
        d = self.get_data_dict()
        try:
            d['voltage'] = "%.2f" % float(sp[0].split(":")[-1])
            d['disk_space'] = '%d MiB' % int(float(sp[1].split(":")[-1]) / 1024 / 1024)
            d['time'] = sp[2].split(":")[-1].replace('|', ' ').replace('.', ':')
            d['serial'] = sp[3].split(":")[-1].replace('|', ' ')
            d['data_hash'] = sp[4].split(":")[-1]
            d['data_points'] = "%d" % int(sp[5].split(":")[-1])
            self.update_ui(d)
            if self.get_obj("keepalive_btn").get_active() and not self.pinger.ping:
                self.pinger.address = ip
                self.pinger.ping = True
        except Exception as e:
            print("Error receiving packet: %r" % e)
            pass
