from socket import socket, AF_INET, SOCK_DGRAM
from select import select
from time import sleep, time
from .thread import ThreadBase
import requests


class NetworkListener(ThreadBase):

    def __init__(self, port, onrecv, onconnchange, idle_add_func):
        self.port = port
        self.onrecv = onrecv
        self.idle_add_func = idle_add_func
        self.onconnchange = onconnchange
        super(NetworkListener, self).__init__(NetworkListener._loop)

    @staticmethod
    def _loop(gui):
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.bind(('', gui.port))
        connected = False
        conn_time = 0
        while not gui.stop_thread:
            ins, outs, ex = select([sock], [], [], 0.01)
            for i in ins:
                recv = i.recvfrom(1500)
                print(recv)
                gui.idle_add_func(gui.onrecv, recv)
                conn_time = time()
                if not connected:
                    connected = True
                    gui.idle_add_func(gui.onconnchange, True)
            sleep(0.1)
            if connected and time() - conn_time > 10:
                connected = False
                gui.idle_add_func(gui.onconnchange, False)
        sock.close()


class NetworkPinger(ThreadBase):

    def __init__(self):
        self.address = 'localhost'
        self.ping = False
        super(NetworkPinger, self).__init__(NetworkPinger._ping)

    @staticmethod
    def _ping(gui):
        while not gui.stop_thread:
            if gui.ping:
                # Send ping
                url = "http://%s/cgi-bin/ui.py" % gui.address
                print("pinging %s" % url)
                try:
                    requests.get(url, params={"cmd": "ping"})
                except Exception as e:
                    print("Unable to ping %r" % e)
                gui.ping = False
            sleep(0.1)
