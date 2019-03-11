from connectors import SmoothieConnector, PythonConnectorServer
from threading import Thread, Lock


def start_transmitting(data_list: list, locker: Lock, pcs: PythonConnectorServer):
    sm_host = "192.168.1.222"
    sc = SmoothieConnector(sm_host, verbose=True)

    print("Connecting to smoothie...")
    sc.connect()
    print("Connected.")

    while True:
        if len(data_list) > 0:
            locker.acquire()
            item = data_list.pop(0)
            locker.release()

            if len(item) > 0:
                print("Sending g-code to smoothie: " + item)
                sm_resp = sc.send_recv(item)
                print("Sending response from smoothie: " + sm_resp)
                pcs.send(sm_resp)

    # print("Connection closed normally.")


def main():
    ws_host = "127.0.0.1"
    ws_port = 8081

    g_codes_list = list()
    pcs = PythonConnectorServer(ws_host, ws_port, verbose=True)

    print("Starting threads...")

    lock = Lock()
    t1 = Thread(target=pcs.receive, args=(g_codes_list, lock,), name="Web server connector thread")
    t2 = Thread(target=start_transmitting, args=(g_codes_list, lock, pcs,), name="Smoothie connector thread")

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("Main thread done!")


if __name__ == "__main__":
    main()
