from flask import Flask, render_template, send_from_directory, jsonify
from flask_cors import CORS
import os

# Import the new Supabase API blueprint
from supabase_api import supabase_api_blueprint

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Register the blueprint for all Supabase API routes
app.register_blueprint(supabase_api_blueprint, url_prefix='/api')

@app.route('/')
def index():
    """Serve the main application page."""
    # This now serves the redesigned frontend
    return render_template('index_redesign.html')

@app.route('/static/<path:path>')
def send_static(path):
    """Serve files from the static directory."""
    return send_from_directory('static', path)

@app.route('/health')
def health_check():
    """A simple health check endpoint."""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # Use the PORT environment variable if available, otherwise default to 5000
    port = int(os.environ.get('PORT', 8080))
    # Running with debug=False to better simulate production and avoid hangs
    app.run(host='0.0.0.0', port=port, debug=False)
