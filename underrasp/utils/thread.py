import threading

class ThreadBase:

    def __init__(self, func):
        self.stop_thread = False
        self.thread = threading.Thread(target=func, args=(self,))
        self.thread.daemon = True
        self.thread.start()

    def stop_wait(self):
        self.stop_thread = True
        self.thread.join()


