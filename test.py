#!/usr/bin/python
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from datetime import datetime

class UnderRaspWaterGUI:

    def __init__(self):

        # Parse the XML file
        self.builder = Gtk.Builder()
        self.builder.add_from_file("main.xml")

        # Setup window and close event handling
        self.window = self.builder.get_object("window")
        self.window.connect("delete-event", Gtk.main_quit)

        #
        # Setup signals
        #

        # Timestamp editing
        self.builder.get_object("eeprom_time_write").connect("button-release-event", self.open_time_dialog)
        self.builder.get_object("rtc_time_write").connect("button-release-event", self.open_time_dialog)

        #
        # Show window
        #

        self.window.show_all()

    def open_time_dialog(self, widget, event):
        self.update_time_dialog()
        name = Gtk.Buildable.get_name(widget)
        rtc = name == "rtc_time_write"
        calendar = self.builder.get_object("time_dialog")
        calendar.show()
        response = calendar.run()
        calendar.hide()
        if response == Gtk.ResponseType.OK:
            if rtc:
                print("sending data to RTC")
            else:
                print("sending data to EEPROM")

    def update_time_dialog(self):
        date = datetime.utcnow()
        self.builder.get_object("hours_value").set_value(date.hour)
        self.builder.get_object("minutes_value").set_value(date.minute)
        self.builder.get_object("seconds_value").set_value(date.second)

    def read_value():
        pass

#builder = Gtk.Builder()
#builder.add_from_file("main.xml")
#
#window = builder.get_object("window")
#window.connect("delete-event", Gtk.main_quit)
#
#builder.get_object("eeprom_time_value").connect("grab-focus", eeprom_time_activate)
#
#window.show_all()

if __name__ == "__main__":
    gui = UnderRaspWaterGUI()
    Gtk.main()
