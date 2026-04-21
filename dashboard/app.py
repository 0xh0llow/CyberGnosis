"""
Dashboard Web Application for Security Monitoring System
Provides web interface for viewing alerts, metrics, and conducting investigations
"""
import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
import requests
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
csrf = CSRFProtect(app)

# Central server configuration
API_URL = os.getenv('CENTRAL_SERVER_URL', 'http://localhost:8000')
API_TOKEN = os.getenv('API_TOKEN')

# HTTP session configuration
session = requests.Session()
session.headers.update({
    'Authorization': f'Bearer {API_TOKEN}',
    'Content-Type': 'application/json'
})


def handle_api_error(f):
    """Decorator to handle API errors gracefully"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            flash(f"Error communicating with server: {str(e)}", "danger")
            return render_template('error.html', error=str(e)), 500
    return decorated_function


@app.route('/')
@handle_api_error
def index():
    """Dashboard overview page"""
    # Get system statistics
    stats_response = session.get(f'{API_URL}/api/stats', timeout=10)
    stats_response.raise_for_status()
    stats = stats_response.json()
    
    # Get recent alerts
    alerts_response = session.get(
        f'{API_URL}/api/alerts',
        params={'limit': 10, 'status': 'new'},
        timeout=10
    )
    alerts_response.raise_for_status()
    alerts = alerts_response.json()
    
    # Get hosts status
    hosts_response = session.get(f'{API_URL}/api/hosts', timeout=10)
    hosts_response.raise_for_status()
    hosts = hosts_response.json()
    
    # Get recent metrics for charts
    metrics_response = session.get(
        f'{API_URL}/api/metrics',
        params={'limit': 50},
        timeout=10
    )
    metrics_response.raise_for_status()
    metrics = metrics_response.json()
    
    return render_template(
        'overview.html',
        stats=stats,
        alerts=alerts,
        hosts=hosts,
        metrics=metrics
    )


@app.route('/alerts')
@handle_api_error
def alerts_list():
    """Alerts list page with filtering"""
    # Get filter parameters
    severity = request.args.get('severity')
    alert_type = request.args.get('type')
    status = request.args.get('status')
    host_id = request.args.get('host')
    
    # Build query parameters
    params = {'limit': 100}
    if severity:
        params['severity'] = severity
    if alert_type:
        params['alert_type'] = alert_type
    if status:
        params['status'] = status
    if host_id:
        params['host_id'] = host_id
    
    # Get alerts
    response = session.get(f'{API_URL}/api/alerts', params=params, timeout=10)
    response.raise_for_status()
    alerts = response.json()
    
    # Get unique values for filters
    hosts_response = session.get(f'{API_URL}/api/hosts', timeout=10)
    hosts = hosts_response.json()
    
    return render_template(
        'alerts.html',
        alerts=alerts,
        hosts=hosts,
        current_filters={
            'severity': severity,
            'type': alert_type,
            'status': status,
            'host': host_id
        }
    )


@app.route('/alerts/<int:alert_id>')
@handle_api_error
def alert_detail(alert_id):
    """Alert detail page with investigation tools"""
    # Get alert details
    response = session.get(f'{API_URL}/api/alerts/{alert_id}', timeout=10)
    response.raise_for_status()
    alert = response.json()
    
    # Get host details
    if alert.get('host_id'):
        host_response = session.get(
            f'{API_URL}/api/hosts',
            params={'host_id': alert['host_id']},
            timeout=10
        )
        host = host_response.json()[0] if host_response.json() else None
    else:
        host = None
    
    # Get metrics around alert time (if available)
    metrics = []
    if alert.get('timestamp') and alert.get('host_id'):
        alert_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
        start_time = alert_time - timedelta(hours=1)
        end_time = alert_time + timedelta(minutes=30)
        
        metrics_response = session.get(
            f'{API_URL}/api/metrics',
            params={
                'host_id': alert['host_id'],
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            },
            timeout=10
        )
        metrics = metrics_response.json() if metrics_response.ok else []
    
    return render_template(
        'alert_detail.html',
        alert=alert,
        host=host,
        metrics=metrics
    )


@app.route('/alerts/<int:alert_id>/update', methods=['POST'])
@handle_api_error
def update_alert(alert_id):
    """Update alert status"""
    status = request.form.get('status')
    notes = request.form.get('notes')
    
    if not status:
        flash("Status is required", "danger")
        return redirect(url_for('alert_detail', alert_id=alert_id))
    
    # Update alert
    update_data = {'status': status}
    if notes:
        update_data['resolution_notes'] = notes
    
    response = session.patch(
        f'{API_URL}/api/alerts/{alert_id}',
        json=update_data,
        timeout=10
    )
    response.raise_for_status()
    
    flash(f"Alert updated to status: {status}", "success")
    return redirect(url_for('alert_detail', alert_id=alert_id))


@app.route('/api/search/similar-alerts', methods=['POST'])
@handle_api_error
def search_similar_alerts():
    """API endpoint for finding similar alerts via vector search"""
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({'error': 'Query parameter required'}), 400
    
    query = data['query']
    top_k = data.get('top_k', 5)
    
    # Call central server vector search API
    response = session.post(
        f'{API_URL}/api/search/similar-alerts',
        json={'query': query, 'top_k': top_k},
        timeout=30
    )
    response.raise_for_status()
    
    return jsonify(response.json())


@app.route('/hosts')
@handle_api_error
def hosts_list():
    """Hosts list page"""
    response = session.get(f'{API_URL}/api/hosts', timeout=10)
    response.raise_for_status()
    hosts = response.json()
    
    # Enrich with recent alert counts
    for host in hosts:
        alerts_response = session.get(
            f'{API_URL}/api/alerts',
            params={
                'host_id': host['host_id'],
                'limit': 100,
                'start_time': (datetime.now() - timedelta(days=7)).isoformat()
            },
            timeout=10
        )
        host['recent_alerts'] = len(alerts_response.json())
    
    return render_template('hosts.html', hosts=hosts)


@app.route('/hosts/<host_id>')
@handle_api_error
def host_detail(host_id):
    """Host detail page with metrics and alerts"""
    # Get host info
    hosts_response = session.get(
        f'{API_URL}/api/hosts',
        params={'host_id': host_id},
        timeout=10
    )
    hosts = hosts_response.json()
    host = hosts[0] if hosts else None
    
    if not host:
        flash(f"Host not found: {host_id}", "danger")
        return redirect(url_for('hosts_list'))
    
    # Get recent metrics
    metrics_response = session.get(
        f'{API_URL}/api/metrics',
        params={
            'host_id': host_id,
            'limit': 100
        },
        timeout=10
    )
    metrics = metrics_response.json()
    
    # Get alerts
    alerts_response = session.get(
        f'{API_URL}/api/alerts',
        params={
            'host_id': host_id,
            'limit': 50
        },
        timeout=10
    )
    alerts = alerts_response.json()
    
    return render_template(
        'host_detail.html',
        host=host,
        metrics=metrics,
        alerts=alerts
    )


@app.route('/search')
@handle_api_error
def search():
    """Global search page"""
    query = request.args.get('q', '')
    
    if not query:
        return render_template('search.html', query=query, results=None)
    
    # Search alerts by text
    alerts_response = session.get(
        f'{API_URL}/api/alerts',
        params={'limit': 100},
        timeout=10
    )
    all_alerts = alerts_response.json()
    
    # Simple text search (can be enhanced with vector search)
    results = {
        'alerts': [
            a for a in all_alerts 
            if query.lower() in a.get('title', '').lower() 
            or query.lower() in a.get('description', '').lower()
        ]
    }
    
    return render_template('search.html', query=query, results=results)


@app.route('/reports')
def reports():
    """Reports page placeholder"""
    return render_template('reports.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Check API connectivity
        response = session.get(f'{API_URL}/health', timeout=5)
        response.raise_for_status()
        
        return jsonify({
            'status': 'healthy',
            'dashboard': 'ok',
            'api': 'ok',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'dashboard': 'ok',
            'api': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html', error="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal error: {error}")
    return render_template('error.html', error="Internal server error"), 500


@app.context_processor
def utility_processor():
    """Inject utility functions into templates"""
    def format_timestamp(timestamp_str):
        """Format ISO timestamp for display"""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return timestamp_str
    
    def severity_color(severity):
        """Get Bootstrap color class for severity"""
        colors = {
            'critical': 'danger',
            'high': 'warning',
            'medium': 'info',
            'low': 'secondary'
        }
        return colors.get(severity, 'secondary')
    
    def status_badge(status):
        """Get Bootstrap badge class for status"""
        badges = {
            'new': 'warning',
            'investigating': 'info',
            'resolved': 'success',
            'false_positive': 'secondary'
        }
        return badges.get(status, 'secondary')
    
    return dict(
        format_timestamp=format_timestamp,
        severity_color=severity_color,
        status_badge=status_badge
    )


if __name__ == '__main__':
    # Check required environment variables
    if not API_TOKEN:
        logger.warning("API_TOKEN not set. Using default for development.")
    
    # Run Flask development server
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('FLASK_PORT', 5000))
    
    logger.info(f"Starting dashboard on port {port}")
    logger.info(f"Connecting to API: {API_URL}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
