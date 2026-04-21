# 📚 API Reference

Documentazione completa delle API REST del Central Server.

## Base URL

```
http://localhost:8000/api
```

## Autenticazione

Alcune endpoint richiedono autenticazione JWT.

```http
Authorization: Bearer <your-jwt-token>
```

### Ottenere Token

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Endpoints

### Health Check

#### GET /health

Verifica stato sistema.

**Headers:** None required

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "chroma": "connected",
  "timestamp": "2026-01-24T10:00:00Z"
}
```

---

### Metrics

#### POST /metrics

Invia metriche da agent.

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "host_id": "server-01",
  "agent_type": "performance",
  "timestamp": "2026-01-24T10:00:00Z",
  "metrics": {
    "cpu_percent": 45.5,
    "memory_percent": 60.2,
    "disk_percent": 70.1,
    "network_in": 1024000,
    "network_out": 512000
  }
}
```

**Response:** `201 Created`
```json
{
  "id": 123,
  "message": "Metrics stored successfully"
}
```

#### GET /metrics

Recupera metriche memorizzate.

**Query Parameters:**
- `host_id` (optional): Filtra per host
- `agent_type` (optional): Filtra per tipo agent
- `start_time` (optional): ISO timestamp
- `end_time` (optional): ISO timestamp
- `limit` (optional): Max risultati (default: 100)

**Response:**
```json
[
  {
    "id": 123,
    "host_id": "server-01",
    "agent_type": "performance",
    "timestamp": "2026-01-24T10:00:00Z",
    "metrics": {
      "cpu_percent": 45.5,
      "memory_percent": 60.2
    }
  }
]
```

---

### Alerts

#### POST /alerts

Crea nuovo alert.

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "host_id": "server-01",
  "alert_type": "performance",
  "severity": "high",
  "title": "High CPU Usage",
  "description": "CPU usage exceeded 90% for 5 minutes",
  "timestamp": "2026-01-24T10:00:00Z",
  "metadata": {
    "cpu_percent": 95.5,
    "threshold": 90.0,
    "duration_seconds": 300
  }
}
```

**Fields:**
- `severity`: `critical` | `high` | `medium` | `low`
- `alert_type`: `performance` | `malware` | `intrusion` | `code_security`

**Response:** `201 Created`
```json
{
  "id": 456,
  "status": "new",
  "created_at": "2026-01-24T10:00:00Z"
}
```

#### GET /alerts

Lista tutti gli alert.

**Query Parameters:**
- `severity` (optional): Filtra per severity
- `status` (optional): `new` | `investigating` | `resolved` | `false_positive`
- `host_id` (optional): Filtra per host
- `alert_type` (optional): Filtra per tipo
- `limit` (optional): Max risultati
- `offset` (optional): Per paginazione

**Response:**
```json
[
  {
    "id": 456,
    "host_id": "server-01",
    "alert_type": "performance",
    "severity": "high",
    "title": "High CPU Usage",
    "description": "CPU usage exceeded 90%",
    "status": "new",
    "timestamp": "2026-01-24T10:00:00Z",
    "metadata": {},
    "resolution_notes": null
  }
]
```

#### GET /alerts/{alert_id}

Dettagli singolo alert.

**Response:**
```json
{
  "id": 456,
  "host_id": "server-01",
  "alert_type": "performance",
  "severity": "high",
  "title": "High CPU Usage",
  "description": "CPU usage exceeded 90% for 5 minutes",
  "status": "investigating",
  "timestamp": "2026-01-24T10:00:00Z",
  "metadata": {
    "cpu_percent": 95.5,
    "threshold": 90.0
  },
  "resolution_notes": "Investigating high load. Possible malware."
}
```

#### PUT /alerts/{alert_id}

Aggiorna alert esistente.

**Body:**
```json
{
  "status": "resolved",
  "resolution_notes": "False alarm. Planned batch job."
}
```

**Response:** `200 OK`

#### DELETE /alerts/{alert_id}

Elimina alert.

**Response:** `204 No Content`

---

### Vector Search

#### POST /search/similar-alerts

Ricerca semantica alert simili.

**Body:**
```json
{
  "query": "high CPU usage and memory leak",
  "top_k": 5,
  "threshold": 0.7
}
```

**Response:**
```json
{
  "query": "high CPU usage and memory leak",
  "results": [
    {
      "id": "alert-456",
      "content": "CPU usage exceeded 90% for 5 minutes",
      "distance": 0.23,
      "metadata": {
        "alert_id": 456,
        "severity": "high",
        "timestamp": "2026-01-24T10:00:00Z"
      }
    }
  ],
  "search_time_ms": 45
}
```

**Fields:**
- `distance`: 0.0 (identico) - 1.0 (molto diverso)
- Threshold di solito: 0.7 (70% similarity)

#### POST /search/add-document

Aggiungi documento al vector DB (per knowledge base).

**Body:**
```json
{
  "document_id": "kb-article-123",
  "content": "How to respond to DDoS attacks...",
  "metadata": {
    "title": "DDoS Response Playbook",
    "category": "incident_response",
    "tags": ["ddos", "network", "mitigation"]
  }
}
```

**Response:** `201 Created`

---

### Hosts

#### GET /hosts

Lista host monitorati.

**Response:**
```json
[
  {
    "host_id": "server-01",
    "first_seen": "2026-01-20T08:00:00Z",
    "last_seen": "2026-01-24T10:00:00Z",
    "metadata": {
      "os": "Ubuntu 22.04",
      "location": "datacenter-us-east"
    }
  }
]
```

#### GET /hosts/{host_id}

Dettagli singolo host.

**Response:**
```json
{
  "host_id": "server-01",
  "first_seen": "2026-01-20T08:00:00Z",
  "last_seen": "2026-01-24T10:00:00Z",
  "metadata": {
    "os": "Ubuntu 22.04",
    "ip": "ip_<hash>",
    "location": "datacenter-us-east"
  },
  "recent_alerts_count": 5,
  "status": "active"
}
```

#### GET /hosts/{host_id}/metrics

Metriche recenti per host specifico.

**Query Parameters:**
- `limit`: Max risultati (default: 50)
- `start_time`: ISO timestamp
- `end_time`: ISO timestamp

**Response:** Array di metrics (vedi GET /metrics)

#### GET /hosts/{host_id}/alerts

Alert recenti per host specifico.

**Response:** Array di alerts (vedi GET /alerts)

---

### Statistics

#### GET /stats/overview

Statistiche generali sistema.

**Response:**
```json
{
  "total_alerts": 1234,
  "alerts_by_severity": {
    "critical": 45,
    "high": 123,
    "medium": 567,
    "low": 499
  },
  "alerts_by_status": {
    "new": 234,
    "investigating": 89,
    "resolved": 900,
    "false_positive": 11
  },
  "total_hosts": 25,
  "total_metrics": 456789,
  "last_update": "2026-01-24T10:00:00Z"
}
```

#### GET /stats/timeline

Statistiche temporali.

**Query Parameters:**
- `start_time`: ISO timestamp
- `end_time`: ISO timestamp
- `interval`: `hour` | `day` | `week`

**Response:**
```json
{
  "interval": "hour",
  "data": [
    {
      "timestamp": "2026-01-24T10:00:00Z",
      "alerts_created": 12,
      "metrics_received": 3456
    }
  ]
}
```

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Missing required field: host_id",
    "details": {
      "field": "host_id",
      "reason": "required"
    }
  },
  "timestamp": "2026-01-24T10:00:00Z"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request succeeded |
| 201 | Created - Resource created |
| 204 | No Content - Success, no body |
| 400 | Bad Request - Invalid data |
| 401 | Unauthorized - Auth required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

### Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_REQUEST` | Malformed request |
| `MISSING_FIELD` | Required field missing |
| `INVALID_VALUE` | Invalid field value |
| `NOT_FOUND` | Resource not found |
| `UNAUTHORIZED` | Authentication failed |
| `FORBIDDEN` | Permission denied |
| `RATE_LIMIT_EXCEEDED` | Too many requests |

---

## Rate Limiting

API ha rate limiting per prevenire abusi:

- **Default**: 100 requests/minute per IP
- **Authenticated**: 1000 requests/minute

**Headers Response:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1643040000
```

---

## Examples

### Python

```python
import requests

# Health check
response = requests.get("http://localhost:8000/api/health")
print(response.json())

# Send metrics
metrics = {
    "host_id": "my-server",
    "agent_type": "performance",
    "timestamp": "2026-01-24T10:00:00Z",
    "metrics": {
        "cpu_percent": 45.5,
        "memory_percent": 60.2
    }
}
response = requests.post(
    "http://localhost:8000/api/metrics",
    json=metrics
)
print(response.status_code)

# Search similar alerts
search = {
    "query": "high CPU usage",
    "top_k": 5
}
response = requests.post(
    "http://localhost:8000/api/search/similar-alerts",
    json=search
)
print(response.json())
```

### cURL

```bash
# Health check
curl http://localhost:8000/api/health

# Create alert
curl -X POST http://localhost:8000/api/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "host_id": "server-01",
    "alert_type": "performance",
    "severity": "high",
    "title": "High CPU",
    "description": "CPU at 95%",
    "timestamp": "2026-01-24T10:00:00Z"
  }'

# Get alerts
curl "http://localhost:8000/api/alerts?severity=critical&limit=10"
```

---

## Interactive Documentation

Quando il server è running, visita:

**Swagger UI**: http://localhost:8000/docs
**ReDoc**: http://localhost:8000/redoc

---

## Changelog

### v1.0.0 (2026-01-24)
- Initial release
- All core endpoints implemented
- Vector search integration
- Rate limiting

---

Per domande: [email di supporto]
