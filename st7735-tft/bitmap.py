import gc


class Bitmap(object):

    _f = None

    _bpp = None
    _width = 0
    _height = 0

    _image_size = 0
    _image_pointer = 0

    def __init__(self, path):
        self._f = open(path, 'rb')

        d = self._f.read(2)
        if d != b'BM':
            self.close()
            return

        self._bf_size = int.from_bytes(self._f.read(4), 4)
        self._f.read(4) # Reserved
        header_size = int.from_bytes(self._f.read(4), 4)

        self._bi_size = int.from_bytes(self._f.read(4), 4)
        self._width = int.from_bytes(self._f.read(4), 4)
        self._height = int.from_bytes(self._f.read(4), 4)
        self._f.read(2) # Jump 2 bytes
        self._bpp = int.from_bytes(self._f.read(2), 2)
        self._f.read(4) # Jump 4 bytes
        self._image_size = int.from_bytes(self._f.read(4), 4)
        self._f.read(16) # Jump 16 bytes

        # Move to beginning of data by jumping over remaining header
        remainder = 54 - header_size
        if remainder > 0:
            self._f.read(remainder)

    def w(self):
        return self._width

    def h(self):
        return self._height

    def get_pixel_arrays(self, pixel_count=64):
        if self._f is None or self._image_pointer>=self._image_size-2:
            return None
        # Determine how many bytes can be extracted at once for a chunk of data
        byte_count = pixel_count*3
        byte_left = self._image_size-self._image_pointer-2

        if byte_count < byte_left:
            byte_data = self._f.read(byte_count)
            self._image_pointer += byte_count
        else:
            byte_data = self._f.read(byte_left)
            self._image_pointer += byte_left

        byte_data = [c for c in byte_data]
        for i in range(0, len(byte_data), 3):
            temp = byte_data[i+2]
            byte_data[i+2] = byte_data[i]
            byte_data[i] = temp
        return byte_data

    def close(self):
        if self._f is not None:
            self._f.close()
            self._f = None
            gc.collect()
