import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import logging

class Bot:
    def __init__(self, api_key, host='127.0.0.1', port=8000):
        self.api_key = api_key
        self.host = host
        self.port = port
        self.handlers = {}
        self.logger = logging.getLogger("Bot")
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    def command(self, name):
        def decorator(func):
            self.handlers[name] = func
            return func
        return decorator

    def run(self):
        bot = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                path = urlparse(self.path).path
                length = int(self.headers.get('Content-Length', 0))
                data_str = self.rfile.read(length).decode('utf-8')
                try:
                    data = json.loads(data_str)
                except Exception as e:
                    bot.logger.error("Invalid JSON: %s", e)
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'{"error":"Invalid JSON"}')
                    return

                key = self.headers.get("X-API-Key")
                if key != bot.api_key:
                    bot.logger.warning("Authentication failed from %s", self.client_address)
                    self.send_response(403)
                    self.end_headers()
                    self.wfile.write(b'{"error":"Forbidden"}')
                    return

                command = data.get("command")
                if not command:
                    bot.logger.error("Missing command")
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'{"error":"Missing command"}')
                    return

                handler = bot.handlers.get(command)
                if not handler:
                    bot.logger.error("Unknown command: %s", command)
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b'{"error":"Unknown command"}')
                    return

                bot.logger.info("Handling command: %s from %s", command, self.client_address)
                try:
                    response = handler(data)
                except Exception as e:
                    bot.logger.exception("Handler error")
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(b'{"error":"Internal error"}')
                    return

                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"result": response}).encode('utf-8'))

            def log_message(self, format, *args):
                # suppress built-in HTTP server logging in stdout
                return

        server = HTTPServer((self.host, self.port), Handler)
        bot.logger.info("Bot running at http://%s:%d", self.host, self.port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            bot.logger.info("Shutting down bot...")