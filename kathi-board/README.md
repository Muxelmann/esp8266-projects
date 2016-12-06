# Kathi Board

## Details

This is a *surprise* present that uses the [ST7735 screen for ESP8266](https://github.com/Muxelmann/esp8266-projects/tree/master/st7735-tft) to:

1. Display graphics and text on the screen
2. Connects to one access point
3. Regularly downloads either:
	- Random images
	- Status updates
	- Recent images
4. Checks and installs (unfrozen) module updates

## Content

This folder contains both the `source`, `pcb` and `php` directories. These contain, respectively, the ES8266's source code, the EAGLE files to build the board, and the PHP webserver code.

## Functionality

The board code is a finite state machine that (once fully implemented) follows the following decision logic:

1. Start config webserver
2. Try connecting to a wifi from a `wifi.txt` list
3. If connected:
  1. Check for update -> update or continue
  2. Check for status -> display or continue
  3. Check for image -> display and wait
4. If not connected
  1. Display Wifi name
  2. Display personalised image

