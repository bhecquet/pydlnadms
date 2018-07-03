
from backend.pydlnadms.http import rfc1123_date, HTTPResponse, HTTPRequest
import logging

RESOURCE_PATH = '/res'
ICON_PATH = '/icon'

from http.server import HTTPServer as HTTPServerP, BaseHTTPRequestHandler

UPNP_ROOT_DEVICE = 'upnp:rootdevice'
UPNP_DOMAIN_NAME = 'schemas-upnp-org'
ROOT_DESC_PATH = '/rootDesc.xml'
serverActive = False
import platform

SERVER_FIELD = '{}/{} DLNADOC/1.50 UPnP/1.0 PyDLNADMS/1.0'.format(
    *platform.linux_distribution()[0:2])





import collections
RequestHandlerContext = collections.namedtuple(
    'RequestHandlerContext',
    'socket request dms start_response')

def setServerActive():
    global serverActive
    serverActive = True
    
def getServerActive():
    global serverActive
    return serverActive

def recv_http_header(sock):
    import socket
    from .http import HTTP_BODY_SEPARATOR
    buffer = b''
    while True:
        # determine bufsize so that body is left in the socket
        #
        peek_data = sock.recv(0x1000, socket.MSG_PEEK)
        if not peek_data:
            return buffer
        index = (buffer + peek_data).find(HTTP_BODY_SEPARATOR)
        if index == -1:
            bufsize = len(peek_data)
        else:
            bufsize = index - len(buffer) + len(HTTP_BODY_SEPARATOR)
        assert 0 < bufsize <= len(peek_data), (bufsize, len(peek_data))

        data = sock.recv(bufsize)
        assert data == peek_data[:bufsize], (data, peek_data)
        buffer += data

        if index != -1:
            assert buffer.endswith(HTTP_BODY_SEPARATOR)
            break
    assert buffer.count(HTTP_BODY_SEPARATOR) <= 1
    return buffer

from http.client import HTTPException
import http.client


class HandleRequest(object):

    def __init__(self, sock, dms):
        self.socket = sock
        self.dms = dms
        self.sent_header = False

    def start_response(self, code, headers):
        headers = [
            ('Server', SERVER_FIELD),
            ('Date', rfc1123_date())
        ] + headers
        bytes = HTTPResponse(headers, code=code).to_bytes()
        logging.debug('%s', bytes)
        self.socket.sendall(bytes)
        return self.socket

    def get_handler(self, request):
        from . import handlers
        from functools import partial
        from backend.pydlnadms.services import SERVICE_LIST
        method = request.method
        path = request.path
        print(path)
        if method in {'GET'}:
            if path == ROOT_DESC_PATH:
                return partial(handlers.xml_description, self.dms.device_desc)
            for service in SERVICE_LIST:
                if path == service.SCPDURL:
                    return partial(handlers.xml_description, service.xmlDescription)
            if path in {RESOURCE_PATH, ICON_PATH}:
                query = request.query
                if 'transcode' in query:
                    return handlers.transcode_resource
                elif 'thumbnail' in query:
                    return handlers.thumbnail_resource
                else:
                    return handlers.file_resource
            else:
                return partial(handlers.error, http.client.NOT_FOUND)
        elif method in {'HEAD'}:
            if path in {RESOURCE_PATH}:
                query = request.query
                return handlers.head_file_resource
        elif method in {'POST'}:
            if path in (service.controlURL for service in SERVICE_LIST):
                return handlers.service
            return handlers.error(http.client.NOT_FOUND)
        elif method in {'SUBSCRIBE'}:
            for service in SERVICE_LIST:
                if path == service.eventSubURL:
                    return partial(handlers.error, http.client.NOT_IMPLEMENTED)
            else:
                return partial(handlers.error, http.client.NOT_FOUND)
        else:
            return partial(handlers.error, http.client.NOT_IMPLEMENTED)

    def __call__(self):
        request = HTTPRequest.from_bytes(recv_http_header(self.socket))
        
        try:
#             print(request.headers)
            handler = self.get_handler(request)
        except:
            from . import handlers
            logging.exception('Error getting handler')
            handler = handlers.error(http.client.INTERNAL_SERVER_ERROR)
            raise
        finally:
            handler(RequestHandlerContext(
                start_response=self.start_response,
                socket=self.socket,
                dms=self.dms,
                request=request))

            # TODO verifier qu'il est possible d'utiliser le HTTPServer multi-threade

# class DlnaRequestHandler(BaseHTTPRequestHandler):
#     
#     dms = None
#     
#     def _start_response(self, code, headers):
#         headers = [
#             ('Server', SERVER_FIELD),
#             ('Date', rfc1123_date())
#         ] + headers
#         bytes = HTTPResponse(headers, code=code).to_bytes()
#         logging.debug('%s', bytes)
#         self.socket.sendall(bytes)
#         return self.socket
#     
#     def _get_handler(self, method, path, request):
#         from . import handlers
#         from functools import partial
# 
#         dms = self.dms
#         if method in {'GET'}:
#             if path == ROOT_DESC_PATH:
#                 return partial(handlers.xml_description, dms.device_desc)
#             for service in SERVICE_LIST:
#                 if path == service.SCPDURL:
#                     return partial(handlers.xml_description, service.xmlDescription)
#             if path in {RESOURCE_PATH, ICON_PATH}:
#                 if 'transcode' in request.query:
#                     return handlers.transcode_resource
#                 elif 'thumbnail' in request.query:
#                     return handlers.thumbnail_resource
#                 else:
#                     return handlers.file_resource
#             else:
#                 return partial(handlers.error, http.client.NOT_FOUND)
#         elif method in {'POST'}:
#             if path in (service.controlURL for service in SERVICE_LIST):
#                 return handlers.service
#             return handlers.error(http.client.NOT_FOUND)
#         elif method in {'SUBSCRIBE'}:
#             for service in SERVICE_LIST:
#                 if path == service.eventSubURL:
#                     return partial(handlers.error, http.client.NOT_IMPLEMENTED)
#             else:
#                 return partial(handlers.error, http.client.NOT_FOUND)
#         else:
#             return partial(handlers.error, http.client.NOT_IMPLEMENTED)
#     
#     def _reply(self, method, path):
#         request = HTTPRequest.from_http_request(method, path, self.headers)
#         
#         try:
#             handler = self._get_handler(method, path, request)
#         except:
#             from . import handlers
#             logging.exception('Error getting handler')
#             handler = handlers.error(http.client.INTERNAL_SERVER_ERROR)
#             raise
#         finally:
#             self.socket = self.request
#             handler(RequestHandlerContext(
#                 start_response=self._start_response,
#                 socket=self.request, # self.request is a socket
#                 dms=self.dms,
#                 request=request))
#     
#     @classmethod
#     def setDms(cls, dms):
#         cls.dms = dms
#     
#     def do_GET(self):
#         self._reply('GET', self.path)
#     
#     def do_POST(self):
#         self._reply('POST', self.path)
#     
#     def do_SUBSCRIBE(self):
#         self._reply('SUBSCRIBE', self.path)
        
        
#        
#class HTTPServer(threading.Thread):
#
#    def __init__(self, port, dms):
#        DlnaRequestHandler.setDms(dms)
#        self.httpd = HTTPServerP(('', port), DlnaRequestHandler)
#        self.socket = self.httpd.socket
#        super(HTTPServer, self).__init__()
#        
#    def run(self):
#        self.httpd.serve_forever()
            
class HTTPServer(object):

    def __init__(self, port, dms):
        self.socket = self.create_socket(port)
        self.dms = dms

    def create_socket(self, port):
        import errno, socket, itertools
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        for port in itertools.count(port):
            try:
                sock.bind(('', port))
            except socket.error as exc:
                if exc.errno != errno.EADDRINUSE:
                    raise
            else:
                break
        sock.listen(socket.SOMAXCONN)
        return sock

    def handle_client(self, sock):
        try:
            HandleRequest(sock, self.dms)()
        finally:
            sock.close()

    def run(self):
        import threading
        while True:
            sock, addr = self.socket.accept()
            
            thread = threading.Thread(
                target=self.handle_client,
                args=[sock],
                name=addr)
            thread.daemon = True
            thread.start()
