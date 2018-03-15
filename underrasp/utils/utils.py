import serial.tools.list_ports
from time import time

def step_filter(s):
    if len(s) != 13:
        return "N/A"
    return "%s/%s/20%s %s:%s %s" % (s[4:6], s[2:4], s[0:2], s[6:8], s[8:10], s[10:13])

def mode_filter(s):
    try:
        v = int(float(s))
        d = v & 0x80 == 0x80
        t = v & 0x40 == 0x40
        v = v & 0x3F
        out = str(v)
        if d and t:
            out += " (D T)"
        elif d:
            out += " (D)"
        elif t:
            out += " (T)"
        return out
    except:
        return "N/A"

ERRORS = {
    0: "No error",
    11: "I2C init failed",
    12: "I2C busy",
    21: "RTC init failed",
    22: "RTC invalid date",
    41: "RPI unpowered",
    42: "RPI boot failed",
    43: "RPI unresponsive",
}

def error_filter(s):
    try:
        v = int(float(s))
        if v in ERRORS:
            return ERRORS[v]
        return "Unknown error: %d" % v
    except:
        return "N/A"

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
