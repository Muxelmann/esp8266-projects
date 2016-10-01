class Bitmap(object):

    _f = None
    _bpp = None

    def __init__(self, path, bpp=24):
        self._f = open(path, 'rb')

        d = self._f.read(2)
        if d != b'BM':
            self.close()
            return

        self._bf_size = int.from_bytes(self._f.read(4), 4)
        self._f.read(4) # Reserved
        self._bf_offset = int.from_bytes(self._f.read(4), 4)

        self._bi_size = int.from_bytes(self._f.read(4), 4)
        self._bi_width = int.from_bytes(self._f.read(4), 4)
        self._bi_height = int.from_bytes(self._f.read(4), 4)
        self._bi_planes = int.from_bytes(self._f.read(2), 2)
        self._bi_bit_count = int.from_bytes(self._f.read(2), 2)
        self._bi_compression = int.from_bytes(self._f.read(4), 4)
        self._bi_size_image = int.from_bytes(self._f.read(4), 4)
        self._bi_x_pels_per_meter = int.from_bytes(self._f.read(4), 4)
        self._bi_y_pels_per_meter = int.from_bytes(self._f.read(4), 4)
        self._bi_clr_used = int.from_bytes(self._f.read(4), 4)
        self._bi_clr_important = int.from_bytes(self._f.read(4), 4)

        # Move to beginning of data by jumping over remaining header
        remainder = 54 - self._bf_offset
        if remainder > 0:
            self._f.read(remainder)

        self._bpp = bpp

    def w(self):
        return self._bi_width

    def h(self):
        return self._bi_height

    def get_pixel_color(self):
        if self._f is None:
            return 0xff0000

        if self._bpp == 24:
            r = self._f.read(1)
            g = self._f.read(1)
            b = self._f.read(1)
            return int.from_bytes(r+g+b, 3)
        else:
            return 0x000000

    def close(self):
        if self._f is not None:
            self._f.close()
            self._f = None
