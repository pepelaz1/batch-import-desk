"""Local demo HTTP adapter. Application logic lives in engine.py."""
import json, os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
import engine
ROOT = Path(__file__).parent
class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data, mime='application/json'):
        body = json.dumps(data).encode() if mime == 'application/json' else data
        self.send_response(status)
        self.send_header('Content-Type', mime+'; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Cache-Control','no-store')
        self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path == '/': return self.reply(200,(ROOT/'index.html').read_bytes(),'text/html')
        if self.path == '/api/state': return self.reply(200,engine.state())
        self.reply(404,{'error':'Not found'})
    def do_POST(self):
        # Loopback demo: reject cross-origin writes and DNS-rebinding Host values.
        host=self.headers.get('Host','')
        if host not in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'):
            return self.reply(403,{'error':'Invalid host'})
        origin=self.headers.get('Origin')
        if origin and origin not in (f'http://{host}',):
            return self.reply(403,{'error':'Invalid origin'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0 < size <= 3000000: raise ValueError('Request must be between 1 byte and 3 MB')
            data=json.loads(self.rfile.read(size))
            if not isinstance(data,dict): raise ValueError('Expected a JSON object')
            self.reply(200,engine.action(self.path,data))
        except (ValueError,KeyError,TypeError) as e: self.reply(400,{'error':str(e)})
        except Exception:
            self.reply(500,{'error':'Operation failed; inspect server configuration'})
if __name__ == '__main__':
    port=int(os.getenv('PORT','8765'))
    print(f'Open http://127.0.0.1:{port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
