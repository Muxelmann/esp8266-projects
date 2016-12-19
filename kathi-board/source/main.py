import machine


def setup():
    from machine import freq
    freq(160000000)

    import webrepl
    webrepl.start()


    # from maxi import hotspot
    # # Try connecting to one of the the networks in wifi.txt
    # hotspot.join_home_net

    # if isconnected:
    #     from maxi import updates
    #     # Check for updates if a connection was established
    #     from maxi import app
    #     # Run the main app
    # else:
    #     from maxi import defaults
    #     # Display a disconnectivity message and run default Display


if __name__ == '__main__':
    setup()
    # Import all libraries
    from maxi import hotspot, st7735, web, bitmap
    from maxi.font import terminalfont as font

    st7735.init()
    if hotspot.join_net_on_list():
        st7735.text(1, 1, 'I am connected', font)

        # # Downloading an image
        # st7735.text(1, 1, '\nDownloading...', font)
        # web.http_get('http://api.gerfficient.com/esp/get_image')
        # st7735.text(1, 1, '\n\nSplitting...', font)
        # web.http_resp_split()
        #
        # st7735.text(1, 1, '\n\n\nLoading BMP...', font)
        # bitmap.load_bitmap('resp_body')
        #
        # st7735.prep_rect(bitmap.w(), bitmap.h())
        # while st7735.fill_rect(bitmap.get_pixel_arrays()):
        #     continue
        #
        # bitmap.close()
        print('I am connected and will start server')


        import network
        sta_if = network.WLAN(network.STA_IF)
        ip, _, _, _ = sta_if.ifconfig()

        st7735.clear(0xffffff)
        st7735.text(1, 1, 'Starting server\nIP: ' + ip, font, 0x000000)

        import server
        server.start_server()

    else:
        print('I need to be connected manually')

        import os
        essid = 'chipOS'
        # password = ''.join([chr(97 + int.from_bytes(os.urandom(1), 'little') % 26) for _ in range(8)])
        password = 'muxelmann'
        ip, _, _, _ = hotspot.open_ap(essid, password)

        print('\nPW: ' + password + '\nSorry, you need to\nconnect manually...')
        st7735.text(1, 1, 'WLAN: ' + essid + '\nPW:   ' + password + '\n\nSorry you need to\nconnect manually.\n\nIP: ' + ip, font)

        import server
        server.start_server()
