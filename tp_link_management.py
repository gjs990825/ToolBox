from copy import deepcopy
from typing import Optional, Callable
import json

import requests


def dict_modify(d, key, new_val=None, copy=True):
    if copy:
        d = deepcopy(d)

    q = [d]
    while q:
        e = q.pop(0)
        if isinstance(e, dict):
            q.extend(e.values())
            if key in e:
                e[key] = new_val
    return d


class PostRequestTemplate:
    def __init__(self, name: str, payload: dict, response_handler: Optional[Callable], url=None):
        self.url = url
        self.response_handler = response_handler
        self.name = name
        self.payload = payload

    def fill_payload(self, **kwargs):
        payload = self.payload
        for k, v in kwargs.items():
            payload = dict_modify(payload, k, v, copy=True)
        return payload

    def request(self, url=None, request_params=None, **kwargs):
        if url is None:
            url = self.url

        assert url is not None
        if request_params is None:
            request_params = {}

        response = requests.post(
            self.url if url is None else url,
            json=self.fill_payload(**kwargs),
            **request_params
        )
        response = json.loads(response.content.decode())
        if callable(self.response_handler):
            return self.response_handler(response)
        return response

    def __eq__(self, other):
        return self.name == other

    def __repr__(self) -> str:
        return f'<PostRequestTemplate: {self.name}>'


class TP_LINK:
    TEMPLATES = [
        PostRequestTemplate(
            name='login',
            payload={"method": "do", "login": {"password": None}},
            response_handler=lambda r: r['stok'] if r['error_code'] == 0 else None
        ),
        PostRequestTemplate(
            name='renew_dhcp',
            payload={"network": {"change_wan_status": {"proto": "dhcp", "operate": "renew"}}, "method": "do"},
            response_handler=lambda r: r['error_code'] == 0
        ),
        PostRequestTemplate(
            name='logout',
            payload={"system": {"logout": "null"}, "method": "do"},
            response_handler=lambda r: r['error_code'] == 0
        )
    ]

    def __init__(self, base_url, password):
        self.password = password
        self.password_encoded = self.orgAuthPwd(password)
        self.base_url = base_url
        self.session_id = None

    def __getitem__(self, name):
        try:
            return next(iter(t for t in self.TEMPLATES if t == name))
        except StopIteration:
            raise Exception(f'no such template: {name}')

    def data_request_url(self):
        if self.session_id is None:
            return None
        return self.base_url + 'stok=' + self.session_id + '/ds'

    def login(self):
        if self.session_id is not None:
            return True
        self.session_id = self['login'].request(self.base_url, password=self.password_encoded)
        return self.session_id is not None

    def logout(self):
        if self.session_id is None:
            return True

        if self['logout'].request(
                self.data_request_url()
        ):
            self.session_id = None
            return True
        return False

    def default_request(self, name, in_session):
        return self[name].request(url=self.data_request_url() if in_session else self.base_url)

    @property
    def is_logged_in(self):
        return self.session_id is not None

    @staticmethod
    def orgAuthPwd(pwd):
        """from http://tplogin.cn/web-static/dynaform/class.js"""

        strDe = "RDpbLfCPsJZ7fiv"
        dic = "yLwVl0zKqws7LgKPRQ84Mdt708T1qQ3Ha7xv3H7NyU84p21BriUWBU43odz3iP4rBL3cD02KZciXTysVXiV8ngg6vL48rPJyAUw0HurW20xqxv9aYb4M9wK1Ae0wlro510qXeU07kV57fQMc8L6aLgMLwygtc0F10a0Dg70TOoouyFhdysuRMO51yY5ZlOZZLEal1h0t9YQW0Ko7oBwmCAHoic4HYbUyVeU3sfQ1xtXcPcf1aT303wAQhv66qzW"

        return TP_LINK.securityEncode(pwd, strDe, dic)

    @staticmethod
    def securityEncode(password, input2, dictionary):
        """from http://tplogin.cn/web-static/dynaform/class.js"""

        output = []

        len1 = len(password)
        len2 = len(input2)
        len_dict = len(dictionary)
        len_max = max(len1, len2)

        for index in range(len_max):
            cl = 0xBB
            cr = 0xBB

            if index >= len1:
                cr = ord(input2[index])
            elif index >= len2:
                cl = ord(password[index])
            else:
                cl = ord(password[index])
                cr = ord(input2[index])

            output.append(dictionary[(cl ^ cr) % len_dict])

        return ''.join(output)


if __name__ == '__main__':
    base_url = 'http://192.168.1.1/'
    password = '*****'

    tp_link = TP_LINK(base_url=base_url, password=password)

    print(tp_link.password, tp_link.password_encoded)

    tp_link.login()
    tp_link.default_request('renew_dhcp', in_session=True)
    tp_link.logout()
