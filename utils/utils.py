import serial.tools.list_ports

def get_ports():
    return serial.tools.list_ports.comports()

def get_ports_list():
    return [[p.name, p.device] for p in get_ports()]

def get_serial(port):
    ser = serial.Serial()
    ser.baudrate = 9600
    ser.port = port
    ser.timeout = 1
    try:
        ser.open()
    except:
        pass
    return ser
