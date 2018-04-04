# -*- coding: utf-8 -*-
"""server module"""

__author__  = "Adrien DELLE CAVE"
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

import logging
import time

from dwho.classes.modules import DWhoModuleBase, MODULES
from dwho.classes.plugins import PLUGINS

LOG            = logging.getLogger('mjcast.modules.server')

_BOUNDARY_NAME = 'frame'
_CONTENT_TYPE  = "multipart/x-mixed-replace; boundary=%s" % _BOUNDARY_NAME
_CACHE         = {'loading': None}


class MjCastServerModule(DWhoModuleBase):
    MODULE_NAME = 'server'

    def _push_loading(self, request):
        if not self.config['general'].get('loading_file'):
            return

        if not _CACHE['loading']:
            f = None

            with open(self.config['general']['loading_file'], 'rb') as f:
                data = f.read()
                _CACHE['loading'] = (len(data), data)
                data = None

            if f:
                f.close()

        LOG.info("streaming loading")

        request.end_headers()
        request.wfile.write("--" + _BOUNDARY_NAME)
        request.end_headers()
        request.send_header('Content-Type', 'image/jpeg')
        request.send_header('Content-Length', _CACHE['loading'][0])
        request.end_headers()
        request.wfile.write(_CACHE['loading'][1])

    def status(self, request):
        return True

    def stream(self, request):
        request.send_response(200)
        request.send_header('Content-type', _CONTENT_TYPE)
        request.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
        request.send_header('Pragma', 'no-cache')
        request.end_headers()

        while True:
            for media in PLUGINS['playlist'].get_medias():
                while True:
                    result = media.get_result()
                    if not result:
                        self._push_loading(request)
                        time.sleep(0.5)
                        continue

                    try:
                        result.try_acquire(media.get_name())
                        gmtime = result.get(media.get_name(), 'gmtime')
                        xlen   = result.get(media.get_name(), 'length')
                        data   = result.get(media.get_name(), 'data')
                        wait   = result.get(media.get_name(), 'wait')
                    except Exception, e:
                        LOG.error(e)
                    finally:
                        result.try_release(media.get_name())

                    if data:
                        break

                    self._push_loading(request)
                    time.sleep(0.5)

                LOG.info("streaming %r ready", media.get_name())
                begin = time.time()

                while begin + wait >= time.time():
                    request.end_headers()
                    request.wfile.write("--" + _BOUNDARY_NAME)
                    request.end_headers()
                    request.send_header('X-Mjcast-Name', media.get_name())
                    request.send_header('X-Mjcast-Gmtime', gmtime)
                    request.send_header('X-Mjcast-Wait', wait)
                    request.send_header('Content-Type', 'image/jpeg')
                    request.send_header('Content-Length', xlen)
                    request.end_headers()
                    request.wfile.write(data)
                    if ((begin + wait) - time.time()) >= 0.5:
                        time.sleep(0.5)


if __name__ != "__main__":
    def _start():
        MODULES.register(MjCastServerModule())
    _start()
