from flask import Flask, request, jsonify, render_template_string
import json
import os

app = Flask(__name__)

DATA_FILE = "received_data.json"

# Ensure the file exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

@app.route('/upload', methods=['POST'])
def upload():
    data = request.json
    print(f"📥 Received data:\n{data}\n")

    # Save incoming message to file
    with open(DATA_FILE, "r+", encoding="utf-8") as f:
        existing = json.load(f)
        existing.append(data)
        f.seek(0)
        json.dump(existing, f, indent=2)

    return jsonify({"status": "success"}), 200

@app.route('/messages')
def messages():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Render basic HTML
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Received Messages</title>
        <style>
            body { font-family: Arial; margin: 2em; }
            .msg { margin-bottom: 2em; padding: 1em; border: 1px solid #ccc; border-radius: 5px; }
            .email { color: #666; }
            pre { white-space: pre-wrap; word-wrap: break-word; }
        </style>
    </head>
    <body>
        <h1>📨 Received Messages</h1>
        {% for item in data %}
            <div class="msg">
                <strong>{{ item.name }}</strong>
                <div class="email">{{ item.email }}</div>
                <pre>{{ item.message }}</pre>
            </div>
        {% else %}
            <p>No messages received yet.</p>
        {% endfor %}
    </body>
    </html>
    '''
    return render_template_string(html, data=data)

if __name__ == '__main__':
    app.run(port=5000)
