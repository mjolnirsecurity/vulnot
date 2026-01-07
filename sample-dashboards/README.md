# VULNOT Sample Dashboards

Interactive HTML dashboards demonstrating the HMI interfaces for each VULNOT scenario.

## Available Dashboards

| Dashboard | Scenario | Protocol | File |
|-----------|----------|----------|------|
| Water Treatment Plant | Scenario 1 | Modbus TCP | [water-treatment.html](water-treatment.html) |
| Power Grid Substation | Scenario 2 | DNP3 | [power-grid.html](power-grid.html) |
| Manufacturing Line | Scenario 3 | S7comm | [manufacturing.html](manufacturing.html) |
| Chemical Reactor | Scenario 4 | OPC UA | [chemical-reactor.html](chemical-reactor.html) |
| Building Automation | Scenario 5 | BACnet | [building-automation.html](building-automation.html) |
| Packaging Line | Scenario 6 | EtherNet/IP | [packaging-line.html](packaging-line.html) |
| IIoT Smart Factory | Scenario 7 | MQTT | [iiot-factory.html](iiot-factory.html) |
| CNC Motion Control | Scenario 8 | PROFINET | [cnc-motion.html](cnc-motion.html) |
| OT Historian | Scenario 9 | HTTP API | [historian.html](historian.html) |

## Usage

Simply open any HTML file in a modern web browser. The dashboards are self-contained with embedded CSS and JavaScript for realistic HMI simulation.

```bash
# Open in default browser (macOS)
open water-treatment.html

# Open in default browser (Linux)
xdg-open water-treatment.html

# Or serve via Python HTTP server
python3 -m http.server 8000
# Then visit http://localhost:8000
```

## Features

- **Realistic HMI Design**: Industrial-style interfaces matching real SCADA systems
- **Live Animations**: Simulated real-time data updates, pump animations, and process flows
- **Protocol Information**: Network details, port numbers, and device addresses
- **Interactive Elements**: Clickable buttons, gauges, and status indicators
- **MITRE ATT&CK Context**: Attack vectors and technique mappings

## Custom Dashboards

Need custom dashboards for your organization or training program?

Contact **Mjolnir Security** for:
- Custom scenario development
- Industry-specific HMI designs
- Integration with your SIEM platform
- Enterprise deployment support

**Contact:** sales@mjolnirsecurity.com

---

*VULNOT Sample Dashboards - Developed by Milind Bhargava at Mjolnir Security*
