from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import socket
import json
import threading
from datetime import datetime
import RPi.GPIO as GPIO
import time

app = Flask(__name__)
CORS(app)

PORT = 5001
SATELLITE_IP = "192.168.4.3"  # Replace with Pi 3's IP
messages = []

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
GPIO.output(18, GPIO.LOW)

def receive_messages():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("", PORT))
        server.listen()
        print("Sender waiting for messages...")

        while True:
            conn, addr = server.accept()
            try:
                data = conn.recv(1024).decode()
                message = json.loads(data)
                print(f"Emergency Message Received: {message}")
                messages.append({
                    'text': message['text'],
                    'timestamp': message['timestamp'],
                    'type': 'received'
                })

                # Blink GPIO 18 in the requested pattern
                for _ in range(3):  # Repeat for ~600ms
                    GPIO.output(18, GPIO.HIGH)
                    time.sleep(0.1)  # High for 100ms
                    GPIO.output(18, GPIO.LOW)
                    time.sleep(0.05)  # Low for 50ms

            except Exception as e:
                print(f"Error receiving message: {e}")
            finally:
                conn.close()



def send_to_satellite(message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SATELLITE_IP, PORT))
            s.sendall(json.dumps({
                'text': message,
                'timestamp': datetime.now().isoformat(),
                'type': 'sent'
            }).encode())
            return True
    except:
        return False

@app.route('/')
def home():
    return render_template('transceiver.html')

@app.route('/messages')
def get_messages():
    return jsonify({'messages': messages})

@app.route('/send', methods=['POST'])
def send_message():
    data = request.json
    message = data.get('message')
    if message:
        success = send_to_satellite(message)
        if success:
            messages.append({
                'text': message,
                'timestamp': datetime.now().isoformat(),
                'type': 'sent'
            })
            return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 500

if __name__ == "__main__":
    # Start the message receiver in a separate thread
    receiver_thread = threading.Thread(target=receive_messages)
    receiver_thread.daemon = True
    receiver_thread.start()

    # Start the Flask web server
    try:
        app.run(host="0.0.0.0", port=5050)
    finally:
        GPIO.cleanup()