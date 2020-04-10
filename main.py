import wifimgr
import gwmgr
from time import localtime, sleep, time
from ntptime import settime
from machine import Pin

wlan = wifimgr.get_connection()
if wlan is None:
    print("Could not initialize the network connection.")
    while True:
        pass

def time_stamp(time):
  return "{}-{:0>2d}-{:0>2d}{}{:0>2d}:{:0>2d}:{:0>2d}{}".format(time[0], time[1], time[2], "T", time[3], time[4], time[5], "Z")

def handleButtonPress(pin):
  global start
  start = time()
  print(time)

def handleButtonRelease(pin):
  global stop
  stop = time()
  print(time)

button = Pin(2, Pin.IN, Pin.PULL_UP)

button.irq(trigger=Pin.IRQ_RISING, handler=handleButtonPress)
button.irq(trigger=Pin.IRQ_FALLING, handler=handleButtonRelease)

setup = {}
setup = gwmgr.get_setup()
print("Ruuvi GW Configured")

settime()
print("Time Set to: " + time_stamp(localtime()))

if int(setup['mode']) == 0:
  import gwhttp
  gwhttp.start(setup)
else:
  import gwmqtt
  gwmqtt.start(setup)
