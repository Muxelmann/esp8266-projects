from machine import Pin, SPI
import time
import ustruct

# No Operation
_NOP = const(0x00)
# Software reset
_SWRESET = const(0x01)
# Read Display ID
_RDDID = const(0x04)
# Read Display Status
_RDDST = const(0x09)
# Read Display Power
_RDDPM = const(0x0A)
# Read Display
_RDDMADCTL = const(0x0B)
# Read Display Pixel
_RDDCOLMOD = const(0x0C)
# Read Display Image
_RDDIM = const(0x0D)
# Read Display Signal
_RDDSM = const(0x0E)

# Sleep in & booster off
_SLPIN = const(0x10)
# Sleep out & booster on
_SLPOUT = const(0x11)
# Partial mode on
_PTLON = const(0x12)
# Partial off (Normal)
_NORON = const(0x13)

# Display inversion off
_INVOFF = const(0x20)
# Display inversion on
_INVON = const(0x21)
# Hamma curve select
_GAMSET = const(0x26)
# Display off
_DISPOFF = const(0x28)
# Display on
_DISPON = const(0x29)
# Column address set
_CASET = const(0x2A)
# Row address set
_RASET = const(0x2B)
# Memory write
_RAMWR = const(0x2C)
# Memory read
_RAMRD = const(0x2E)

# Partial start/end address set
_PTLAR = const(0x30)
# Tearing effect line off
_TEOFF = const(0x34)
# Tearing effect mode set & on
_TEON = const(0x35)
# Memory data access control
_MADCTL = const(0x36)
# Idle mode off
_IDMOFF = const(0x38)
# Idle mode on
_IDMON = const(0x39)
# Interface pixel format
_COLMOD = const(0x3A)
# Read IDn (1..3)
_RDID1 = const(0xDA)
_RDID2 = const(0xDB)
_RDID3 = const(0xDC)


class ST7735(object):
    """
    My take on implementing the ST7735 TFT screen protocol
    """

    # Chip Select (not used as tied to ground)
    # cs = None
    # Register Select (a0 or dc)
    dc = None
    # Reset
    rst = None

    # hardware or software SPI, both use the following pins:
    # SCK 14, MOSI 13, MISO 12
    spi = None
    _spi_polarity = 0
    _spi_phase = 0

    width = None
    height = None

    _ms_delay = 50

    def __init__(self, dc, rst, width=128, height=160, hardware=True):
        if hardware:
            print('TFT via hardware-SPI')
            self.spi = SPI(1,
                           baudrate=20000000,
                           polarity=self._spi_polarity,
                           phase=self._spi_phase)
        else:
            print('TFT via software-SPI')
            self.spi = SPI(-1,
                           baudrate=500000,
                           polarity=self._spi_polarity,
                           phase=self._spi_phase)

        self.dc = dc
        self.dc.init(self.dc.OUT, value=0)
        self.rst = rst
        self.rst.init(self.rst.OUT, value=0)
        self.reset()

        self.width = width
        self.height = height

        self.init_display()

    def reset(self):
        """
        Resets the screen
        """
        self.rst.low()
        time.sleep_ms(200)
        self.rst.high()
        time.sleep_ms(200)

    def init_display(self):
        """
        Initialises display
        """
        self._write(command=_SWRESET)
        self._write(command=_SLPOUT)
        self._write(command=_DISPON)

    def _set_rect(self, x0, y0, x1, y1):
        """
        Sets a rectangular display window into which pixel data is placed
        """
        self._write(command=_CASET)
        self._write(data=self.encode_address(x0))
        self._write(data=self.encode_address(x1))
        self._write(command=_RASET)
        self._write(data=self.encode_address(y0))
        self._write(data=self.encode_address(y1))

    def draw_pixel(self, x, y, color):
        """
        Draws a single pixel on screen
        """
        self._set_rect(x, y, x, y)
        self._write(command=_RAMWR, data=self.encode_color(color))

    def fill_rect(self, x, y, w, h, color):
        """
        Draws a rectangle in a given color
        """
        x = min(self.width-1, max(0, x))
        y = min(self.height-1, max(0, y))
        w = min(self.width-x, max(1, w))
        h = min(self.height-y, max(1, h))

        self._set_rect(x, y, x+w-1, y+h-1)
        self._write(command=_RAMWR)
        self._write_chunks(self.encode_color(color), w*h)

    def encode_color(self, color):
        """
        Encodes 24bit int to address array with three 8bit values
        """
        return [(color >> 16) & 0xff, (color >> 8) & 0xff, color & 0xff]

    def encode_address(self, address):
        """
        Encodes 16bit int to address array with two 8bit values
        """
        return [(address >> 8) & 0xff, address & 0xff]

    def _write_chunks(self, data, reps, chunk_size=1024):
        """
        Writes a multiple of single bytes (8 bits) in one chunk to
        speed up transfer
        """
        # Reduce since max SPI buffer is 1024 bytes
        chunk_size //= len(data)
        chunks, rest = divmod(reps, chunk_size)
        if chunks:
            for _ in range(chunks):
                self._write(data=data*chunk_size)
        self._write(data=data*rest)

    def _write(self, command=None, data=None):
        """
        Sends a command and/or data
        """
        if command is not None:
            # Low for command
            self.dc.low()
            self.spi.write(bytearray([command]))
        if data is not None:
            # High for data
            self.dc.high()
            self.spi.write(bytearray(data))
        self.dc.low()
