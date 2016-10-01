# ST7735 screen for ESP8266

## Details

### Serial Peripheral Interface (SPI)

The code uses the ESP's hardware SPI to accelerate communication. GPIO pins are connected as follows:

SPI      | function            | GPIO pin   | direction
-------- | ------------------- | ---------- | ---------
**SCK**  | Clock               | 14         | `Pin.OUT`
**MOSI** | Master Out Slave In | 13         | `Pin.OUT`
**MISO** | Master In Slave Out | 12 (*n/c*) | *n/a*

SPI is set to transmit at **20MHz** (despite slower speeds, e.g.16MHz, may be more stable). Polarity and phase are both set to zero.

### Control Lines

Next to SPI, which is used to transfer data, three more control lines are required to interface with the screen:

Name                | function        | required | default
------------------- | --------------- | -------- | -------
**CS**              | Chip Select     | `False`  | **GND**
**A0** or **RS/DC** | Register Select | `True`   | *n/a*
**RES**             | Reset           | `True`   | *n/a*

If only a single SPI device is connected, the the **CS** pin may be pulled low all the time. The register select determines whether SPI transmission is a command or data. Set **A0** or **RS/DC** low for command, and high for data. To reset the chip, pull **RES** low and return back high after a short period (~200ms). A reset pulse needs to be applied prior to screen initialisation.

### Screen Command and Data Transmission

All commands and associated data (if applicable) are summarised in the Appendix. Essentially, the interface works by sending an 8bit command to the screen, followed by the data associated with the command.

For the initialisation (after hardware reset, i.e. pulsing **RST**), three commands are sent (without data):

order | name    | value  | function
----- | ------- | ------ | --------
1.    | SWRESET | `0x01` | Software Reset
2.    | SLPOUT  | `0x11` | Sleep Out & Booster On
3.    | DISPON  | `0x29` | Display On

Sending data with a command is pretty easy, too. When setting the column and row addresses for which pixel data is transmitted, three steps are executed:

1. Select which columns (i.e. `x0` to `x1`) will be affected (CASET : `0x2a`)
2. Select which rows (i.e. `y0`to `y1`) will be affected (RASET : `0x2b`)
3. Write data to RAM (i.e. loads of data...) (RAMWR : `0x2b`)

When more than one byte of data is transmitted after a command byte has been sent, you can simply continue sending data until the entire datastream is transmitted. For the ESP8266, this can be achieved as a software loop (slow) or by sending an array of bytes at a time (fast). It is guestimated, that the ESP's SPI has a 1kB output buffer, and this is filled with *chuncks* of data. Now the screen updates in <1s.

### Color implementation

Color is saved as 18bit resolution (i.e. 262144 colours). Here, red, green, and blue are assigned 6bit each, in that order.

### Appendix

The screen's datasheet can be obtained from [here](http://www.displayfuture.com/Display/datasheet/controller/ST7735.pdf). But the most important instructions, their values and associated data requirements are summarised below:

instruction | function             | value  | data array
----------- | -------------------- | ------ | ----------
SWRESET     | Software Reset       | `0x01` | *n/a*
SLPOUT      | Sleep Out & Boost On | `0x11` | *n/a*
DISPON      | Display On           | `0x29` | *n/a*
CASET       | Column Address Set   | `0x2a` | `[15:8, 7:0]`
RASET       | Row Address Set      | `0x2b` | `[15:8, 7:0]`
RAMWR       | Memory Write         | `0x2e` | `[byte_0, byte_1, ..., byte_N]`


