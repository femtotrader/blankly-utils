import threading

# from threading import Event
import uuid
import json
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
from blankly import Strategy

from .utils import get_account_values


def MakeServerRequestHandler(token: str, strategy: Strategy, quote: str):
    title = "Monitor"

    class ServerRequestHandler(BaseHTTPRequestHandler):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)

        def do_GET(self):
            # print(self.client_address[0])
            parsed_url = urlparse(self.path)
            # print(parsed_url)
            received_token = parse_qs(parsed_url.query).get("token", None)
            if parsed_url.path == "/api/health":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(bytes("0", "utf-8"))
                return
            if received_token is None or received_token[0] != token:
                self.send_response(401)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(
                    bytes(f"<html><head><title>{title}]</title></head>", "utf-8")
                )
                self.wfile.write(bytes("<body>", "utf-8"))
                self.wfile.write(bytes("<p>Not allowed.</p>", "utf-8"))
                self.wfile.write(bytes("</body></html>", "utf-8"))
                return
            else:
                if parsed_url.path == "/api/account":
                    self.send_response(200)
                    self.send_header("Content-type", "text/json")
                    self.end_headers()
                    df = get_account_values(strategy.interface, quote)
                    self.wfile.write(
                        bytes(
                            json.dumps(df.transpose().to_dict(orient="dict")), "utf-8"
                        )
                    )
                    return
                elif parsed_url.path == "/api/account_sum":
                    self.send_response(200)
                    self.send_header("Content-type", "text/json")
                    self.end_headers()
                    df = get_account_values(strategy.interface, quote)
                    df_sum = df[["available_amount", "hold_amount"]].sum()
                    self.wfile.write(bytes(json.dumps(df_sum.to_dict()), "utf-8"))
                    return
                elif parsed_url.path == "/":
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(
                        bytes(f"<html><head><title>{title}</title></head>", "utf-8")
                    )
                    self.wfile.write(bytes(f"<p>Request: {self.path}</p>", "utf-8"))
                    self.wfile.write(bytes("<body>", "utf-8"))
                    self.wfile.write(
                        bytes(
                            "<p>This is a web server for monitoring. See code for API usage.</p>",
                            "utf-8",
                        )
                    )
                    self.wfile.write(bytes("</body></html>", "utf-8"))
                    return
                else:
                    self.send_response(404)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(
                        bytes(f"<html><head><title>{title}</title></head>", "utf-8")
                    )
                    self.wfile.write(bytes("<body>", "utf-8"))
                    self.wfile.write(bytes("<p>Not found.</p>", "utf-8"))
                    self.wfile.write(bytes("</body></html>", "utf-8"))
                    return

    return ServerRequestHandler


class MonitorWebServer:
    def __init__(
        self, strategy: Strategy, quote: str, host="0.0.0.0", port=8000, token=None
    ):
        self.strategy = strategy
        self.quote = quote

        self.host = host
        self.port = port

        if token is None or len(token) == 0:
            self.token = uuid.uuid4().hex
        else:
            self.token = token

    def display(self):
        print(
            f"Running webserver with host={self.host} port={self.port} token={self.token}"
        )

    def process(self):
        MyServerRequestHandler = MakeServerRequestHandler(
            self.token, self.strategy, self.quote
        )
        httpd = HTTPServer((self.host, self.port), MyServerRequestHandler)
        httpd.serve_forever()

    def start(self):
        thread = threading.Thread(target=self.process)
        thread.start()
