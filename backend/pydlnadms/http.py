import itertools
import time
import urllib.parse
import logging

def rfc1123_date():
    return time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())

HTTP_BODY_SEPARATOR = b'\r\n' * 2

class HTTPMessage(object):

    def __init__(self, first_line, headers, body):
        self.first_line = first_line
        self.headers = headers
        self.body = body

    def to_bytes(self):
        return (
            self.first_line + '\r\n' +
            httpify_headers(self.headers) + '\r\n'
        ).encode('utf-8') + self.body

class HTTPRequest(object):

    __slots__ = 'method', 'path', 'protocol', 'headers', 'body', 'query'

    def __init__(self, method, resource, headers=None, body=b''):
        self.method = method
        self.headers = headers or {}
        split_result = urllib.parse.urlsplit(resource)
        self.query = urllib.parse.parse_qs(split_result.query)
        self.path = urllib.parse.unquote(split_result.path)
        if split_result.fragment:
            logging.warning(
                'Unused fragment in HTTP request resource: %r',
                split_result.fragment)
        self.body = body

    def __setitem__(self, key, value):
        self.headers[key.upper()] = value.strip()

    def __getitem__(self, key):
        return self.headers[key.upper()]

    def __contains__(self, key):
        return key.upper() in self.headers

    def to_bytes(self):
        return HTTPMessage(
            ' '.join((self.method, self.path, 'HTTP/1.1')),
            self.headers,
            self.body).to_bytes()
            
    @classmethod
    def from_http_request(cls, method, path, headers):
        request = cls(method, path)
        for headerName, headerValue in headers.items():
            request[headerName] = headerValue
        return request

    @classmethod
    def from_bytes(cls, buf):
        lines = (a.decode('utf-8') for a in buf.split(b'\r\n'))
        try:
            line = lines.__next__()
            method, path, protocol = line.split()
        except ValueError:
            method = 'GET'
            path = '/rootDesc.xml'
            lines = ['HOST:127.0.0.1', 'User-Agent: Twisted PageGetter2']
            
        request = cls(method, path)
        for h in lines:
            if h:
                name, value = h.split(':', 1)
                request[name] = value
        return request

class HTTPResponse(object):

    from http.client import responses

    def __init__(self, headers=None, body=b'', code=None, reason=None):
        self.headers = dict(headers) or {}
        self.body = body
        self.code = code
        self.reason = reason

    def to_bytes(self):
        return HTTPMessage(
            'HTTP/1.1 {:03d} {}'.format(
                self.code,
                self.reason or self.responses[self.code]),
            self.headers.items(),
            self.body).to_bytes()

def httpify_headers(headers):
    '''Build HTTP headers string, including the trailing CRLF's for each header'''
    def lines():
        for key, value in headers:
            assert key, key
            if value:
                yield '{}: {}'.format(key, value)
            else:
                yield key + ':'
    return '\r\n'.join(itertools.chain(lines(), ['']))

class HTTPRange(object):

    def __init__(self):
        self.start = '0'
        self.end = ''
        self.size = ''

    @classmethod
    def from_string(class_, str_):
        instance = class_()
        if '/' in str_:
            range_, instance.size = str_.split('/')
        else:
            range_ = str_
        instance.start, instance.end = range_.split('-')
        return instance

    def __str__(self):
        s = self.start + '-' + self.end
        if self.size:
            s += '/' + str(self.size)
        return s


class HTTPRangeField(dict):

    @classmethod
    def from_string(class_, str_):
        instance = class_()
        for forms_ in str_.split():
            units, range_ = forms_.split('=')
            instance[units] = HTTPRange.from_string(range_)
        return instance

    def __str__(self):
        return ' '.join('{}={}'.format(units, range) for units, range in self.items())
