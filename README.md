# ruuvi.gateway.micropython
Micropython FW for the ESP32 on the Ruuvi Gateway

Working on https://micropython.org/resources/firmware/esp32-idf4-20200328-v1.12-310-g9418611c8.bin

Once downloaded the device can be flashed with esptool.

```bash
pip install esptool
esptool.py --port /dev/ttyUSB0 erase_flash
esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 ~/Downloads/esp32-idf4-20200328-v1.12-310-g9418611c8.bin
```

Once the device has been flashed Pymakr can be used to upload the files to the board.

In vscode in pymakr. In the pymakr global settings page add "Silicon Labs" to "autoconnect_comport_manufacturers" so it will connect.

Open the simple folder of the cloned repo and select upload to save the files onto the device.

The WiFi hot-spot SSID and password is set in wifimgr.py

Once connect navigate to 192.168.4.1 and connect to your WiFi network.

The device will then get connected to your WiFi and receive an IP from your router.

Check your router or the REPL in pymakr and you will see the assigned IP.

Once connected to your network again navigate to that IP in a web browser.

You will be able to configure the device from the web page.

Sample configurations can be found on the samples page by adding /samples to the URL.

# Note
I have not implemented the Ethernet adapter as I do not have the physical hardware yet.
