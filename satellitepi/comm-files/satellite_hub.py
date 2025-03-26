import socket
import json
import threading

PORT = 5001
PEER_IPS = ["192.168.4.117", "192.168.4.48"]  # List of all connected Raspberry Pis

def handle_client(conn, addr):
    try:
        data = conn.recv(1024).decode()
        message = json.loads(data)
        print(f"Received message: {message}")

        # Forward message to all peers except the sender
        for ip in PEER_IPS:
            if ip != addr[0]:  # Avoid sending the message back to the sender
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect((ip, PORT))
                        s.sendall(json.dumps(message).encode())
                        print(f"Message forwarded to {ip}.")
                except Exception as e:
                    print(f"Error forwarding to {ip}: {e}")

    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        conn.close()

def satellite_hub():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("", PORT))
        server.listen()
        print("Satellite Hub running...")

        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()

if __name__ == "__main__":
    satellite_hub()