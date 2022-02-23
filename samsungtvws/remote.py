"""
SamsungTVWS - Samsung Smart TV WS API wrapper

Copyright (C) 2019 Xchwarze

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor,
    Boston, MA  02110-1335  USA

"""
import logging
import time
from typing import overload

from . import art, connection, helper, rest, shortcuts

_LOGGING = logging.getLogger(__name__)


class SamsungTVWS(connection.SamsungTVWSConnection):
    _REMOTE_ENDPOINT = "samsung.remote.control"

    def __init__(
        self,
        host,
        token=None,
        token_file=None,
        port=8001,
        timeout=None,
        key_press_delay=1,
        name="SamsungTvRemote",
    ):
        super().__init__(
            host,
            endpoint=self._REMOTE_ENDPOINT,
            token=token,
            token_file=token_file,
            port=port,
            timeout=timeout,
            key_press_delay=key_press_delay,
            name=name,
        )
        self._rest_api = None

    def _ws_send(self, command, key_press_delay=None):
        return super().send_command(command, key_press_delay)

    # endpoint is kept here for compatibility - can be removed in v2
    @overload
    def open(self, endpoint):
        return super().open()

    # required for overloading - can be removed in v2
    def open(self):
        return super().open()

    def send_key(self, key, times=1, key_press_delay=None, cmd="Click"):
        for _ in range(times):
            _LOGGING.debug("Sending key %s", key)
            self._ws_send(
                {
                    "method": "ms.remote.control",
                    "params": {
                        "Cmd": cmd,
                        "DataOfCmd": key,
                        "Option": "false",
                        "TypeOfRemote": "SendRemoteKey",
                    },
                },
                key_press_delay,
            )

    def hold_key(self, key, seconds):
        self.send_key(key, cmd="Press")
        time.sleep(seconds)
        self.send_key(key, cmd="Release")

    def move_cursor(self, x, y, duration=0):
        self._ws_send(
            {
                "method": "ms.remote.control",
                "params": {
                    "Cmd": "Move",
                    "Position": {"x": x, "y": y, "Time": str(duration)},
                    "TypeOfRemote": "ProcessMouseDevice",
                },
            },
            key_press_delay=0,
        )

    def run_app(self, app_id, app_type="DEEP_LINK", meta_tag=""):
        _LOGGING.debug(
            "Sending run app app_id: %s app_type: %s meta_tag: %s",
            app_id,
            app_type,
            meta_tag,
        )
        self._ws_send(
            {
                "method": "ms.channel.emit",
                "params": {
                    "event": "ed.apps.launch",
                    "to": "host",
                    "data": {
                        # action_type: NATIVE_LAUNCH / DEEP_LINK
                        # app_type == 2 ? 'DEEP_LINK' : 'NATIVE_LAUNCH',
                        "action_type": app_type,
                        "appId": app_id,
                        "metaTag": meta_tag,
                    },
                },
            }
        )

    def open_browser(self, url):
        _LOGGING.debug("Opening url in browser %s", url)
        self.run_app("org.tizen.browser", "NATIVE_LAUNCH", url)

    def app_list(self):
        _LOGGING.debug("Get app list")
        self._ws_send(
            {
                "method": "ms.channel.emit",
                "params": {"event": "ed.installedApp.get", "to": "host"},
            }
        )

        response = helper.process_api_response(self.connection.recv())
        if response.get("data"):
            data = response["data"]
            if isinstance(data, dict) and data.get("data"):
                return data["data"]
            return data
        else:
            return response

    def _get_rest_api(self):
        if self._rest_api is None:
            self._rest_api = rest.SamsungTVRest()
        return self._rest_api

    def rest_device_info(self):
        return self._get_rest_api().rest_device_info()

    def rest_app_status(self, app_id):
        return self._get_rest_api().rest_app_status(app_id)

    def rest_app_run(self, app_id):
        return self._get_rest_api().rest_app_run(app_id)

    def rest_app_close(self, app_id):
        return self._get_rest_api().rest_app_close(app_id)

    def rest_app_install(self, app_id):
        return self._get_rest_api().rest_app_install(app_id)

    def shortcuts(self):
        return shortcuts.SamsungTVShortcuts(self)

    def art(self):
        return art.SamsungTVArt(self)
