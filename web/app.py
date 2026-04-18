#!/usr/bin/env python3
"""
AI Drawing Board - Web Version
Flask server to serve the web application
"""

from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')


@app.route('/')
def index():
    """Serve the main drawing board page."""
    return render_template('index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('static', filename)


if __name__ == '__main__':
    print("\n=== AI Drawing Board - Web Version ===")
    print("Open https://localhost:5000 in your browser")
    print("(Accept the security warning for the self-signed certificate)")
    print("Make sure to allow camera access when prompted")
    print("======================================\n")
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context='adhoc')
