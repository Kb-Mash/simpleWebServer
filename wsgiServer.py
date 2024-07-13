import socket
import sys
import io
import email.utils

class WSGIServer:
    """
    A simple WSGI server implementation.
    """

    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 1

    def __init__(self, server_address):
        """
        Initialize the WSGI server with the given server address.

        Args:
        - server_address: A tuple (host, port) indicating the server's address.
        """
        self.listen_socket = listen_socket = socket.socket(
            self.address_family,
            self.socket_type
        )
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_socket.bind(server_address)
        listen_socket.listen(self.request_queue_size)
        host, port = self.listen_socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port
        self.headers_set = []

    def set_app(self, application):
        """
        Set the WSGI application callable that will be called to handle requests.

        Args:
        - application: The WSGI application callable.

        This method sets the WSGI application that will be invoked for each incoming request.
        """
        self.application = application

    def serve_forever(self):
        """
        Serve requests indefinitely.

        This method starts serving incoming requests indefinitely.
        """
        listen_socket = self.listen_socket
        while True:
            self.client_connection, client_address = listen_socket.accept()
            self.handle_one_request()

    def handle_one_request(self):
        """
        Handle a single request.

        This method handles one incoming client connection/request.
        """
        request_data = self.client_connection.recv(1024).decode('utf-8')
        if not request_data:
            self.client_connection.close()
            return
        print(''.join(f'< {line}\n' for line in request_data.splitlines()))
        self.parse_request(request_data)
        self.request_data = request_data  # Store the request data for WSGI application
        env = self.get_environ()
        result = self.application(env, self.start_response)
        self.finish_response(result)

    def parse_request(self, text):
        """
        Parse the incoming request.

        Args:
        - text: The request data as a string.

        This method parses the incoming HTTP request to extract request method, path, and version.
        """
        request_line = text.splitlines()
        if len(request_line) > 0:
            request_line = request_line[0].rstrip('\r\n')
            self.request_method, self.path, self.request_version = request_line.split()
        else:
            self.request_method, self.path, self.request_version = '', '', ''

    def get_environ(self):
        """
        Create and return the WSGI environment dictionary.

        Returns:
        - env: The WSGI environment dictionary.

        This method creates and returns the WSGI environment dictionary based on the current request.
        """
        env = {}
        env['wsgi.version'] = (1, 0)
        env['wsgi.url_scheme'] = 'http'
        env['wsgi.input'] = io.StringIO(self.request_data)  # Set request data as WSGI input
        env['wsgi.errors'] = sys.stderr
        env['wsgi.multithread'] = False
        env['wsgi.multiprocess'] = False
        env['wsgi.run_once'] = False
        env['REQUEST_METHOD'] = self.request_method
        env['PATH_INFO'] = self.path
        env['SERVER_NAME'] = self.server_name
        env['SERVER_PORT'] = str(self.server_port)
        return env

    def start_response(self, status, response_headers, exc_info=None):
        """
        Start the HTTP response.

        Args:
        - status: The HTTP status code and message.
        - response_headers: A list of (header_name, header_value) tuples.
        - exc_info: Optional exception information.

        This method prepares the HTTP response headers.
        """
        server_headers = [
            ('Date', email.utils.formatdate(usegmt=True)),
            ('Server', 'WSGIServer 0.2'),
        ]
        self.headers_set = [status, response_headers + server_headers]

    def finish_response(self, result):
        """
        Finish sending the HTTP response.

        Args:
        - result: An iterable containing the response body.

        This method constructs the full HTTP response and sends it to the client.
        """
        try:
            status, response_headers = self.headers_set
            response = f'HTTP/1.1 {status}\r\n'
            for header in response_headers:
                response += f'{header[0]}: {header[1]}\r\n'
            response += '\r\n'
            for data in result:
                response += data.decode('utf-8')
            print(''.join(f'> {line}\n' for line in response.splitlines()))
            self.client_connection.sendall(response.encode())
        finally:
            self.client_connection.close()

SERVER_ADDRESS = (HOST, PORT) = '', 8080

def make_server(server_address, application):
    """
    Create a WSGI server instance.

    Args:
    - server_address: A tuple (host, port) indicating the server's address.
    - application: The WSGI application callable.

    Returns:
    - server: A WSGIServer instance.

    This function creates and returns a WSGI server instance configured with the given
    server address and WSGI application.
    """
    server = WSGIServer(server_address)
    server.set_app(application)
    return server

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Provide a WSGI application object as module:callable')
    app_path = sys.argv[1]
    module, application = app_path.split(':')
    module = __import__(module)
    application = getattr(module, application)
    httpd = make_server(SERVER_ADDRESS, application)
    print(f'WSGIServer: Serving HTTP on port {PORT} ...\n')
    httpd.serve_forever()

