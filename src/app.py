"""Flask app to display MNET MAMA rankings with change tracking."""
from flask import Flask, render_template, jsonify, request
import os
from .fetcher import fetch_current_rankings, extract_rankings_summary
from .storage import init_db, save_rankings, get_latest_rankings, get_recent_changes

APP = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'rankings.db')


@APP.before_request
def setup():
    """Initialize database on first request."""
    if not hasattr(APP, 'db_initialized'):
        init_db(DB_PATH)
        APP.db_initialized = True


@APP.route('/')
def index():
    """Display current rankings."""
    # Try DB first
    rankings = get_latest_rankings(DB_PATH)
    if not rankings:
        # Fallback to fetcher and persist
        rankings = fetch_current_rankings()
        if rankings:
            save_rankings(DB_PATH, rankings)

    # Get recent changes
    changes = get_recent_changes(DB_PATH, limit=20)

    return render_template('index.html', rankings=rankings, changes=changes)


@APP.route('/api/rankings')
def api_rankings():
    """API endpoint for current rankings."""
    rankings = get_latest_rankings(DB_PATH)
    if rankings:
        return jsonify(extract_rankings_summary(rankings))
    return jsonify({'error': 'No rankings available'}), 404


@APP.route('/api/changes')
def api_changes():
    """API endpoint for recent ranking changes."""
    limit = int(request.args.get('limit', 50))
    changes = get_recent_changes(DB_PATH, limit=limit)
    return jsonify({'changes': changes})


@APP.route('/refresh')
def refresh():
    """Manually fetch and update rankings."""
    rankings = fetch_current_rankings()
    if rankings:
        save_rankings(DB_PATH, rankings)
        return jsonify({'status': 'success', 'message': 'Rankings updated'})
    return jsonify({'status': 'error', 'message': 'Failed to fetch rankings'}), 500


if __name__ == '__main__':
    APP.run(debug=True)
