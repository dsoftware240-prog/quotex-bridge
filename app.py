import os
import json
import time
import websocket

from flask import Flask, jsonify, request

app = Flask(__name__)

QUOTEX_SSID = os.getenv("QUOTEX_SSID", "").strip()

# Quotex WebSocket endpoint.
# Can be changed in Faable Variables using QUOTEX_WS_URL.
WS_URL = os.getenv(
    "QUOTEX_WS_URL",
    "wss://ws2.market-qx.trade/socket.io/?EIO=3&transport=websocket"
)


def get_session():
    """
    Accept either:
    1. Raw SSID/session token
    2. Full 42["authorization", {...}] message
    """
    value = QUOTEX_SSID.strip()

    if not value:
        return ""

    if value.startswith("42"):
        try:
            payload = json.loads(value[2:])
            if isinstance(payload, list) and len(payload) >= 2:
                data = payload[1]
                return data.get("session", "")
        except Exception:
            pass

    return value


def get_otc_data(asset, period):
    session = get_session()

    if not session:
        return {
            "success": False,
            "error": "QUOTEX_SSID is not configured"
        }

    ws = None

    try:
        ws = websocket.create_connection(
            WS_URL,
            timeout=8,
            origin="https://qxbroker.com"
        )

        # Socket.IO / Engine.IO handshake
        first = ws.recv()

        # Socket.IO namespace connection
        ws.send("40")

        # Authenticate
        auth = [
            "authorization",
            {
                "session": session,
                "isDemo": 0,
                "tournamentId": 0
            }
        ]

        ws.send("42" + json.dumps(auth, separators=(",", ":")))

        # Ask Quotex for instrument information / stream.
        update = [
            "instruments/update",
            {
                "asset": asset,
                "period": period
            }
        ]

        ws.send("42" + json.dumps(update, separators=(",", ":")))

        # Also request tick data.
        ws.send('42["tick"]')

        deadline = time.time() + 7
        messages = []

        while time.time() < deadline:
            remaining = max(0.2, deadline - time.time())
            ws.settimeout(remaining)

            try:
                message = ws.recv()
            except Exception:
                break

            if not message:
                continue

            # Keep Socket.IO alive.
            if message == "2":
                ws.send("3")
                continue

            if isinstance(message, bytes):
                continue

            messages.append(message)

            # Parse Socket.IO event messages.
            if message.startswith("42"):
                try:
                    payload = json.loads(message[2:])

                    if isinstance(payload, list) and len(payload) >= 2:
                        event = payload[0]
                        data = payload[1]

                        # Return useful market/instrument response.
                        if event in (
                            "instruments/update",
                            "tick",
                            "candle",
                            "candles",
                            "quote"
                        ):
                            return {
                                "success": True,
                                "asset": asset,
                                "period": period,
                                "event": event,
                                "data": data
                            }

                except Exception:
                    continue

        return {
            "success": False,
            "asset": asset,
            "period": period,
            "error": "No OTC market-data response received",
            "messages_received": len(messages)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass


@app.get("/")
def home():
    return jsonify({
        "status": "online",
        "service": "Quotex OTC Read-Only Bridge",
        "message": "Bridge is running"
    })


@app.get("/api/status")
def status():
    return jsonify({
        "configured": bool(QUOTEX_SSID),
        "websocket": WS_URL,
        "mode": "read-only"
    })


@app.get("/api/otc")
def otc():
    asset = request.args.get("asset", "EURUSD_otc")
    period = request.args.get("period", "60")

    try:
        period = int(period)
    except ValueError:
        period = 60

    result = get_otc_data(asset, period)
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
