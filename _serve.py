#!/usr/bin/env python3
"""Local preview server that never lets the browser cache a page.

python3 -m http.server sends only Last-Modified, so a rebuilt page is often
served from the browser's own cache and a change looks like it did not land.
Asset URLs dodge this because the build stamps them with ?v=<hash>; the HTML
pages have no such stamp. This adds the headers that close that gap.

Preview only. Nothing here affects the built site.

    python3 _serve.py [port]            default 8777
"""
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class NoCache(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8777
    print(f"preview on http://127.0.0.1:{port}/  (no-store; every reload is fresh)")
    ThreadingHTTPServer(("127.0.0.1", port), NoCache).serve_forever()
