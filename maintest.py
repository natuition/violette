from connectors import PythonConnectorClient as PCC
from time import sleep


def main():
    host = "127.0.0.1"
    port = 8081

    pcc = PCC(host, port, verbose=True)
    pcc.connect()
    for i in range(20):
        pcc.send("G0 X5 Y5 F100")
        print(pcc.receive())
        sleep(1)

    print("Done.")


main()
