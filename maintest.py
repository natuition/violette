from connectors import PythonConnectorClient
from time import sleep


def main():
    host = "127.0.0.1"
    port = 9090

    pcc = PythonConnectorClient(host, port)
    pcc.connect()

    for i in range(5):
        pcc.send("G0 X5 Y5 F100")
        print(pcc.receive())
        sleep(1)

    print("Done.")


if __name__ == "__main__":
    main()
