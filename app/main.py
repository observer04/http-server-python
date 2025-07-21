import asyncio
from genericpath import isfile
import sys
import os


#get dir from sys.argv
directory = None
for i, arg in enumerate(sys.argv):
    if arg == "--directory" and i + 1 < len(sys.argv):
        directory = sys.argv[i+1]


async def handle_request(reader, writer):
    try:
        request = (await reader.read(1024)).decode()
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
            elif path.startswith('/files') and directory:
                filename_idx = len("/files/")
                filename = path[filename_idx:]
                file_path = os.path.join(directory, filename)
                
                if method=='POST':
                    content_length=0
                    for line in request_lines[1:]:
                        if line.lower().startswith("conten-length:"):
                            content_length =  int(line.split(':', 1).strip())
                            break
                
                    #read the body after headers:
                    headers_end = request.find('\r\n\r\n')
                    body= request[headers_end +4 : ].encode()
                    
                    #if not all bytes read from body, read rest > then write to local file
                    if len(body) < content_length:
                        body += await reader.read(content_length - len(body))
                    
                    with open(file_path, 'wb') as f:
                        f.write(body)
                
                    response = "HTTP/1.1 201 Created\r\n\r\n"
                
                # respond file content if valid path else 404
                elif os.path.isfile(file_path):
                    with open(file_path, 'rb') as f:
                        file_content= f.read()

                    response = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: application/octet-stream\r\n"
                        f"Content-Length: {len(file_content)}\r\n"
                        "\r\n"
                    )
                    writer.write(response.encode() + file_content)
                    await writer.drain()
                    writer.close()
                    await writer.wait_closed()
                    return
                else:
                    response= "HTTP/1.1 404 Not Found\r\n\r\n"
            
            else:
                response = "HTTP/1.1 404 Not Found\r\n\r\n"
        writer.write(response.encode())
        await writer.drain()
    except Exception:
        writer.write(b"HTTP/1.1 404 Bad Request\r\n\r\n")
        await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


async def main():
    print("Logs from your program will appear here!")
    server= await asyncio.start_server(handle_request, 'localhost', 4221)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main=main())
