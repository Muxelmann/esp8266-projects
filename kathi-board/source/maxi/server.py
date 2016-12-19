import socket, time
from machine import Pin


html_head = "HTTP/1.0 %s\r\nConnection: close\r\nContent-Type: %s; charset=UTF-8\r\n\r\n"

run_server = True
s = None

cl = None

def start_server():
    global html_head, run_server, s, cl

    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    if not s:
        s = socket.socket()
        s.bind(addr)
        s.listen(1)

    print('listening on', addr)

    while run_server:
        if cl is None:
            cl, addr = s.accept()
            print('client connected from', addr)
        else:
            run_server = False
            print('ERR: A connection was held open...')
            cl = None
            continue

        cl_file = cl.makefile('rb', 0)
        line = cl_file.readline()
        if line:
            http_action, http_file = line.decode('utf-8').split(' ')[0:2]
            print(line)

            if http_action == 'GET':
                _get_reply(http_file, cl_file)
            elif http_action == 'POST':
                _post_reply(http_file, cl_file)

        cl.close()
        cl = None
        print('closing')


def _send(msg, delay=100):
    global cl
    if cl is None:
        print('ERR: Connection no longer available')
        return
    cl.send(msg)
    time.sleep_ms(delay)
    # print('-->' + msg)


def _get_reply(http_file, cl_file):
    global html_head

    # Only allow index GETs
    if http_file not in ['/', '/index', '/index.html']:
        print(http_file + ' not found')
        _send(html_head % ('400 Not Found', '*/*'))
        return

    while True:
        line = cl_file.readline()
        print(line)
        if not line or line == b'\r\n':
            break

    _send(html_head % ('200 OK', 'text/html'))
    f = open('index.html', 'r')
    while True:
        line = f.readline()
        if not line:
            break
        if '<!-- ##DATA## -->' in line:
            _send_essid_list()
        elif '<!-- ##FAVICON## -->' in line:
            continue
        else:
            _send(line)
    f.close()


def _post_reply(http_file, cl_file):
    global html_head, run_server

    # Only allow add and delete wifi POSTs
    if http_file not in ['/add_wifi', '/delete_wifi']:
        print(http_file + ' not found')
        _send(html_head % ('400 Not Found', '*/*'))
        return

    content_length = 0
    while True:
        line = cl_file.readline()
        print(line)
        if b'Content-Length: ' in line:
            content_length = int(line.decode('utf-8').split(' ')[1])
        if not line or line == b'\r\n':
            break

    line = cl_file.read(content_length)
    print(line)

    essid = None
    password = None
    data = line.decode('utf-8').split('&')
    for pairs in data:
        name, value = pairs.split('=')
        print(name + ' -> ' + value)
        if name == 'wifi':
            essid = value.replace('+', ' ')
        elif name == 'password':
            password = value.replace('+', ' ')

    if '/add_wifi' == http_file:
        reply = _add_wifi(essid, password)
    elif '/delete_wifi' == http_file:
        reply = _delete_wifi(essid)

    _send(html_head % ('200 OK', 'text/html'))
    _send('<html><head></head><body><h1>OK</h1></body></html>')


def _send_essid_list():
    _send('<h2>Saved Wifis:</h2><ol>')
    from maxi import hotspot
    essids, _ = hotspot.get_list()
    for essid in essids:
        _send('<li><input type="button" value="delete" onclick="delete_wlan(\'' + essid + '\')"> ' + essid + '</li>')
    _send('</ol>')


def _add_wifi(essid, password):
    if not essid or not password:
        return '<b>Incomplete information...</b>'

    from maxi import hotspot
    essids, _ = hotspot.get_list()
    if essid not in essids:
        print('Adding new ESSID and PW')
        f = open('wifi.txt', 'a')
        f.write(essid + ',' + password + '\n')
        f.close()
    else:
        print('Updating ESSID with new PW')
        f_in = open('wifi.txt', 'r')
        f_out = open('wifi.tmp', 'w')

        while True:
            line = f_in.readline()
            if not essid == line.split(',')[0]:
                f_out.write(line)
            if not line:
                break
        f_out.write(essid + ',' + password + '\n')
        f_in.close()
        f_out.close()

        import os
        os.rename('wifi.tmp', 'wifi.txt')
    return '<b>New Wifi added!</b>'


def _delete_wifi(essid):
    if not essid:
        return '<b>Wifi was not deleted!</b>'

    f_in = open('wifi.txt', 'r')
    f_out = open('wifi.tmp', 'w')

    while True:
        line = f_in.readline()
        if not essid == line.split(',')[0]:
            f_out.write(line)
        if not line:
            break
    f_in.close()
    f_out.close()

    import os
    os.rename('wifi.tmp', 'wifi.txt')
    return '<b>Wifi ' + essid + ' removed!</b>'
