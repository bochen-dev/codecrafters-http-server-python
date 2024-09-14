import socket  # noqa: F401


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    connection, address = server_socket.accept() # wait for client

    """
    // Status line
    HTTP/1.1  // HTTP version
    200       // Status code
    OK        // Optional reason phrase
    \r\n      // CRLF that marks the end of the status line

    // Headers (empty)
    \r\n      // CRLF that marks the end of the headers

    // Response body (empty)
    """
    status_line = b"HTTP/1.1 200 OK\r\n"
    headers = b"\r\n"
    body = b""
    http_response = status_line + headers + body
    connection.sendall(http_response)


if __name__ == "__main__":
    main()
