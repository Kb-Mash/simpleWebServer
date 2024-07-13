import socket
from io import StringIO

class WSGIServer:
    def __init__(self, host, port, application):
        self.host = host
        self.port = port
        self.application = application
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print(f'Serving HTTP on {self.host} port {self.port} ...')

    def start_response(self, status, headers):
        response_headers = [f'{status}\r\n']
        for header in headers:
            response_headers.append(f'{header[0]}: {header[1]}\r\n')
        response_headers.append('\r\n')
        return ''.join(response_headers)

    def handle_request(self, client_connection):
        request = client_connection.recv(1024).decode('utf-8')
        print(request)

        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/',
            'SERVER_NAME': self.host,
            'SERVER_PORT': str(self.port),
            'wsgi.input': StringIO(request),
        }

        response_body = self.application(environ, self.start_response)
        response_headers = self.start_response('200 OK', [('Content-Type', 'text/plain')])

        response_body_str = ''.join([part.decode('utf-8') for part in response_body])
        http_response = f'HTTP/1.1 200 OK\r\n{response_headers}{response_body_str}'
        client_connection.sendall(http_response.encode('utf-8'))
        client_connection.close()

    def serve_forever(self):
        while True:
            client_connection, client_address = self.server_socket.accept()
            self.handle_request(client_connection)


def simple_app(environ, start_response):
    status = '200 OK'
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    return [b"Hello, WSGI World!"]

if __name__ == '__main__':
    server = WSGIServer('127.0.0.1', 8080, simple_app)
    server.serve_forever()

