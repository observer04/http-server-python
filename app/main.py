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
        print(f"Connection from {ret_addr} has been established.")
        response = (
            "HTTP/1.1 200 OK\r\n"
            "\r\n"
            
        )
        c_socket.sendall(response.encode())
        c_socket.close()
        

if __name__ == "__main__":
    main()
