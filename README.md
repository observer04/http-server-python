[![progress-banner](https://backend.codecrafters.io/progress/http-server/2a1a34b2-762f-49ec-82bc-b2ad4d364d8b)](https://app.codecrafters.io/users/codecrafters-bot?r=2qF)

# HTTP Server in Python

A simple, asynchronous HTTP/1.1 server built in Python using `asyncio`. This server supports basic HTTP features including routing, file serving, content encoding, and persistent connections.

## Features

- **Asynchronous I/O**: Uses `asyncio` for non-blocking, concurrent client handling.
- **Routing**: Supports multiple endpoints with clean, object-oriented routing.
- **File Operations**: GET and POST for file serving and uploading.
- **Content Encoding**: Supports gzip and deflate compression based on client headers.
- **Persistent Connections**: HTTP/1.1 keep-alive support with proper connection management.
- **Error Handling**: Robust handling of client disconnections and exceptions.
- **Command-Line Interface**: Optional directory flag for file serving.

## Requirements

- Python 3.7+
- Standard library modules: `asyncio`, `sys`, `os`, `gzip`, `zlib`, `dataclasses`, `typing`

## Installation

Clone the repository and navigate to the project directory:

```sh
git clone https://github.com/observer04/http-server-python.git
cd http-server-python
```

## Usage

Run the server with:

```sh
python app/main.py
```

For file serving, specify a directory:

```sh
python app/main.py --directory /path/to/your/files
```

The server starts on `localhost:4221` by default.

## API Endpoints

### GET /

Returns a 200 OK response.

**Example:**
```sh
curl http://localhost:4221/
```

### GET /echo/{str}

Echoes back the string in the URL path.

**Example:**
```sh
curl http://localhost:4221/echo/hello
# Response: hello
```

### GET /user-agent

Returns the User-Agent header from the request.

**Example:**
```sh
curl -H "User-Agent: MyBrowser/1.0" http://localhost:4221/user-agent
# Response: MyBrowser/1.0
```

### GET /files/{filename}

Serves a file from the specified directory (requires `--directory` flag).

**Example:**
```sh
python app/main.py --directory /tmp
curl http://localhost:4221/files/example.txt
# Returns the content of /tmp/example.txt
```

### POST /files/{filename}

Uploads a file to the specified directory (requires `--directory` flag).

**Example:**
```sh
python app/main.py --directory /tmp
curl -X POST -d "file content" http://localhost:4221/files/newfile.txt
# Creates /tmp/newfile.txt with "file content"
```

## Architecture

- **Request/Response Classes**: Dataclasses for parsing HTTP requests and building responses.
- **HTTPServer Class**: Manages the server lifecycle, routing, and connection handling.
- **Async Handlers**: Each endpoint is handled asynchronously for scalability.

## Examples

### Basic Server Run

```sh
python app/main.py
# Server starts on localhost:4221
```

### File Server

```sh
python app/main.py --directory /home/user/files
# Now /files/ endpoints are active
```

### Testing with curl

```sh
# Test echo
curl http://localhost:4221/echo/test

# Test file upload
echo "Hello World" | curl -X POST --data-binary @- http://localhost:4221/files/hello.txt

# Test file download
curl http://localhost:4221/files/hello.txt
```

## Contributing

This is a personal project for learning HTTP server implementation. Feel free to fork and experiment!

## License

None specified.
