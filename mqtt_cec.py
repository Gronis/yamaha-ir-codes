#!/usr/bin/env python3

import socket
import time
import os.path
import argparse
import subprocess
import threading

import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import cec

DEFAULT_MQTT_BROKER_HOST = "192.168.1.102"
DEFAULT_MQTT_BROKER_PORT = 1883
HOSTNAME = socket.gethostname()
DEFAULT_ROOT_TOPIC = "/raw/hdmi-cec/" + HOSTNAME

parser = argparse.ArgumentParser(description='MQTT service for sending hdmi-cec signals to connected hdmi devices')
parser.add_argument('--host', '-H', type=str, nargs=1, default=DEFAULT_MQTT_BROKER_HOST,
                    help='The host for the mqtt broker, default {0}'.format(DEFAULT_MQTT_BROKER_HOST))
parser.add_argument('--port', '-p', type=int, nargs=1, default=DEFAULT_MQTT_BROKER_PORT,
                    help='The port for the mqtt broker, default {0}'.format(DEFAULT_MQTT_BROKER_PORT))
parser.add_argument('--topic', '-t', type=str, nargs=1, default=DEFAULT_ROOT_TOPIC,
                    help='The topic to use, default {0}'.format(DEFAULT_ROOT_TOPIC))
parser.add_argument('--send', '-s', type=str, nargs=1, default=None,
                    help='Only send this payload and exit')

def main():
    args = parser.parse_args()
    mqtt_broker_host = args.host
    mqtt_broker_port = args.port
    root_topic = args.topic
    read_topic = os.path.join(root_topic, "in")
    write_topic = os.path.join(root_topic, "out")
    inactive_timesteps = 0

    if args.send is not None:
        publish.single(write_topic,
                       payload=" ".join(args.send),
                       hostname=mqtt_broker_host,
                       port=mqtt_broker_port)
        exit(0)

    log_level = cec.CEC_LOG_TRAFFIC
    mqtt_client = mqtt.Client()
    cec_client = CecClient()

    def on_mqtt_connect(client, userdata, flags, rc):
        if rc is 0:
            print("Connected to MQTT broker")
            print("MQTT Topic: {}, Connected to {}".format(root_topic, mqtt_broker_host))
            client.subscribe(read_topic)

    def on_mqtt_disconnect(client, userdata, rc):
        mqtt_connect(client, mqtt_broker_host, mqtt_broker_port)

    def on_mqtt_message(client, userdata, msg):
        try:
            cmd = str(msg.payload.decode("utf-8"))
            if len(cmd.split()) >= 1:
                print("received {} from mqtt broker".format(cmd))
                action, *args = cmd.split()
                {
                    "on": cec_client.power_on,
                    "standby": cec_client.standby,
                    "tx": cec_client.send_command,
                }[action](*args)
            else:
                print("unknown command {} received from mqtt broker".format(cmd))        
        except Exception as e:
            print(e)

    def on_mqtt_publish(client, userdata, mid):
        pass

    def setup_mqtt_client(client):
        mqtt_connect(client, mqtt_broker_host, mqtt_broker_port)
        client.on_connect = on_mqtt_connect
        client.on_message = on_mqtt_message
        client.on_disconnect = on_mqtt_disconnect
        client.on_publish = on_mqtt_publish

    def on_cec_log(level, time, message):
        if level > log_level:
            return 0

        if level == cec.CEC_LOG_ERROR:
            levelstr = "ERROR:   "
        elif level == cec.CEC_LOG_WARNING:
            levelstr = "WARNING: "
        elif level == cec.CEC_LOG_NOTICE:
            levelstr = "NOTICE:  "
        elif level == cec.CEC_LOG_TRAFFIC:
            levelstr = "TRAFFIC: "
        elif level == cec.CEC_LOG_DEBUG:
            levelstr = "DEBUG:   "

        print(levelstr + "[" + str(time) + "]     " + message)
        return 0

    def on_cec_command(cmd):
        cmd = cmd.replace(">> ", "")
        mqtt_client.publish(write_topic, cmd)
        print("[Sending CEC message through mqtt] " + cmd)
        return 0

    def setup_cec_client(client):
        client.on_log = on_cec_log
        client.on_command = on_cec_command
        client.connect()

    setup_cec_client(cec_client)
    setup_mqtt_client(mqtt_client)

    # Lock main thread
    mqtt_client.loop_forever()

# Connects the client. If fails due to host being down or localhost network is down, retry
def mqtt_connect(client, host, port):
    reconnected = False
    while not reconnected:
        try:
            client.connect(host, port, 60)
            reconnected = True
        except:
            print("Unable to connect, trying again...")
        time.sleep(1)

class CecClient:
    def __init__(self):
        pass

    def on_log(self, level, time, message):
        pass

    def on_command(self, cmd):
        pass

    def connect(self):
        self.cecconfig = cec.libcec_configuration()
        self.cecconfig.strDeviceName = "mqtt_cec"
        self.cecconfig.bActivateSource = 0
        self.cecconfig.deviceTypes.Add(cec.CEC_DEVICE_TYPE_RECORDING_DEVICE)
        self.cecconfig.clientVersion = cec.LIBCEC_VERSION_CURRENT

        def log_callback(level, time, message):
            try:
                return self.on_log(level, time, message)
            except Exception as e:
                print(e)

        def command_callback(cmd):
            try:
                return self.on_command(cmd)
            except Exception as e:
                print(e)

        self.cecconfig.SetLogCallback(log_callback)
        self.cecconfig.SetCommandCallback(command_callback)

        self.lib = cec.ICECAdapter.Create(self.cecconfig)
        self.log_level = cec.CEC_LOG_TRAFFIC
        print("libCEC version " + self.lib.VersionToString(self.cecconfig.serverVersion) + " loaded: " + self.lib.GetLibInfo())
        adapter = self.detect_adapter()
        if adapter == None:
            print("No adapters found")
        else:
            if self.lib.Open(adapter):
                print("HDMI-CEC connection opened")
                return True
            else:
                print("failed to open a connection to the CEC adapter")
                return False

    def detect_adapter(self):
        res = None
        adapters = self.lib.DetectAdapters()
        for adapter in adapters:
            print("found a CEC adapter:")
            print("port:     " + adapter.strComName)
            print("vendor:   " + hex(adapter.iVendorId))
            print("product:  " + hex(adapter.iProductId))
            res = adapter.strComName
        return res

    def standby(self, device):
        device = device if device is not "f" else cec.CECDEVICE_BROADCAST
        self.lib.StandbyDevices(int(device))

    def power_on(self, device):
        device = device if device is not "f" else cec.CECDEVICE_BROADCAST
        self.lib.PowerOnDevices(int(device))

    def send_command(self, data, retries=0):
        retries = int(retries)
        cmd = self.lib.CommandFromString(data)
        print("transmit " + data)
        if not self.lib.Transmit(cmd) and retries > 0:
            print("failed to transmit " + data + ", retrying...")
            #time.sleep(0.2)
            thread = threading.Timer(0.2, lambda: self.send_command(data, retries - 1))
            thread.start()
            #self.send_command(data, retries - 1)
        else:
            print("success")

main()
