from flask import Flask, render_template
from flask_socketio import SocketIO
from connectors import PythonConnectorClient as PCC

pcc_host = "127.0.0.1"
pcc_port = 8081
pcc = PCC(pcc_host, pcc_port, verbose=True)
pcc.connect()

web_host = "192.168.8.101"
web_port = 8080

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
    s=str('G0 X'+str(json.get('X')) + ' Y' + str(json.get('Y')) + ' F100')
    print(s)
    if str(json.get('Y')) != 'None' and str(json.get('Y')) :
      socketio.emit('my response', pcc.send_recv(s), callback=messageReceived)
 
      


if __name__ == '__main__':
    socketio.run(app, debug=True, host=web_host, port=web_port)
    pcc.disconnect()
