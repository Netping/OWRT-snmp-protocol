import ubus
import os
import time
from owrt_snmp_protocol import snmp_protocol




def test_module_existance():
    ret = False

    try:
        if not os.path.isfile("/usr/lib/python3.7/owrt_snmp_protocol.py"):
            raise ValueError('Module file not found')

        ret = True

    except Exception as ex:
        print(ex)

    assert ret

def test_get_snmp_poll():
    ret = False

    try:
        snmp_pr = snmp_protocol()

        config_relay = { 'address' : '127.0.0.1',
                        'community' : '0',
                        'oid' : '0',
                        'port' : '0',
                        'timeout' : '5',
                        'period' : '1' }

        id_poll = snmp_pr.start_snmp_poll(config_relay['address'], config_relay['community'], config_relay['oid'], config_relay['port'], config_relay['timeout'], config_relay['period'])
        value, error = snmp_pr.get_snmp_poll(id_poll)
        snmp_pr.stop_snmp_poll(id_poll)

        ret = True
    except Exception as ex:
        print(ex)

    assert ret

def test_get_snmp_value():
    ret = False

    try:
        snmp_pr = snmp_protocol()

        sensor = { 'snmp_addr' : '127.0.0.1',
                        'community' : '0',
                        'oid' : '0',
                        'snmp_port' : '0',
                        'timeout' : '5' }

        snmp_id = snmp_pr.get_snmp_value(sensor['snmp_addr'], sensor['community'], sensor['oid'], sensor['snmp_port'], sensor['timeout'])
        time.sleep(int(sensor['timeout']))
        value, err = snmp_pr.res_get_snmp_value(snmp_id)

        ret = True
    except Exception as ex:
        print(ex)

    assert ret

def test_set_snmp_value():
    ret = False

    try:
        snmp_pr = snmp_protocol()

        sensor = { 'snmp_addr' : '127.0.0.1',
                        'community' : '0',
                        'oid' : '0',
                        'snmp_port' : '0',
                        'timeout' : '5' }

        snmp_id = snmp_pr.set_snmp_value(sensor['snmp_addr'], sensor['community'], sensor['oid'], sensor['snmp_port'], sensor['timeout'])
        time.sleep(int(sensor['timeout']))
        err = snmp_pr.res_set_snmp_value(snmp_id)

        ret = True
    except Exception as ex:
        print(ex)

    assert ret
