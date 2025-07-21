import asyncio
import sys
import os
import gzip, zlib


# Get directory from sys.argv
directory = None
for i, arg in enumerate(sys.argv):
    if arg == "--directory" and i + 1 < len(sys.argv):
        directory = sys.argv[i+1]


async def handle_request(reader, writer):
    try:
        # Persistent connection: handle multiple requests per connection
        while True:
            request = (await reader.read(1024)).decode()
            if not request:
                break
            request_lines = request.splitlines()
            # Defensive: always check request line format
            if not request_lines or len(request_lines[0].split()) < 3:
                response = "HTTP/1.1 400 Bad Request\r\n\r\n"
                body_bytes = b""
                writer.write(response.encode())
                await writer.drain()
                break
            else:
                method, path, _ = request_lines[0].split()
                user_agent = ""
                encodings = []
                connection_close = False

                # Parse headers for user-agent, accept-encoding, connection
                for line in request_lines[1:]:
                    if line.lower().startswith('user-agent'):
                        user_agent = line.split(":", maxsplit=1)[1].strip()
                    elif line.lower().startswith('accept-encoding'):
                        accept_encoding = line.split(":", maxsplit=1)[1].strip()
                        # Multiple encoding support: parse comma separated
                        encodings = [e.strip() for e in accept_encoding.split(',')] if accept_encoding else []
                    elif line.lower().startswith('connection:'):
                        if 'close' in line.lower():
                            connection_close = True

                # Helper for encoding response body if requested
                def maybe_encode(data: bytes) -> tuple:
                    # Prefer gzip, then deflate, else plain
                    if 'gzip' in encodings:
                        encoded = gzip.compress(data)
                        return encoded, 'gzip'
                    elif 'deflate' in encodings:
                        encoded = zlib.compress(data)
                        return encoded, 'deflate'
                    return data, None

                response = ""
                body_bytes = b""

                # Routing logic for endpoints
                if path == "/":
                    response = "HTTP/1.1 200 OK\r\n\r\n"
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
                    response += '\r\n'
                elif path == "/user-agent":
                    body_bytes, encoding = maybe_encode(user_agent.encode())
                    response = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: text/plain\r\n"
                        f"Content-Length: {len(body_bytes)}\r\n"
                    )
                    if encoding:
                        response += f"Content-Encoding: {encoding}\r\n"
                    response += "\r\n"
                elif path.startswith('/files') and directory:
                    filename_idx = len("/files/")
                    filename = path[filename_idx:]
                    file_path = os.path.join(directory, filename)
                    if method == 'POST':
                        # POST: create file from request body
                        content_length = 0
                        for line in request_lines[1:]:
                            if line.lower().startswith("content-length:"):
                                content_length = int(line.split(':', 1)[1].strip())
                                break
                        headers_end = request.find('\r\n\r\n')
                        body = request[headers_end + 4:].encode()
                        # Read remaining body bytes if not all received
                        if len(body) < content_length:
                            body += await reader.read(content_length - len(body))
                        with open(file_path, 'wb') as f:
                            f.write(body)
                        response = "HTTP/1.1 201 Created\r\n\r\n"
                        body_bytes = b""
                    elif os.path.isfile(file_path):
                        # GET: serve file, support encoding
                        with open(file_path, 'rb') as f:
                            file_content = f.read()
                        body_bytes, encoding = maybe_encode(file_content)
                        response = (
                            "HTTP/1.1 200 OK\r\n"
                            "Content-Type: application/octet-stream\r\n"
                            f"Content-Length: {len(body_bytes)}\r\n"
                        )
                        if encoding:
                            response += f"Content-Encoding: {encoding}\r\n"
                        response += "\r\n"
                    else:
                        response = "HTTP/1.1 404 Not Found\r\n\r\n"
                        body_bytes = b""
                else:
                    response = "HTTP/1.1 404 Not Found\r\n\r\n"
                    body_bytes = b""

            # Persistent connection: add Connection: close header only if needed
            if connection_close:
                header_end = response.find('\r\n\r\n')
                if header_end != -1:
                    response = response[:header_end] + "\r\nConnection: close" + response[header_end:]

            # Send headers and body (never mix binary with string formatting)
            writer.write(response.encode() + body_bytes)
            await writer.drain()
            # If client requested close, break after response
            if connection_close:
                break
    except Exception:
        # Always send Connection: close on error and close the connection
        writer.write(b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n")
        await writer.drain()
    finally:
        # Always close the stream to free resources
        writer.close()
        await writer.wait_closed()


async def main():
    print("Logs from your program will appear here!")
    server = await asyncio.start_server(handle_request, 'localhost', 4221)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
