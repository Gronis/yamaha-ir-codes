#!/usr/bin/env python

import socket
import time
import os.path
import argparse
import subprocess

import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
try:
    import urllib.request as request
except:
    import urllib2 as request
# The callback for when the client receives a CONNACK response from the server.

DEFAULT_MQTT_BROKER_HOST = "192.168.1.102"
DEFAULT_MQTT_BROKER_PORT = 1883
HOSTNAME = socket.gethostname()
COMMAND = "irsend"
TIME_TO_INACTIVE = 120.0 # sec
DELTA_TIME_PLAYING_STATUS = 0.1
DEFAULT_ROOT_TOPIC = "/raw/receivers/" + HOSTNAME

parser = argparse.ArgumentParser(description='MQTT service for sending ir signals it irsend')
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


    def on_connect(client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        print("MQTT Topic: {}, Connected to {}".format(root_topic, mqtt_broker_host))
        client.subscribe(read_topic)


    def on_disconnect(client, userdata, rc):
        connect(client, mqtt_broker_host, mqtt_broker_port)

    def on_message(client, userdata, msg):
        print(msg.payload)
        irsend(msg.payload)

    def on_publish(client, userdata, mid):
        pass

    client =  mqtt.Client()
    connect(client, mqtt_broker_host, mqtt_broker_port)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish
    client.loop_forever()

# Connects the client. If fails due to host being down or localhost network is down, retry
def connect(client, host, port):
    reconnected = False
    while not reconnected:
        try:
            client.connect(host, port, 60)
            reconnected = True
        except:
            print("Unable to connect, trying again...")
        time.sleep(1)

def irsend(command):
    subproc = subprocess.Popen([COMMAND] +  command.split())
    output = subproc.communicate()[0]
    return output

main()
