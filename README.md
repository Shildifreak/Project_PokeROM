# Software Info:
 - only MBC 1 and MBC 3 are implemented
 - RAM access is not completely implemented

# Hardware Info:

 - Beaglebone Black
 - bone-debian-10.3-iot-armhf-2020-04-06-4gb.img
 - disabled HDMI and eMMC in /boot/uEnv.txt to have enough GPIO Pins
 - cleared eMMC to always automatically boot from SD card
 - TXS0108E 8 Channel Logic Level Converter for data lines (Cartridge is 5V logic!)

# Results
The python library for GPIO is extremely slow, it took 1-2 hours to read a Cartridge once, this could easily be speed up by at least a factor of 1000 by memory mapping the device files.

Reading Pokemon Blue (Jap) worked flawless.

Reading Pokemon Pikachu Edition (Jap) had a lot of random errors that I didn't figure out how to fix.  
I ended up reading multiple times and comparing results.  

It may have been a power supply problem since I used USB Power only.  
Also additional level shifters for the Address lines etc. may improve stability.

# Resources
<https://problemkaputt.de/pandocs.htm#thecartridgeheader>  
(gone as of 2021-01-25, I really hope it will be reuploaded by someone, since it was one of the best resources out there)  

<https://b13rg.github.io/Gameboy-Bank-Switching/>  

<https://dhole.github.io/post/gameboy_cartridge_emu_1/>