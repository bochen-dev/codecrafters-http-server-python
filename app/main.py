import argparse
import http
import os
import socket  # noqa: F401
from dataclasses import dataclass
from datetime import datetime
from threading import Thread

file_dir: str = '.'

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


def client_thread(conn: socket.socket, addr: tuple[str, int]):
    print(f"Connected by {addr}")
    handle_request(conn)
    print("Connection closed by client")


def handle_request(conn: socket.socket):
    try:
        if not (received_data := conn.recv(1024)):
            # No data received means the client has closed the connection
            return

        request = parse_request(received_data)

        match request.method, request.path:
            case 'GET', '/':
                response = ResponseBuilder().set_status_code(200)

            case 'GET', s if s.startswith("/echo/"):
                echo = s[len("/echo/") :]
                response = (
                    ResponseBuilder()
                    .set_status_code(200)
                    .set_header(("Content-Type", "text/plain"))
                    .set_header(("Content-Length", str(len(echo))))
                    .set_body(echo)
                )

            case 'GET', '/user-agent':
                user_agent = request.ci_headers.get("User-Agent".lower(), "")
                response = (
                    ResponseBuilder()
                    .set_status_code(200)
                    .set_header(("Content-Type", "text/plain"))
                    .set_header(("Content-Length", str(len(user_agent))))
                    .set_body(user_agent)
                )

            case 'GET', s if s.startswith("/files/"):
                if not (file_name := s[len("/files/") :]):
                    response = ResponseBuilder().set_status_code(404)
                else:
                    try:
                        file_path = os.path.join(file_dir, file_name)
                        print(f"File path: {file_path}")
                        with open(file_path, "rb") as file:
                            file_content = file.read().decode()
                            response = (
                                ResponseBuilder()
                                .set_status_code(200)
                                .set_header(("Content-Type", "application/octet-stream"))
                                .set_header(("Content-Length", str(len(file_content))))
                                .set_body(file_content)
                            )
                    except FileNotFoundError:
                        response = ResponseBuilder().set_status_code(404)

            case 'POST', s if s.startswith("/files/"):
                if not (file_name := s[len("/files/") :]):
                    response = ResponseBuilder().set_status_code(404)
                else:
                    try:
                        file_path = os.path.join(file_dir, file_name)
                        print(f"File path: {file_path}")
                        with open(file_path, "wb") as file:
                            file.write(request.body.encode())
                            response = ResponseBuilder().set_status_code(201)
                    except FileNotFoundError:
                        response = ResponseBuilder().set_status_code(404)

            case _:
                response = ResponseBuilder().set_status_code(404)

        print(f"{datetime.now()} {request} {response.status_code}")
        response_data = response.build()
        conn.sendall(response_data)
    finally:
        conn.close()


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


def main():

    with socket.create_server(("localhost", 4221), reuse_port=True) as server_socket:
        print("Server started at http://localhost:4221")

        try:
            while True:
                conn, addr = server_socket.accept()  # wait for client
                Thread(target=client_thread, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("\nServer stopped")
        finally:
            server_socket.close()


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--directory", default=".")
    args = arg_parser.parse_args()

    file_dir = args.directory

    main()
