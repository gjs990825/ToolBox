r"""Campus Net Login

Quick campus network authentication for Anhui University of Science and Technology

USAGE:
    python campus_net_login.py login -id your_id -op your_operator -pwd your_password

    python campus_net_login.py login -id your_id -op your_operator -pwd your_password --make_script

    python campus_net_login.py logout
"""

import argparse
import json
import os

import requests

operator_mapper = {
    'ctcc': 'aust',
    'cmcc': 'cmcc',
    'unicom': 'unicom'
}
URL_BASE = 'http://10.255.0.19/drcom/'


def check_result(response_text, callback_name: str):
    response_text = response_text.strip().removeprefix(f'{callback_name}(').removesuffix(')')
    return json.loads(response_text)['result'] == 1


def login(student_id, network_operator, password, session_id=None):
    url = URL_BASE + 'login'
    params = {
        'callback': 'dr1003',
        'DDDDD': f'{student_id}@{network_operator}',
        'upass': password,
        '0MKKey': '123456',
        'R1': '0',
        'R3': '0',
        'R6': '0',
        'para': '00',
        'v6ip': '',
        'v': 5568
    }
    cookies = None if session_id is None else {'PHPSESSID': session_id}

    print(url, params, cookies)
    response = requests.get(url=url, params=params, cookies=cookies)
    print('OK' if check_result(response.text, callback_name='dr1003') else 'FAIL')


def logout():
    url = URL_BASE + 'logout'
    params = {'callback': 'dr1002'}
    response = requests.get(url=url, params=params)
    print('OK' if check_result(response.text, callback_name='dr1002') else 'FAIL')


def make_cmd(student_id, network_operator, password, session_id=None):
    py_script_name = os.path.basename(__file__)
    cmd_name = py_script_name.removesuffix('py') + 'cmd'
    with open(cmd_name, 'w+') as f:
        f.write(f'python {py_script_name} login -id {student_id} -op {network_operator} -pwd {password}')
        if session_id:
            f.write(f' -sid {session_id}')
        f.write('\npause\n')


def run(opt):
    if opt.parser_name == 'logout':
        logout()
        return

    make_script = opt.make_script
    student_id = opt.student_id
    network_operator = opt.operator.lower()
    password = opt.password
    session_id = opt.session_id
    assert network_operator in operator_mapper
    network_operator = operator_mapper[network_operator.lower()]

    operation = make_cmd if make_script else login
    operation(student_id, network_operator, password, session_id)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='parser_name', help='choose what to do')

    parser_login = subparsers.add_parser('login')
    parser_logout = subparsers.add_parser('logout')

    parser_login.add_argument('-id', '--student_id', type=str, required=True, help='Your student ID number.')
    parser_login.add_argument('-op', '--operator', type=str, required=True,
                              help='Network operator (ctcc, cmcc or unicom).')
    parser_login.add_argument('-pwd', '--password', type=str, required=True, help='Your password.')
    parser_login.add_argument('-sid', '--session_id', type=str, help='PHP session ID, seems not helping? :(')
    parser_login.add_argument('--make_script', action=argparse.BooleanOptionalAction,
                              help='Make a command line script using provided information.')
    opt = parser.parse_args()

    print(opt)
    run(opt)
