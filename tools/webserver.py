import http.server
import socketserver

PORT = 8001

Handler = http.server.SimpleHTTPRequestHandler
Handler.extensions_map={
    '.vue':	'text/html'
}

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    
    httpd.serve_forever()