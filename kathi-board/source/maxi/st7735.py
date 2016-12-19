from machine import Pin, SPI, PWM
import time

# Some commands to interface
_SWRESET = const(0x01)
_SLPOUT = const(0x11)
_DISPON = const(0x29)
_CASET = const(0x2A)
_RASET = const(0x2B)
_RAMWR = const(0x2C)

# cs = None # Chip Select (not used as tied to ground)
_dc = None # Register Select
_rst = None # Reset
_led_pwm = None # PWM for backlight

# hardware or software SPI, both use the following pins:
# SCK 14, MOSI 13, MISO 12
_spi = None

_width = None
_height = None


def _encode_color(color):
    return [(color >> 16) & 0xff, (color >> 8) & 0xff, color & 0xff]


def _encode_address(address):
    return [(address >> 8) & 0xff, address & 0xff]


def reset():
    global _rst
    _rst.low()
    time.sleep_ms(200)
    _rst.high()
    time.sleep_ms(200)


def _write(command=None, data=None):
    global _spi, _dc
    if command is not None:
        # Low for command
        _dc.low()
        _spi.write(bytearray([command]))
    if data is not None:
        # High for data
        _dc.high()
        _spi.write(bytearray(data))
    _dc.low()


def _write_chunks(data, reps, chunk_size=512):
    chunk_size //= (len(data))
    chunks, rest = divmod(reps, chunk_size)
    if chunks:
        for _ in range(chunks):
            _write(data=data*chunk_size)
    _write(data=data*rest)


def _set_rect(x0, y0, x1, y1):
    global _CASET, _RASET
    _write(command=_CASET)
    _write(data=_encode_address(x0))
    _write(data=_encode_address(x1))
    _write(command=_RASET)
    _write(data=_encode_address(y0))
    _write(data=_encode_address(y1))


def _fill_pixel(x, y, color):
    global _RAMWR
    _set_rect(x, y, x, y)
    _write(command=_RAMWR, data=_encode_color(color))


def _fill_rect(x, y, w, h, color):
    global _width, _height, _RAMWR
    x = min(_width-1, max(0, x))
    y = min(_height-1, max(0, y))
    w = min(_width-x, max(1, w))
    h = min(_height-y, max(1, h))

    _set_rect(x, y, x+w-1, y+h-1)
    _write(command=_RAMWR)
    _write_chunks(_encode_color(color), w*h)


def clear(color=0x000000):
    global _width, _height
    _fill_rect(0, 0, _width, _height, color)


def brightness(b):
    global _led_pwm
    if 1.0 < b:
        b = 1
    elif b < 0.0:
        b = 0
    _led_pwm.duty(int(-b * 1023 + 1023))


def init_display():
    global _SWRESET, _SLPOUT, _DISPON
    _write(command=_SWRESET)
    time.sleep_ms(150)
    _write(command=_SLPOUT)
    time.sleep_ms(255)
    _write(command=_DISPON)
    clear()


def char(x, y, char, font, color=0xffffff, size=1):
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
                        _fill_pixel(px, py, color)
                    py += 1
                    c >>= 1
                px += 1
        else:
            for c in ch:
                py = y
                for _ in range(height):
                    if c & 0x01:
                        _fill_rect(px, py, size, size, color)
                    py += size
                    c >>= 1
                px += size
    else:
        return


def text(x, y, string, font, color=0xffffff, size=1):
    if font is None:
        return

    width = size * font['width'] + 1

    px = x
    for c in string:
        if c == '\n':
            y += size * font['height'] + 1
            px = x
        else:
            char(px, y, c, font, color, size)
            px += width

            if px + width > _width:
                y += size * font['height'] + 1
                px = x


def prep_rect(w, h, x=0, y=0):
    global _width, _height, _RAMWR
    if w is None or h is None:
        return False

    x = min(_width-1, max(0, x))
    y = min(_height-1, max(0, y))
    if _width < x+w:
        return False
    if _height < y+h:
        return False

    _set_rect(x, y, x+w-1, y+h-1)
    _write(command=_RAMWR)
    return True


def fill_rect(data):
    if data is not None:
        _write(data=data)
        return True
    return False


def init(dc=Pin(4), rst=Pin(16), led=Pin(5), width=128, height=160):
    global _spi, _led_pwm, _dc, _rst, _width, _height
    _led_pwm = PWM(led, freq=500, duty=0)
    _spi = SPI(1, baudrate=20000000, polarity=0, phase=0)

    _dc = dc
    _dc.init(_dc.OUT, value=0)
    _rst = rst
    _rst.init(_rst.OUT, value=0)
    reset()

    _width = width
    _height = height

    init_display()
