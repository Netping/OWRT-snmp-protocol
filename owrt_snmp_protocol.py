from threading import Thread
import puresnmp
from puresnmp.x690.types import Integer
import time
import uuid

class snmp_protocol:

    def __init__(self):
        self.__tasks = {}
        self.__templ_init = {'value': '-1', 'error': '-1', 'run': False, 'type': None, 'thread': None}

    def __gen_id(self):
        while True:
            new_id = str(uuid.uuid4())
            try:
                a = self.__tasks[new_id]
            except KeyError:
                # get unique identifier
                return new_id

    def __snmp_poll(self, id_task, address, community, oid, port, timeout, period):
        try:
            val_task = self.__tasks[id_task]
        except KeyError:
            return -1

        while val_task['run']:
            try:
                result = puresnmp.get(address, community, oid, port=int(port), timeout=float(timeout))
            except puresnmp.exc.Timeout as e:
                # no connection
                # print("STOP {0} ERROR no connection: {1}".format(address, e))
                val_task['error'] = "1"
            except puresnmp.exc.NoSuchOID as e:
                # ERROR
                #print("STOP ERROR: {0}".format(e))
                val_task['error'] = "2"
            else:
                val_task['error'] = "0"
                val_task['value'] = str(result)
            finally:
                time.sleep(float(period))

    def start_snmp_poll(self, address, community, oid, port, timeout, period):
        id_task = self.__gen_id()
        val_task = self.__templ_init.copy()
        val_task['type'] = 'poll'
        val_task['run'] = True
        val_task['thread'] = Thread(target=self.__snmp_poll, args=(id_task, address, community, oid, port, timeout, period))
        self.__tasks[id_task] = val_task

        val_task['thread'].start()

        return id_task

    def __stop_poll(self, id_task, val_task):
        val_task['thread'].join()
        del self.__tasks[id_task]

    def stop_snmp_poll(self, id_task):
        try:
            val_task = self.__tasks[id_task]
        except KeyError:
            # id not found
            return -2

        if val_task['type'] == 'poll':
            val_task['run'] = False

            th = Thread(target=self.__stop_poll, args=(id_task, val_task))
            th.start()

            return 0
        else:
            # task with the given ID is not a poll
            return -1

    def get_snmp_poll(self, id_task):
        try:
            val_task = self.__tasks[id_task]
        except KeyError:
            # id not found
            value = '-1'
            error = '-2'
            return value, error
        else:
            return val_task['value'], val_task['error']

    def __snmp_get(self, id_task, address, community, oid, port, timeout):
        try:
            val_task = self.__tasks[id_task]
        except KeyError:
            return -1

        try:
            result = puresnmp.get(address, community, oid, port=int(port), timeout=float(timeout))
        except puresnmp.exc.Timeout as e:
            # no connection
            # print("STOP {0} ERROR no connection: {1}".format(address, e))
            val_task['error'] = "1"
        except puresnmp.exc.NoSuchOID as e:
            # ERROR
            #print("STOP ERROR: {0}".format(e))
            val_task['error'] = "2"
        else:
            val_task['error'] = "0"
            val_task['value'] = str(result)
        finally:
            val_task['run'] = False

    def get_snmp_value(self, address, community, oid, port, timeout):
        id_task = self.__gen_id()
        val_task = self.__templ_init.copy()
        val_task['type'] = 'single'
        val_task['run'] = True
        val_task['thread'] = Thread(target=self.__snmp_get, args=(id_task, address, community, oid, port, timeout))
        self.__tasks[id_task] = val_task

        val_task['thread'].start()

        return id_task

    def res_get_snmp_value(self, id_task):
        try:
            val_task = self.__tasks[id_task]
        except KeyError:
            # id not found
            value = '-1'
            error = '-2'
            return value, error

        if val_task['type'] == 'single':
            if val_task['run'] == False:
                del self.__tasks[id_task]

            return val_task['value'], val_task['error']
        else:
            # task with the given ID is not a single
            value = '-1'
            error = '-3'
            return value, error
