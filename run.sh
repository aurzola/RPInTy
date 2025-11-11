#!/bin/bash

SDL_VIDEO_EGL_DRIVER=libEGL.so SDL_VIDEO_GL_DRIVER=libGLESv2.so bin/jzintv -z1 --kbdhackfile=hackfile.txt "$1"
#SDL_VIDEO_EGL_DRIVER=libEGL.so SDL_VIDEO_GL_DRIVER=libGLESv2.so bin/jzintv -z1 --kbdhackfile=hackfile.txt rom/Armor\ Battle\ \(1978\)\ \(Mattel\).int 

