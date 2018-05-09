# -*- coding: utf-8 -*-
"""mjcast channels"""

__author__  = "Adrien DELLE CAVE <adc@doowan.net>"
__license__ = """
    Copyright (C) 2018  doowan

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA..
"""

import base64
import cv2
import os
import logging
import threading
import time

from datetime import datetime
from dwho.adapters.redis import DWhoAdapterRedis
from dwho.classes.plugins import DWhoPluginBase, PLUGINS
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from sonicprobe.libs.keystore import Keystore
from tempfile import mkstemp


LOG              = logging.getLogger('mjcast.playlist')

DATETIME_DEFAULT = {'position': 'auto',
                    'format': "%Y-%m-%d %H:%M:%S %Z",
                    'face': cv2.FONT_HERSHEY_PLAIN,
                    'color': [0, 0, 0],
                    'scale': 0,
                    'thickness': 1}


class MjCastMedia(threading.Thread):
    def __init__(self, name, params, adapter_redis):
        threading.Thread.__init__(self)
        self.daemon        = True
        self.killed        = False
        self.result        = Keystore().add(self.name)

        self.name          = name
        self.params        = params
        self.adapter_redis = adapter_redis
        self.ttl           = int(self.params.get('ttl') or 1)

        self.init_driver()

    def get_name(self):
        return self.name

    def get_result(self):
        return self.result

    def add_datetime(self, img):
        if not isinstance(self.params.get('datetime'), dict):
            return img

        dt = DATETIME_DEFAULT.copy()
        dt.update(self.params['datetime'])

        text      = time.strftime(dt['format'])
        textsize  = cv2.getTextSize(text, dt['face'], float(dt['scale']), dt['thickness'])

        if dt['position'] == 'auto':
            dt['org'] = (img.shape[1] - (textsize[0][0] + 10), 20)

        cv2.putText(img,
                    text,
                    dt['org'],
                    dt['face'],
                    float(dt['scale']),
                    dt['color'],
                    dt['thickness'])

        return img

    def save_screenshot(self):
        (tmpfd, tmpfile, filepath, data) = (0, None, None, None)

        try:
            (tmpfd, tmpfile) = mkstemp()
            filepath = "%s.png" % tmpfile
            os.rename(tmpfile, filepath)
            self.driver.save_screenshot(filepath)
            img      = self.add_datetime(cv2.imread(filepath))

            gmtime   = datetime.utcnow().strftime('%s')
            data     = cv2.imencode('.jpg', img)[1].tostring()
            xlen     = len(data)

            self.adapter_redis.set_key(self.name,
                                       "%s|%d|%s" % (gmtime,
                                                     xlen,
                                                     base64.b64encode(data)),
                                       self.ttl)

            return (gmtime, xlen, data)
        finally:
            data = None

            if tmpfd:
                os.close(tmpfd)

            if tmpfile and os.path.exists(tmpfile):
                os.unlink(tmpfile)

            if filepath and os.path.exists(filepath):
                os.unlink(filepath)

    def init_driver(self):
        self.driver = webdriver.Chrome(
                          executable_path = self.params['executable_path'],
                          chrome_options  = self.driver_options())

    def driver_options(self):
        r = Options()

        for option in self.params['options']:
            r.add_argument(option)

        r.binary_location = self.params['binary_location']

        return r

    def run(self):
        self.driver.get(self.params['url'])
        if self.params.get('delay'):
            time.sleep(float(self.params['delay']))

        self.save_screenshot()

        while not self.killed:
            try:
                value = self.adapter_redis.get_key(self.name)
                wait  = float(self.params.get('wait', 1))
                if value:
                   (gmtime, xlen, data) = value.split('|', 2)
                   self.result.try_acquire(self.name)
                   (self.result.set(self.name, 'gmtime', gmtime)
                               .set(self.name, 'length', long(xlen))
                               .set(self.name, 'data', base64.b64decode(data))
                               .set(self.name, 'wait', wait))
                   self.result.try_release(self.name)
                else:
                    try:
                        self.driver.refresh()
                    except (TimeoutException, WebDriverException):
                        self.quit()
                        self.init_driver()
                        self.driver.get(self.params['url'])

                    if self.params.get('delay'):
                        time.sleep(float(self.params['delay']))
                    (gmtime, xlen, data) = self.save_screenshot()
                    self.result.try_acquire(self.name)
                    (self.result.set(self.name, 'gmtime', gmtime)
                                .set(self.name, 'length', long(xlen))
                                .set(self.name, 'data', data)
                                .set(self.name, 'wait', wait))
                    self.result.try_release(self.name)
                time.sleep(self.ttl)
            except Exception, e:
                LOG.exception(repr(e))
            finally:
                self.result.try_release(self.name)

    def quit(self):
        try:
            self.driver.quit()
        except (TimeoutException, WebDriverException):
            pass

    def terminate(self):
        self.killed = True

        self.quit()

        self.driver = None


class MjCastPlaylistPlugin(DWhoPluginBase):
    PLUGIN_NAME = 'playlist'

    def safe_init(self):
        self.medias        = []
        self.adapter_redis = DWhoAdapterRedis(self.config, prefix = 'playlist')

        for params in self.config['plugins']['playlist']:
            self.medias.append(MjCastMedia(params['name'], params, self.adapter_redis))

    def get_medias(self):
        return self.medias

    def at_start(self):
        for media in self.medias:
            media.start()

    def at_stop(self):
        for media in self.medias:
            media.terminate()


if __name__ != "__main__":
    def _start():
        PLUGINS.register(MjCastPlaylistPlugin())
    _start()
