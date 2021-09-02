import json
import socket
import select
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler

socekt_map = {}
process_map = {}

def send_501(func):
    def _wrapper(self, *args, **kwargs):
        try:
            ret = func(self, *args, **kwargs)
        except:
            traceback.print_exc()
            self.send_response(501)
            self.send_header("Content-type","text/html")
            self.wfile.write("internal error\n".encode())
        return ret
    return _wrapper
        

class SimpleHTTPHandler(BaseHTTPRequestHandler):
    """ attr                    type            annotation
    self.command                str              GET or POST
    self.path                   str                 
    self.headers       http.client.HTTPMessage      first line
    self.raw_requestline        bytes
    self.rfile        <class '_io.BufferedReader'>  read body
    self.wfile        <class '_io.BufferedReader'>  write response
    self.version
    """
    def do_GET(self):
        attr = ["command", "path", "headers", "raw_requestline", "rfile"]
        for i in attr:
            obj = getattr(self, i)
            print("%s|%s|%s" % (i, type(obj), str(obj)))

        self.send_response(200)
        #self.send_header("Content-type","text/html")
        self.send_header("Content-type","application/json")
        self.send_header("test","This is test!")
        self.end_headers()
        buf = json.dumps({"code": 0}).encode()
        buf+=b'\r\n'
        self.wfile.write(buf)

    def do_POST(self):
        print(self.headers)
        data_len = int(self.headers.get("content-length"))
        if data_len:
            data = self.rfile.read(data_len)
            print("receive data|%s|%s" % (type(data), data))
        self.send_response(200)
        #self.send_header("Content-type","text/html")
        self.send_header("Content-type","application/json")
        self.send_header("test","This is test!")
        self.end_headers()
        buf = json.dumps({"code": 0}).encode()
        buf+=b'\r\n'
        self.wfile.write(buf)
    
    def ctrl_proc(self):
        pass

    def query_proc(self):
        pass

    def ws_shake_hands(self):
        pass

    def empty_ws_req(self):
        # Avoid unexpected ws request from clients
        pass


class ReliableServer(HTTPServer):
    def _handle_request_noblock(self):
        try:
            request, client_address = self.get_request()
        except OSError:
            return
        if self.verify_request(request, client_address):
            try:
                self.process_request(request, client_address)
            except:
                self.handle_error(request, client_address)
                self.shutdown_request(request)
        else:
            self.shutdown_request(request)
        # TODO if websocket return request: socket_conn

    def process_request(self, request, client_address):
        """Call finish_request.

        Overridden by ForkingMixIn and ThreadingMixIn.

        """
        self.finish_request(request, client_address)
        # TODO insert websocket, if it is, return True
        self.shutdown_request(request)

    def finish_request(self, request, client_address):
        """Finish one request by instantiating RequestHandlerClass."""
        self.RequestHandlerClass(request, client_address, self)

    def service_actions(self):
        # TODO deal http request
        # TODO what else to do?
        pass

if __name__ == "__main__":
    http_server = HTTPServer(("", 7005), SimpleHTTPHandler)
    http_server.serve_forever()
# http_server.socket
# class HttpServer(object):
#     def __init__(self, ip, port, max_listen):
#         self.ip = ip
#         self.port = port
#         self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self.server_socket.bind((ip, port))
#         self.server_socket.listen(max_listen)
    
#     def send(self, conn, data):
#         # If data is big, send method will not finish it 
#         conn.sendall(data.encode("utf-8"))
    
#     def read(self, conn):
#         raw = b''
#         while True:
#             data = conn.recv(4096)
#             if not data:
#                 raw += data
#         return raw.decode("utf-8")

#     def accept(self):
#         return self.server_socket.accept()

