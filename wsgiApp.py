def app(environ, start_response):
    """
    A simple WSGI application that returns a plain text response.
    """
    status = '200 OK'
    response_headers = [('Content-Type', 'text/plain')]
    start_response(status, response_headers)
    return [b"Hello, World! This is a simple WSGI application."]

