from threading import Thread, Lock
import puresnmp
from puresnmp.x690.types import Integer
import time
import uuid
from journal import journal

class snmp_protocol:

    def __init__(self):
        self.__tasks = {}
        self.__templ_init = {'value': '-1', 'error': '-1', 'run': False, 'type': None, 'thread': None}
        self.__lock_tasks = Lock()

    def __gen_id(self):
        fl_id_uniq = False
        while not fl_id_uniq:
            new_id = str(uuid.uuid4())
            try:
                self.__lock_tasks.acquire()
                a = self.__tasks[new_id]
            except KeyError:
                # get unique identifier
                fl_id_uniq = True
            finally:
                self.__lock_tasks.release()
        return new_id

    def __snmp_poll(self, id_task, address, community, oid, port, timeout, period):
        try:
            self.__lock_tasks.acquire()
            val_task = self.__tasks[id_task]
        except KeyError:
            self.__lock_tasks.release()
            journal.WriteLog("OWRT_SNMP_Protocol", "Normal", "err",
                             "__snmp_poll() id_task " + id_task + " not found")
            return -1

        err = val_task['error']
        val = val_task['value']
        run_stat = val_task['run']
        self.__lock_tasks.release()

        while run_stat:
            try:
                result = puresnmp.get(address, community, oid, port=int(port), timeout=float(timeout))
            except puresnmp.exc.Timeout as e:
                # no connection
                journal.WriteLog("OWRT_SNMP_Protocol", "Normal", "err",
                                 "__snmp_poll() ERROR no connection: {0}".format(e) +
                                 " address: " + address + " community: " + community +
                                 " oid: " + oid + " port: " + port + " timeout: " + timeout)
                err = "1"
            except puresnmp.exc.NoSuchOID as e:
                # ERROR
                journal.WriteLog("OWRT_SNMP_Protocol", "Normal", "err",
                                 "__snmp_poll() STOP ERROR: {0}".format(e) + " address: " + address +
                                 " community: " + community + " oid: " + oid + " port: " + port +
                                 " timeout: " + timeout)
                err = "2"
            else:
                err = "0"
                val = str(result)
            finally:
                self.__lock_tasks.acquire()
                val_task['error'] = err
                val_task['value'] = val
                run_stat = val_task['run']
                self.__lock_tasks.release()
                time.sleep(float(period))

    def start_snmp_poll(self, address, community, oid, port, timeout, period):
        id_task = self.__gen_id()
        val_task = self.__templ_init.copy()
        val_task['type'] = 'poll'
        val_task['run'] = True
        val_task['thread'] = Thread(target=self.__snmp_poll, args=(id_task, address, community, oid, port, timeout, period))
        self.__lock_tasks.acquire()
        self.__tasks[id_task] = val_task
        val_task['thread'].start()
        self.__lock_tasks.release()

        return id_task

    def __stop_poll(self, id_task, thrd):
        thrd.join()
        self.__lock_tasks.acquire()
        del self.__tasks[id_task]
        self.__lock_tasks.release()

    def stop_snmp_poll(self, id_task):
        try:
            self.__lock_tasks.acquire()
            val_task = self.__tasks[id_task]
        except KeyError:
            # id not found
            self.__lock_tasks.release()
            journal.WriteLog("OWRT_SNMP_Protocol", "Normal", "err",
                             "stop_snmp_poll() id_task " + id_task + " not found")
            return -2

        if val_task['type'] == 'poll':
            val_task['run'] = False
            thrd = val_task['thread']
            self.__lock_tasks.release()

            th = Thread(target=self.__stop_poll, args=(id_task, thrd))
            th.start()

            return 0
        else:
            # task with the given ID is not a poll
            self.__lock_tasks.release()
            journal.WriteLog("OWRT_SNMP_Protocol", "Normal", "err",
                             "stop_snmp_poll() task with the given ID is not a poll")
            return -1

    def get_snmp_poll(self, id_task):
        try:
            self.__lock_tasks.acquire()
            val_task = self.__tasks[id_task]
            value = val_task['value']
            error = val_task['error']
        except KeyError:
            # id not found
            journal.WriteLog("OWRT_SNMP_Protocol", "Normal", "err",
                             "get_snmp_poll() KeyError")
            value = '-1'
            error = '-2'
        finally:
            self.__lock_tasks.release()
            return value, error

    def __snmp_get(self, id_task, address, community, oid, port, timeout):
        try:
            self.__lock_tasks.acquire()
            val_task = self.__tasks[id_task]
        except KeyError:
            self.__lock_tasks.release()
            return -1

        err = val_task['error']
        val = val_task['value']
        self.__lock_tasks.release()

        try:
            result = puresnmp.get(address, community, oid, port=int(port), timeout=float(timeout))
        except puresnmp.exc.Timeout as e:
            # no connection
            journal.WriteLog("OWRT_SNMP_Protocol", "Normal", "err",
                             "__snmp_get() ERROR no connection: {0}".format(e) +
                             " address: " + address + " community: " + community +
                             " oid: " + oid + " port: " + port + " timeout: " + timeout)
            err = "1"
        except puresnmp.exc.NoSuchOID as e:
            # ERROR
            journal.WriteLog("OWRT_SNMP_Protocol", "Normal", "err",
                             "__snmp_get() STOP ERROR: {0}".format(e) + " address: " + address +
                             " community: " + community + " oid: " + oid + " port: " + port +
                             " timeout: " + timeout)
            err = "2"
        else:
            err = "0"
            val = str(result)
        finally:
            self.__lock_tasks.acquire()
            val_task['error'] = err
            val_task['value'] = val
            val_task['run'] = False
            self.__lock_tasks.release()

    def get_snmp_value(self, address, community, oid, port, timeout):
        id_task = self.__gen_id()
        val_task = self.__templ_init.copy()
        val_task['type'] = 'single'
        val_task['run'] = True
        val_task['thread'] = Thread(target=self.__snmp_get, args=(id_task, address, community, oid, port, timeout))
        self.__lock_tasks.acquire()
        self.__tasks[id_task] = val_task
        val_task['thread'].start()
        self.__lock_tasks.release()

        return id_task

    def res_get_snmp_value(self, id_task):
        try:
            self.__lock_tasks.acquire()
            val_task = self.__tasks[id_task]
            value = val_task['value']
            error = val_task['error']
        except KeyError:
            # id not found
            self.__lock_tasks.release()
            journal.WriteLog("OWRT_SNMP_Protocol", "Normal", "err",
                             "res_get_snmp_value() KeyError")
            value = '-1'
            error = '-2'
            return value, error

        if val_task['type'] == 'single':
            if val_task['run'] == False:
                del self.__tasks[id_task]

            self.__lock_tasks.release()
            return value, error
        else:
            # task with the given ID is not a single
            self.__lock_tasks.release()
            journal.WriteLog("OWRT_SNMP_Protocol", "Normal", "err",
                             "res_get_snmp_value() task with the given ID is not a single")
            value = '-1'
            error = '-3'
            return value, error

    def __snmp_set(self, id_task, address, community, oid, port, timeout, value):
        try:
            self.__lock_tasks.acquire()
            val_task = self.__tasks[id_task]
        except KeyError:
            self.__lock_tasks.release()
            journal.WriteLog("OWRT_SNMP_Protocol", "Normal", "err",
                             "__snmp_set() id_task " + id_task + " not found")
            return -1

        err = val_task['error']
        self.__lock_tasks.release()

        try:
            set_res = puresnmp.set(address, community, oid, Integer(int(value)), port=int(port), timeout=float(timeout))
            # returns the set value
        except puresnmp.exc.Timeout as e:
            # no connection
            journal.WriteLog("OWRT_SNMP_Protocol", "Normal", "err",
                             "__snmp_set() ERROR no connection: {0}".format(e) +
                             " address: " + address + " community: " + community +
                             " oid: " + oid + " port: " + port + " timeout: " + timeout)
            err = "1"
        except puresnmp.exc.NoSuchOID as e:
            # ERROR
            journal.WriteLog("OWRT_SNMP_Protocol", "Normal", "err",
                             "__snmp_set() STOP ERROR: {0}".format(e) + " address: " + address +
                             " community: " + community + " oid: " + oid + " port: " + port +
                             " timeout: " + timeout)
            err = "2"
        else:
            if str(set_res) == value:
                err = "0"
        finally:
            self.__lock_tasks.acquire()
            val_task['error'] = err
            val_task['run'] = False
            self.__lock_tasks.release()

    def set_snmp_value(self, address, community, oid, port, timeout, value):
        id_task = self.__gen_id()
        val_task = self.__templ_init.copy()
        val_task['type'] = 'single'
        val_task['run'] = True
        val_task['thread'] = Thread(target=self.__snmp_set, args=(id_task, address, community, oid, port, timeout, value))
        self.__lock_tasks.acquire()
        self.__tasks[id_task] = val_task
        val_task['thread'].start()
        self.__lock_tasks.release()

        return id_task

    def res_set_snmp_value(self, id_task):
        try:
            self.__lock_tasks.acquire()
            val_task = self.__tasks[id_task]
            error = val_task['error']
        except KeyError:
            # id not found
            self.__lock_tasks.release()
            journal.WriteLog("OWRT_SNMP_Protocol", "Normal", "err",
                             "res_set_snmp_value() KeyError")
            error = '-2'
            return error

        if val_task['type'] == 'single':
            if val_task['run'] == False:
                del self.__tasks[id_task]

            self.__lock_tasks.release()
            return error
        else:
            # task with the given ID is not a single
            self.__lock_tasks.release()
            journal.WriteLog("OWRT_SNMP_Protocol", "Normal", "err",
                             "res_set_snmp_value() task with the given ID is not a single")
            error = '-3'
            return error
