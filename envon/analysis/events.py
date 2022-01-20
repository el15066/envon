
from envon.helpers import Log

log = Log(__name__)

class Events:

    def __init__(self):
        self._pending = []

    def new_event(self, ev):
        # log.debug('+ ev', ev)
        self._pending.append(ev)

    def get_and_clear(self):
        res = self._pending
        self._pending = []
        return res

events = Events()
