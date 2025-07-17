from flask import Flask, render_template, jsonify
from database.db_handler import get_pulses, get_pulse_details
from waitress import serve

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/api/pulses')
def api_pulses():
    """API endpoint to provide a list of recent pulses."""
    pulses = get_pulses(limit=100)
    return jsonify(pulses)

@app.route('/api/pulse/<int:pulse_id>')
def api_pulse_detail(pulse_id):
    """API endpoint for details of a single pulse, including indicators."""
    pulse_details = get_pulse_details(pulse_id)
    return jsonify(pulse_details)

if __name__ == '__main__':
    print("Starting CTI Dashboard Flask server on http://0.0.0.0:8080")
    serve(app, host='0.0.0.0', port=8080)
