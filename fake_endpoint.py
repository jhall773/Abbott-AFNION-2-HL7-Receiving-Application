from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/a1c", methods=["POST"])
def receive_a1c():
    data = request.get_json()
    print("Received:", data)
    return jsonify({"status": "ok", "received": data})

app.run(port=5000)

