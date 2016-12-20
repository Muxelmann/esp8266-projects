import socket


_run_server = True
_wifi_data_file = 'wifi.txt'
_post_pages = ['/add_wifi.html', '/delete_wifi.html', '/esp_instruction.html']
_html_head = "HTTP/1.0 %s\r\nConnection: close\r\nContent-Type: %s; charset=UTF-8\r\n\r\n"
_web_files, _s, _cl = None, None, None


def start(web_files='.', wifi_data_file='wifi.txt'):
    global _run_server, _s, _cl, _web_files, _wifi_data_file

    _web_files = web_files
    _wifi_data_file = wifi_data_file
    if not _s:
        _s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]
        _s.bind(addr)
        _s.listen(1)
        print('listening on %s:%d' % (addr[0], 8080))

    while _run_server:
        if _cl is None:
            print('Waiting...')
            _cl, addr = _s.accept()
            print('... connection ' + str(addr[0]) + ':' + str(addr[1]))
        else:
            print('ERR: A connection was held open...')
            _run_server = False
            continue

        request, resource, options = _read_header(_cl)

        if request == 'GET':
            _get(_cl, resource, options)
        elif request == 'POST':
            _post(_cl, resource, options)
        else:
            _get(_cl, None, None)

        _cl.close()
        _cl = None
        print('closing')

    _s.close()
    _s = None
    print('terminated -> restarting')
    quit()


#### HELPER FUNCTIONS ####


def _read_header(cl):
    global _web_files, _post_pages
    cl_file = cl.makefile('rb', 0)
    content_length = 0
    connection_persist = 'False'
    line = cl_file.readline()

    request, resource, _ = line.decode('utf-8').split(' ')
    if resource == '/':
        resource = '/index.html'
    import os
    if resource[1:] not in os.listdir(_web_files):
        if request != 'POST' or resource not in _post_pages:
            resource = None

    options = {'data' : _get_essid_list}
    while True:
        line = cl_file.readline()
        if b'Content-Length: ' in line:
            options['content_length'] = int(line.decode('utf-8').split(' ')[1])
        elif b'Connection: ' in line:
            options['connection_persist'] = 'keep-alive' in line.decode('utf-8').split(' ')[1]
        elif not line or line == b'\r\n':
            break

    cl_file.close()

    return request, resource, options


def _send(cl, msg, delay=100):
    if cl is None:
        print('ERR: Connection no longer available')
        return
    cl.send(msg)
    # time.sleep_ms(delay)


def _decode_url(text):
    i = 0
    text = text.replace('+', ' ')
    while i < len(text):
        if text[i] == '%':
            decoded = str(chr(int(text[i+1:i+3], 16)))
            text = text[:i] + decoded + text[i+3:]
        i += 1
    return text

#### GET FUNCTIONS ####


def _get(cl, resource, options):
    global _html_head, _web_files
    print('----- GET -----')

    if resource is None:
        _send(cl, _html_head % ('404 Not Found', '*/*'))
        _send(cl, '<html><body><h1>404 Not Found</h1></body><html>')
        return
    _send(cl, _html_head % ('200 OK', 'text/html'))

    f = open(_web_files + resource)
    while True:
        line = f.readline()
        if not line:
            break
        elif b'<!-- ##DATA## -->' in line:
            options['data'](cl)
        elif b'<!-- ##HEAD## -->' in line:
            if 'redirect_page' in options.keys():
                _send(cl, '<meta http-equiv="refresh" content="5; url=' + options['redirect_page'] + '" />')
        else:
            _send(cl, line.decode('utf-8'))
    f.close()


def _get_essid_list(cl):
    global _wifi_data_file
    import os
    essids = []
    if _wifi_data_file in os.listdir('.'):
        f = open(_wifi_data_file, 'r')
        while True:
            line = f.readline()
            if not line:
                break
            essids.append(line.split(',')[0])
        f.close()

    _send(cl, '<ol>\r\n')
    for essid in essids:
        _send(cl, '<li><input type="button" value="delete" onclick="delete_wlan(\'' + essid + '\')"> ' + essid + '</li>\r\n')
    _send(cl, '</ol>\r\n')


def _get_ack_message(cl):
    _send(cl, '<span style="color: red; font-size: 18px;">Update received!</span>')


#### POST FUNCTIOSN ####


def _post(cl, resource, options):
    print('----- POST -----')
    if 'content_length' not in options.keys():
        resource = None

    if resource == '/add_wifi.html':
        print('adding!')
        _post_add_wifi(cl, options['content_length'])
        options['redirect_page'] = '/index.html'
        options['data'] = _get_ack_message
        _get(cl, '/index.html', options)
    elif resource == '/delete_wifi.html':
        print('deleting!')
        _post_delete_wifi(cl, options['content_length'])
        options['redirect_page'] = '/index.html'
        options['data'] = _get_ack_message
        _get(cl, '/index.html', options)
    elif resource == '/esp_instruction.html':
        print('instruction!')
        _post_instruction(cl, options['content_length'])
        options['redirect_page'] = '/index.html'
        options['data'] = _get_ack_message
        _get(cl, '/index.html', options)
    else:
        _get(cl, None, options)


def _post_add_wifi(cl, content_length):
    global _wifi_data_file
    cl_file = cl.makefile('rb')
    pairs = cl_file.read(content_length).decode('utf-8').split('&')
    cl_file.close()

    wifi, password = None, None
    for pair in pairs:
        name, value = pair.split('=')
        if name == 'wifi':
            wifi = _decode_url(value)
        elif name == 'password':
            password = _decode_url(value)

    if wifi is None or password is None or ',' in wifi or ',' in password:
        print('bad input to add')
        return

    import os
    if _wifi_data_file not in os.listdir('.'):
        f = open(_wifi_data_file, 'w')
        f.close()
    f_in = open(_wifi_data_file, 'r')
    f_out = open('wifi.tmp', 'w')

    replaced = False
    while True:
        line = f_in.readline()
        if not line:
            break
        if wifi == line.split(',')[0]:
            f_out.write(wifi + ',' + password + '\r\n')
            replaced = True
        else:
            f_out.write(line)

    if not replaced:
        f_out.write(wifi + ',' + password + '\r\n')
    f_in.close()
    f_out.close()
    os.rename('wifi.tmp', _wifi_data_file)


def _post_delete_wifi(cl, content_length):
    global _wifi_data_file
    cl_file = cl.makefile('rb')
    pairs = cl_file.read(content_length).decode('utf-8').split('&')
    cl_file.close()

    wifi = None
    for pair in pairs:
        name, value = pair.split('=')
        if name == 'wifi':
            wifi = _decode_url(value)

    import os
    if _wifi_data_file not in os.listdir('.') or wifi is None:
        print('bad input to delete')
        return

    f_in = open(_wifi_data_file, 'r')
    f_out = open('wifi.tmp', 'w')

    while True:
        line = f_in.readline()
        if not line:
            break
        essid, _ = line.split(',')
        if wifi != essid:
            f_out.write(line)

    f_in.close()
    f_out.close()
    os.rename('wifi.tmp', _wifi_data_file)


def _post_instruction(cl, content_length):
    cl_file = cl.makefile('rb')
    pairs = cl_file.read(content_length).decode('utf-8').split('&')
    cl_file.close()

    instruction = None
    data = []
    for pair in pairs:
        name, value = pair.split('=')
        if name == 'instruction':
            instruction = _decode_url(value)
        else:
            data.append(_decode_url(value))

    if instruction is None:
        print('bad instuction received')
        return

    if instruction == 'restart':
        global _run_server
        _run_server = False
    elif instruction == 'print':
        print(data[0])
