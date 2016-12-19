import socket
import os
from machine import Pin


def flicker():
    Pin(2).value(not Pin(2).value())

def http_get(url):
    f = open('tmp', 'wb')
    _, _, host, path = url.split('/', 3)
    addr = socket.getaddrinfo(host, 80)[0][-1]
    s = socket.socket()
    s.connect(addr)
    s.send(bytes('GET /%s HTTP/1.1\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
    while True:
        data = s.recv(512)
        flicker()
        print(len(data))
        if data:
            f.write(data)
        else:
            break
    f.close()

def convert():
    f_in = open('tmp', 'rb')
    bmp_start = False
    while not bmp_start:
        data = f_in.read(1)
        if data == b'\r':
            data = f_in.read(3)
            if data == b'\n\r\n':
                bmp_start = True
    if bmp_start:
        f_out = open('image.bmp', 'wb')
        data = f_in.read(1024)
        while data and len(data) > 0:
            f_out.write(data)
            data = f_in.read(1024)
            print(len(data))
            flicker()
        f_out.close()
    f_in.close()
    return bmp_start

def display_image(display):
    import bitmap
    http_get('http://api.gerfficient.com/img/esp_image')
    if convert():
        Pin(2).low()
        display.draw_bitmap(bitmap.Bitmap('image.bmp'))
        os.remove('tmp')
        Pin(2).high()
