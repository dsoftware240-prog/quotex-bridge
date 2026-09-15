from flask import Flask, jsonify, request
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

latest = {
    "asset": None,
    "price": None,
    "timestamp": None,
    "raw": None
}


@app.get("/")
def home():
    return jsonify({
        "status": "online",
        "service": "Quotex OTC Read-Only Bridge"
    })


@app.get("/api/status")
def status():
    return jsonify({
        "configured": True,
        "mode": "browser-relay",
        "read_only": True
    })


@app.get("/api/otc")
def otc():
    return jsonify({
        "success": latest["price"] is not None,
        "asset": latest["asset"],
        "price": latest["price"],
        "timestamp": latest["timestamp"],
        "raw": latest["raw"]
    })


@app.post("/api/tick")
def tick():
    data = request.get_json(silent=True) or {}

    asset = data.get("asset")
    price = data.get("price")
    timestamp = data.get("timestamp", time.time())
    raw = data.get("raw")

    if asset and price is not None:
        latest["asset"] = asset
        latest["price"] = price
        latest["timestamp"] = timestamp
        latest["raw"] = raw

        return jsonify({
            "success": True,
            "message": "Tick received"
        })

    return jsonify({
        "success": False,
        "message": "asset and price required"
    }), 400


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(__import__("os").environ.get("PORT", 5000))
    )
