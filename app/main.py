import http
import socket  # noqa: F401
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Request:
    method: str
    path: str
    version: str
    headers: dict[str, str]
    body: str

    @property
    def ci_headers(self) -> dict[str, str]:
        # Case-insensitive headers
        return {k.lower(): v for k, v in self.headers.items()}

    def __repr__(self):
        return f"Request(method={self.method}, path={self.path})"

    def __str__(self) -> str:
        return f"[{self.method}] {self.path}"


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
        self.status_code: int
        self.headers: dict[str, str] = {}
        self.body: bytes = b""

    def set_status_code(self, status_code: int):
        self.status_code = status_code
        return self

    def set_header(self, header: tuple[str, str]):
        k, v = header
        self.headers[k] = v
        return self

    def set_body(self, body: str):
        self.body = body.encode()
        return self

    def build(self) -> bytes:
        if not self.status_code:
            raise ValueError("Status code is required")

        reason_phrase = http.HTTPStatus(self.status_code).phrase

        status_line = f"{self.version} {self.status_code} {reason_phrase}\r\n".encode()

        str_headers = ""
        for key, value in self.headers.items():
            str_headers += f"{key}: {value}\r\n"
        str_headers += "\r\n"

        return status_line + str_headers.encode() + self.body


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    def parse_request(
        received_data: bytes,
    ) -> Request:
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

        return Request(method, path, version, headers_dict, body)

    with socket.create_server(("localhost", 4221), reuse_port=True) as server_socket:

        while True:
            conn, addr = server_socket.accept()  # wait for client

            received_data = conn.recv(1024)
            # print("Received: " + str(received_data))

            request = parse_request(received_data)
            # print("Parsed: " + str(parsed_data))

            match request.path:
                case "/":
                    response = ResponseBuilder().set_status_code(200)

                case s if s.startswith("/echo/"):
                    echo = s[len("/echo/") :]
                    response = (
                        ResponseBuilder()
                        .set_status_code(200)
                        .set_header(("Content-Type", "text/plain"))
                        .set_header(("Content-Length", str(len(echo))))
                        .set_body(echo)
                    )

                case '/user-agent':
                    user_agent = request.ci_headers.get('User-Agent'.lower(), '')
                    response = (
                        ResponseBuilder()
                        .set_status_code(200)
                        .set_header(("Content-Type", "text/plain"))
                        .set_header(("Content-Length", str(len(user_agent))))
                        .set_body(user_agent)
                    )

                case _:
                    response = ResponseBuilder().set_status_code(404)

            print(f"{datetime.now()} {request} {response.status_code}")
            response_data = response.build()
            # print("Response: " + str(response_data))
            conn.sendall(response_data)

            conn.close()


if __name__ == "__main__":
    main()
