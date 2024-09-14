import socket  # noqa: F401


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    with socket.create_server(("localhost", 4221), reuse_port=True) as server_socket:

        while True:
            conn, addr = server_socket.accept()  # wait for client

            received_data = conn.recv(1024)
            print("Received: " + str(received_data))

            def parse_request(received_data: bytes) -> tuple[str, str, str, dict[str, str], str]:
                """
                received_data
                > b'GET / HTTP/1.1\r\nHost: localhost:4221\r\nUser-Agent: curl/8.7.1\r\nAccept: */*\r\n\r\n'
                """

                parts = received_data.decode().split("\r\n")
                """
                > [
                    'GET / HTTP/1.1',
                    'Host: localhost:4221',
                    'User-Agent: curl/8.7.1',
                    'Accept: */*',
                    '',
                    ''
                ]
                """

                start_line, *headers, _, body = parts

                method, path, version = start_line.split(" ")

                headers_dict = {}
                for header in headers:
                    key, value = header.split(": ")
                    headers_dict[key] = value

                return method, path, version, headers_dict, body

            parsed_data = parse_request(received_data)
            print("Parsed: " + str(parsed_data))
            method, path, version, headers_dict, body = parsed_data

            match path:
                case "/":
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
                    response_body = status_line + headers + body

                case _:
                    response_body = b"HTTP/1.1 404 Not Found\r\n\r\n"

            conn.sendall(response_body)

            conn.close()


if __name__ == "__main__":
    main()
