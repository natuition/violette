from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
from connectors import SmoothieConnector
from multiprocessing import Value
import json
import os
import traceback

CONFIG_GLOBAL_PATH = "config/config_global.json"
CONFIG_LOCAL_PATH = "config/config_local.json"

# load configuration from config files
with open(CONFIG_GLOBAL_PATH, "r") as file:
    config_global = json.loads(file.read())
with open(CONFIG_LOCAL_PATH, "r") as file:
    config_local = json.loads(file.read())

NOT_SENT_MSG = "g-code wasn't sent to smoothie."
SIMULATING_SMOOTHIE_MSG = "ok (SIMULATING SMOOTHIE CONNECTION!)"

x_current = Value('i', 0)
y_current = Value('i', 0)
z_current = Value('i', 0)

smc = SmoothieConnector(config_local["SMOOTHIE_HOST"], True)
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


def calibrate_axis(axis_current: Value, axis_label, axis_min_key, axis_max_key):
    distanse = 1000
    with axis_current.get_lock():
        if config_local["{0}_AXIS_CALIBRATION_TO_MAX".format(axis_label)]:
            smc.send("G28 {0}{1}".format(axis_label, distanse))
            read_until_contains("ok")
            axis_current.value = config_local[axis_max_key] - config_local["AFTER_CALIBRATION_AXIS_OFFSET"]
        else:
            smc.send("G28 {0}{1}".format(axis_label, -distanse))
            read_until_contains("ok")
            axis_current.value = config_local[axis_min_key] + config_local["AFTER_CALIBRATION_AXIS_OFFSET"]

        # set fresh current coordinates on smoothie too
        smc.send("G92 {0}{1}".format(axis_label, axis_current.value))
        read_until_contains("ok")


def corkscrew_to_start_pos():
    # X axis calibration
    if config_local["USE_X_AXIS_CALIBRATION"]:
        print("X axis calibration...", end=" ")
        calibrate_axis(x_current, "X", "X_MIN", "X_MAX")
        print("Ok")

    # Y axis calibration
    if config_local["USE_Y_AXIS_CALIBRATION"]:
        print("Y axis calibration...", end=" ")
        calibrate_axis(y_current, "Y", "Y_MIN", "Y_MAX")
        print("Ok")

    # Z axis calibration
    if config_local["USE_Z_AXIS_CALIBRATION"]:
        print("Z axis calibration...", end=" ")
        calibrate_axis(z_current, "Z", "Z_MIN", "Z_MAX")
        print("Ok")


def send_response(params):
    add_cur_coords_to(params)
    print(params)
    socket_io.emit('response', params)


def add_cur_coords_to(params: dict):
    """This function takes response_params dict, and adds to that dict X Y Z current values by that keys"""
    params["X"], params["Y"], params["Z"] = x_current.value, y_current.value, z_current.value


def validate_moving_key(params, key_name, key_min, key_max, current_value):
    """For F current_value must be 0"""

    if params[key_name] is None or params[key_name] == "None":
        return "{0} key is present but value is None, ".format(key_name) + NOT_SENT_MSG
    if current_value + params[key_name] > key_max:
        return "Command with {0}{1} goes beyond max acceptable range of {0}_MAX = {2}, " \
                   .format(key_name, params[key_name], key_max) + NOT_SENT_MSG
    if current_value + params[key_name] < key_min:
        return "Command with {0}{1} goes beyond min acceptable range of {0}_MIN = {2}, " \
                   .format(key_name, params[key_name], key_min) + NOT_SENT_MSG
    return None


# BUTTONS HANDLERS
def extraction_move_cmd_handler(params):
    # by this key command handler stored in backend, and response handler stored in frontend
    handler_key = "extraction-move"
    response_params = {"response_handler": handler_key, "executed_g_code": "(None)"}

    # F key should be present anyway
    if "F" not in params:
        response_params["error_message"] = "F key is missed, " + NOT_SENT_MSG
        send_response(response_params)
        return
    else:
        error_msg = validate_moving_key(params, "F", config_local["F_MIN"], config_local["F_MAX"], 0)
        if not (error_msg is None):
            response_params["error_message"] = error_msg
            send_response(response_params)
            return

    # at least one of X Y Z keys should be present
    if "X" not in params and "Y" not in params and "Z" not in params:
        response_params["error_message"] = "At least one of X Y Z keys should be present, none found, " + NOT_SENT_MSG
        send_response(response_params)
        return

    g_code = "G0 "

    # check and add X key (x axis)
    if "X" in params:
        error_msg = validate_moving_key(params, "X", config_local["X_MIN"], config_local["X_MAX"], x_current.value)
        if error_msg is None:
            with x_current.get_lock():
                x_current.value += params["X"]
            g_code += "X" + str(params["X"]) + " "
        else:
            response_params["error_message"] = error_msg
            send_response(response_params)
            return

    # check and add Y key (y axis)
    if "Y" in params:
        error_msg = validate_moving_key(params, "Y", config_local["Y_MIN"], config_local["Y_MAX"], y_current.value)
        if error_msg is None:
            with y_current.get_lock():
                y_current.value += params["Y"]
            g_code += "Y" + str(params["Y"]) + " "
        else:
            response_params["error_message"] = error_msg
            send_response(response_params)
            return

    # check and add Z key (z axis)
    if "Z" in params:
        error_msg = validate_moving_key(params, "Z", config_local["Z_MIN"], config_local["Z_MAX"], z_current.value)
        if error_msg is None:
            with z_current.get_lock():
                z_current.value += params["Z"]
            g_code += "Z" + str(params["Z"]) + " "
        else:
            response_params["error_message"] = error_msg
            send_response(response_params)
            return

    g_code += "F" + str(params["F"])
    print("Converted to g-code: " + g_code + ", sending...")

    if not config_local["USE_SMOOTHIE_CONNECTION_SIMULATION"]:
        smc.send(g_code)
        response = read_until_not(">")
    else:
        response = SIMULATING_SMOOTHIE_MSG

    response_params["executed_g_code"] = g_code
    response_params["response_message"] = response
    send_response(response_params)


def set_axis_current_value_cmd_handler(params):
    # by this key command handler stored in backend, and response handler stored in frontend
    handler_key = "set-z-current"
    response_params = {"response_handler": handler_key, "executed_g_code": "(None)"}

    if "z_current" not in params:
        response_params["error_message"] = "Z current key is missing, " + NOT_SENT_MSG
        send_response(response_params)
        return

    if params["z_current"] is None or params["z_current"] == "None" or params["z_current"] == "":
        response_params["error_message"] = "Z key is present but empty or contains None, " + NOT_SENT_MSG
        send_response(response_params)
        return

    g_code = "G92 Z{0}".format(params["z_current"])
    print("Converted to g-code: " + g_code + ", sending...")
    with z_current.get_lock():
        if not config_local["USE_SMOOTHIE_CONNECTION_SIMULATION"]:
            smc.send(g_code)
            response = read_until_contains("ok")
        else:
            response = SIMULATING_SMOOTHIE_MSG
        z_current.value = params["z_current"]

    response_params["executed_g_code"] = g_code
    response_params["response_message"] = response
    send_response(response_params)


def enable_disable_engines_cmd_handler(params):
    # by this key command handler stored in backend, and response handler stored in frontend
    handler_key = "enable_disable_engines"
    response_params = {"response_handler": handler_key, "executed_g_code": "(None)"}

    if "command" not in params:
        response_params["error_message"] = "Command key is missing, " + NOT_SENT_MSG
        send_response(response_params)
        return

    if params["command"] == "enable_engines":
        g_code = "M17"
    elif params["command"] == "disable_engines":
        g_code = "M84"
    else:
        response_params["error_message"] = "Command key is present, but contains invalid value, " + NOT_SENT_MSG
        send_response(response_params)
        return

    if config_local["USE_SMOOTHIE_CONNECTION_SIMULATION"]:
        response = SIMULATING_SMOOTHIE_MSG
    else:
        smc.send(g_code)
        response = read_until_contains("ok")

    response_params["executed_g_code"] = g_code
    response_params["response_message"] = response
    send_response(response_params)


def raw_g_code_cmd_handler(params):
    # by this key command handler stored in backend, and response handler stored in frontend
    handler_key = "raw_g_code"
    response_params = {"response_handler": handler_key, "executed_g_code": "(None)"}

    if "raw_g_code" not in params:
        response_params["error_message"] = "raw_g_code key is missing, " + NOT_SENT_MSG
        send_response(response_params)
        return
    if params["raw_g_code"] == "" or params["raw_g_code"] == "None" or params["raw_g_code"] is None:
        response_params["error_message"] = "raw_g_code key is present, but empty or contains None, " + NOT_SENT_MSG
        send_response(response_params)
        return

    if config_local["USE_SMOOTHIE_CONNECTION_SIMULATION"]:
        response = SIMULATING_SMOOTHIE_MSG
    else:
        smc.send(params["raw_g_code"])
        response = read_until_not(">")

    response_params["executed_g_code"] = params["raw_g_code"]
    response_params["response_message"] = response
    send_response(response_params)


command_handlers["extraction-move"] = extraction_move_cmd_handler
command_handlers["set-z-current"] = set_axis_current_value_cmd_handler
command_handlers["enable_disable_engines"] = enable_disable_engines_cmd_handler
command_handlers["raw_g_code"] = raw_g_code_cmd_handler


# ROUTES
@app.route('/')
def sessions():
    return render_template('interface.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/images'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


# SOCKET IO EVENTS
@socket_io.on('command')
def on_command(params, methods=['GET', 'POST']):
    try:
        command_handlers[params["command_handler"]](params)
    except KeyboardInterrupt:
        exit()
    except Exception:
        print(traceback.format_exc())


def main():
    if not config_local["USE_SMOOTHIE_CONNECTION_SIMULATION"]:
        print("Connecting to smoothie...", end=" ")
        smc.connect()
        switch_to_relative()
        print("Ok")

    corkscrew_to_start_pos()

    socket_io.run(app, debug=True, host=config_local["WEB_SERVER_HOST"], port=config_local["WEB_SERVER_PORT"])

    if not config_local["USE_SMOOTHIE_CONNECTION_SIMULATION"]:
        print("Disconnecting from smoothie...", end=" ")
        smc.disconnect()
        print("Done.")


if __name__ == '__main__':
    main()
