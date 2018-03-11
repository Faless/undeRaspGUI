from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
import matplotlib.pyplot as plt
import sys
from os import path

def get_dict_from_file(filename):
    f = open(filename, 'rt')

    ctd={
      "Depth":[],
      "Temp":[],
      "Cond":[],
      "Sal.":[],
      "O2Sat%":[],
      "O2ppm":[],
      "pH":[],
      "Eh":[],
      "Date":[]}

    i=0
    try:
       for line in f.readlines():
          if i>0 and len(line)>1:
             ctd["Depth"].append(float(line[:7]))
             ctd["Temp"].append(float(line[8:15]))
             ctd["Cond"].append(float(line[16:24]))
             ctd["Sal."].append(float(line[25:33]))
             ctd["O2Sat%"].append(float(line[34:40]))
             ctd["O2ppm"].append(float(line[41:46]))
             ctd["pH"].append(float(line[47:53]))
             ctd["Eh"].append(float(line[54:59]))
             ctd["Date"].append(line[60:])
          i=i+1
    finally:
        f.close()
        ctd["Depth"]=[x*-1 for x in ctd["Depth"]]

    return ctd

def get_plot_from_dict(ctd):
    host = host_subplot(111, axes_class=AA.Axes)
    plt.subplots_adjust(bottom=0.4)
    plt.subplots_adjust(left=0.1)
    plt.subplots_adjust(right=0.9)
    plt.subplots_adjust(top=0.8)

    sal = host.twiny()
    ph = host.twiny()
    o2 = host.twiny()
    eh = host.twiny()

    p1, = host.plot(ctd["Temp"],ctd["Depth"],label="Temperature")
    p2, = sal.plot(ctd["Sal."],ctd["Depth"],label="Salinity")
    p3, = ph.plot(ctd["pH"],ctd["Depth"],label="pH")
    p4, = o2.plot(ctd["O2Sat%"],ctd["Depth"],label="O2")
    p5, = eh.plot(ctd["Eh"],ctd["Depth"],label="Eh")

    offset = -40
    new_fixed_axis = ph.get_grid_helper().new_fixed_axis
    ph.axis["bottom"] = new_fixed_axis(loc="bottom", axes=ph, offset=(0, offset))
    ph.axis["top"].toggle(all=False)

    new_fixed_axis = o2.get_grid_helper().new_fixed_axis
    o2.axis["bottom"] = new_fixed_axis(loc="bottom", axes=o2, offset=(0, 2*offset))
    o2.axis["top"].toggle(all=False)

    new_fixed_axis = eh.get_grid_helper().new_fixed_axis
    eh.axis["top"] = new_fixed_axis(loc="top", axes=eh, offset=(0, -1*offset))
    eh.axis["bottom"].toggle(all=False)

    host.set_xlim(0, max(ctd["Temp"])+1)
    host.set_ylim(min(ctd["Depth"])-1,0)

    host.set_ylabel("Depth")
    host.set_xlabel("Temperature")
    sal.set_xlabel("Salinity")
    ph.set_xlabel("pH")
    o2.set_xlabel("O2 perc")
    eh.set_xlabel("Eh")

    sal.set_xlim(min(ctd["Sal."])-1,max(ctd["Sal."])+1)
    eh.set_xlim(min(ctd["Eh"])-20,max(ctd["Eh"])+20)
    ph.set_xlim(0, 14)
    o2.set_xlim(0, 100)

    host.axis["bottom"].label.set_color(p1.get_color())
    sal.axis["top"].label.set_color(p2.get_color())
    ph.axis["bottom"].label.set_color(p3.get_color())
    o2.axis["bottom"].label.set_color(p4.get_color())
    eh.axis["top"].label.set_color(p5.get_color())

    return plt

if __name__ == "__main__":
    txt = sys.argv[1]
    print("Reading: %s" % txt)
    ctd = get_dict_from_file(txt)
    plt = get_plot_from_dict(ctd)
    plt.draw()
    image=path.splitext(txt)[0] + ".jpg"
    print("Saving: %s" % image)
    plt.savefig(image)
