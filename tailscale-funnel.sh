#!/bin/bash

# Tailscale Funnel Management Script
# This script handles Tailscale Funnel startup, network connectivity, and automatic reconnection

set -e

# Configuration
FUNNEL_PORT=${TAILSCALE_FUNNEL_PORT:-8000}
FUNNEL_HOSTNAME=${TAILSCALE_FUNNEL_HOSTNAME:-pgshospital}
LOG_FILE="/home/ubuntu/Fastag/logs/tailscale-funnel.log"
PID_FILE="/home/ubuntu/Fastag/tailscale-funnel.pid"

# Create logs directory if it doesn't exist
mkdir -p /home/ubuntu/Fastag/logs

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if Tailscale is running
check_tailscale() {
    if ! command -v tailscale >/dev/null 2>&1; then
        log "ERROR: Tailscale is not installed"
        return 1
    fi
    
    if ! tailscale status >/dev/null 2>&1; then
        log "ERROR: Tailscale is not running"
        return 1
    fi
    
    return 0
}

# Check if the target port is available
check_port() {
    if ! netstat -tlnp 2>/dev/null | grep -q ":$FUNNEL_PORT "; then
        log "WARNING: Port $FUNNEL_PORT is not listening. Waiting for service to start..."
        return 1
    fi
    return 0
}

# Start Funnel
start_funnel() {
    log "Starting Tailscale Funnel for port $FUNNEL_PORT..."
    
    # Kill any existing funnel processes
    pkill -f "tailscale funnel" || true
    
    # Start the funnel
    if tailscale funnel --bg "$FUNNEL_PORT" >/dev/null 2>&1; then
        log "SUCCESS: Funnel started successfully"
        log "Funnel URL: https://${FUNNEL_HOSTNAME}.tail1b76dc.ts.net/"
        return 0
    else
        log "ERROR: Failed to start funnel"
        return 1
    fi
}

# Stop Funnel
stop_funnel() {
    log "Stopping Tailscale Funnel..."
    pkill -f "tailscale funnel" || true
    log "Funnel stopped"
}

# Main loop
main() {
    log "Starting Tailscale Funnel service..."
    
    # Write PID file
    echo $$ > "$PID_FILE"
    
    # Trap signals for graceful shutdown
    trap 'log "Received shutdown signal"; stop_funnel; rm -f "$PID_FILE"; exit 0' SIGTERM SIGINT
    
    while true; do
        # Check if Tailscale is available
        if ! check_tailscale; then
            log "Tailscale not available, waiting 30 seconds..."
            sleep 30
            continue
        fi
        
        # Check if the target service is running
        if ! check_port; then
            log "Target service not available on port $FUNNEL_PORT, waiting 10 seconds..."
            sleep 10
            continue
        fi
        
        # Start funnel
        if start_funnel; then
            log "Funnel is running. Monitoring for issues..."
            
            # Monitor funnel status
            while true; do
                # Check if funnel is still running
                if ! pgrep -f "tailscale funnel" >/dev/null; then
                    log "WARNING: Funnel process died, restarting..."
                    break
                fi
                
                # Check if Tailscale is still connected
                if ! check_tailscale; then
                    log "WARNING: Tailscale connection lost, restarting funnel..."
                    break
                fi
                
                # Check if target service is still available
                if ! check_port; then
                    log "WARNING: Target service not available, waiting..."
                    sleep 10
                    continue
                fi
                
                # Everything is good, sleep for a bit
                sleep 30
            done
        else
            log "Failed to start funnel, retrying in 30 seconds..."
            sleep 30
        fi
    done
}

# Handle command line arguments
case "${1:-}" in
    start)
        main
        ;;
    stop)
        stop_funnel
        if [ -f "$PID_FILE" ]; then
            kill $(cat "$PID_FILE") 2>/dev/null || true
            rm -f "$PID_FILE"
        fi
        ;;
    status)
        if pgrep -f "tailscale funnel" >/dev/null; then
            echo "Funnel is running"
            tailscale funnel --list 2>/dev/null || echo "No active funnels"
        else
            echo "Funnel is not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac 