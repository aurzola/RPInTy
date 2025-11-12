#!/usr/bin/env python3

import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library
import time
import os
import sys
from luma.core.interface.serial import i2c
from luma.oled.device import sh1107
import subprocess, time, shlex, os, signal


from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
 
Direc = './rom/'
roms = os.listdir(Direc)
# Filtering only the games.
roms = [f for f in roms  if '.int' in f]
roms = [sub[: -4] for sub in roms]
roms.sort()
#print(*roms, sep="\n")


def start_emulator(romfile):
    # Stop any running instance cleanly
    subprocess.run(["killall", "-q", "jzintv"])
    time.sleep(0.5)  # give EGL driver time to clean up

    emucmd = [
        "bin/jzintv",
        video,
        "--kbdhackfile=hackfile.txt",
        f"rom/{romfile}"
    ]
    env = os.environ.copy()
    env["SDL_VIDEO_EGL_DRIVER"] = "libEGL.so"
    env["SDL_VIDEO_GL_DRIVER"] = "libGLESv2.so"

    # start without blocking the main script
    subprocess.Popen(emucmd, env=env)

def initDisplay():
  global device, image, font, draw
  serial = i2c(port=1, address=0x3C)
  device = sh1107(serial, rotate=1)
  # Create image buffer.
  # Make sure to create image with mode '1' for 1-bit color.
  image = Image.new(device.mode, device.size)
  font = ImageFont.truetype('SFIntellivised.ttf', 24)
  # Create drawing object.
  draw = ImageDraw.Draw(image)

def updateDisplay():
  global selected, pos, font, draw, device, image
  velocity = -4
  startpos = 1
# Animate text moving 
  pos = startpos
  while True:
    try:
      maxwidth = draw.textlength(roms[selected], font=font)
      # Clear image buffer by drawing a black filled box.
      draw.rectangle((0,0,device.width,device.height), outline=0, fill=0)
      # Enumerate characters and draw them offset horizontally
      x = pos
      for i, c in enumerate(roms[selected]):
        # Stop drawing if off the right side of screen.
        if x > device.width:
            break
        # Calculate width but skip drawing if off the left side of screen.
        if x < -10:
            char_width = draw.textlength(c, font=font)
            x += char_width
            continue
        y = 18  
        # Draw text.
        draw.text((x, y), c, font=font, fill=255)
        # Increment x position based on chacacter width.
        char_width = draw.textlength(c, font=font)
        x += char_width
      # Draw the image buffer.
      device.display(image)
      # Move position for next frame.
      pos += velocity
      # Start over if text has scrolled completely off left side of screen.
      if pos < -maxwidth or maxwidth <= device.width :
        pos = startpos
      # Pause briefly before drawing next frame.
      time.sleep(0.5)
    except:
      print("cart off")
      time.sleep(0.5)


def button_callback(channel):
    global selected, pos, video, videoInitialized
    #Debounce
    time.sleep(0.01)
    if channel == 21:
       time.sleep(5)
       if GPIO.input(channel):
         initDisplay() 
         pos=-999
         return
    if not GPIO.input(channel):
       return
    print("channel on " + str(channel))
    if channel == 15:
        selected = selected + 1
        if selected == len(roms) :
           selected = 0
        print(roms[selected])
        pos=-999
    if channel == 23:
        selected = selected - 1
        if selected < 0:
           selected = len(roms)-1
        print(roms[selected])
        pos=-999
    if channel == 18 or channel == 24:
       start_emulator(roms[selected])

pos=1
video = os.popen('tvservice -s').read()
if video.find("HDMI") > -1: 
   video="-z3" #z4 looks good on big tv
   os.system("sudo raspi-config nonint do_audio 1")
else:
   video="-z1"
   os.system("sudo raspi-config nonint do_audio 0")

# 128x32 device with hardware I2C:
serial = i2c(port=1, address=0x3C)
device = sh1107(serial, rotate=1)
draw = 1
GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
GPIO.add_event_detect(21,GPIO.BOTH,callback=button_callback) 

if GPIO.input(21):
  initDisplay()
#initDisplay()
selected = 0
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
GPIO.add_event_detect(15,GPIO.RISING,callback=button_callback) # Setup event on pin rising edge
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
GPIO.add_event_detect(18,GPIO.RISING,callback=button_callback) 
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
GPIO.add_event_detect(23,GPIO.RISING,callback=button_callback) 
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
GPIO.add_event_detect(24,GPIO.RISING,callback=button_callback) 

#emucmd = "SDL_VIDEO_EGL_DRIVER=libEGL.so SDL_VIDEO_GL_DRIVER=libGLESv2.so bin/jzintv "
#os.system(emucmd + video + " --kbdhackfile=hackfile.txt 'INTV - Intelligent TV Demo Intl. #5859 (1982) (Mattel).int' & ")
start_emulator('INTV - Intelligent TV Demo Intl. #5859 (1982) (Mattel).int')

updateDisplay()
GPIO.cleanup() 
print("all done")
