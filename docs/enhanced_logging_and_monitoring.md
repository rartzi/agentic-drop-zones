# Enhanced Logging & Error Handling

This document describes the enhanced logging, error handling, and monitoring capabilities added to the Agentic Drop Zone system.

## 🎯 Overview

The enhanced system provides:
- **Structured JSON logging** with multiple log files
- **Real-time error notifications** via webhooks
- **Workflow monitoring** with timeout detection
- **Health check endpoints** for system monitoring
- **Automatic error recovery** and notifications

## 📊 Features

### 1. Structured Logging System

#### **Log Files Created**
- `logs/agentic_drop_zone.log` - Main application events (INFO+)
- `logs/errors.log` - Errors and critical issues only (ERROR+)
- `logs/workflows.log` - Detailed workflow processing (DEBUG+)

#### **Log Format**
```json
{
  "timestamp": "2025-10-01T15:30:45.123456+00:00",
  "level": "info",
  "event": "Workflow started",
  "workflow_id": "abc123ef",
  "zone_name": "Echo Drop Zone",
  "file_path": "/path/to/file.txt",
  "agent": "claude_code",
  "model": "sonnet"
}
```

### 2. Error Notification System

#### **Webhook Integration**
Supports any webhook-compatible service (Slack, Discord, Microsoft Teams, etc.)

#### **Configuration**
```bash
# .env file
NOTIFICATION_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
NOTIFICATION_MIN_LEVEL=error  # info, warning, error, critical
NOTIFICATION_TIMEOUT=10
```

#### **Notification Payload**
```json
{
  "timestamp": "2025-10-01T15:30:45.123456+00:00",
  "level": "error",
  "title": "Workflow Failed: Echo Drop Zone",
  "message": "File: test.txt\nAgent: claude_code\nError: Connection timeout",
  "system": "agentic-drop-zone",
  "context": {
    "workflow_id": "abc123ef",
    "agent": "claude_code",
    "file_path": "/path/to/test.txt",
    "zone_name": "Echo Drop Zone"
  }
}
```

### 3. Workflow Monitoring

#### **Real-time Tracking**
- Each workflow gets a unique 8-character ID
- Start/end times tracked automatically
- Duration and status monitoring
- Automatic timeout detection (5 minutes default)

#### **Workflow States**
- `PENDING` - Queued for processing
- `RUNNING` - Currently being processed
- `COMPLETED` - Successfully finished
- `FAILED` - Error occurred during processing
- `TIMEOUT` - Exceeded maximum execution time

### 4. Health Check Endpoints

#### **Available Endpoints**

**Basic Health Check**
```bash
curl http://localhost:8080/health
```
```json
{
  "status": "healthy",
  "timestamp": "2025-10-01T15:30:45.123456+00:00",
  "system": "agentic-drop-zone"
}
```

**Detailed Health Information**
```bash
curl http://localhost:8080/health/detailed
```
```json
{
  "active_workflows": 2,
  "completed_workflows": 15,
  "oldest_active_workflow": "2025-10-01T15:25:30.000Z",
  "system_status": "healthy",
  "timestamp": "2025-10-01T15:30:45.123456+00:00",
  "drop_zones": 5,
  "notification_config": {
    "enabled": true,
    "webhook_configured": true,
    "min_level": "error"
  }
}
```

**Active Workflows**
```bash
curl http://localhost:8080/workflows/active
```

**Recent Workflows**
```bash
curl http://localhost:8080/workflows/recent
```

## 🚀 Usage Examples

### Production Deployment with Process Management

#### Recommended Startup Method
```bash
# Start with full process management
./start.sh

# The startup script automatically:
# - Checks port availability (8080/8081)
# - Prevents duplicate instances
# - Creates PID file for tracking
# - Provides colored status output
# - Sets up signal handlers for cleanup
```

#### Health Monitoring
```bash
# Check if system is running
./start.sh status

# Monitor health endpoints
curl http://localhost:8080/health/detailed

# Check active workflows
curl http://localhost:8080/workflows/active
```

#### Graceful Shutdown
```bash
# Clean shutdown with process cleanup
./stop.sh

# The stop script automatically:
# - Sends SIGTERM for graceful shutdown
# - Waits for process termination
# - Force kills if needed (SIGKILL)
# - Cleans up PID files
# - Frees all ports (8080/8081)
# - Removes any remaining processes
```

### Setting Up Slack Notifications

1. **Create Slack Webhook**
   - Go to Slack App settings
   - Create a new Incoming Webhook
   - Copy the webhook URL

2. **Configure Environment**
   ```bash
   # .env
   NOTIFICATION_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WORKSPACE/TOKEN
   NOTIFICATION_MIN_LEVEL=error
   ```

3. **Test Notification**
   ```bash
   # Drop a file that will cause an error to test notifications
   echo "invalid content" > agentic_drop_zone/echo_zone/test_error.txt
   ```

### Monitoring with Health Checks

#### **Basic Monitoring Script**
```bash
#!/bin/bash
# monitor_health.sh

HEALTH_URL="http://localhost:8080/health/detailed"

while true; do
    response=$(curl -s "$HEALTH_URL")
    active=$(echo "$response" | jq '.active_workflows')

    if [ "$active" -gt 5 ]; then
        echo "WARNING: High workflow load - $active active workflows"
    fi

    echo "$(date): Active workflows: $active"
    sleep 30
done
```

#### **Integration with Monitoring Systems**

**Prometheus Metrics** (future enhancement)
```yaml
# prometheus.yml
- job_name: 'agentic-drop-zone'
  static_configs:
    - targets: ['localhost:8080']
  metrics_path: '/metrics'
```

### Advanced Logging Configuration

#### **Custom Log Levels**
```python
import structlog
logger = structlog.get_logger("my_component")

logger.debug("Detailed debugging info")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred", error="details")
logger.critical("Critical system failure")
```

#### **Structured Context**
```python
# Automatic context from workflow
logger.info(
    "Processing started",
    workflow_id="abc123ef",
    file_path="/path/to/file.txt",
    file_size_bytes=1024,
    zone_name="Echo Drop Zone"
)
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NOTIFICATION_WEBHOOK_URL` | None | Webhook URL for notifications |
| `NOTIFICATION_MIN_LEVEL` | `error` | Minimum level to send notifications |
| `NOTIFICATION_TIMEOUT` | `10` | Webhook request timeout (seconds) |
| `HEALTH_SERVER_PORT` | `8080` | Port for health check endpoints |
| `HEALTH_SERVER_HOST` | `localhost` | Host for health check server |

### Timeout Configuration

```python
# In workflow_monitor initialization
workflow_monitor.timeout_seconds = 600  # 10 minutes instead of default 5
```

### Log File Rotation

For production environments, configure log rotation:

```bash
# /etc/logrotate.d/agentic-drop-zone
/path/to/agentic-drop-zones/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 user group
}
```

## 🐛 Troubleshooting

### Common Issues

#### **Notifications Not Sending**
1. Check webhook URL is correct
2. Verify network connectivity
3. Check notification level threshold
4. Review error logs: `tail -f logs/errors.log`

#### **Health Server Won't Start**
1. Check port 8080 is available: `lsof -i :8080`
2. Verify FastAPI dependencies installed
3. Check logs for detailed error messages

#### **Workflows Timing Out**
1. Review timeout threshold (default 5 minutes)
2. Check system resources and Claude Code performance
3. Monitor active workflows: `curl localhost:8080/workflows/active`

### Debug Commands

```bash
# Check log files
tail -f logs/agentic_drop_zone.log
tail -f logs/errors.log
tail -f logs/workflows.log

# Test health endpoints
curl localhost:8080/health
curl localhost:8080/health/detailed
curl localhost:8080/workflows/active

# Test notification manually
curl -X POST "$NOTIFICATION_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test notification from Agentic Drop Zone"}'
```

## 📈 Benefits

### **Before vs After**

| Aspect | Before | After |
|--------|--------|-------|
| **Error Visibility** | Console only | Structured logs + webhooks |
| **Workflow Tracking** | None | Full lifecycle monitoring |
| **Debugging** | Manual investigation | Searchable JSON logs |
| **Failure Recovery** | Manual restart | Automatic timeout detection |
| **System Health** | Unknown | Real-time API endpoints |
| **Production Ready** | Development only | Enterprise monitoring |

### **Operational Improvements**

- **Faster Issue Detection**: Immediate webhook notifications
- **Better Debugging**: Structured logs with context
- **Proactive Monitoring**: Health check integration
- **Automatic Recovery**: Timeout detection and cleanup
- **Historical Analysis**: Complete workflow metrics

## 🔮 Future Enhancements

### Planned Features

1. **Metrics Collection**: Prometheus/Grafana integration
2. **Database Persistence**: SQLite/PostgreSQL for metrics
3. **Retry Logic**: Automatic retry with exponential backoff
4. **Circuit Breaker**: Prevent cascading failures
5. **Performance Analytics**: Workflow performance trends
6. **Custom Dashboards**: Real-time monitoring interfaces

### Integration Possibilities

- **Slack Bot**: Interactive workflow management
- **Grafana Dashboards**: Visual monitoring
- **PagerDuty**: Critical alert escalation
- **Datadog/New Relic**: APM integration
- **Kubernetes**: Health probes and metrics