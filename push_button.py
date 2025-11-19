#!/usr/bin/env python3

import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library
import time
import os
import sys
from luma.core.interface.serial import i2c
from luma.oled.device import sh1107
import subprocess, time, shlex, os, signal
import threading

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

def detect_display_type():
    try:
        # Method 1: Check HDMI attributes
        result = subprocess.run(['vcgencmd', 'get_hdmi_attr', 'name'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return "HDMI"
        
        # Method 2: Check DRM devices
        import os
        if os.path.exists('/sys/class/drm/card0-HDMI-A-1/status'):
            with open('/sys/class/drm/card0-HDMI-A-1/status', 'r') as f:
                if f.read().strip() == 'connected':
                    return "HDMI"
        
        return "COMPOSITE"
        
    except Exception as e:
        print(f"Display detection error: {e}")
        return "COMPOSITE"

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
  global selected, pos, font, draw, device, image, running
  velocity = -4
  startpos = 1
# Animate text moving 
  pos = startpos
  while running:
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
    except Exception as e:
      print(f"cart off: {e}")
      time.sleep(0.5)

class ButtonHandler:
    def __init__(self):
        self.running = True
        self.last_states = {}
        self.button_pins = [15, 18, 21, 23, 24]
        self.thread = None
        
    def start(self):
        # Setup all GPIO pins
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Initialize all button pins
        for pin in self.button_pins:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            self.last_states[pin] = GPIO.input(pin)
        
        # Start polling thread
        self.thread = threading.Thread(target=self._poll_buttons)
        self.thread.daemon = True
        self.thread.start()
        print("✅ Button handler started with polling method")
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        GPIO.cleanup()
        
    def _poll_buttons(self):
        while self.running:
            for pin in self.button_pins:
                current_state = GPIO.input(pin)
                
                # Check for state changes with debouncing
                if current_state != self.last_states[pin]:
                    time.sleep(0.02)  # 20ms debounce
                    current_state = GPIO.input(pin)  # Re-read after debounce
                    
                    if current_state != self.last_states[pin]:
                        self.last_states[pin] = current_state
                        
                        # Only trigger on button press (HIGH state for pull-down)
                        if current_state == GPIO.HIGH:
                            self._handle_button_press(pin)
            
            time.sleep(0.01)  # 10ms polling interval
    
    def _handle_button_press(self, channel):
        global selected, pos, video
        
        print(f"Button pressed on channel {channel}")
        
        if channel == 21:
            # Special handling for pin 21
            time.sleep(5)  # Long press detection
            if GPIO.input(channel):  # Still pressed after 5 seconds
                initDisplay() 
                pos = -999
                return
        
        if channel == 15:
            selected = selected + 1
            if selected == len(roms):
                selected = 0
            print(roms[selected])
            pos = -999
            
        elif channel == 23:
            selected = selected - 1
            if selected < 0:
                selected = len(roms) - 1
            print(roms[selected])
            pos = -999
            
        elif channel == 18 or channel == 24:
            start_emulator(roms[selected])

# Global variables
pos = 1
running = True
selected = 0

# Video detection
video = detect_display_type()
if video == "HDMI": 
   video = "-z3"  # z4 looks good on big tv
   os.system("sudo raspi-config nonint do_audio 1")
else:
   video = "-z1"
   os.system("sudo raspi-config nonint do_audio 0")

# Initialize display and buttons
button_handler = ButtonHandler()
button_handler.start()

# 128x32 device with hardware I2C:
serial = i2c(port=1, address=0x3C)
device = sh1107(serial, rotate=1)
draw = 1

# Initialize display if button 21 is pressed
if GPIO.input(21):
    initDisplay()

# Start initial emulator
start_emulator('INTV - Intelligent TV Demo Intl. #5859 (1982) (Mattel).int')

try:
    # Run display update
    updateDisplay()
except KeyboardInterrupt:
    print("Interrupted by user")
finally:
    # Cleanup
    running = False
    button_handler.stop()
    print("All done")
