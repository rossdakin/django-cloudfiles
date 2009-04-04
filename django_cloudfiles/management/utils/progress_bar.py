from .string import write

TOTAL_TICKS = 76
BEGIN_CHAR = '['
END_CHAR = ']'
RUN_CHAR = '='
TIP_CHAR = '>'
BACKSPACE = '\b'

class ProgressBar(object):
    """
    Dirt simple command-line progress bar.

    Exports three public methods:
     * start(self) - call this to start the progress bar
     * end(self) - call this to end the progress bar (fills it to 100%)
     * tick(self, progress, total) - call this to make the progress bar grow to
                                     progress/total of its full length

    Allows for some customization by specifying in the constructor the
    characters used in the progress bar proper and the total bar length:
     * total_ticks
     * begin_char
     * end_char
     * run_char
     * tip_char
    """
    def __init__(self, total_ticks=TOTAL_TICKS, begin_char=BEGIN_CHAR,
                 end_char=END_CHAR, run_char=RUN_CHAR, tip_char=TIP_CHAR):
        self.total_ticks = total_ticks
        self.begin_char = begin_char
        self.end_char = end_char
        self.run_char = run_char
        self.tip_char = tip_char
        self._ticks_printed = 0
        self._started = False
        self._ended = False

    def _print_tick(self):
        write("%s%s%s" % (BACKSPACE, self.run_char, self.tip_char))
        self._ticks_printed += 1

    def start(self):
        if self._started:
            return
        self._started = True
        write("  %s%s" % (self.begin_char, self.tip_char))

    def tick(self, progress, total):
        if self._ended or not self._started:
            return
        if progress == total:
            self.end()
        percent = progress * 100 / total # no need for floating point division
        ticks_wanted = percent * self.total_ticks / 100
        while self._ticks_printed < ticks_wanted:
            self._print_tick()

    def end(self):
        if self._started and not self._ended:
            self._ended = True
            while self._ticks_printed < self.total_ticks:
                self._print_tick()
            print self.end_char
