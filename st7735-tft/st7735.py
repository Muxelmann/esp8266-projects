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
                           baudrate=16000000,
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
        self.heigh = height

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
        self.write_command(_SWRESET)
        self.write_command(_SLPOUT)
        self.write_command(_DISPON)

    def write_command(self, command):
        self._write(command=command)

    def write_data(self, data):
        self._write(data=[data])

    def write_list(self, byte_list):
        """
        Sends a list of bytes to the display as data
        """
        self._write(data=byte_list)

    def write888(self, value, reps=1):
        """
        Writes a 24bit value of data to the display
        """
        d0 = (value >> 16) & 0xff # upper 8 bits e.g. red
        d1 = (value >> 8) & 0xff  # middle 8 bits e.g. green
        d2 = value & 0xff         # lover 8 bits e.g. blue
        d_list = [d0, d1, d2]
        for _ in range(reps):
            self.write_list(d_list)

    def write88(self, value, reps=1):
        """
        Writes a 16bit value of data to the display
        """
        d0 = (value >> 8) & 0xff
        d1 = value & 0xff
        d_list = [d0, d1]
        for _ in range(reps):
            self.write_list(d_list)

    def set_addr_window(self, x0, y0, x1, y1):
        """
        Sets a rectangular display window into which pixel data is placed
        """
        self.write_command(_CASET)
        self.write88(x0)
        self.write88(x1)
        self.write_command(_RASET)
        self.write88(y0)
        self.write88(y1)

    def draw_pixel(self, x, y, color):
        """
        Draws a single pixel on screen
        """
        self.set_addr_window(x, y, x, y)
        self.write_command(_RAMWR)
        self.write888(color)

    def fill_rect(self, x, y, w, h, color):
        """
        Draws a rectangle in a given color
        """
        self.set_addr_window(x, y, x+w-1, y+h-1)
        self.write_command(_RAMWR)
        self.write888(color, reps=w*h)

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
