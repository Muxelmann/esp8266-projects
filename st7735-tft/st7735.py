from machine import Pin, SPI
import time
import ustruct
import gc

gc.collect()

# Software reset
_SWRESET = const(0x01)
# Sleep out & booster on
_SLPOUT = const(0x11)
# Display on
_DISPON = const(0x29)
# Column address set
_CASET = const(0x2A)
# Row address set
_RASET = const(0x2B)
# Memory write
_RAMWR = const(0x2C)


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
        time.sleep_ms(150)
        self._write(command=_SLPOUT)
        time.sleep_ms(255)
        self._write(command=_DISPON)
        self.clear()

    def _set_rect(self, x0, y0, x1, y1):
        """
        Sets a rectangular display window into which pixel data is placed
        """
        self._write(command=_CASET)
        self._write(data=self._encode_address(x0))
        self._write(data=self._encode_address(x1))
        self._write(command=_RASET)
        self._write(data=self._encode_address(y0))
        self._write(data=self._encode_address(y1))

    def fill_pixel(self, x, y, color):
        """
        Draws a single pixel on screen
        """
        self._set_rect(x, y, x, y)
        self._write(command=_RAMWR, data=self._encode_color(color))

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
        self._write_chunks(self._encode_color(color), w*h)

    def clear(self, color=0x000000):
        """
        Clears the screen to a color
        """
        self.fill_rect(0, 0, self.width, self.height, color)
        gc.collect()

    def char(self, x, y, char, font, color=0xffffff, size=1):
        """
        Draws a camera at a given position using the user font. The
        font is a dictionary and can be scaled by size
        """
        if font is None:
            return

        start_char = font['start']
        end_char = font['end']
        ci = ord(char)

        if start_char <= ci <= end_char:
            width = font['width']
            height = font['height']
            ci = (ci - start_char) * width

            ch = font['data'][ci:ci+width]

            px = x
            if size <= 1:
                for c in ch:
                    py = y
                    for _ in range(height):
                        if c & 0x01:
                            self.fill_pixel(px, py, color)
                        py += 1
                        c >>= 1
                    px += 1
            else:
                for c in ch:
                    py = y
                    for _ in range(height):
                        if c & 0x01:
                            self.fill_rect(px, py, size, size, color)
                        py += size
                        c >>= 1
                    px += size
        else:
            return

    def text(self, x, y, string, font, color=0xffffff, size=1):
        """
        Draws text at a given position using the user font. Font can be
        scaled with the size argument.
        """
        if font is None:
            return

        width = size * font['width'] + 1

        px = x
        for c in string:
            if c == '\n':
                y += size * font['height'] + 1
                px = x
            else:
                self.char(px, y, c, font, color, size)
                px += width

                if px + width > self.width:
                    y += size * font['height'] + 1
                    px = x

    def draw_bitmap(self, bmp, x=0, y=0):
        """
        Takes bitmap from file and draws it to screen. For landscape, it may
        need to be mirrored vertically to display correctly.
        """
        if bmp is None:
            return

        x = min(self.width-1, max(0, x))
        y = min(self.height-1, max(0, y))
        w = bmp.w()
        h = bmp.h()
        if self.width < x+w:
            return
        if self.height < y+h:
            return

        self._set_rect(x, y, x+w-1, y+h-1)
        self._write(command=_RAMWR)
        for _ in range(w*h):
            c = bmp.get_pixel_color()
            self._write(data=self._encode_color(c))
        bmp.close()

    def _encode_color(self, color):
        """
        Encodes 24bit int to address array with three 8bit values
        """
        return [(color >> 16) & 0xff, (color >> 8) & 0xff, color & 0xff]

    def _encode_address(self, address):
        """
        Encodes 16bit int to address array with two 8bit values
        """
        return [(address >> 8) & 0xff, address & 0xff]

    def _write_chunks(self, data, reps, chunk_size=512):
        """
        Writes a multiple of single bytes (8 bits) in one chunk to
        speed up transfer
        """
        chunk_size //= (len(data))
        chunks, rest = divmod(reps, chunk_size)
        if chunks:
            for _ in range(chunks):
                self._write(data=data*chunk_size)
                gc.collect()
        self._write(data=data*rest)
        gc.collect()

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
