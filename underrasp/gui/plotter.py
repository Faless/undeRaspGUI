from . import Gtk, FigureCanvas, NavigationToolbar
from ..plotter import plotter

class PlotterGUI:

    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("plotter.xml")
        self.window = self.builder.get_object("plotter_window")

        cdt = plotter.get_dict_from_file("data/test.txt")
        plt = plotter.get_plot_from_dict(cdt)
        plt.draw()

        self.canvas = FigureCanvas(plt.gcf())
        self.canvas.set_size_request(750, 550)
        self.builder.get_object("plotter_plot_scrollable").add_with_viewport(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas, self.window)
        self.builder.get_object("plotter_toolbar_scrollable").add_with_viewport(self.toolbar)
        self.window.show_all()

    def destroy(self):
        self.window.destroy()

