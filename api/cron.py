import json
from http.server import BaseHTTPRequestHandler
import os
import sys

# Add root directory to sys.path to import fetch_posts
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.fetch_posts import fetch_mnd, fetch_army
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            mnd_posts = fetch_mnd()
            army_posts = fetch_army()
            all_posts = mnd_posts + army_posts
            all_posts.sort(key=lambda x: x.get('date', ''), reverse=True)

            data = {
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_count": len(all_posts),
                "mnd_count": len(mnd_posts),
                "army_count": len(army_posts),
                "posts": all_posts
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
