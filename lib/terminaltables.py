"""Generate simple tables in terminals from a nested list of strings.

Example:
>>> from terminaltables import AsciiTable
>>> table = AsciiTable([['Name', 'Type'], ['Apple', 'fruit'], ['Carrot', 'vegetable']])
>>> print table.table
+--------+-----------+
| Name   | Type      |
+--------+-----------+
| Apple  | fruit     |
| Carrot | vegetable |
+--------+-----------+

Use SingleTable or DoubleTable instead of AsciiTable for box-drawing characters instead.

https://github.com/Robpol86/terminaltables
https://pypi.python.org/pypi/terminaltables
"""

import ctypes
import os
import re
import struct
import sys
if os.name != 'nt':
    import fcntl
    import termios
else:
    import ctypes.wintypes

__author__ = '@Robpol86'
__license__ = 'MIT'
__version__ = '1.1.1'


class _WindowsCSBI(object):

    """Interfaces with Windows CONSOLE_SCREEN_BUFFER_INFO API/DLL calls. Gets info for stderr and stdout.

    References:
        https://code.google.com/p/colorama/issues/detail?id=47.
        pytest's py project: py/_io/terminalwriter.py.

    Class variables:
    CSBI -- ConsoleScreenBufferInfo class/struct (not instance, the class definition itself) defined in _define_csbi().
    HANDLE_STDERR -- GetStdHandle() return integer for stderr.
    HANDLE_STDOUT -- GetStdHandle() return integer for stdout.
    WINDLL -- my own loaded instance of ctypes.WinDLL.
    """

    CSBI = None
    HANDLE_STDERR = None
    HANDLE_STDOUT = None
    WINDLL = ctypes.LibraryLoader(getattr(ctypes, 'WinDLL', None))

    @staticmethod
    def _define_csbi():
        """Defines structs and populates _WindowsCSBI.CSBI."""
        if _WindowsCSBI.CSBI is not None:
            return

        class COORD(ctypes.Structure):

            """Windows COORD structure. http://msdn.microsoft.com/en-us/library/windows/desktop/ms682119"""
            _fields_ = [('X', ctypes.c_short), ('Y', ctypes.c_short)]

        class SmallRECT(ctypes.Structure):

            """Windows SMALL_RECT structure. http://msdn.microsoft.com/en-us/library/windows/desktop/ms686311"""
            _fields_ = [
                ('Left',
                 ctypes.c_short),
                ('Top',
                 ctypes.c_short),
                ('Right',
                 ctypes.c_short),
                ('Bottom',
                 ctypes.c_short)]

        class ConsoleScreenBufferInfo(ctypes.Structure):

            """Windows CONSOLE_SCREEN_BUFFER_INFO structure.
            http://msdn.microsoft.com/en-us/library/windows/desktop/ms682093
            """
            _fields_ = [
                ('dwSize', COORD),
                ('dwCursorPosition', COORD),
                ('wAttributes', ctypes.wintypes.WORD),
                ('srWindow', SmallRECT),
                ('dwMaximumWindowSize', COORD)
            ]

        _WindowsCSBI.CSBI = ConsoleScreenBufferInfo

    @staticmethod
    def initialize():
        """Initializes the WINDLL resource and populated the CSBI class variable."""
        _WindowsCSBI._define_csbi()
        _WindowsCSBI.HANDLE_STDERR = _WindowsCSBI.HANDLE_STDERR or _WindowsCSBI.WINDLL.kernel32.GetStdHandle(
            -12)
        _WindowsCSBI.HANDLE_STDOUT = _WindowsCSBI.HANDLE_STDOUT or _WindowsCSBI.WINDLL.kernel32.GetStdHandle(
            -11)
        if _WindowsCSBI.WINDLL.kernel32.GetConsoleScreenBufferInfo.argtypes:
            return

        _WindowsCSBI.WINDLL.kernel32.GetStdHandle.argtypes = [
            ctypes.wintypes.DWORD]
        _WindowsCSBI.WINDLL.kernel32.GetStdHandle.restype = ctypes.wintypes.HANDLE
        _WindowsCSBI.WINDLL.kernel32.GetConsoleScreenBufferInfo.restype = ctypes.wintypes.BOOL
        _WindowsCSBI.WINDLL.kernel32.GetConsoleScreenBufferInfo.argtypes = [
            ctypes.wintypes.HANDLE, ctypes.POINTER(_WindowsCSBI.CSBI)
        ]

    @staticmethod
    def get_info(handle):
        """Get information about this current console window (for Microsoft Windows only).

        Raises IOError if attempt to get information fails (if there is no console window).

        Don't forget to call _WindowsCSBI.initialize() once in your application before calling this method.

        Positional arguments:
        handle -- either _WindowsCSBI.HANDLE_STDERR or _WindowsCSBI.HANDLE_STDOUT.

        Returns:
        Dictionary with different integer values. Keys are:
            buffer_width -- width of the buffer (Screen Buffer Size in cmd.exe layout tab).
            buffer_height -- height of the buffer (Screen Buffer Size in cmd.exe layout tab).
            terminal_width -- width of the terminal window.
            terminal_height -- height of the terminal window.
            bg_color -- current background color (http://msdn.microsoft.com/en-us/library/windows/desktop/ms682088).
            fg_color -- current text color code.
        """
        # Query Win32 API.
        csbi = _WindowsCSBI.CSBI()
        try:
            if not _WindowsCSBI.WINDLL.kernel32.GetConsoleScreenBufferInfo(
                    handle,
                    ctypes.byref(csbi)):
                raise IOError(
                    'Unable to get console screen buffer info from win32 API.')
        except ctypes.ArgumentError:
            raise IOError(
                'Unable to get console screen buffer info from win32 API.')

        # Parse data.
        result = dict(
            buffer_width=int(csbi.dwSize.X - 1),
            buffer_height=int(csbi.dwSize.Y),
            terminal_width=int(csbi.srWindow.Right - csbi.srWindow.Left),
            terminal_height=int(csbi.srWindow.Bottom - csbi.srWindow.Top),
            bg_color=int(csbi.wAttributes & 240),
            fg_color=int(csbi.wAttributes % 16),
        )
        return result


def _align_and_pad(input_, align, width, height, lpad, rpad):
    """Aligns a string with center/rjust/ljust and adds additional padding.

    Positional arguments:
    input_ -- input string to operate on.
    align -- 'left', 'right', or 'center'.
    width -- align to this column width.
    height -- pad newlines and spaces to set cell to this height.
    lpad -- number of spaces to pad on the left.
    rpad -- number of spaces to pad on the right.

    Returns:
    Modified string.
    """
    # Handle trailing newlines or empty strings, str.splitlines() does not
    # satisfy.
    lines = input_.splitlines() or ['']
    if input_.endswith('\n'):
        lines.append('')

    # Align.
    if align == 'center':
        aligned = '\n'.join(l.center(width) for l in lines)
    elif align == 'right':
        aligned = '\n'.join(l.rjust(width) for l in lines)
    else:
        aligned = '\n'.join(l.ljust(width) for l in lines)

    # Pad.
    padded = '\n'.join((' ' * lpad) + l + (' ' * rpad)
                       for l in aligned.splitlines() or [''])

    # Increase height.
    additional_padding = height - 1 - padded.count('\n')
    if additional_padding > 0:
        padded += ('\n{0}'.format(' ' * (width + lpad + rpad))) * \
            additional_padding

    return padded


def _convert_row(row, left, middle, right):
    """Converts a row (list of strings) into a joined string with left and right borders. Supports multi-lines.

    Positional arguments:
    row -- list of strings representing one row.
    left -- left border.
    middle -- column separator.
    right -- right border.

    Returns:
    String representation of a row.
    """
    if not row:
        return left + right

    if not any('\n' in c for c in row):
        return left + middle.join(row) + right

    # Split cells in the row by newlines. This creates new rows.
    split_cells = [(c.splitlines() or ['']) +
                   ([''] if c.endswith('\n') else []) for c in row]
    height = len(split_cells[0])

    # Merge rows into strings.
    converted_rows = list()
    for row_number in range(height):
        converted_rows.append(
            left + middle.join([c[row_number] for c in split_cells]) + right)
    return '\n'.join(converted_rows)


def set_terminal_title(title):
    """Sets the terminal title.

    Positional arguments:
    title -- the title to set.
    """
    if os.name == 'nt' and sys.version_info[0] == 3:
        ctypes.windll.kernel32.SetConsoleTitleW(title)
        return
    if os.name == 'nt' and sys.version_info[0] == 2:
        ctypes.windll.kernel32.SetConsoleTitleA(title)
        return
    sys.stdout.write('\033]0;{0}\007'.format(title))


def terminal_height():
    """Returns the terminal's height (number of lines)."""
    try:
        if os.name == 'nt':
            _WindowsCSBI.initialize()
            return _WindowsCSBI.get_info(
                _WindowsCSBI.HANDLE_STDOUT)['terminal_height']
        return struct.unpack(
            'hhhh',
            fcntl.ioctl(
                0,
                termios.TIOCGWINSZ,
                '\000' *
                8))[0]
    except IOError:
        return 24


def terminal_width():
    """Returns the terminal's width (number of character columns)."""
    try:
        if os.name == 'nt':
            _WindowsCSBI.initialize()
            return _WindowsCSBI.get_info(
                _WindowsCSBI.HANDLE_STDOUT)['terminal_width']
        return struct.unpack(
            'hhhh',
            fcntl.ioctl(
                0,
                termios.TIOCGWINSZ,
                '\000' *
                8))[1]
    except IOError:
        return 80


class AsciiTable(object):

    """Draw a table using regular ASCII characters, such as `+`, `|`, and `-`."""
    CHAR_CORNER_LOWER_LEFT = '+'
    CHAR_CORNER_LOWER_RIGHT = '+'
    CHAR_CORNER_UPPER_LEFT = '+'
    CHAR_CORNER_UPPER_RIGHT = '+'
    CHAR_HORIZONTAL = '-'
    CHAR_INTERSECT_BOTTOM = '+'
    CHAR_INTERSECT_CENTER = '+'
    CHAR_INTERSECT_LEFT = '+'
    CHAR_INTERSECT_RIGHT = '+'
    CHAR_INTERSECT_TOP = '+'
    CHAR_VERTICAL = '|'

    def __init__(self, table_data, title=None):
        self.table_data = table_data
        self.title = title

        self.inner_column_border = True
        self.inner_heading_row_border = True
        self.inner_row_border = False
        self.justify_columns = dict()  # {0: 'right', 1: 'left', 2: 'center'}
        self.outer_border = True
        self.padding_left = 1
        self.padding_right = 1

    def column_max_width(self, column_number):
        """Returns the maximum width of a column based on the current terminal width.

        Positional arguments:
        column_number -- the column number to query.

        Returns:
        The max width of the column (integer).
        """
        column_widths = self.column_widths
        borders_padding = (len(
            column_widths) * self.padding_left) + (len(column_widths) * self.padding_right)
        if self.outer_border:
            borders_padding += 2
        if self.inner_column_border and column_widths:
            borders_padding += len(column_widths) - 1
        other_column_widths = sum(column_widths) - column_widths[column_number]
        return terminal_width() - other_column_widths - borders_padding

    @property
    def column_widths(self):
        """Returns a list of integers representing the widths of each table column without padding."""
        if not self.table_data:
            return list()

        number_of_columns = max(len(r) for r in self.table_data)
        widths = [0] * number_of_columns

        for row in self.table_data:
            for i in range(len(row)):
                if not row[i]:
                    continue
                widths[i] = max(
                    widths[i], len(max(row[i].splitlines(), key=len)))

        return widths

    @property
    def ok(self):
        """Returns True if the table fits within the terminal width, False if the table breaks."""
        return self.table_width <= terminal_width()

    @property
    def padded_table_data(self):
        """Returns a list of lists of strings. It's self.table_data but with the cells padded with spaces and newlines.

        Most of the work in this class is done here.
        """
        if not self.table_data:
            return list()

        # Set all rows to the same number of columns.
        max_columns = max(len(r) for r in self.table_data)
        new_table_data = [
            r + [''] * (max_columns - len(r)) for r in self.table_data]

        # Pad strings in each cell, and apply text-align/justification.
        column_widths = self.column_widths
        for row in new_table_data:
            height = max([c.count('\n') for c in row] or [0]) + 1
            for i in range(len(row)):
                align = self.justify_columns.get(i, 'left')
                cell = _align_and_pad(
                    row[i],
                    align,
                    column_widths[i],
                    height,
                    self.padding_left,
                    self.padding_right)
                row[i] = cell

        return new_table_data

    def table(self, row_separator=1):
        """Returns a large string of the entire table ready to be printed to the terminal."""
        padded_table_data = self.padded_table_data
        column_widths = [
            c +
            self.padding_left +
            self.padding_right for c in self.column_widths]
        final_table_data = list()

        # Append top border.
        max_title = sum(
            column_widths) + ((len(column_widths) - 1) if self.inner_column_border else 0)
        if self.outer_border and self.title and len(self.title) <= max_title:
            pseudo_row = _convert_row(
                ['h' * w for w in column_widths], 'l', 't' if self.inner_column_border else '', 'r')
            pseudo_row_key = dict(
                h=self.CHAR_HORIZONTAL,
                l=self.CHAR_CORNER_UPPER_LEFT,
                t=self.CHAR_INTERSECT_TOP,
                r=self.CHAR_CORNER_UPPER_RIGHT)
            pseudo_row_re = re.compile(
                '({0})'.format(
                    '|'.join(
                        list(pseudo_row_key.keys()))))
            substitute = lambda s: pseudo_row_re.sub(
                lambda x: pseudo_row_key[
                    x.string[
                        x.start():x.end()]],
                s)
            row = substitute(
                pseudo_row[:1]) + self.title + substitute(pseudo_row[1 + len(self.title):])
            final_table_data.append(row)
        elif self.outer_border:
            row = _convert_row(
                [
                    self.CHAR_HORIZONTAL *
                    w for w in column_widths],
                self.CHAR_CORNER_UPPER_LEFT,
                self.CHAR_INTERSECT_TOP if self.inner_column_border else '',
                self.CHAR_CORNER_UPPER_RIGHT)
            final_table_data.append(row)

        # Build table body.
        indexes = list(range(len(padded_table_data)))
        for i in indexes:
            row = _convert_row(
                padded_table_data[i],
                self.CHAR_VERTICAL if self.outer_border else '',
                self.CHAR_VERTICAL if self.inner_column_border else '',
                self.CHAR_VERTICAL if self.outer_border else '')
            final_table_data.append(row)

            # Insert row separator.
            if i == indexes[-1]:
                continue
            if self.inner_row_border or (
                    self.inner_heading_row_border and i < row_separator):
                row = _convert_row(
                    [
                        self.CHAR_HORIZONTAL *
                        w for w in column_widths],
                    self.CHAR_INTERSECT_LEFT if self.outer_border else '',
                    self.CHAR_INTERSECT_CENTER if self.inner_column_border else '',
                    self.CHAR_INTERSECT_RIGHT if self.outer_border else '')
                final_table_data.append(row)

        # Append bottom border.
        if self.outer_border:
            row = _convert_row(
                [
                    self.CHAR_HORIZONTAL *
                    w for w in column_widths],
                self.CHAR_CORNER_LOWER_LEFT,
                self.CHAR_INTERSECT_BOTTOM if self.inner_column_border else '',
                self.CHAR_CORNER_LOWER_RIGHT)
            final_table_data.append(row)

        return '\n'.join(final_table_data)

    @property
    def table_width(self):
        """Returns the width of the table including padding and borders."""
        column_widths = self.column_widths
        borders_padding = (len(
            column_widths) * self.padding_left) + (len(column_widths) * self.padding_right)
        if self.outer_border:
            borders_padding += 2
        if self.inner_column_border and column_widths:
            borders_padding += len(column_widths) - 1
        return sum(column_widths) + borders_padding


class UnixTable(AsciiTable):

    """Draw a table using box-drawing characters on Unix platforms. Table borders won't have any gaps between lines.

    Similar to the tables shown on PC BIOS boot messages, but not double-lined.
    """
    CHAR_CORNER_LOWER_LEFT = '\033(0\x6d\033(B'
    CHAR_CORNER_LOWER_RIGHT = '\033(0\x6a\033(B'
    CHAR_CORNER_UPPER_LEFT = '\033(0\x6c\033(B'
    CHAR_CORNER_UPPER_RIGHT = '\033(0\x6b\033(B'
    CHAR_HORIZONTAL = '\033(0\x71\033(B'
    CHAR_INTERSECT_BOTTOM = '\033(0\x76\033(B'
    CHAR_INTERSECT_CENTER = '\033(0\x6e\033(B'
    CHAR_INTERSECT_LEFT = '\033(0\x74\033(B'
    CHAR_INTERSECT_RIGHT = '\033(0\x75\033(B'
    CHAR_INTERSECT_TOP = '\033(0\x77\033(B'
    CHAR_VERTICAL = '\033(0\x78\033(B'

    @property
    def table(self):
        ascii_table = super(UnixTable, self).table
        optimized = ascii_table.replace('\033(B\033(0', '')
        return optimized


class WindowsTable(AsciiTable):

    """Draw a table using box-drawing characters on Windows platforms. This uses Code Page 437. Single-line borders.

    From: http://en.wikipedia.org/wiki/Code_page_437#Characters
    """
    CHAR_CORNER_LOWER_LEFT = b'\xc0'.decode('ibm437')
    CHAR_CORNER_LOWER_RIGHT = b'\xd9'.decode('ibm437')
    CHAR_CORNER_UPPER_LEFT = b'\xda'.decode('ibm437')
    CHAR_CORNER_UPPER_RIGHT = b'\xbf'.decode('ibm437')
    CHAR_HORIZONTAL = b'\xc4'.decode('ibm437')
    CHAR_INTERSECT_BOTTOM = b'\xc1'.decode('ibm437')
    CHAR_INTERSECT_CENTER = b'\xc5'.decode('ibm437')
    CHAR_INTERSECT_LEFT = b'\xc3'.decode('ibm437')
    CHAR_INTERSECT_RIGHT = b'\xb4'.decode('ibm437')
    CHAR_INTERSECT_TOP = b'\xc2'.decode('ibm437')
    CHAR_VERTICAL = b'\xb3'.decode('ibm437')


class WindowsTableDouble(AsciiTable):

    """Draw a table using box-drawing characters on Windows platforms. This uses Code Page 437. Double-line borders."""
    CHAR_CORNER_LOWER_LEFT = b'\xc8'.decode('ibm437')
    CHAR_CORNER_LOWER_RIGHT = b'\xbc'.decode('ibm437')
    CHAR_CORNER_UPPER_LEFT = b'\xc9'.decode('ibm437')
    CHAR_CORNER_UPPER_RIGHT = b'\xbb'.decode('ibm437')
    CHAR_HORIZONTAL = b'\xcd'.decode('ibm437')
    CHAR_INTERSECT_BOTTOM = b'\xca'.decode('ibm437')
    CHAR_INTERSECT_CENTER = b'\xce'.decode('ibm437')
    CHAR_INTERSECT_LEFT = b'\xcc'.decode('ibm437')
    CHAR_INTERSECT_RIGHT = b'\xb9'.decode('ibm437')
    CHAR_INTERSECT_TOP = b'\xcb'.decode('ibm437')
    CHAR_VERTICAL = b'\xba'.decode('ibm437')


class SingleTable(WindowsTable if os.name == 'nt' else UnixTable):

    """Cross-platform table with single-line box-drawing characters."""
    pass


class DoubleTable(WindowsTableDouble):

    """Cross-platform table with box-drawing characters. On Windows it's double borders, on Linux/OSX it's unicode."""
    pass
