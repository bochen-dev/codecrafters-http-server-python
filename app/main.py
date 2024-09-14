import http
import socket  # noqa: F401
from datetime import datetime


class ResponseBuilder:
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

    def __init__(self):
        self.version = "HTTP/1.1"
        self.status_code = b""
        self.headers = b""
        self.body = b""

    def set_status_code(self, status_code: int):
        self.status_code = status_code
        return self

    def set_headers(self, headers: dict[str, str]):
        for key, value in headers.items():
            self.headers += f"{key}: {value}\r\n".encode()
        self.headers += b"\r\n"
        return self

    def set_body(self, body: str):
        self.body = body.encode()
        return self

    def build(self) -> bytes:
        if not self.status_code:
            raise ValueError("Status code is required")

        reason_phrase = http.HTTPStatus(self.status_code).phrase

        status_line = f"{self.version} {self.status_code} {reason_phrase}\r\n".encode()

        return status_line + self.headers + self.body


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    def parse_request(
        received_data: bytes,
    ) -> tuple[str, str, str, dict[str, str], str]:
        """
        received_data
        > b'GET / HTTP/1.1\r\nHost: localhost:4221\r\nUser-Agent: curl/8.7.1\r\nAccept: */*\r\n\r\n'
        """

        parts = received_data.decode().split("\r\n")

        start_line, *headers, _, body = parts

        method, path, version = start_line.split(" ")

        headers_dict: dict[str, str] = {}
        for header in headers:
            key, value = header.split(": ")
            headers_dict[key] = value

        return method, path, version, headers_dict, body

    with socket.create_server(("localhost", 4221), reuse_port=True) as server_socket:

        while True:
            conn, addr = server_socket.accept()  # wait for client

            received_data = conn.recv(1024)
            # print("Received: " + str(received_data))

            parsed_data = parse_request(received_data)
            # print("Parsed: " + str(parsed_data))
            method, path, version, headers_dict, body = parsed_data

            match path:
                case "/":
                    response = ResponseBuilder().set_status_code(200)

                case s if s.startswith("/echo/"):
                    echo = s[len("/echo/") :]
                    response = (
                        ResponseBuilder()
                        .set_status_code(200)
                        .set_headers(
                            {
                                "Content-Type": "text/plain",
                                "Content-Length": str(len(echo)),
                            }
                        )
                        .set_body(echo)
                    )

                case _:
                    response = ResponseBuilder().set_status_code(404)

            print(f"{datetime.now()} [{method}] {path} {response.status_code}")
            conn.sendall(response.build())

            conn.close()


if __name__ == "__main__":
    main()
