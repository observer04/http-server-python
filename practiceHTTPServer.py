import asyncio
from email import header
from fileinput import filename
from operator import truediv
import re
import sys
import os 
import gzip
from urllib import request
import zlib

from dataclasses import Field, dataclass, field
from typing import Dict, Optional, Tuple


# Data classes for request and response


@dataclass
class Request:
   """Represents and http request, parsed from a client connection"""
   method: str
   path: str
   version: str
   headers: Dict[str, str] = field(default_factory=dict)
   body: bytes = b""
   
   
   @classmethod
   async def from_reader(cls, reader: asyncio.StreamReader) -> Optional["Request"] :
      """Reads from the stream and parses the request."""
      request_line_bytes= await reader.readline()
      if not request_line_bytes: 
         return None
      
      request_line = request_line_bytes.decode().strip()
      method, path, version = request_line.split()
      
      #store headers one iteration at a time 
      headers = {}
      while True:
         line_bytes = await reader.readline()
         line = line_bytes.decode().strip()
         if not line:
            break
         k, v = line.split(":", 1)
         headers[k.lower()] = v.strip()
         
      body = b""
      if "content-length" in headers:
         content_length = int(headers["content-length"])
         body = await reader.readexactly(content_length)
         
      return cls(method, path, version, headers, body)
   
@dataclass
class Response:
   """Represents an HTTP response to be sent to a client."""
   status_code : int
   status_message: str
   headers: Dict[str, str] = field(default_factory=dict)
   body: bytes = b""
   
   def to_bytes(self) -> bytes:
      """Constructs the full raw http response."""
      response_line = f"HTTP/1.1 {self.status_code} {self.status_message}\r\n"
      headers_str = "".join(f"{k}: {v}\r\n" for k, v in self.headers.items())
      
      return response_line.encode() + headers_str.encode() + b"\r\n" + self.body
   

###-----Http server with routing-----

class HTTPServer:
   def __init__(self, host: str = "localhost", port: int = 4444, directory: Optional[str] = None) :
      self.host = host
      self.port = port
      self.directory= directory
      
   async def start(self):
      """Starts the asyncio Server."""
      server = await asyncio.start_server(self._handle_connection, self.host, self.port)
      print(f"Logs from your program will appear here.")
      print(f"Server started on {self.host}:{self.port}")
      async with server as s:
         await s.serve_forever()

   async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
      """Handles a single client connection, potentially with multiple requests."""
      try:
         while True:
            request = await Request.from_reader(reader)
            if not request:
               break

            response = await self._route_request(request)

            # Accept-Encoding handling
            accept_encoding = request.headers.get("accept-encoding", "")
            body, encoding = self._encode_body(response.body, accept_encoding)
            response.body = body
            if encoding:
               response.headers["Content-Encoding"] = encoding
            response.headers["Content-Length"] = str(len(response.body))

            # handle persistent connection ie, Http/1.1 Keep-alive
            con_header = request.headers.get("connection", "keep-alive")
            if con_header.lower() == "close":
               response.headers["Connection"] = "close"

            writer.write(response.to_bytes())
            await writer.drain()

            if con_header.lower() == "close":
               break

      except (ConnectionResetError, asyncio.IncompleteReadError):
         pass

      except Exception as e:
         print(f"An error occured:{e}")

      finally:
         writer.close()
         await writer.wait_closed()

   async def _route_request(self, req: Request) -> Response:
      """Routes the request to the respective handler based on path and method."""
      if req.path == "/":
         return self.handle_root(req)

      elif req.path.startswith("/echo/"):
         return self.handle_echo(req)

      elif req.path == "/user-agent":
         return self.handle_user_agent(req)

      elif req.path.startswith("/files/"):
         if req.method == "GET":
            return self.handle_get_file(req)
         elif req.method == "POST":
            return self.handle_post_file(req)

      return Response(404, "Not Found")

   def _encode_body(self, body: bytes, encode_types: str) -> Tuple[bytes, Optional[str]]:
      """Compress the response body if the client supports it."""
      encodings = [e.strip() for e in encode_types.split(",")]
      if "gzip" in encodings:
         return gzip.compress(body), "gzip"
      if "deflate" in encodings:
         return zlib.compress(body), "deflate"
      return body, None
      
      
      
   def handle_root(self, req: Request) -> Response:
      """Handle request to the root path"""
      return Response(200, "OK")
   
   def handle_echo(self, req: Request) -> Response:
      """Handles /echo/{string}"""
      echo_str= req.path.split("/echo/", 1)[1]
      return Response(200, "OK", {"Content-Type": "text/plain"}, echo_str.encode())
   
   def handle_user_agent(self, req: Request)-> Response:
      """return user-agent"""
      user_agent = req.headers.get("user-agent", "")
      return Response(200, "OK", {"Content-Type": "text/plain"}, user_agent.encode())
   
   def handle_get_file(self, req: Request)-> Response:
      """Handle GET /files/{name} """
      if not self.directory:
         return Response(404, "Not Found")
      
      file_name = req.path.split("/files/", 1)[1]
      file_path = os.path.join(self.directory, file_name)
      
      if os.path.isfile(file_path):
         with open(file_path, "rb") as f:
            content = f.read()
            
         return Response(200, "OK", {"Content-Type": "application/octet-stream"}, content)
      else:
         return Response(404, "Not Found")
      
   def handle_post_file(self, req: Request) -> Response:
      """Handles POST /files/{name}"""
      if not self.directory:
         return Response(404, "Not Found")
      
      file_name = req.path.split("/files/", 1)[1]
      file_path = os.path.join(self.directory, file_name)
      
      with open(file_path, "wb") as f:
         f.write(req.body)
         
      return Response(201, "Created")
   
   
### main appppppp

def main():
   """Parse Command-Line args and start the server."""
   dir =None
   if "--directory" in sys.argv:
      try:
         dir_index = sys.argv.index("--directory") + 1
         dir = sys.argv[dir_index]
      except (ValueError, IndexError):
         print("Usage: python3 app.py --directory /path/to/files")
         sys.exit(1)
         
   server = HTTPServer(directory=dir)
   
   try:
      asyncio.run(server.start())
   except KeyboardInterrupt:
      print("\nServer shutting down.")
      
if __name__ == "__main__":
   main()