## YAMAHA IR codes
NOTE: doc is lacking.

Turn your yamaha receiver to a smart one. This repo provides ir codes for yamaha-receivers as well
as a small python program which uses mqtt to communicate with a mqtt broker.

I'm running this on a raspberry pi with volumio installed, so a few hardcoded things exists in here
that assumes volumio is running (just comment that out). There might be other hardcoded things as
well.

The idea is that you take a raspberry pi, put volumio on it. Download this repo, connect an ir led,
and you can then play music to your yamaha receiver through tcp/ip. The receiver will turn on when
music starts playing and set input to hdmi_1 (hardcoded, easy to change in code). An added plus
is to be able to send mqtt requests to control the receiver.

I recommend to use this with `volspotconnect2` for spotify-connect support and
`volumio-snapcast-plugin` for multiroom speaker support if you need that. I'm also using
`home-assistant` to send mqtt requests to the receiver.

Right now, the states on the `out` topic is `playing|stopped|inactive` where volumio is considered
`inactive` after `2 min` of being `stopped` continusly.

Drop an issue if you want to are having trouble interpreting how to set everything up.


### Usage (ir codes for yamaha)

```
python yamahanec2lirc.py yamaha_rxv.csv RECEIVER ${RECEIVERVERSION} 1 > yamaha_${RECEIVERVERSION}.lircd
```

Example: HTR-2064:
```
python yamahanec2lirc.py yamaha_rxv.csv RECEIVER 2064 1 > yamaha_htr_2064.lircd
```

Import the final lircd like so in `/etc/lirc/lircd.conf`:

```
include "<path/from/root>/yamaha_htr_2064.lircd"
```

## Mqtt client:

This is a MQTT client that can be used to send ir codes to control your yamaha

### Setup (dev)
```
pip install pipenv
pipenv install
pipenv shell
```

Run `pipenv shell` to active virtual env, then run deamon: `receiver.py`

### Setup (rpi)
```
sudo apt-get install python python-pip
pip install pipenv
pipenv install --system
```

### Usage:

```
./receiver.py --help
```

You can use this to see the mqtt topic to use.
Example can be `/raw/receivers/volumio/out` for outgoing signals and `/raw/receivers/volumio/in`
for sending. Everything in the payload is sent as args to irsend.

The following mqtt request will turn off my receiver (modify to match your receiver with your needs):
```
topic:   /raw/receivers/multiroom/in
payload: SEND_ONCE RECEIVER_2064_MAIN POWER_STANDBY
```


### Run automatically on startup:
```
sudo cp receiver /etc.init.d/receiver
sudo update-rc.d receiver defaults
```



### Contributions
Thanks to `nobbin` for his guide <a href="https://nobbin.net/2012/12/08/converting-yamaha-nec-infrared-codes-to-lirc-format/">here</a>, and for providing ir codes for yamaha reveivers. Look at his guide for a complete explaination how to use lirc with yamaha receivers.

I added a few codes for changing between all inputs on a Yamaha HTR-2064 Receiver.