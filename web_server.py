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

sm_host = "192.168.1.222"
web_port = 8080
web_host = "192.168.8.100"  # for testing using smoothie
#web_host = "127.0.0.1"  # for local testing

x_current = Value('i', 0)
y_current = Value('i', 0)
z_current = Value('i', 0)

# UNCOMMENT THIS SECTION IF USING SMOOTHIE
#"""
print("Connecting to smoothie...")
smc = SmoothieConnector(sm_host, True)
smc.connect()

# switch smoothie to relative coords mode
print("Switching to relative mode...")
smc.send("G91")
while True:
    response = smc.receive()
    if response != ">":
        print(response)
        break
#"""


# KEEP THIS BLOCKS COMMENTED IF STOPPERS ARE NOT INSTALLED AND ENABLED, OR ENGINES MAY CRASH!
"""
# move to X axis stopper
print("Moving to X axis stopper...")
smc.send("G0 X-1000 F100")
# wait until stopper hit
while True:
    response = smc.receive()
    if response.count("M999") > 0:
        print("X axis stopper hit")
        break
# halt state needs M999 command to keep working
smc.send("M999")

# move to Y axis stopper
print("Moving to Y axis stopper...")
smc.send("G0 Y1000 F100")
# wait until stopper hit
while True:
    response = smc.receive()
    if response.count("M999") > 0:
        print("Y axis stopper hit")
        break
# halt state needs M999 command to keep working
smc.send("M999")

# separate block for Z axis while we havent stopper (just in case)
'''
# move to Z axis stopper (HOPING THAT STOPPER INSTALLET ON THE "TOP" OF AXIS WHERE'S Z_MAX VALUE)
print("Moving to Z axis stopper...")
smc.send("G0 Z1000 F100")
# wait until stopper hit
while True:
    response = smc.receive()
    if response.count("M999") > 0:
        print("Z axis stopper hit")
        break
# halt state needs M999 command to keep working
smc.send("M999")

# set Z axis current coordinates
z_current = Value('i', Z_MAX)
smc.send("G92 Z{0}".format(z_current.value))
'''

x_current = Value('i', X_MIN)
y_current = Value('i', Y_MAX)
smc.send("G92 X{0} Y{1}".format(x_current.value, y_current.value))
"""


app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socketio = SocketIO(app)


def set_home(smc: SmoothieConnector):
    pass


def send_response(msg):
    print(msg)
    socketio.emit('response', msg)


def cur_coords_str():
    global x_current, y_current, z_current
    return "current coordinates: X: {0}, Y: {1}, Z: {2}".format(x_current.value, y_current.value, z_current.value)


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

    print("Got answer: " + response + ", " + cur_coords_str())
    socketio.emit('response', g_code + ": " + response + ", " + cur_coords_str())


if __name__ == '__main__':
    socketio.run(app, debug=True, host=web_host, port=web_port)
    print("Disconnecting from smoothie...")

    # UNCOMMENT IF USING SMOOTHIE
    smc.disconnect()

    print("Done.")
