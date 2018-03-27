from ..utils.thread import ThreadBase
from time import sleep

class Worker(ThreadBase):

    @staticmethod
    def _worker(gui):
        while not gui.stop_thread:
            if gui.job != None:
                gui.job()
                gui.job = None
                gui.done()
            sleep(0.05)

    def __init__(self, builder, idle_add):

        self.builder = builder
        self.idle_add_func = idle_add
        self.wait_dialog = self.builder.get_object("wait_dialog")

        # This is the job funciton, will be executed by the worker if not None
        self.job = None

        super(Worker, self).__init__(Worker._worker)

    def set_job(self, func, data=[], title=""):
        assert(self.job is None)
        if title == "":
            title = "Running command..."
        self.builder.get_object("wait_label").set_label(title)
        self.wait_dialog.show_all()
        self.job = lambda: func(*data)

    def done(self):
        self.idle_add(self.wait_dialog.hide)

    def idle_add(self, what, *args):
        self.idle_add_func(what, *args)
