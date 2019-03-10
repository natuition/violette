#!/usr/bin/env python

import telnetlib
import re


class SmoothieConnector:

    def __init__(self, verbose=True, allow_comments=False):
        self._ip = None
        self._allow_comments = allow_comments
        self._verbose = verbose
        self._tn = None

    def connect(self, ip):
        try:
            self._ip = ip
            self._tn = telnetlib.Telnet(self._ip)
            # read Smoothie startup prompt
            self._tn.read_until("Smoothie command shell".encode('ascii'))
            return True
        except KeyboardInterrupt:
            exit()
        except Exception as ex:
            if self._verbose:
                print(type(ex))
                print(ex.args)
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
        except Exception as ex:
            if self._verbose:
                print(type(ex))
                print(ex.args)
            return False

    def send(self, command: str):
        try:
            if not self._allow_comments:
                command = re.sub("[ ]*;.*", '', command)  # remove everything after ;
                command = command.strip()  # send only the bare necessity

            if len(command) > 0:
                if self._verbose:
                    print("Streaming g-code to " + self._ip)

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
        except Exception as ex:
            if self._verbose:
                print(type(ex))
                print(ex.args)
            return False


def test_smoothie_connector():
    g_code = "G0 X10 Y5 F200"
    ip = "192.168.1.222"
    sc = SmoothieConnector()
    if sc.connect(ip):
        print("Connection established.")
        if sc.send(g_code):
            print("Code executed successfully.")
    if sc.disconnect():
        print("Connection closed normally.")


if __name__ == "__main__":
    test_smoothie_connector()
