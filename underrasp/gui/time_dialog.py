from . import Gtk
from datetime import datetime

class TimeDialog:

    def __init__(self, window):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("time_dialog.xml")
        self.dialog = self.get_obj("time_dialog")
        self.dialog.set_attached_to(window)
        self.dialog.set_transient_for(window)

    def show(self):
        self.dialog.show()

    def hide(self):
        self.dialog.hide()

    def run(self):
        return self.dialog.run()

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

    def get_date_time(self):
        hours = int(self.get_obj("hours_value").get_value())
        mins = int(self.get_obj("minutes_value").get_value())
        secs = int(self.get_obj("seconds_value").get_value())
        date = self.get_obj("calendar").get_date()
        dt = datetime(date[0], date[1]+1, date[2], hours, mins, secs)
        return dt

    def get_time_step(self):
        hours = int(self.get_obj("hours_value").get_value())
        mins = int(self.get_obj("minutes_value").get_value())
        step = int(self.get_obj("seconds_value").get_value())
        date = self.get_obj("calendar").get_date()
        dt = datetime(date[0], date[1]+1, date[2], hours, mins)
        return (dt, step)

    def get_obj(self, obj):
        return self.builder.get_object(obj)
