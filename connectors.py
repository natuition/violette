#!/usr/bin/env python

import telnetlib
import re
import socket
from threading import Thread, Lock
import json


class SmoothieConnector:

    def __init__(self, host, verbose=False, allow_comments=False):
        self._host = host
        self._allow_comments = allow_comments
        self._verbose = verbose
        self._tn = None

    def connect(self):
        self._tn = telnetlib.Telnet(self._host)
        # read Smoothie startup prompt
        self._tn.read_until("Smoothie command shell".encode('ascii'))

    def disconnect(self):
        # send disconnect command
        self._tn.write("exit".encode('ascii') + b"\n")
        self._tn.read_all()
        self._tn.close()

    def send_recv(self, command: str):
            if not self._allow_comments:
                command = re.sub("[ ]*;.*", '', command)  # remove everything after ;
                command = command.strip()  # send only the bare necessity

            if len(command) > 0:
                if self._verbose:
                    print("Streaming g-code to " + self._host)

                self._tn.write(command.encode('ascii') + b"\n")

                if self._verbose:
                    print("Sent code: " + command.strip())

                while True:
                    responce = self._tn.read_some()
                    if responce.count("ok".encode('ascii')) > 0:
                        return responce.decode()


class PythonConnectorServer:

    def __init__(self, host, port, bufsize=4096):
        self._host = host
        self._port = port
        self._buffer_size = bufsize
        self._socket = socket.socket()
        self._socket.bind((self._host, self._port))
        self._incoming_connection = None
        self._incoming_address = None

    def wait_connection(self):
        self._socket.listen(1)
        self._incoming_connection, self._incoming_address = self._socket.accept()

    def close_connection(self):
        self._incoming_connection.close()

    def receive(self):
        received_data = self._incoming_connection.recv(self._buffer_size).decode()
        return json.loads(received_data) if received_data else None

    def send(self, data):
        self._incoming_connection.send(json.dumps(data).encode())


class PythonConnectorClient:

    def __init__(self, host, port, bufsize=4096, verbose=False):
        self._host = host
        self._port = port
        self._buffer_size = bufsize
        self._verbose = verbose
        self._socket = socket.socket()

    def _conn_close(self):
        try:
            self._socket.close()
        except:
            pass

    def connect(self):
        if self._verbose:
            print("Connecting to " + str(self._host) + ":" + str(self._port))

        self._socket.connect((self._host, self._port))

        if self._verbose:
            print("Connection successful")

    def disconnect(self):
        if self._verbose:
            print("Disconnecting from " + str(self._host) + ":" + str(self._port))
        self._conn_close()

    def send(self, data):
        if self._verbose:
            print("Sending: " + str(data))

        self._socket.send(json.dumps(data).encode())

        if self._verbose:
            print("Sending successful.")

    def receive(self):
        if self._verbose:
            print("Receiving...")

        received_data = self._socket.recv(self._buffer_size).decode()

        if received_data:
            received_data = json.loads(received_data)
            if self._verbose:
                print("Received: " + received_data)
            return received_data
        else:
            if self._verbose:
                print("Connection was closed from the other side.")
            self._socket.close()
            return None


def _test_SmoothieConnector():
    g_code = "G0 X10 Y5 F200"
    host = "192.168.1.222"
    sc = SmoothieConnector(host, verbose=True)
    sc.connect()
    print("Connection established. Sending data.")
    resp = sc.send_recv(g_code)
    print("Response: " + resp)
    sc.disconnect()
    print("Connection closed normally.")


def _test_PythonConnectorServer():
    def writer(data_list: list, locker: Lock):
        while True:
            if len(data_list) > 0:
                locker.acquire()
                item = data_list.pop(0)
                locker.release()

                if item == "stop":
                    print("Stopping writer thread.")
                    break
                else:
                    print(item)

    host = "127.0.0.1"
    port = 8081

    data_list = list()
    pcs = PythonConnectorServer(host, port, verbose=True)

    lock = Lock()
    t1 = Thread(target=pcs.receive, args=(data_list, lock,), name="Th-Connector")
    t2 = Thread(target=writer, args=(data_list, lock,), name="Th-Writer")

    t1.start()
    t2.start()

    t1.join()
    t2.join()


if __name__ == "__main__":
    #_test_PythonConnectorServer()
    _test_SmoothieConnector()
