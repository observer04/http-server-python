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
        request_line = request.splitlines()[0]
        method, path, _ = request_line.split()
        
        
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
        
        
        
        else:
            response = (
                "HTTP/1.1 404 Not Found\r\n"
                "\r\n"
            )
        
        
        
            
        
        c_socket.sendall(response.encode())
        c_socket.close()
        

if __name__ == "__main__":
    main()
