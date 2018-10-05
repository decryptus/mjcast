# MJCast

Streaming MJPEG screenshots.

We created this project for streaming monitoring with Raspberry.
Raspberry was slow when we loaded web pages with many graphics,
so we decide to display screenshots with MJPEG procotol.

Installation on Debian
======================

- apt-get install chromium-driver chromium python-dev python-pip redis-server
- pip install -r requirements.txt
- pip install mjcast

Running with Docker
===================

If you want to run this project with docker you first need to build it.

```sh
docker build -t mjcast .
```

Then you would run it with the following command:
```sh
docker run -d -p 8670:8670 mjcast
```

Results
=======

Streaming URL: http://localhost:8670/server/stream
