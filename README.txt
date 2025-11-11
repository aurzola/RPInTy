============================================================================
 RpInty  -- 
============================================================================


 jzintv homepage:   http://spatula-city.org/~im14u2c/intv


RPI 3 OS Setup
-----------

sudo dd if=2025-05-13-raspios-bookworm-armhf-lite.img of=/dev/sda1 bs=512

SDL 2 with the default Broadcom blobs & the KMS/DRM backend:
-----------------------------------------------------------

Make sure your user is in the input group & relogin:

sudo adduser pi input

Install SDL2 build dependencies:

# install everything Debian uses to build SDL
sudo apt build-dep libsdl2

# needed for the KMSDRM backend:
sudo apt install libdrm-dev libgbm-dev

Grab the latest stable SDL source tarball or tag (release-2.0.10) from Git and extract it somewhere like ~/sdl-src

Run SDL's configure script:

cpp
cd ~/sdl-src
./configure --enable-video-kmsdrm
Here's my configure summary:

SDL2 Configure Summary:
Building Shared Libraries
Building Static Libraries
Enabled modules : atomic audio video render events joystick haptic sensor power filesystem threads timers file loadso cpuinfo assembly
Assembly Math   :
Audio drivers   : disk dummy oss alsa(dynamic) pulse(dynamic) sndio(dynamic)
Video drivers   : dummy rpi x11(dynamic) kmsdrm(dynamic) opengl opengl_es1 opengl_es2 vulkan wayland(dynamic)
X11 libraries   : xcursor xdbe xinerama xinput2 xinput2_multitouch xrandr xscrnsaver xshape xvidmode
Input drivers   : linuxev linuxkd
Using libsamplerate : YES
Using libudev       : YES
Using dbus          : YES
Using ime           : YES
Using ibus          : YES
Using fcitx         : YES

Note the rpi and kmsdrm(dynamic) entries in the Video drivers list:

Video drivers   : dummy rpi x11(dynamic) kmsdrm(dynamic) opengl opengl_es1 opengl_es2 vulkan wayland(dynamic)
                        ^^^              ^^^^^^^^^^^^^^^
Build & install SDL; took ~4.5 minutes on my Rpi3:

make -j4 && sudo make install
Build test program:

g++ main.cpp `pkg-config --cflags --libs sdl2`
(Optional) Enable the "Full KMS" driver if you want to use the KMSDRM backend instead of the default OpenGL ES blobs:

$ sudo raspi-config
select '7 Advanced Options'
select 'A7 GL Driver'
select 'G3 GL (Full KMS)'
reboot

Run test program:

$ ./a.out 
Testing video drivers...
The path /dev/dri/ cannot be opened or is not available
The path /dev/dri/ cannot be opened or is not available
SDL_VIDEODRIVER available: x11 wayland KMSDRM RPI dummy
SDL_VIDEODRIVER usable   : RPI
The path /dev/dri/ cannot be opened or is not available
The path /dev/dri/ cannot be opened or is not available
SDL_VIDEODRIVER selected : RPI
SDL_RENDER_DRIVER available: opengl opengles2 opengles software
SDL_RENDER_DRIVER selected : opengles2
You can use environment variables to override the default video/render driver selection:

SDL_VIDEODRIVER=KMSDRM SDL_RENDER_DRIVER=software ./a.out
I had to hold SDL's hand a bit with envvars to get the KMSDRM backend to load:

# no envvars, fails:
$ ./a.out 
Testing video drivers...
SDL_VIDEODRIVER available: x11 wayland KMSDRM RPI dummy
SDL_VIDEODRIVER usable   : KMSDRM
SDL_VIDEODRIVER selected : KMSDRM
SDL_CreateWindow(): Could not initialize OpenGL / GLES library

# with envvars, succeeds:
$ SDL_VIDEO_EGL_DRIVER=libEGL.so SDL_VIDEO_GL_DRIVER=libGLESv2.so ./a.out
Testing video drivers...
SDL_VIDEODRIVER available: x11 wayland KMSDRM RPI dummy
SDL_VIDEODRIVER usable   : KMSDRM
SDL_VIDEODRIVER selected : KMSDRM
SDL_RENDER_DRIVER available: opengl opengles2 opengles software
SDL_RENDER_DRIVER selected : opengl

Here's the test program I've been using: [main.cpp](https://github.com/aurzola/RPInTy/blob/master/main.cpp).


How to set default audio output on Raspberry Pi to hdmi?

Audio didn't go through and I couldn't change default output in raspi-config.


edit ~/boot/config.txt

uncomment:

hdmi_drive=2

change this line

dtoverlay=vc4-kms-v3d

to

dtoverlay=vc4-fkms-v3d

save the file and reboot the system.
After reboot, open raspi-config , HDMI output should be default option now.


Change Default Audio Outout from CLI:

sudo raspi-config nonint do_audio <N>
On Raspberry Pi 4B, you can use the following options:

0: bcm2835 headphone jack

1: vc4-hdmi-0

