from flask import Flask, render_template
from flask_socketio import SocketIO
from connectors import SmoothieConnector
from multiprocessing import Value

# global constants
# DO NOT CHANGE MIN AND MAX LIMITATIONS!
X_MIN = 0
X_MAX = 198
Y_MIN = 0
Y_MAX = 79
Z_MIN = 0
Z_MAX = 52
F_MIN = 1
F_MAX = 100
NOT_SENT_MSG = "g-code wasn't sent to smoothie."

SMOOTHIE_HOST = "192.168.1.222"
WEB_SERV_PORT = 8080
WEB_SERV_HOST = "192.168.8.100"  # for testing using smoothie
#WEB_SERV_HOST = "127.0.0.1"  # for local testing

x_current = Value('i', 0)
y_current = Value('i', 0)
z_current = Value('i', 0)

smc = SmoothieConnector(SMOOTHIE_HOST, True)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socket_io = SocketIO(app)


def read_until_contains(pattern):
    while True:
        response = smc.receive()
        if pattern in response:
            return response


def read_until_not(value):
    while True:
        response = smc.receive()
        if response != value:
            return response


def switch_to_relative():
    smc.send("G91")
    return read_until_not(">")


def move_until_stopper(axis: str, direction: int):
    # send move command on X axis
    smc.send("G0 {0}{1} F100".format(axis, direction))
    # wait until stopper hit
    read_until_contains("M999")
    # halt state needs M999 command to renew working state
    smc.send("M999")
    read_until_contains("ok")


def corkscrew_to_start_pos():
    # move to X axis stopper and wait for ok
    print("Moving to X axis stopper...")
    move_until_stopper("X", -1000)
    print("Ok")

    # move to Y axis stopper and wait for ok
    print("Moving to Y axis stopper...")
    move_until_stopper("Y", 1000)
    print("Ok")

    # move to Z axis stopper and wait for ok
    '''
    print("Moving to Z axis stopper...")
    move_until_stopper("Z", 1000)
    print("Ok")
    
    z_current.value = Z_MAX
    smc.send("G92 Z{0}".format(z_current.value))
    read_until_contains("ok")
    '''
    x_current.value = X_MIN
    y_current.value = Y_MAX
    smc.send("G92 X{0} Y{1}".format(x_current.value, y_current.value))
    read_until_contains("ok")


def send_response(msg):
    print(msg)
    socket_io.emit('response', msg)


def cur_coords_str():
    return "current coordinates: X: {0}, Y: {1}, Z: {2}".format(x_current.value, y_current.value, z_current.value)


@app.route('/')
def sessions():
    return render_template('interface.html')


@socket_io.on('command')
def on_command(params, methods=['GET', 'POST']):
    g_code = "G0 "

    # check and add X key (x axis)
    if "X" in params:
        x = params["X"]
        if x is None or x == "None":
            send_response("X key is present but value is None, " + NOT_SENT_MSG)
            return
        if x_current.value + x >= X_MAX:
            send_response("Corkscrew will go beyond the right border (X_MAX), " + cur_coords_str() + ", " + NOT_SENT_MSG)
            return
        if x_current.value + x <= X_MIN:
            send_response("Corkscrew will go beyond the left border (X_MIN), " + cur_coords_str() + ", " + NOT_SENT_MSG)
            return

        with x_current.get_lock():
            x_current.value += x
        g_code += "X" + str(x) + " "

    # check and add Y key (y axis)
    if "Y" in params:
        y = params["Y"]
        if y is None or y == "None":
            send_response("Y key is present but value is None, " + NOT_SENT_MSG)
            return
        if y_current.value + y >= Y_MAX:
            send_response("Corkscrew will go beyond the front border (Y_MAX), " + cur_coords_str() + ", " + NOT_SENT_MSG)
            return
        if y_current.value + y <= Y_MIN:
            send_response("Corkscrew will go beyond the back border (Y_MIN), " + cur_coords_str() + ", " + NOT_SENT_MSG)
            return

        with y_current.get_lock():
            y_current.value += y
        g_code += "Y" + str(y) + " "

    # check and add Z key (z axis)
    if "Z" in params:
        z = params["Z"]
        if z is None or z == "None":
            send_response("Z key is present but value is None, " + NOT_SENT_MSG)
            return
        if z_current.value + z >= Z_MAX:
            send_response("Corkscrew will go beyond the upper border (Z_MAX), " + cur_coords_str() + ", " + NOT_SENT_MSG)
            return
        if z_current.value + z <= Z_MIN:
            send_response("Corkscrew will go beyond the down border (Z_MIN), " + cur_coords_str() + ", " + NOT_SENT_MSG)
            return

        with z_current.get_lock():
            z_current.value += z
        g_code += "Z" + str(z) + " "

    # check and add F key (force)
    if "F" in params:
        f = params["F"]
        if f is None or f == "None":
            send_response("F key is present but value is None, " + NOT_SENT_MSG)
            return
        if f > F_MAX:
            send_response("Force value is too big ({0} max), ".format(F_MAX) + NOT_SENT_MSG)
            return
        if f < F_MIN:
            send_response("Force value is too low ({0} min), ".format(F_MIN) + NOT_SENT_MSG)
            return
        g_code += "F" + str(f)
    else:
        send_response("F key is missed, " + NOT_SENT_MSG)
        return

    print("Converted to g-code: " + g_code + ", sending...")

    # stub for testing without real smoothie connection
    #response = "ok (USING STUB INSTEAD OF SMOOTHIE CONNECTION)"  # COMMENT IF USING SMOOTHIE

    # UNCOMMENT THAT BLOCK IF YOU USING SMOOTHIE
    #"""
    smc.send(g_code)
    while True:
        response = smc.receive()
        if response != ">":
            break
    #"""

    send_response(g_code + ": " + response + ", " + cur_coords_str())


def main():
    print("Connecting to smoothie...")
    smc.connect()
    switch_to_relative()

    # KEEP THIS BLOCKS COMMENTED IF STOPPERS ARE NOT INSTALLED AND ENABLED, OR ENGINES MAY CRASH!
    '''
    move_corkscrew_to_start()
    '''

    socket_io.run(app, debug=True, host=WEB_SERV_HOST, port=WEB_SERV_PORT)

    print("Disconnecting from smoothie...")
    # UNCOMMENT IF USING SMOOTHIE
    smc.disconnect()
    print("Done.")


if __name__ == '__main__':
    main()
