import asyncio
import sys
import os
import gzip
import zlib
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


# --- Data Classes for Request and Response ---

@dataclass
class Request:
    """Represents an HTTP request, parsed from a client connection."""
    method: str
    path: str
    version: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: bytes = b""

    @classmethod
    async def from_reader(cls, reader: asyncio.StreamReader) -> Optional["Request"]:
        """Reads from the stream and parses the request."""
        request_line_bytes = await reader.readline()
        if not request_line_bytes:
            return None
        
        request_line = request_line_bytes.decode().strip()
        method, path, version = request_line.split()

        headers = {}
        while True:
            line_bytes = await reader.readline()
            line = line_bytes.decode().strip()
            if not line:
                break
            key, value = line.split(":", 1)
            headers[key.lower()] = value.strip()

        body = b""
        if "content-length" in headers:
            content_length = int(headers["content-length"])
            body = await reader.readexactly(content_length)

        return cls(method, path, version, headers, body)

@dataclass
class Response:
    """Represents an HTTP response to be sent to a client."""
    status_code: int
    status_message: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: bytes = b""

    def to_bytes(self) -> bytes:
        """Constructs the full raw HTTP response."""
        response_line = f"HTTP/1.1 {self.status_code} {self.status_message}\r\n"
        headers_str = "".join(f"{k}: {v}\r\n" for k, v in self.headers.items())
        return response_line.encode() + headers_str.encode() + b"\r\n" + self.body

# --- HTTP Server with Routing ---

class HTTPServer:
    """A simple, asynchronous HTTP server with routing."""
    def __init__(self, host: str = "localhost", port: int = 4221, directory: Optional[str] = None):
        self.host = host
        self.port = port
        self.directory = directory

    async def start(self):
        """Starts the asyncio server."""
        server = await asyncio.start_server(self._handle_connection, self.host, self.port)
        print(f"Logs from your program will appear here!")
        print(f"Server started on {self.host}:{self.port}")
        async with server:
            await server.serve_forever()

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handles a single client connection, potentially with multiple requests."""
        try:
            while True:
                request = await Request.from_reader(reader)
                if not request:
                    break

                response = await self._route_request(request)
                
                # Handle content encoding based on client's Accept-Encoding header
                accept_encoding = request.headers.get("accept-encoding", "")
                body, encoding = self._encode_body(response.body, accept_encoding)
                response.body = body
                if encoding:
                    response.headers["Content-Encoding"] = encoding
                response.headers["Content-Length"] = str(len(response.body))

                # Handle persistent connections (HTTP/1.1 keep-alive)
                connection_header = request.headers.get("connection", "keep-alive")
                if connection_header.lower() == "close":
                    response.headers["Connection"] = "close"

                writer.write(response.to_bytes())
                await writer.drain()

                if connection_header.lower() == "close":
                    break
        except (ConnectionResetError, asyncio.IncompleteReadError):
            # Client closed the connection unexpectedly
            pass
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def _route_request(self, request: Request) -> Response:
        """Routes the request to the appropriate handler based on path and method."""
        if request.path == "/":
            return self.handle_root(request)
        elif request.path.startswith("/echo/"):
            return self.handle_echo(request)
        elif request.path == "/user-agent":
            return self.handle_user_agent(request)
        elif request.path.startswith("/files/"):
            if request.method == "GET":
                return self.handle_get_file(request)
            elif request.method == "POST":
                return self.handle_post_file(request)
        
        return Response(404, "Not Found")

    def _encode_body(self, body: bytes, accept_encoding: str) -> Tuple[bytes, Optional[str]]:
        """Compresses the response body if the client supports it."""
        encodings = [e.strip() for e in accept_encoding.split(",")]
        if "gzip" in encodings:
            return gzip.compress(body), "gzip"
        if "deflate" in encodings:
            return zlib.compress(body), "deflate"
        return body, None

    # --- Route Handlers ---

    def handle_root(self, request: Request) -> Response:
        """Handles requests to the root path."""
        return Response(200, "OK")

    def handle_echo(self, request: Request) -> Response:
        """Handles /echo/{str} requests."""
        echo_str = request.path.split("/echo/", 1)[1]
        return Response(200, "OK", {"Content-Type": "text/plain"}, echo_str.encode())

    def handle_user_agent(self, request: Request) -> Response:
        """Handles /user-agent requests."""
        user_agent = request.headers.get("user-agent", "")
        return Response(200, "OK", {"Content-Type": "text/plain"}, user_agent.encode())

    def handle_get_file(self, request: Request) -> Response:
        """Handles GET /files/{filename} requests."""
        if not self.directory:
            return Response(404, "Not Found")
        
        filename = request.path.split("/files/", 1)[1]
        file_path = os.path.join(self.directory, filename)

        if os.path.isfile(file_path):
            with open(file_path, "rb") as f:
                content = f.read()
            return Response(200, "OK", {"Content-Type": "application/octet-stream"}, content)
        else:
            return Response(404, "Not Found")

    def handle_post_file(self, request: Request) -> Response:
        """Handles POST /files/{filename} requests."""
        if not self.directory:
            return Response(404, "Not Found")
            
        filename = request.path.split("/files/", 1)[1]
        file_path = os.path.join(self.directory, filename)

        with open(file_path, "wb") as f:
            f.write(request.body)
        
        return Response(201, "Created")

# --- Main Execution ---

def main():
    """Parses command-line arguments and starts the server."""
    directory = None
    if "--directory" in sys.argv:
        try:
            directory_index = sys.argv.index("--directory") + 1
            directory = sys.argv[directory_index]
        except (ValueError, IndexError):
            print("Usage: ./your_program.sh --directory <directory_path>")
            sys.exit(1)

    server = HTTPServer(port=4221, directory=directory)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nServer shutting down.")

if __name__ == "__main__":
    main()
