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
#WEB_SERV_HOST = "192.168.8.100"  # for testing using smoothie
WEB_SERV_HOST = "127.0.0.1"  # for local testing

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
    return "current coordinates: X={0} Y={1} Z={2}".format(x_current.value, y_current.value, z_current.value)


def validate_moving_key(params, key_name, key_min, key_max, current_value):
    """For F current_value must be 0"""

    if params[key_name] is None or params[key_name] == "None":
        return "{0} key is present but value is None, ".format(key_name) + NOT_SENT_MSG
    if current_value + params[key_name] >= key_max:
        return "Command with {0}{1} goes beyond max acceptable range of {0}_MAX = {2}, "\
                   .format(key_name, params[key_name], key_max) + cur_coords_str() + ", " + NOT_SENT_MSG
    if current_value + params[key_name] <= key_min:
        return "Command with {0}{1} goes beyond min acceptable range of {0}_MIN = {2}, " \
                   .format(key_name, params[key_name], key_min) + cur_coords_str() + ", " + NOT_SENT_MSG
    return None


@app.route('/')
def sessions():
    return render_template('interface.html')


@socket_io.on('command')
def on_command(params, methods=['GET', 'POST']):
    g_code = "G0 "

    # check and add X key (x axis)
    if "X" in params:
        error_msg = validate_moving_key(params, "X", X_MIN, X_MAX, x_current.value)
        if error_msg is None:
            x = params["X"]
            with x_current.get_lock():
                x_current.value += x
            g_code += "X" + str(x) + " "
        else:
            send_response(error_msg)
            return

    # check and add Y key (y axis)
    if "Y" in params:
        error_msg = validate_moving_key(params, "Y", Y_MIN, Y_MAX, y_current.value)
        if error_msg is None:
            y = params["Y"]
            with y_current.get_lock():
                y_current.value += y
            g_code += "Y" + str(y) + " "
        else:
            send_response(error_msg)
            return

    # check and add Z key (z axis)
    if "Z" in params:
        error_msg = validate_moving_key(params, "Z", Z_MIN, Z_MAX, z_current.value)
        if error_msg is None:
            z = params["Z"]
            with z_current.get_lock():
                z_current.value += z
            g_code += "Z" + str(z) + " "
        else:
            send_response(error_msg)
            return

    # check and add F key (force)
    if "F" in params:
        error_msg = validate_moving_key(params, "F", F_MIN, F_MAX, 0)
        if error_msg is None:
            g_code += "F" + str(params["F"])
        else:
            send_response(error_msg)
            return

    print("Converted to g-code: " + g_code + ", sending...")

    # stub for testing without real smoothie connection
    response = "ok (USING STUB INSTEAD OF SMOOTHIE CONNECTION)"  # COMMENT IF USING SMOOTHIE

    # UNCOMMENT THAT BLOCK IF YOU USING SMOOTHIE
    """
    smc.send(g_code)
    while True:
        response = smc.receive()
        if response != ">":
            break
    """

    send_response(g_code + ": " + response + ", " + cur_coords_str())


def main():
    # UNCOMMENT THIS BLOCK
    '''
    print("Connecting to smoothie...")
    smc.connect()
    switch_to_relative()
    '''

    # UNCOMMENT THIS BLOCK ONLY (!) IF STOPPERS ARE INSTALLED AND ENABLED, OR ENGINES MAY CRASH!
    '''
    move_corkscrew_to_start()
    '''

    socket_io.run(app, debug=True, host=WEB_SERV_HOST, port=WEB_SERV_PORT)

    # UNCOMMENT THIS BLOCK IF USING SMOOTHIE
    '''
    print("Disconnecting from smoothie...")
    smc.disconnect()
    print("Done.")
    '''


if __name__ == '__main__':
    main()
