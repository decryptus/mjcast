# MJCast

Streaming MJPEG screenshots.

We created this project for streaming monitoring with Raspberry.
Raspberry was slow when we loaded web pages with many graphics,
so we decide to display screenshots with MJPEG procotol.

Installation on Debian
======================

apt-get install chromium-driver chromium python-dev python-pip redis-server
pip install -r requirements.txt
pip install mjcast
