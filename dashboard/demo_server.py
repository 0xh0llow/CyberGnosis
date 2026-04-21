#!/usr/bin/env python3
"""
Quick demo server per testare la dashboard senza Docker.
Usa dati mock per mostrare le funzionalità.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
import random

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.secret_key = 'demo-secret-key-not-for-production'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.jinja_env.cache = {}

# Mock data
MOCK_HOSTS = [
    {
        'host_id': 'web-server-01',
        'last_seen': (datetime.utcnow() - timedelta(minutes=2)).isoformat() + 'Z',
        'metadata': {
            'os': 'Ubuntu 22.04', 
            'location': 'Milano, Italia',
            'cliente': 'Rossi Informatica S.r.l.',
            'partita_iva': 'IT12345678901'
        },
        'recent_alerts': 3
    },
    {
        'host_id': 'db-server-01',
        'last_seen': (datetime.utcnow() - timedelta(minutes=5)).isoformat() + 'Z',
        'metadata': {
            'os': 'Ubuntu 20.04', 
            'location': 'Roma, Italia',
            'cliente': 'Tech Solutions S.p.A.',
            'partita_iva': 'IT98765432109'
        },
        'recent_alerts': 1
    },
    {
        'host_id': 'app-server-01',
        'last_seen': (datetime.utcnow() - timedelta(minutes=1)).isoformat() + 'Z',
        'metadata': {
            'os': 'CentOS 8', 
            'location': 'Torino, Italia',
            'cliente': 'Marco Bianchi',
            'partita_iva': 'IT11223344556'
        },
        'recent_alerts': 0
    }
]

MOCK_ALERTS = [
    {
        'id': 1,
        'host_id': 'web-server-01',
        'alert_type': 'performance',
        'severity': 'critical',
        'title': 'High CPU Usage Detected',
        'description': 'CPU usage exceeded 95% for 10 minutes continuously',
        'timestamp': (datetime.utcnow() - timedelta(hours=1)).isoformat() + 'Z',
        'status': 'new',
        'metadata': {'cpu_percent': 97.5, 'threshold': 90}
    },
    {
        'id': 2,
        'host_id': 'web-server-01',
        'alert_type': 'intrusion',
        'severity': 'high',
        'title': 'Multiple Failed SSH Login Attempts',
        'description': 'Detected 15 failed SSH login attempts from same IP',
        'timestamp': (datetime.utcnow() - timedelta(hours=2)).isoformat() + 'Z',
        'status': 'investigating',
        'metadata': {'failed_attempts': 15, 'source_ip': 'ip_hash_abc123'}
    },
    {
        'id': 3,
        'host_id': 'db-server-01',
        'alert_type': 'malware',
        'severity': 'critical',
        'title': 'Suspicious Process Detected',
        'description': 'Process with high entropy and suspicious network activity',
        'timestamp': (datetime.utcnow() - timedelta(hours=3)).isoformat() + 'Z',
        'status': 'new',
        'metadata': {'process': 'proc_hash_xyz789', 'entropy': 7.8}
    },
    {
        'id': 4,
        'host_id': 'app-server-01',
        'alert_type': 'code_security',
        'severity': 'medium',
        'title': 'SQL Injection Vulnerability Found',
        'description': 'Code scanner detected potential SQL injection in user input handler',
        'timestamp': (datetime.utcnow() - timedelta(hours=5)).isoformat() + 'Z',
        'status': 'resolved',
        'resolution_notes': 'Fixed by parameterizing queries. Deployed patch v1.2.3'
    }
]

MOCK_METRICS = []
for i in range(20):
    timestamp = datetime.utcnow() - timedelta(minutes=i*3)
    MOCK_METRICS.append({
        'timestamp': timestamp.isoformat() + 'Z',
        'metrics': {
            'cpu_percent': random.uniform(30, 70) + (random.uniform(-10, 20) if i < 5 else 0),
            'memory_percent': random.uniform(40, 60),
            'disk_percent': random.uniform(50, 65)
        }
    })
MOCK_METRICS.reverse()

# Template filters
def format_timestamp(timestamp_str):
    """Format ISO timestamp to readable format"""
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
    """Get Bootstrap color class for status"""
    colors = {
        'new': 'warning',
        'investigating': 'info',
        'resolved': 'success',
        'false_positive': 'secondary'
    }
    return colors.get(status, 'secondary')

# Context processor to make functions available to all templates
@app.context_processor
def utility_processor():
    return {
        'format_timestamp': format_timestamp,
        'severity_color': severity_color,
        'status_badge': status_badge
    }

# Routes
@app.route('/')
def index():
    stats = {
        'alerts_by_severity': {
            'critical': sum(1 for a in MOCK_ALERTS if a['severity'] == 'critical'),
            'high': sum(1 for a in MOCK_ALERTS if a['severity'] == 'high'),
            'medium': sum(1 for a in MOCK_ALERTS if a['severity'] == 'medium'),
            'low': sum(1 for a in MOCK_ALERTS if a['severity'] == 'low'),
        },
        'total_metrics': 1234
    }
    recent_alerts = sorted(MOCK_ALERTS, key=lambda x: x['timestamp'], reverse=True)[:5]
    return render_template('overview.html', 
                         stats=stats, 
                         alerts=recent_alerts,
                         hosts=MOCK_HOSTS,
                         metrics=MOCK_METRICS[:10])

@app.route('/alerts')
def alerts_list():
    current_filters = {
        'severity': request.args.get('severity', ''),
        'type': request.args.get('type', ''),
        'status': request.args.get('status', ''),
        'host': request.args.get('host', '')
    }
    
    filtered_alerts = MOCK_ALERTS
    if current_filters['severity']:
        filtered_alerts = [a for a in filtered_alerts if a['severity'] == current_filters['severity']]
    if current_filters['status']:
        filtered_alerts = [a for a in filtered_alerts if a['status'] == current_filters['status']]
    
    return render_template('alerts.html', 
                         alerts=filtered_alerts,
                         hosts=MOCK_HOSTS,
                         current_filters=current_filters)

@app.route('/alerts/<int:alert_id>')
def alert_detail(alert_id):
    alert = next((a for a in MOCK_ALERTS if a['id'] == alert_id), None)
    if not alert:
        return render_template('error.html', error='Alert not found'), 404
    
    host = next((h for h in MOCK_HOSTS if h['host_id'] == alert['host_id']), None)
    metrics = MOCK_METRICS[:10]
    
    return render_template('alert_detail.html', 
                         alert=alert, 
                         host=host,
                         metrics=metrics)

@app.route('/alerts/<int:alert_id>/update', methods=['POST'])
def update_alert(alert_id):
    alert = next((a for a in MOCK_ALERTS if a['id'] == alert_id), None)
    if alert:
        alert['status'] = request.form.get('status', alert['status'])
        alert['resolution_notes'] = request.form.get('notes', alert.get('resolution_notes'))
    return redirect(url_for('alert_detail', alert_id=alert_id))

@app.route('/api/search/similar-alerts', methods=['POST'])
def search_similar_alerts():
    data = request.get_json()
    # Mock similar alerts
    results = [
        {
            'content': a['description'],
            'distance': random.uniform(0.1, 0.5),
            'metadata': {
                'title': a['title'],
                'severity': a['severity'],
                'timestamp': a['timestamp']
            }
        }
        for a in MOCK_ALERTS[:3]
    ]
    return jsonify({'results': results})

@app.route('/hosts')
def hosts_list():
    return render_template('hosts.html', hosts=MOCK_HOSTS)

@app.route('/hosts/<host_id>')
def host_detail(host_id):
    host = next((h for h in MOCK_HOSTS if h['host_id'] == host_id), None)
    if not host:
        return render_template('error.html', error='Host not found'), 404
    
    host_alerts = [a for a in MOCK_ALERTS if a['host_id'] == host_id]
    return render_template('host_detail.html',
                         host=host,
                         alerts=host_alerts,
                         metrics=MOCK_METRICS[:15])

@app.route('/search')
def search():
    query = request.args.get('q', '')
    results = {'alerts': []} if not query else {'alerts': MOCK_ALERTS[:2]}
    return render_template('search.html', query=query, results=results)

@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/presentazione_simple')
def presentazione_simple():
    """Serve la presentazione HTML semplice per il pitch"""
    presentazione_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'presentazione_simple.html')
    if os.path.exists(presentazione_path):
        with open(presentazione_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Presentazione non trovata", 404

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'mode': 'demo'})

@app.route('/presentazione')
def presentazione():
    """Serve la presentazione HTML per il pitch"""
    presentazione_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'presentazione.html')
    if os.path.exists(presentazione_path):
        with open(presentazione_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Presentazione non trovata", 404

if __name__ == '__main__':
    # Register template filters
    app.add_template_filter(format_timestamp, 'format_timestamp')
    app.add_template_filter(severity_color, 'severity_color')
    app.add_template_filter(status_badge, 'status_badge')
    
    print("\n" + "="*60)
    print("🚀 CyberGnosis Demo Server")
    print("="*60)
    print("\n📊 Dashboard URL: http://localhost:5000")
    print("📝 Modalità: DEMO con dati mock")
    print("\n💡 Features disponibili:")
    print("   - Overview dashboard con statistiche")
    print("   - Lista alert con filtri")
    print("   - Dettaglio alert con investigation tools")
    print("   - Host monitoring")
    print("   - Semantic search (simulato)")
    print("\n⚠️  Nota: Questo è un server demo senza backend reale")
    print("   Per ambiente completo usa: docker-compose up")
    print("\n🛑 Premi Ctrl+C per fermare il server")
    print("="*60 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000)
