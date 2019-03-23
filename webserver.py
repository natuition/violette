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


def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')


@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    s = str('G0 X' + str(json.get('X')) + ' Y' + str(json.get('Y')) + ' F100')
    print("Got from HTML: " + s)

    if str(json.get('Y')) != 'None' and str(json.get('Y')):
        """
        print("Sending g-code...")
        response = smc.send_recv(s)
        print("Got answer: " + response)
        """
        response = "ok"
        socketio.emit('my response', s + ": " + response, callback=messageReceived)


if __name__ == '__main__':
    socketio.run(app, debug=True, host=web_host, port=web_port)
    # smc.disconnect()
