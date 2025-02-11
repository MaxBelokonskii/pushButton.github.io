class SessionStore:
    def __init__(self):
        self.store = {}

    def get(self, key):
        try:
            return self.store[key]
        except KeyError:
            raise KeyError(f"Key '{key}' not found in store.")

    def set(self, key, value):
        self.store[key] = value


from flask import Flask, render_template, request, session, jsonify
from flask_socketio import SocketIO, emit
import time

app = Flask(__name__)
app.secret_key = 'my-secret-key-is-so-hard'
socketio = SocketIO(app, cors_allowed_origins="*")

session_store = SessionStore()

clicks = []
running = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    role = request.form['role']
    name = request.form['name']
    if role == 'admin':
        session['role'] = 'admin'
    else:
        session['role'] = 'user'
    session['name'] = name
    return jsonify({'status': 'ok'})

@socketio.on('connect')
def connect():
    session['sid'] = request.sid

@socketio.on('start_timer')
def handle_start_timer():
    global running
    if not running:
        running = True
        session_store.set('start_time', int(time.time() * 1000))
        emit('activate_button', broadcast=True)
        emit('timer_started', broadcast=True)

@socketio.on('stop_timer')
def handle_stop_timer():
    global running
    if running:
        running = False
        emit('deactivate_button', broadcast=True)
        emit('timer_stopped', broadcast=True)

@socketio.on('button_click')
def handle_button_click(data):
    global clicks
    if running:
        user_name = data['username']
        clicks.append((user_name))
        
        if session_store.get('start_time'):
            current_time_ms = int(time.time() * 1000) - session_store.get('start_time')
            minutes = int(current_time_ms // 60000)
            seconds = int(current_time_ms % 60000) / 1000
            
            log_entry = f"{user_name} - "
            if minutes < 10:
                log_entry += f"0{minutes}:"
            else:
                log_entry += f"{minutes}:"
                
            if seconds < 10:
                log_entry += f"0{seconds}"
            else:
                log_entry += f"{seconds}"
            
            emit('update_log', {'log': log_entry}, broadcast=True)
        else:
            emit('update_log', {'log': f"{user_name} - Таймер еще не запущен."}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)