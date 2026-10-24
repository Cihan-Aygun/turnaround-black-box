import argparse
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
from .engine import scenario,uncertainty

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url=urlparse(self.path)
        try:
            if url.path=='/':
                body=Path(__file__).with_name('index.html').read_bytes(); mime='text/html; charset=utf-8'
            elif url.path=='/api/scenario':
                q=parse_qs(url.query)
                result=scenario(q.get('task',['TB101-clean'])[0],int(q.get('extra',['15'])[0]),int(q.get('saving',['8'])[0]),q.get('priority',['TB101'])[0])
                body=json.dumps(result).encode(); mime='application/json'
            elif url.path=='/api/uncertainty':
                body=json.dumps(uncertainty()).encode(); mime='application/json'
            else:
                self.send_error(404); return
            status=200
        except (ValueError,TypeError) as error:
            body=json.dumps({'error':str(error)}).encode(); mime='application/json'; status=400
        self.send_response(status); self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=8001); args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'Turnaround Black Box: http://127.0.0.1:{args.port}',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
if __name__=='__main__': main()
