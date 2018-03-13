import serial.tools.list_ports
from time import time

def get_ports():
    return serial.tools.list_ports.comports()

def get_ports_list():
    return [[p.name, p.device] for p in get_ports()]

def get_serial(port):
    ser = serial.Serial()
    ser.baudrate = 9600
    ser.port = port
    try:
        ser.open()
    except:
        pass
    return ser

def read_all(ser, timeout=1):
    start = time()
    lines = []
    while True:
        t = timeout - (time() - start)
        if t <= 0:
            break
        ser.timeout = t
        line = ""
        try:
            line = ser.readline().strip()
        except:
            break
        if line == "":
            break
        try:
            line = line.decode('ascii')
        except:
            continue
        lines.append(line)
    return lines

def read_line(ser, timeout=1):
    ser.timeout = timeout
    line = ""
    try:
        line = ser.readline().strip()
    except:
        pass
    if line != "":
        line = line.decode('ascii')
    return line

def write_line(ser, data):
    ser.write(('%s\n' % data).encode())
