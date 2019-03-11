from flask import Flask, render_template
from flask_socketio import SocketIO
from connectors import PythonConnectorClient

pcc_host = "127.0.0.1"
pcc_port = 9090

web_host = "192.168.8.101"
web_port = 8080

pcc = PythonConnectorClient(pcc_host, pcc_port)
pcc.connect()

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
        print("Sending g-code...")
        pcc.send(s)
        print("Waiting for answer...")
        response = pcc.receive()
        print("Got answer: " + response)
        socketio.emit('my response', response, callback=messageReceived)


if __name__ == '__main__':
    socketio.run(app, debug=True, host=web_host, port=web_port)
    pcc.disconnect()
