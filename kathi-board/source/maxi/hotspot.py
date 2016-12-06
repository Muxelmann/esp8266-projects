from machine import Pin
import network
import time

_attempts = 30

def open_ap(essid, password):
    Pin(2, Pin.OUT).low()
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(True)
    ap_if.config(essid=essid, password=password)
    print('WLAN set up as: "' + essid + '"')
    if ap_if.isconnected():
        Pin(2, Pin.OUT).high()
    else:
        Pin(2, Pin.OUT).low()

def join_home_net(essid, password):
    global _attempts
    Pin(2, Pin.OUT).low()
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)

    if sta_if.active() and sta_if.isconnected():
        sta_if.disconnect()
    if not sta_if.isconnected():
        sta_if.active(True)
        print('Attempting to connect to: "' + str(essid) + '"')
        sta_if.connect(essid, password)
        attempt_count = 0
        while not sta_if.isconnected() and attempt_count < _attempts:
            time.sleep(1)
            attempt_count += 1
            pass
    print('network config: ', sta_if.ifconfig())

    if sta_if.isconnected():
        Pin(2, Pin.OUT).high()
        return True
    else:
        Pin(2, Pin.OUT).low()
        sta_if.active(False)
        return False

def join_net_on_list(wifi_list='wifi.txt'):
    essids = get_wifis()
    wifi_list = get_list()

    for essid in wifi_list.keys():

        if essid not in essids:
            continue

        if join_home_net(essid, wifi_list[essid]):
            print('Did connect to: "' + essid + '"')
            return True
        else:
            print('Connection to ""' + essid + '" failed')
    return False

def get_list(wifi_file='wifi.txt'):
    f = open(wifi_file)
    wifi = f.readline()
    wifi_list = {}
    while len(wifi) > 1:
        (essid, password) = str(wifi[0:-1]).split(',')
        wifi_list[essid] = password
        wifi = f.readline()
    f.close()
    return wifi_list

def get_wifis():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    details = sta_if.scan()
    return [d[0].decode('utf-8') for d in details]
