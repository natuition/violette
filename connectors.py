#!/usr/bin/env python

import telnetlib
import re
import socket
from threading import Thread
import traceback
import json


class SmoothieConnector:

    def __init__(self, host, verbose=False, allow_comments=False):
        self._host = host
        self._allow_comments = allow_comments
        self._verbose = verbose
        self._tn = None

    def connect(self):
        try:
            self._tn = telnetlib.Telnet(self._host)
            # read Smoothie startup prompt
            self._tn.read_until("Smoothie command shell".encode('ascii'))
            return True
        except KeyboardInterrupt:
            exit()
        except Exception:
            tb = traceback.format_exc()
            print(tb)
            return False

    def disconnect(self):
        try:
            # send disconnect command
            self._tn.write("exit".encode('ascii') + b"\n")
            self._tn.read_all()
            self._tn.close()
            return True
        except KeyboardInterrupt:
            exit()
        except Exception:
            tb = traceback.format_exc()
            print(tb)
            return False

    def send(self, command: str):
        try:
            if not self._allow_comments:
                command = re.sub("[ ]*;.*", '', command)  # remove everything after ;
                command = command.strip()  # send only the bare necessity

            if len(command) > 0:
                if self._verbose:
                    print("Streaming g-code to " + self._host)

                self._tn.write(command.encode('ascii') + b"\n")

                if self._verbose:
                    print("Sent code: " + command.strip())
            else:
                return False

            while True:
                rep = self._tn.read_some()
                if rep.count("ok".encode('ascii')) > 0:
                    return True
        except KeyboardInterrupt:
            exit()
        except Exception:
            tb = traceback.format_exc()
            print(tb)
            return False


class PythonConnectorServer:

    def __init__(self, host, port, bufsize=4096, verbose=False):
        self._host = host
        self._port = port
        self._buffer_size = bufsize
        self._verbose = verbose
        self._socket = socket.socket()
        self._socket.bind((self._host, self._port))
        self._incoming_connection = None
        self._incoming_address = None

    def _conn_close(self):
        try:
            self._incoming_connection.close()
        except:
            pass

    def start(self, shared_resourse: list):
        if self._verbose:
            print("Waiting for client connection...")

        self._socket.listen(1)
        self._incoming_connection, self._incoming_address = self._socket.accept()

        if self._verbose:
            print("Incoming connection from " + str(self._incoming_address))

        while True:
            received_data = self._incoming_connection.recv(self._buffer_size).decode()

            if received_data:
                received_data = json.loads(received_data)
            else:
                if self._verbose:
                    print("Connection was closed from the other side.")
                self._incoming_connection.close()
                break

            shared_resourse.append(received_data)


class PythonConnectorClient:

    def __init__(self, host, port, verbose=False):
        self._host = host
        self._port = port
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


def _test_SmoothieConnector():
    g_code = "G0 X10 Y5 F200"
    host = "192.168.1.222"
    sc = SmoothieConnector(verbose=True)
    if sc.connect(host):
        print("Connection established.")
        if sc.send(g_code):
            print("Code executed successfully.")
    if sc.disconnect():
        print("Connection closed normally.")


def _test_PythonConnectorServer():
    def writer(data_list: list):
        while True:
            if len(data_list) > 0:
                item = data_list.pop(0)
                if item == "stop":
                    print("Stopping writer thread.")
                    break
                else:
                    print(item)

    host = "127.0.0.1"
    port = 8081

    data_list = list()
    pcs = PythonConnectorServer(host, port, verbose=True)

    t1 = Thread(target=pcs.start, args=(data_list,))
    t2 = Thread(target=writer, args=(data_list,))

    t1.start()
    t2.start()

    t1.join()
    t2.join()


if __name__ == "__main__":
    _test_PythonConnectorServer()
