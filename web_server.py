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
engines_enabled = Value('i', 1)

smc = SmoothieConnector(SMOOTHIE_HOST, True)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socket_io = SocketIO(app)
command_handlers = {}


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
    
    with z_current.get_lock():
        z_current.value = Z_MAX
    smc.send("G92 Z{0}".format(z_current.value))
    read_until_contains("ok")
    '''
    with x_current.get_lock():
        x_current.value = X_MIN
    with y_current.get_lock():
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


# BUTTONS HANDLERS
def extraction_move_cmd_handler(params):
    # F key should be present anyway
    if "F" not in params:
        send_response("F key is missed, " + NOT_SENT_MSG)
        return
    else:
        error_msg = validate_moving_key(params, "F", F_MIN, F_MAX, 0)
        if not (error_msg is None):
            send_response(error_msg)
            return

    # at least one of X Y Z keys should be present
    if "X" not in params and "Y" not in params and "Z" not in params:
        send_response("At least one of X Y Z keys should be present, none found, " + NOT_SENT_MSG)
        return

    g_code = "G0 "

    # check and add X key (x axis)
    if "X" in params:
        error_msg = validate_moving_key(params, "X", X_MIN, X_MAX, x_current.value)
        if error_msg is None:
            with x_current.get_lock():
                x_current.value += params["X"]
            g_code += "X" + str(params["X"]) + " "
        else:
            send_response(error_msg)
            return

    # check and add Y key (y axis)
    if "Y" in params:
        error_msg = validate_moving_key(params, "Y", Y_MIN, Y_MAX, y_current.value)
        if error_msg is None:
            with y_current.get_lock():
                y_current.value += params["Y"]
            g_code += "Y" + str(params["Y"]) + " "
        else:
            send_response(error_msg)
            return

    # check and add Z key (z axis)
    if "Z" in params:
        error_msg = validate_moving_key(params, "Z", Z_MIN, Z_MAX, z_current.value)
        if error_msg is None:
            with z_current.get_lock():
                z_current.value += params["Z"]
            g_code += "Z" + str(params["Z"]) + " "
        else:
            send_response(error_msg)
            return

    g_code += "F" + str(params["F"])
    print("Converted to g-code: " + g_code + ", sending...")

    # COMMENT IF USING SMOOTHIE (stub for testing without real smoothie connection)
    response = "ok (USING STUB INSTEAD OF REAL SMOOTHIE CONNECTION)"

    # UNCOMMENT THAT BLOCK IF YOU USING SMOOTHIE
    """
    smc.send(g_code)
    response = read_until_not(">")
    """

    send_response(g_code + ": " + response + ", " + cur_coords_str())


def start_engines_cmd_handler(params):
    pass


def stop_engines_cmd_handler(params):
    pass


command_handlers["extraction-move"] = extraction_move_cmd_handler


# ROUTES AND CLIENT EVENTS
@app.route('/')
def sessions():
    return render_template('interface.html', engines_enabled=engines_enabled.value)


@socket_io.on('command')
def on_command(params, methods=['GET', 'POST']):
    command_handlers[params["command"]](params)


def main():
    # UNCOMMENT THIS BLOCK IF USING SMOOTHIE
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
