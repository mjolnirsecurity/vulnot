# VULNOT Integrations

This directory contains integrations with external platforms and tools.

## Available Integrations

### SIEM Platforms

Forward OT security logs to your SIEM of choice:

| Platform | Path | Documentation |
|----------|------|---------------|
| Sumo Logic | [siem/sumologic](siem/sumologic/) | Primary SIEM integration |
| Splunk | [siem/splunk](siem/splunk/) | Splunk HEC integration |
| ELK Stack | [siem/elk](siem/elk/) | Elasticsearch integration |
| Google Chronicle | [siem/chronicle](siem/chronicle/) | Chronicle UDM integration |

See [siem/README.md](siem/README.md) for details.

## Planned Integrations

- **SOAR**: Palo Alto XSOAR, Splunk SOAR, IBM Resilient
- **Ticketing**: ServiceNow, Jira
- **Threat Intel**: MISP, OpenCTI, ThreatConnect
- **Vulnerability Management**: Tenable, Qualys

---

*VULNOT - Developed by Milind Bhargava at Mjolnir Security*
