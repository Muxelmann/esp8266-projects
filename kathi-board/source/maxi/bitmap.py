_f = None

_bpp = None
_width = 0
_height = 0

_image_size = 0
_image_pointer = 0

def load_bitmap(path):
    global _f, _bbp, _width, _height, _image_size, _image_pointer
    _f = open(path, 'rb')

    d = _f.read(2)
    if d != b'BM':
        _f.close()
        return
    _f.read(4) # bfSize
    _f.read(4) # Reserved
    header_size = int.from_bytes(_f.read(4), 'little')
    _f.read(4) # biSize
    _width = int.from_bytes(_f.read(4), 'little')
    _height = int.from_bytes(_f.read(4), 'little')
    _f.read(2) # biPlanes
    _bpp = int.from_bytes(_f.read(2), 'little') # biBitCount
    _f.read(4) # biCompression
    # -2 because EOF
    _image_size = int.from_bytes(_f.read(4), 'little') - 2 # biSizeImage
    _f.read(4) # biXPelsPerMeter
    _f.read(4) # biYPelsPerMeter
    _f.read(4) # biClrUsed
    _f.read(4) # biClrImportant
    # Move to beginning of data by jumping over remaining header
    remainder = 54 - header_size
    if remainder > 0:
        _f.read(remainder)

    _image_pointer = 0

def w():
    global _width
    return _width

def h():
    global _height
    return _height

def get_pixel_arrays(pixel_count=64):
    global _f, _image_pointer, _image_size
    if _f is None or _image_pointer>=_image_size:
        return None
    # Determine how many bytes can be extracted at once for a chunk of data
    byte_count = pixel_count*3
    byte_left = _image_size-_image_pointer

    if byte_count < byte_left:
        byte_data = _f.read(byte_count)
        _image_pointer += byte_count
    else:
        byte_data = _f.read(byte_left)
        _image_pointer += byte_left

    byte_data = [c for c in byte_data]
    for i in range(0, len(byte_data), 3):
        temp = byte_data[i+2]
        byte_data[i+2] = byte_data[i]
        byte_data[i] = temp
    return byte_data

def close():
    global _f
    if _f is not None:
        _f.close()
        _f = None
