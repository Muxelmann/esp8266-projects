import machine
import network


def main():
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
    main()
    from maxi import hotspot, st7735
    from maxi.font import terminalfont as font
