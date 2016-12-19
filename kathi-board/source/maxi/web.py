def http_get(url):
    import os, socket
    from machine import Pin

    saved_files = os.listdir()
    if 'tmp' in saved_files:
        os.remove('tmp')
    f = open('tmp', 'wb')

    _, _, host, path = url.split('/', 3)
    addr = socket.getaddrinfo(host, 80)[0][-1]
    s = socket.socket()
    s.connect(addr)
    s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))

    while True:
        data = s.recv(512)
        Pin(2).value(not Pin(2).value())
        # print('W-> ' + str(len(data)))
        if data:
            f.write(data)
        else:
            break
    f.close()
    Pin(2).high()


def http_resp_split(file_name='tmp', delete_file=True):
    import os
    from machine import Pin

    saved_files = os.listdir()
    if file_name in saved_files:
        f = open(file_name, 'rb')
    else:
        return False
    if 'resp_head' in saved_files:
        os.remove('resp_head')
    f_head = open('resp_head', 'wb')
    if 'resp_body' in saved_files:
        os.remove('resp_body')
    f_body = open('resp_body', 'wb')

    body_start = False
    print(' -> Saving response head')
    while not body_start:
        data = f.readline()
        if data == b'\r\n':
            body_start = True
        f_head.write(data)
        Pin(2).value(not Pin(2).value())
        # print('->H ' + str(len(data)) + ' = ' + str(data))

    print(' -> Saving response body')
    if body_start:
        while True:
            data = f.read(1024)
            Pin(2).value(not Pin(2).value())
            # print('->B ' + str(len(data)) + ' = ' + str(data))
            if data:
                f_body.write(data)
            else:
                break

    f.close()
    f_head.close()
    f_body.close()

    if delete_file:
        os.remove(file_name)
    Pin(2).high()
