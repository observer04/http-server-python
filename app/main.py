import asyncio
from genericpath import isfile
import sys
import os
import gzip, zlib


#get dir from sys.argv
directory = None
for i, arg in enumerate(sys.argv):
    if arg == "--directory" and i + 1 < len(sys.argv):
        directory = sys.argv[i+1]


async def handle_request(reader, writer):
    try:
        while True:
            request = (await reader.read(1024)).decode()
            if not request:
                break
            request_lines = request.splitlines()
            
            if not request_lines or len(request_lines[0].split()) < 3:
                response = "HTTP/1.1 400 Bad Request\r\n\r\n"
            else:
                method, path, _ = request_lines[0].split()
                
                #extract required headers from request
                user_agent = ""
                encodings= []
                connection_close = False
                
                for line in request_lines[1:]:
                    if line.lower().startswith('user-agent'):
                        user_agent = line.split(":", maxsplit=1)[1].strip()
                        
                    elif line.lower().startswith('accept-encoding'):
                        accept_encoding= line.split(":", maxsplit=1)[1].strip()
                        encodings=[e.strip() for e in accept_encoding.split(',')] if accept_encoding else []
                    elif line.lower().startswith('connection:'):
                        if 'close' in line.lower():
                            connection_close = True
                        
                        
                #if encoding is accepted for response body
                def maybe_encode(data: bytes) -> tuple:
                    if 'gzip' in encodings:
                        encoded = gzip.compress(data)
                        return encoded, 'gzip'
                    elif 'deflate' in encodings:
                        encoded = zlib.compress(data)
                        return encoded, 'deflate'
                    return data, None
                

                #handle path navigation by request
                
                if path == "/":
                    response = "HTTP/1.1 200 OK\r\n\r\n"
                
                #get request for string sent
                elif path.startswith("/echo/"):
                    echo_value = path[len("/echo/"):]
                    body_bytes, encoding = maybe_encode(echo_value.encode())
                    response = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: text/plain\r\n"
                        f"Content-Length: {len(body_bytes)}\r\n"
                    )
                    
                    if encoding:
                        response += f"Content-Encoding: {encoding}\r\n"
                    response+= '\r\n'
                    
                    writer.write(response.encode()+ body_bytes)
                    await writer.drain()
                    continue
                    
                
                #echo user-agent
                elif path == "/user-agent":
                    response = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: text/plain\r\n"
                        f"Content-Length: {len(user_agent)}\r\n"
                        "\r\n"
                        f"{user_agent}"
                    )
                    
                #post and get request for files path
                elif path.startswith('/files') and directory:
                    filename_idx = len("/files/")
                    filename = path[filename_idx:]
                    file_path = os.path.join(directory, filename)
                    
                    #if post request read stream and write to local.
                    if method=='POST':
                        content_length=0
                        for line in request_lines[1:]:
                            if line.lower().startswith("content-length:"):
                                content_length =  int(line.split(':', 1)[1].strip())
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
                        continue
                    
                    else:
                        response= "HTTP/1.1 404 Not Found\r\n\r\n"
                
                else:
                    response = "HTTP/1.1 404 Not Found\r\n\r\n"
            writer.write(response.encode())
            await writer.drain()
            if connection_close:
                break
    except Exception:
        writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")
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
