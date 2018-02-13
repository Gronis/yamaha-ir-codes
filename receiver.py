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

DEFAULT_MQTT_BROKER_HOST = "192.168.1.101"
DEFAULT_MQTT_BROKER_PORT = 1883
HOSTNAME = socket.gethostname()
COMMAND = "irsend"
#DEFAULT_ROOT_TOPIC = "/raw/esp8266/blinds_7622132"
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


    if args.send is not None:
        publish.single(write_topic,
                       payload=" ".join(args.send),
                       hostname=mqtt_broker_host,
                       port=mqtt_broker_port)
        exit(0)


    def on_connect(client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        client.subscribe(read_topic)


    def on_disconnect(client, userdata, rc):
        time.sleep(1)
        client.connect(mqtt_broker_host, mqtt_broker_port, 60)


    def on_message(client, userdata, msg):
        irsend(msg.payload)

    def on_publish(client, userdata, mid):
        pass


    client = initialize_connection(mqtt_broker_host, mqtt_broker_port)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish
    client.loop_start()

    was_playing = False
    is_playing = False

    while True:
        was_playing = is_playing
        is_playing = get_is_playing()
        started_playing = not was_playing and is_playing
        stopped_playing = was_playing and not is_playing

        if started_playing:
            set_receiver_input()
            client.publish(write_topic, "playing")
        if stopped_playing:
            client.publish(write_topic, "stopped")


        time.sleep(0.1)


def initialize_connection(host, port):
    is_network_accessable = False
    while not is_network_accessable:
        try:
            client = mqtt.Client()
            client.connect(host, port, 60)
            is_network_accessable = True
            return client
        except OSError as e:
            print(e)
            time.sleep(1)

def irsend(command):
    subproc = subprocess.Popen([COMMAND] +  command.split())
    output = subproc.communicate()[0]
    return output

def get_is_playing():
    status = str(request.urlopen("http://127.0.0.1:3000/api/v1/getstate").read()).find("play")
    is_playing = status is not -1
    return is_playing

def set_receiver_input():
    irsend("SEND_ONCE RECEIVER_2064_MAIN POWER_POWER_ON")
    time.sleep(0.1)
    # Send two just in case (one fast for responce time and the last for reliability)
    irsend("SEND_ONCE RECEIVER_2064_MAIN INPUT_HDMI1")
    time.sleep(0.9)
    irsend("SEND_ONCE RECEIVER_2064_MAIN INPUT_HDMI1")

main()
