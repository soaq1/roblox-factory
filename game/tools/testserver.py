# A tiny local server that lets a test be started in Roblox Studio from the command line.
#   python3 game/tools/testserver.py            (leave running)
# The Studio plugin (tools/FactorySelfTest.lua) asks it once a second whether there is anything
# to do, runs what it is given, and posts back what happened.
#   POST /cmd     {"cmd": "play", "args": {"scenario": "iron_line"}}   queue a test
#   GET  /next    what the plugin asks; answers with the next queued command or {}
#   POST /result  what the plugin reports; kept in results.jsonl beside this file's working dir
#   GET  /status  what is queued, what came back last, when the plugin last asked
import json, sys, time
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 34873
OUT = sys.argv[1] if len(sys.argv) > 1 else "results.jsonl"
queue, last_result, last_poll, counter = [], None, 0.0, 0


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, body):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n).decode("utf-8") if n else "{}"
        try:
            return json.loads(raw)
        except ValueError:
            return {"raw": raw}

    def do_GET(self):
        global last_poll
        if self.path.startswith("/next"):
            last_poll = time.time()
            self.reply(queue.pop(0) if queue else {})
        else:
            self.reply({"queued": queue, "last_result": last_result,
                        "plugin_seen_seconds_ago": round(time.time() - last_poll, 1) if last_poll else None})

    def do_POST(self):
        global last_result, counter
        data = self.body()
        if self.path.startswith("/cmd"):
            counter += 1
            data["id"] = counter
            queue.append(data)
            self.reply({"queued": counter})
        else:
            data["at"] = time.strftime("%H:%M:%S")
            last_result = data
            with open(OUT, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
            self.reply({"ok": True})


HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
