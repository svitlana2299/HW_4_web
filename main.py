from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO
from datetime import datetime
import json
import os
import threading
import socket


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
socketio = SocketIO(app)

messages = {}
lock = threading.Lock()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/message', methods=['GET', 'POST'])
def message():
    if request.method == 'POST':
        username = request.form['username']
        message = request.form['message']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        messages[timestamp] = {'username': username, 'message': message}

        # Відправити дані на Socket сервер
        send_to_socket_server(messages[timestamp])

        return redirect(url_for('message'))

    return render_template('message.html', messages=messages)


@app.route('/error')
def error():
    return render_template('error.html')


@socketio.on('connect', namespace='/socket')
def socket_connect():
    for timestamp, message in messages.items():
        socketio.emit('new_message', {
            'timestamp': timestamp, 'username': message['username'], 'message': message['message']
        }, namespace='/socket')


@socketio.on('disconnect', namespace='/socket')
def socket_disconnect():
    pass


def send_to_socket_server(message):
    server_address = ('localhost', 5000)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(json.dumps(message).encode(), server_address)


def save_messages_to_json():
    storage_dir = os.path.join(app.root_path, 'storage')
    os.makedirs(storage_dir, exist_ok=True)
    json_path = os.path.join(storage_dir, 'data.json')
    with lock:
        with open(json_path, 'w') as json_file:
            json.dump(messages, json_file, indent=2)


if __name__ == '__main__':
    def background_thread():
        while True:
            socketio.sleep(10)
            save_messages_to_json()

    socketio.start_background_task(background_thread)
    socketio.run(app, port=3000)
