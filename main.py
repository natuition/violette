from connectors import SmoothieConnector, PythonConnectorServer
import traceback


def main():
    sm_host = "192.168.1.222"
    
    pcc_host = "127.0.0.1"
    pcc_port = 9090

    sc = SmoothieConnector(sm_host, verbose=True)

    print("Connecting to smoothie...")
    sc.connect()
    print("Connected.")

    print("Waiting for connection...")
    pcs = PythonConnectorServer(pcc_host, pcc_port)
    pcs.wait_connection()
    print("Connection established.")

    while True:
        print("Waiting for incoming data...")
        rec_data = pcs.receive()

        if rec_data:
            print("Sending g-code to smoothie: " + rec_data)
            sc.send(rec_data)
            sm_resp = None
            while True:
                sm_resp = sc.receive()
                if sm_resp != ">".encode("ascii"):
                    break

            print("Sending response from smoothie: " + sm_resp)
            pcs.send(sm_resp)
        else:
            print("Connection was closed from web server.")
            sc.disconnect()
            break

    print("Done.")


if __name__ == "__main__":
    main()
