from flask import Flask, render_template
from flask_socketio import SocketIO
from connectors import SmoothieConnector

sm_host = "192.168.1.222"

# web_host = "192.168.8.101"
web_host = "127.0.0.1"
web_port = 8080

# smc = SmoothieConnector(sm_host, True)
# smc.connect()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socketio = SocketIO(app)


@app.route('/')
def sessions():
    return render_template('test.html')


@socketio.on('command')
def on_command(params, methods=['GET', 'POST']):
    # check if keys missed or data corrupted
    if "X" not in params or "Y" not in params or "F" not in params \
            or params["X"] == "None" or params["Y"] == "None" or params["F"] == "None" \
            or params["F"] <= 0 or (params["X"] == 0 and params["Y"] == 0):
        print("Received unacceptable value(s), g-code wasn't sent to smoothie.")
        socketio.emit('response', "Received unacceptable value(s), g-code wasn't sent to smoothie.")
        return

    # here should be values correcting (i.e. if we got X-shift 100 but max is 10 - we have to change x to 10
    # ...

    g_code = "G0 X" + str(params["X"]) + " Y" + str(params["Y"]) + " F" + str(params["F"])
    print("Got from HTML: ", params["X"], params["Y"], params["F"])
    print("Converted to g-code: " + g_code)

    """
    print("Sending g-code...")
    response = smc.send_recv(g_code)
    print("Got answer: " + response)
    """
    response = "ok"
    socketio.emit('response', g_code + ": " + response)


if __name__ == '__main__':
    socketio.run(app, debug=True, host=web_host, port=web_port)
    # smc.disconnect()
