from flask import Flask, render_template
from flask_socketio import SocketIO
from connectors import SmoothieConnector

# constants
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

sm_host = "192.168.1.222"
web_port = 8080
#web_host = "192.168.8.101"
web_host = "127.0.0.1"

#smc = SmoothieConnector(sm_host, True)
#print("Connecting to smoothie...")
#smc.connect()

# TO DO: MOVE CORKSCREW TO STARTING POSITION
#

x_current = 0
y_current = 0
z_current = 0

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socketio = SocketIO(app)


def send_response(msg):
    print(msg)
    socketio.emit('response', msg)


def cur_coords_str():
    global x_current, y_current, z_current
    return "current coordinates: X: {0}, Y: {1}, Z: {2}, ".format(x_current, y_current, z_current)


@app.route('/')
def sessions():
    return render_template('interface.html')


@socketio.on('command')
def on_command(params, methods=['GET', 'POST']):
    g_code = "G0 "

    # check and add X key (x axis)
    if "X" in params:
        x = params["X"]
        if x is None or x == "None":
            send_response("X key is present but value is None, " + NOT_SENT_MSG)
            return
        if x_current + x >= X_MAX:
            send_response("Corkscrew will go beyond the right border (X_MAX), " + cur_coords_str() + NOT_SENT_MSG)
            return
        if x_current + x <= X_MIN:
            send_response("Corkscrew will go beyond the left border (X_MIN), " + cur_coords_str() + NOT_SENT_MSG)
            return
        x_current += x
        g_code += "X" + str(x) + " "

    # check and add Y key (y axis)
    if "Y" in params:
        y = params["Y"]
        if y is None or y == "None":
            send_response("Y key is present but value is None, " + NOT_SENT_MSG)
            return
        if y_current + y >= Y_MAX:
            send_response("Corkscrew will go beyond the front border (Y_MAX), " + cur_coords_str() + NOT_SENT_MSG)
            return
        if y_current + y <= Y_MIN:
            send_response("Corkscrew will go beyond the back border (Y_MIN), " + cur_coords_str() + NOT_SENT_MSG)
            return
        y_current += y
        g_code += "Y" + str(y) + " "

    # check and add Z key (z axis)
    if "Z" in params:
        z = params["Z"]
        if z is None or z == "None":
            send_response("Z key is present but value is None, " + NOT_SENT_MSG)
            return
        if z_current + z >= Z_MAX:
            send_response("Corkscrew will go beyond the upper border (Z_MAX), " + cur_coords_str() + NOT_SENT_MSG)
            return
        if z_current + z <= Z_MIN:
            send_response("Corkscrew will go beyond the down border (Y_MIN), " + cur_coords_str() + NOT_SENT_MSG)
            return
        z_current += z
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

    # stub for testing without smoothie
    response = "ok (USING STUB INSTEAD OF SMOOTHIE CONNECTION)"

    """
    # uncomment that block if you using smoothie
    smc.send(g_code)
    response = None
    while True:
        response = smc.receive()
        if response != ">".encode("ascii"):
            break
    """

    print("Got answer: " + response)
    socketio.emit('response', g_code + ": " + response)


if __name__ == '__main__':
    socketio.run(app, debug=True, host=web_host, port=web_port)
    print("Disconnecting from smoothie...")
    #smc.disconnect()
    print("Done.")
