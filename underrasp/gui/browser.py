from . import Gtk, WebKit2

class BrowserGUI:

    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("browser.xml")
        self.window = self.builder.get_object("browser_window")
        self.webview = WebKit2.WebView()
        self.builder.get_object("browser_content").add_with_viewport(self.webview)
        self.window.show_all()

    def load_uri(self, uri):
        self.webview.load_uri(uri)

    def destroy(self):
        self.window.destroy()


