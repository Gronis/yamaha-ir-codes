## YAMAHA IR codes

### Usage

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

### Contributions
Thanks to `nobbin` for his guide <a href="https://nobbin.net/2012/12/08/converting-yamaha-nec-infrared-codes-to-lirc-format/">here</a>, and for providing ir codes for yamaha reveivers. Look at his guide for a complete explaination how to use lirc with yamaha receivers.

I added a few codes for changing between all inputs on a Yamaha HTR-2064 Receiver.