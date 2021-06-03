__all__ = ['getch']


class _Getch:
    """
    Gets a single character from standard input.  Does not echo to the screen.
    """

    def __init__(self, is_blocking=True):
        try:
            self.impl = _GetchWindows(is_blocking)
        except ImportError:
            self.impl = _GetchUnix(is_blocking)

    def __getattr__(self, attr):
        return getattr(self.impl, attr)

    def __call__(self):
        return self.impl()


class _GetchUnix:
    def __init__(self, is_blocking):
        import tty, sys, termios

        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
        if is_blocking is True:
            self._getch = self.blocking
        else:
            self._getch = self.non_blocking

    def blocking(self):
        import sys, tty, termios

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def non_blocking(self):
        import sys, tty, termios

        old_settings = termios.tcgetattr(sys.stdin)
        ch = None
        try:
            tty.setcbreak(sys.stdin.fileno())
            if self._is_data():
                ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        return ch

    def restore_settings(self):
        import sys, tty, termios

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

    @staticmethod
    def _is_data():
        import select, sys

        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

    def __call__(self):
        return self._getch()


class _GetchWindows:
    def __init__(self, is_blocking):
        import msvcrt

        if is_blocking is True:
            self._getch = self.blocking
        else:
            self._getch = self.non_blocking

    def blocking(self):
        import msvcrt

        return msvcrt.getch()

    def non_blocking(self):
        import msvcrt

        if msvcrt.kbhit():
            return msvcrt.getch()

    def restore_settings(self):
        pass

    def __call__(self):
        return self._getch()


getch = _Getch()

if __name__ == '__main__':
    import sys

    def getch_loop(is_blocking=True):
        print(
            f'{"Blocking" if is_blocking is True else "Non-blocking"} getch! Press any key! Esc to quit!'
        )
        i = 0
        getch_func = getch.blocking if is_blocking is True else getch.non_blocking
        while True:
            char = getch_func()
            if char or i % 15000 == 0:
                print(f'{i}: {char}')

            if char == '\x1b':  # ESC key
                break
            i += 1

    getch_file, *args = sys.argv
    print(
        'Getch! Echo key press usage:\n'
        f'Blocking mode: python {getch_file}\n'
        f'Non-blocking mode: python {getch_file} False\n'
    )

    getch_loop(is_blocking=False if len(args) and args[0] == 'False' else True)
