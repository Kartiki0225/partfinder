"""PartFinder: a search engine for engine spare parts.

Run:  python app.py      then open http://127.0.0.1:5070

The catalog is loaded and indexed once, when the server starts.
After that every search is answered from memory.
"""

import threading

from flask import Flask, jsonify, render_template, request

from search import SearchEngine, load_parts

app = Flask(__name__)
engine = SearchEngine(load_parts())

# Flask answers requests on several threads. The cache's linked list must not be
# changed by two of them at once, so only one search runs at a time.
lock = threading.Lock()


@app.get("/")
def home():
    return render_template("index.html", stats=engine.stats())


@app.get("/api/suggest")
def api_suggest():
    """Autocomplete, for example /api/suggest?q=fuel+fi"""
    return jsonify(engine.suggest(request.args.get("q", "")))


@app.get("/api/search")
def api_search():
    """Search, for example /api/search?q=fule+filtr&limit=20"""
    query = request.args.get("q", "")
    try:
        limit = max(1, min(100, int(request.args.get("limit", 20))))
    except ValueError:
        return jsonify({"error": "limit must be a number"}), 400

    with lock:
        result = engine.search(query, limit)
    return jsonify({"query": query, **result})


@app.get("/api/stats")
def api_stats():
    return jsonify(engine.stats())


if __name__ == "__main__":
    app.run(port=5070)
