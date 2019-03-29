from flask import Flask, render_template
from flask_socketio import SocketIO
from connectors import SmoothieConnector

x_current = 0
y_current = 0
x_min = 0
x_max = 10
y_min = 0
y_max = 10
f_max = 100

sm_host = "192.168.1.222"
web_port = 8080
web_host = "192.168.8.101"
#web_host = "127.0.0.1"

smc = SmoothieConnector(sm_host, True)
smc.connect()

# SET HERE SMOOTHIE STARTING POSITION MANUALLY IF NEEDED

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socketio = SocketIO(app)


@app.route('/')
def sessions():
    return render_template('test.html', step_max=x_max, force_max=f_max)


@socketio.on('command')
def on_command(params, methods=['GET', 'POST']):
    # check if keys missed
    if "X" not in params or "Y" not in params or "F" not in params:
        error_msg = "Some keys are missed, g-code wasn't sent to smoothie."
        print(error_msg)
        socketio.emit('response', error_msg)
        return

    x = params["X"]
    y = params["Y"]
    f = params["F"]

    # check if empty data stored
    if x == "None" or y == "None" or f == "None":
        error_msg = "Some keys contain no data, g-code wasn't sent to smoothie."
        print(error_msg)
        socketio.emit('response', error_msg)
        return
    # check for zeros
    if f <= 0 or (x == 0 and y == 0):  # WHAT IF FLOAT ???
        error_msg = "F <= 0, or X and Y == 0 at once, g-code wasn't sent to smoothie."
        print(error_msg)
        socketio.emit('response', error_msg)
        return

    # here should be values correcting (i.e. if we got X-shift 100 but max is 10 - we have to change x to 10
    # ...

    g_code = "G0 X" + str(x) + " Y" + str(y) + " F" + str(f)

    print("Got from HTML: ", params["X"], params["Y"], params["F"])
    print("Converted to g-code: " + g_code)

    print("Sending g-code...")
    response = smc.send_recv(g_code)
    #response = "ok (working in without smoothie connection mode)"
    print("Got answer: " + response)

    # response = "ok"
    socketio.emit('response', g_code + ": " + response)


if __name__ == '__main__':
    socketio.run(app, debug=True, host=web_host, port=web_port)
    smc.disconnect()
