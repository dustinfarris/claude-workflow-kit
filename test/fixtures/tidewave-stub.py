#!/usr/bin/env python3
"""Minimal stand-in for a running Tidewave MCP endpoint, for hooks_test.sh.

Answers a JSON-RPC ping with 200 at /tidewave/mcp and 404 anywhere else, so the
pre-flight hook's "up", "wrong port / wrong transport" and "refused" branches can
all be exercised without a real Phoenix server. Usage: tidewave-stub.py <port>
"""
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/tidewave/mcp":
            body = b'{"id":1,"result":{},"jsonrpc":"2.0"}'
            self.send_response(200)
        else:
            body = b'not found'
            self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


HTTPServer(("127.0.0.1", int(sys.argv[1])), Handler).serve_forever()
