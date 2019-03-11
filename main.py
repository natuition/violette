from connectors import SmoothieConnector, PythonConnectorServer
import traceback


def main():
    sm_host = "192.168.1.222"
    ws_host = "127.0.0.1"
    ws_port = 8081

    sc = SmoothieConnector(sm_host, verbose=True)

    print("Connecting to smoothie...")
    sc.connect()
    print("Connected.")

    print("Waiting for connection...")
    pcs = PythonConnectorServer(ws_host, ws_port)
    pcs.wait_connection()
    print("Connection established. Waiting for incoming data...")

    while True:
        rec_data = pcs.receive()

        if rec_data:
            print("Sending g-code to smoothie: " + rec_data)
            sm_resp = sc.send_recv(rec_data)

            print("Sending response from smoothie: " + sm_resp)
            pcs.send(sm_resp)
        else:
            print("Connection was closed from web server.")
            sc.disconnect()
            break

    print("Done.")


if __name__ == "__main__":
    main()
