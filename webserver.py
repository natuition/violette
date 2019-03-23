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
    g_code = str('G0 X' + str(params.get('X')) + ' Y' + str(params.get('Y')) + ' F' + str(params.get('F')))
    print("Got from HTML: " + g_code)

    if str(params.get('Y')) != 'None' and str(params.get('Y')):
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
