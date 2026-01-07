#!/bin/bash
# VULNOT Quick Start Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   ██╗   ██╗██╗   ██╗██╗     ███╗   ██╗ ██████╗ ████████╗     ║"
echo "║   ██║   ██║██║   ██║██║     ████╗  ██║██╔═══██╗╚══██╔══╝     ║"
echo "║   ██║   ██║██║   ██║██║     ██╔██╗ ██║██║   ██║   ██║        ║"
echo "║   ╚██╗ ██╔╝██║   ██║██║     ██║╚██╗██║██║   ██║   ██║        ║"
echo "║    ╚████╔╝ ╚██████╔╝███████╗██║ ╚████║╚██████╔╝   ██║        ║"
echo "║     ╚═══╝   ╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝    ╚═╝        ║"
echo "║                                                               ║"
echo "║         OT Security Training Platform - Phase 1               ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

cd "$PROJECT_ROOT"

case "${1:-start}" in
    start)
        echo "[*] Starting VULNOT platform..."
        docker-compose -f infrastructure/docker/docker-compose.yml up -d
        
        echo ""
        echo "[*] Waiting for services to initialize..."
        sleep 10
        
        echo ""
        echo "╔═══════════════════════════════════════════════════════════════╗"
        echo "║                    VULNOT is Ready!                           ║"
        echo "╠═══════════════════════════════════════════════════════════════╣"
        echo "║                                                               ║"
        echo "║  🖥️  HMI Dashboard:  http://localhost:3000                    ║"
        echo "║  📊 API Docs:       http://localhost:8000/docs                ║"
        echo "║  📈 Grafana:        http://localhost:3001 (admin/vulnot)      ║"
        echo "║                                                               ║"
        echo "║  🔓 Attacker Shell:                                           ║"
        echo "║     docker exec -it vulnot-attacker bash                      ║"
        echo "║                                                               ║"
        echo "║  🎯 Target PLCs:                                              ║"
        echo "║     PLC-INTAKE:      10.0.1.10:502                            ║"
        echo "║     PLC-TREATMENT:   10.0.1.11:502                            ║"
        echo "║     PLC-DISTRIBUTION: 10.0.1.12:502                           ║"
        echo "║                                                               ║"
        echo "╚═══════════════════════════════════════════════════════════════╝"
        echo ""
        ;;
    
    stop)
        echo "[*] Stopping VULNOT platform..."
        docker-compose -f infrastructure/docker/docker-compose.yml down
        echo "[✓] Platform stopped"
        ;;
    
    reset)
        echo "[*] Resetting VULNOT platform..."
        docker-compose -f infrastructure/docker/docker-compose.yml down -v
        docker-compose -f infrastructure/docker/docker-compose.yml up -d
        echo "[✓] Platform reset complete"
        ;;
    
    logs)
        docker-compose -f infrastructure/docker/docker-compose.yml logs -f
        ;;
    
    status)
        docker-compose -f infrastructure/docker/docker-compose.yml ps
        ;;
    
    attack)
        echo "[*] Connecting to attacker workstation..."
        docker exec -it vulnot-attacker bash
        ;;
    
    *)
        echo "Usage: $0 {start|stop|reset|logs|status|attack}"
        exit 1
        ;;
esac
