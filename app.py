from flask import Flask, jsonify

app = Flask(__name__)

@app.get("/")
def home():
    return jsonify({
        "status": "online",
        "service": "Quotex Bridge",
        "message": "Bridge is running"
    })

@app.get("/api/status")
def status():
    return jsonify({
        "connected": False,
        "message": "OTC data source not connected yet"
    })

@app.get("/api/otc")
def otc():
    return jsonify({
        "success": False,
        "message": "OTC data source is not connected yet"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
