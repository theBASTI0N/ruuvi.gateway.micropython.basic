from machine import UART
import machine
from umqtt.robust import MQTTClient
import time
import ujson
import _thread
from binascii import hexlify
from gc import mem_free
import decoder

global DISCONNECTED
DISCONNECTED = 0
global CONNECTING
CONNECTING = 1
global CONNECTED
CONNECTED = 2



global MAC
MAC = str.upper(hexlify(machine.unique_id(),).decode())

TOPIC = "ruuvigw/" + MAC + "/"

def time_stamp(time):
  return "{}-{:0>2d}-{:0>2d}{}{:0>2d}:{:0>2d}:{:0>2d}{}".format(time[0], time[1], time[2], "T", time[3], time[4], time[5], "Z")

def mqttH(config):#HeartBeat client
    state = DISCONNECTED
    global clientH
    if config['username'] != "NA" and config['password'] != "NA":
        clientH = MQTTClient( MAC + "H", config['host'] ,user=config['username'], password=config['password'], port=int(config['port']), keepalive=60, ssl=False)
    else:
        clientH = MQTTClient( MAC + "H", config['host'], port=int(config['port']), keepalive=60, ssl=False)

    while state != CONNECTED:
        try:
            state = CONNECTING
            clientH.connect()
            state = CONNECTED
        except:
            print('Could not establish MQTT-H connection')
            time.sleep(1)
    if state == CONNECTED:
        print('MQTT-H Connected')

def heartbeat(epoch):
    while True:
        try:
            if epoch == 1:
                flT = time.time() + 946684800
            else:
                flT= time_stamp(time.localtime())
            up = time.ticks_ms() / 1000
            mFr= mem_free()
            m = {'ts' : flT,
                'memFree' : mFr,
                'uptime': up,}
            msgJson = ujson.dumps(m)
            clientH.publish( topic=TOPIC + "heartbeat", msg =msgJson )
            time.sleep(10)
        except:
            print("Unknown error. Performing restart")
            machine.reset()

def mqttB(config):#HeartBeat client
    state = DISCONNECTED
    global clientB
    if config['username'] != "NA" and config['password'] != "NA":
        clientB = MQTTClient( MAC, config['host'] ,user=config['username'], password=config['password'], port=int(config['port']), keepalive=60, ssl=False)
    else:
        clientB = MQTTClient( MAC, config['host'] ,port=int(config['port']), keepalive=60, ssl=False)
    while state != CONNECTED:
        try:
            state = CONNECTING
            clientB.connect()
            state = CONNECTED
        except:
            print('Could not establish MQTT-B connection')
            time.sleep(1)
    if state == CONNECTED:
        print('MQTT-B Connected')    

def uart(epoch, decode):
    uart = UART(2, 115200)
    uart.init(115200, bits=8, parity=0, stop=1, tx=4, rx=5)
    while True:
        pkt = uart.readline()
        if (pkt != None):
            pkt = str(pkt)
            pkt = pkt.upper()
            pkt = pkt[2:-4]
            pkt = pkt.split(",")

            try:
                if len(pkt[0]) == 12 and len(pkt[1]) > 6 and len(pkt[2]) >-3 and int(pkt[2]) <= 0:
                    if epoch:
                       flT = time.time() + 946684800
                    else:
                       flT= time_stamp(time.localtime())
                    m = {'ts' : flT,
                        'mac' : pkt[0],
                        'data': pkt[1],
                        'rssi': int(pkt[2])}
                    if decode:
                        d = decoder.decode(pkt[1])
                        m.update(d)
                    msgJson = ujson.dumps(m)
                    clientB.publish( topic=TOPIC + "ble" + pkt[0], msg =msgJson )
                else:
                    # Malformed UART data
                    pass
            except:
                pass


def start(config):
    epoch = 0
    if int(config['epoch']) == 1:
        epoch = 1
    mqttH(config)
    _thread.start_new_thread(heartbeat, (epoch,)) #Start HeartBeat loop

    mqttB(config)
    uart(epoch, config['dble'])