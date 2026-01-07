# VULNOT Installation Guide

This guide provides detailed instructions for installing and configuring VULNOT.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Installation](#quick-installation)
3. [Detailed Installation](#detailed-installation)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Updating](#updating)
8. [Uninstallation](#uninstallation)

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| CPU | 4 cores |
| RAM | 8 GB |
| Disk | 20 GB free space |
| Docker | v20.10+ |
| Docker Compose | v2.0+ |

### Recommended Requirements

| Component | Requirement |
|-----------|-------------|
| CPU | 8+ cores |
| RAM | 16 GB |
| Disk | 50 GB SSD |
| Docker | Latest stable |
| Docker Compose | Latest stable |

### Supported Operating Systems

- **Linux**: Ubuntu 20.04+, Debian 11+, CentOS 8+, RHEL 8+
- **macOS**: 12.0+ (Monterey) with Docker Desktop
- **Windows**: Windows 10/11 with WSL2 and Docker Desktop

### Network Ports

The following ports must be available:

| Port | Service | Protocol |
|------|---------|----------|
| 8080 | Dashboard | HTTP |
| 8081 | Grafana | HTTP |
| 9000 | Backend API | HTTP |
| 8553 | Historian | HTTP |
| 10502 | Modbus TCP (Water) | TCP |
| 10102 | S7comm | TCP |
| 4840 | OPC UA | TCP |
| 20000 | DNP3 | TCP |
| 44818 | EtherNet/IP | TCP |
| 47808 | BACnet | UDP |
| 1883 | MQTT | TCP |
| 34964 | PROFINET | TCP |
| 6399 | Redis | TCP |
| 8086 | InfluxDB | HTTP |

> **Note:** Ports may differ if you have other services running. Check `docker-compose.yml` for the actual port mappings.

---

## Quick Installation

For most users, the quick installation is sufficient:

```bash
# Clone the repository
git clone https://github.com/mjolnirsecurity/vulnot.git
cd vulnot

# Start all services
docker-compose -f infrastructure/docker/docker-compose.yml up -d

# Wait for initialization
sleep 60

# Verify installation
docker-compose -f infrastructure/docker/docker-compose.yml ps
```

Access the dashboard at http://localhost:8080

---

## Detailed Installation

### Step 1: Install Prerequisites

#### Linux (Ubuntu/Debian)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in for group changes
```

#### macOS

1. Download and install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
2. Start Docker Desktop
3. Verify: `docker --version && docker-compose --version`

#### Windows (WSL2)

1. Enable WSL2: `wsl --install`
2. Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
3. Enable WSL2 backend in Docker Desktop settings
4. Open WSL2 terminal and verify: `docker --version`

### Step 2: Clone Repository

```bash
# Clone from GitHub
git clone https://github.com/mjolnirsecurity/vulnot.git

# Navigate to project directory
cd vulnot

# Verify structure
ls -la
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (optional)
nano .env
```

Environment variables:

```bash
# Core Configuration
VULNOT_VERSION=1.0.0
REDIS_HOST=redis
REDIS_PORT=6379

# Dashboard
DASHBOARD_PORT=8080
API_PORT=9000
GRAFANA_PORT=8081

# Historian
HISTORIAN_PORT=8553

# Credentials
GRAFANA_ADMIN_PASSWORD=vulnot
INFLUXDB_ADMIN_USER=vulnot
INFLUXDB_ADMIN_PASSWORD=vulnot123
```

### Step 4: Build and Start Services

```bash
# Build all containers (first time only)
docker-compose -f infrastructure/docker/docker-compose.yml build

# Start all services
docker-compose -f infrastructure/docker/docker-compose.yml up -d

# View logs
docker-compose -f infrastructure/docker/docker-compose.yml logs -f
```

### Step 5: Initialize Data

```bash
# Wait for services to be healthy
docker-compose -f infrastructure/docker/docker-compose.yml ps

# Initialize historian with sample data (optional)
docker exec vulnot-historian python /app/init_data.py

# Verify OT simulators are running
docker exec vulnot-water-plc python -c "print('Water PLC OK')"
```

---

## Configuration

### Scenario Configuration

Each scenario can be configured via environment variables or config files:

```yaml
# infrastructure/docker/docker-compose.yml
services:
  water-plc:
    environment:
      - MODBUS_PORT=502
      - TANK_CAPACITY=10000
      - CHLORINE_MAX=5.0
```

### Network Configuration

Custom networks can be configured in `docker-compose.yml`:

```yaml
networks:
  vulnot-ot-water:
    driver: bridge
    ipam:
      config:
        - subnet: 10.0.1.0/24
```

### Security Configuration

For isolated deployments:

```bash
# Restrict external access (host firewall)
sudo ufw allow from 192.168.1.0/24 to any port 8080
sudo ufw deny 8080

# Enable HTTPS (requires certificates)
# Edit nginx.conf in infrastructure/nginx/
```

---

## Verification

### Check Container Status

```bash
# All containers should show "Up"
docker-compose -f infrastructure/docker/docker-compose.yml ps

# Expected output:
# vulnot-redis        Up
# vulnot-influxdb     Up
# vulnot-dashboard    Up
# vulnot-api          Up
# vulnot-water-plc    Up
# vulnot-power-rtu    Up
# vulnot-factory-plc  Up
# ... (all 20+ containers)
```

### Test Connectivity

```bash
# Test dashboard
curl -I http://localhost:8080

# Test API
curl http://localhost:9000/health

# Test Grafana
curl -I http://localhost:8081

# Test Modbus simulator (from attacker container)
docker exec vulnot-attacker-water python3 /root/tools/vulnot-scan -n 10.0.1.0/24
```

### Run Smoke Tests

```bash
# Execute built-in tests
docker exec vulnot-redteam /opt/tests/smoke_test.sh

# Expected output:
# [OK] Modbus connection
# [OK] DNP3 connection
# [OK] S7comm connection
# [OK] OPC UA connection
# [OK] BACnet connection
# [OK] EtherNet/IP connection
# [OK] MQTT connection
# [OK] Historian API
```

---

## Troubleshooting

### Common Issues

#### Containers Won't Start

```bash
# Check for port conflicts
sudo netstat -tulpn | grep -E '8080|9000|502|102'

# Check Docker logs
docker-compose -f infrastructure/docker/docker-compose.yml logs --tail=50

# Restart with fresh state
docker-compose -f infrastructure/docker/docker-compose.yml down -v
docker-compose -f infrastructure/docker/docker-compose.yml up -d
```

#### Out of Memory

```bash
# Check Docker memory usage
docker stats --no-stream

# Increase Docker memory limit (Docker Desktop)
# Settings > Resources > Memory > 8GB+

# Or limit per-container memory
# Add to docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       memory: 512M
```

#### Network Issues

```bash
# Verify Docker networks
docker network ls | grep vulnot

# Recreate networks
docker-compose -f infrastructure/docker/docker-compose.yml down
docker network prune -f
docker-compose -f infrastructure/docker/docker-compose.yml up -d

# Check container connectivity
docker exec vulnot-redteam ping -c 3 10.0.1.10
```

#### Simulator Not Responding

```bash
# Check simulator logs
docker logs vulnot-water-plc --tail=100

# Restart specific simulator
docker-compose -f infrastructure/docker/docker-compose.yml restart water-plc

# Rebuild if necessary
docker-compose -f infrastructure/docker/docker-compose.yml build water-plc
docker-compose -f infrastructure/docker/docker-compose.yml up -d water-plc
```

---

## Updating

### Update to Latest Version

```bash
# Stop services
docker-compose -f infrastructure/docker/docker-compose.yml down

# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose -f infrastructure/docker/docker-compose.yml build --no-cache

# Start services
docker-compose -f infrastructure/docker/docker-compose.yml up -d
```

### Backup Data Before Update

```bash
# Backup InfluxDB data
docker exec vulnot-influxdb influx backup /backup
docker cp vulnot-influxdb:/backup ./influx-backup

# Backup Redis data
docker exec vulnot-redis redis-cli BGSAVE
docker cp vulnot-redis:/data/dump.rdb ./redis-backup.rdb
```

---

## Uninstallation

### Complete Removal

```bash
# Stop and remove containers
docker-compose -f infrastructure/docker/docker-compose.yml down -v

# Remove images
docker images | grep vulnot | awk '{print $3}' | xargs docker rmi -f

# Remove networks
docker network prune -f

# Remove project directory
cd ..
rm -rf vulnot
```

### Keep Data

```bash
# Stop containers only
docker-compose -f infrastructure/docker/docker-compose.yml down

# Data volumes are preserved
docker volume ls | grep vulnot
```

---

## Getting Help

### Resources

- [GitHub Issues](https://github.com/mjolnirsecurity/vulnot/issues)
- [Documentation](https://github.com/mjolnirsecurity/vulnot/tree/main/docs)
- [Training](mailto:training@mjolnirsecurity.com) - Mjolnir Training

### Contact

For installation support during official training, contact Mjolnir Training at training@mjolnirsecurity.com.

---

*VULNOT - Developed by Milind Bhargava at Mjolnir Security*
