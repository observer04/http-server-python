import socket
from urllib import response  # noqa: F401


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    
    while True:
        c_socket, ret_addr= server_socket.accept() # wait for client
        #read request from socket , parse it and respond
        request = c_socket.recv(1024).decode()      #read first part of encoded http request
        request_lines = request.splitlines()
        first_request_line = request_lines[0]
        method, path, _ = first_request_line.split()
        
        user_agent = ""
        #extract User-Agent Header:
        for line in request_lines[1:]:
            if line.lower().startswith('user-agent'):
                user_agent= line.split(":", maxsplit=1)[1].strip()
                break
        
        
        if path == "/":
            response = (
                "HTTP/1.1 200 OK\r\n"
                "\r\n"
            )
        elif path.startswith('/echo/'):
            echo_idx= len('/echo/')
            echo_value= path[echo_idx:]
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                f"Content-Length: {len(echo_value)}\r\n"
                "\r\n"
                f"{echo_value}"
            )
        elif path == '/user-agent':
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                f"Content-Length: {len(user_agent)}\r\n"
                "\r\n"
                f"{user_agent}"
            )
        
        
        else:
            response = (
                "HTTP/1.1 404 Not Found\r\n"
                "\r\n"
            )
        
        
        
            
        
        c_socket.sendall(response.encode())
        c_socket.close()
        

if __name__ == "__main__":
    main()
