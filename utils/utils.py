import serial.tools.list_ports

def get_ports():
    return serial.tools.list_ports.comports()

def get_ports_list():
    return [[p.name, p.device] for p in get_ports()]
