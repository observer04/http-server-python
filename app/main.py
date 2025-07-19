import threading
import socket


def handle_request(client_socket):
    try:
        request = client_socket.recv(1024).decode()
        request_lines = request.splitlines()
        if not request_lines or len(request_lines[0].split()) < 3:
            response = "HTTP/1.1 400 Bad Request\r\n\r\n"
        else:
            method, path, _ = request_lines[0].split()
            user_agent = ""
            for line in request_lines[1:]:
                if line.lower().startswith('user-agent'):
                    user_agent = line.split(":", maxsplit=1)[1].strip()
                    break

            if path == "/":
                response = "HTTP/1.1 200 OK\r\n\r\n"
            elif path.startswith("/echo/"):
                echo_value = path[len("/echo/"):]
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/plain\r\n"
                    f"Content-Length: {len(echo_value)}\r\n"
                    "\r\n"
                    f"{echo_value}"
                )
            elif path == "/user-agent":
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/plain\r\n"
                    f"Content-Length: {len(user_agent)}\r\n"
                    "\r\n"
                    f"{user_agent}"
                )
            else:
                response = "HTTP/1.1 404 Not Found\r\n\r\n"
        client_socket.sendall(response.encode())
    except Exception:
        client_socket.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
    finally:
        client_socket.close()


def main():
    print("Logs from your program will appear here!")
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        client_socket, _ = server_socket.accept()
        threading.Thread(target=handle_request, args=(client_socket,)).start()


if __name__ == "__main__":
    main()
