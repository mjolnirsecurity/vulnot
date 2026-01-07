# Contributing to VULNOT

Thank you for your interest in contributing to VULNOT! This document provides guidelines for contributing to the project.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [How to Contribute](#how-to-contribute)
4. [Development Setup](#development-setup)
5. [Coding Standards](#coding-standards)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Submitting Changes](#submitting-changes)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors.

### Standards

- Be respectful and constructive
- Focus on what is best for the community
- Accept constructive criticism gracefully
- Report unacceptable behavior to security@mjolnirsecurity.com

---

## Getting Started

### Repository

```bash
git clone https://github.com/mjolnirsecurity/vulnot.git
cd vulnot
```

### Understanding the Project

Before contributing, familiarize yourself with:

1. [README.md](../README.md) - Project overview
2. [Architecture](ARCHITECTURE.md) - System design
3. [Installation](INSTALLATION.md) - Setup guide

### Areas of Interest

We welcome contributions in these areas:

| Area | Description |
|------|-------------|
| **Protocols** | New OT protocols (HART, FF, PROFIBUS, Modbus RTU) |
| **Scenarios** | New industrial scenarios and simulations |
| **Attack Tools** | New attack techniques and tools |
| **Detection** | IDS rules and SIEM correlations |
| **Training** | Lab exercises and documentation |
| **Dashboard** | UI improvements and new views |
| **Bug Fixes** | Issue resolution and improvements |

---

## How to Contribute

### Reporting Bugs

1. Check existing [issues](https://github.com/mjolnirsecurity/vulnot/issues)
2. Create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Docker version)
   - Logs if applicable

**Example Bug Report:**

```markdown
## Bug: Water PLC fails to start on macOS

### Environment
- OS: macOS 13.0
- Docker: 24.0.5
- VULNOT: v1.0.0

### Steps to Reproduce
1. Run `docker-compose up -d`
2. Wait 60 seconds
3. Check `docker logs vulnot-water-plc`

### Expected Behavior
PLC should start and accept Modbus connections

### Actual Behavior
Container exits with error: "Address already in use"

### Logs
```
[ERROR] Could not bind to port 502
```
```

### Suggesting Features

1. Check existing feature requests
2. Create an issue with `[Feature]` prefix
3. Describe the use case and benefits

### Security Vulnerabilities

For security issues in VULNOT itself (not the intentional training vulnerabilities):

📧 **security@mjolnirsecurity.com**

Do NOT create public issues for security vulnerabilities.

---

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Git

### Local Development

```bash
# Clone repository
git clone https://github.com/mjolnirsecurity/vulnot.git
cd vulnot

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: .\venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements-dev.txt

# Install Node.js dependencies (dashboard)
cd apps/dashboard
npm install
cd ../..

# Start development environment
docker-compose -f infrastructure/docker/docker-compose.yml up -d redis influxdb
```

### Project Structure

```
vulnot/
├── simulators/          # OT device simulators (Python)
├── attacker/
│   └── scripts/         # Attack tools (Python)
├── defense/
│   ├── ids/             # IDS (Python)
│   └── siem/            # SIEM rules (Python)
├── apps/
│   ├── api/             # Backend (FastAPI)
│   └── dashboard/       # Frontend (Next.js)
├── training/
│   └── labs/            # Lab documentation (Markdown)
├── docs/                # Documentation (Markdown)
└── infrastructure/      # Docker configs
```

---

## Coding Standards

### Python

Follow PEP 8 with these specifics:

```python
# Good
def read_modbus_registers(target: str, start: int, count: int) -> list[int]:
    """Read holding registers from Modbus device.
    
    Args:
        target: IP address of target device
        start: Starting register address
        count: Number of registers to read
        
    Returns:
        List of register values
        
    Raises:
        ConnectionError: If device is not reachable
    """
    pass

# Use type hints
# Use docstrings
# Max line length: 100 characters
# Use snake_case for functions and variables
# Use PascalCase for classes
```

**Tools:**

```bash
# Formatting
black .

# Linting
flake8 .
mypy .
```

### TypeScript/JavaScript

```typescript
// Good
interface ProcessData {
  scenario: string;
  timestamp: Date;
  values: Record<string, number>;
}

async function fetchProcessData(scenario: string): Promise<ProcessData> {
  const response = await fetch(`/api/v1/process/${scenario}`);
  return response.json();
}

// Use TypeScript
// Use interfaces over types
// Use async/await
// Use camelCase for functions and variables
// Use PascalCase for components and interfaces
```

**Tools:**

```bash
# Formatting
npm run format

# Linting
npm run lint
```

### Commit Messages

Follow Conventional Commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation |
| `style` | Formatting |
| `refactor` | Code refactoring |
| `test` | Adding tests |
| `chore` | Maintenance |

**Examples:**

```
feat(simulator): add PROFIBUS protocol support

Implements PROFIBUS DP simulation with:
- Master/slave communication
- Diagnostic messages
- Cyclic data exchange

Closes #123
```

```
fix(api): resolve WebSocket connection timeout

Increase timeout from 30s to 60s to handle
slow network conditions.
```

---

## Testing

### Running Tests

```bash
# Python tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=simulators --cov=attacker --cov-report=html

# JavaScript tests
cd apps/dashboard
npm test
```

### Writing Tests

**Python (pytest):**

```python
# tests/test_modbus_simulator.py
import pytest
from simulators.modbus_water.main import WaterTreatmentPLC

@pytest.fixture
def plc():
    return WaterTreatmentPLC()

def test_read_holding_registers(plc):
    """Test reading holding registers returns expected values."""
    values = plc.read_holding_registers(0, 10)
    assert len(values) == 10
    assert all(isinstance(v, int) for v in values)

def test_write_coil(plc):
    """Test writing coil updates state."""
    plc.write_coil(0, True)
    assert plc.get_coil(0) is True
```

**TypeScript (Jest):**

```typescript
// apps/dashboard/__tests__/ProcessData.test.tsx
import { render, screen } from '@testing-library/react';
import ProcessData from '@/components/ProcessData';

describe('ProcessData', () => {
  it('displays tank level', () => {
    render(<ProcessData level={75} />);
    expect(screen.getByText('75%')).toBeInTheDocument();
  });
});
```

### Test Requirements

- All new features require tests
- Bug fixes should include regression tests
- Maintain 80%+ code coverage

---

## Documentation

### Updating Documentation

Documentation is in Markdown format in the `docs/` directory.

**Guidelines:**

- Use clear, concise language
- Include code examples
- Update table of contents
- Add screenshots for UI changes

### Adding Training Labs

New labs should follow the template:

```markdown
# Lab X: [Title]

## Overview
| Property | Value |
|----------|-------|
| Duration | X min |
| Difficulty | ⭐ Beginner/⭐⭐ Intermediate/⭐⭐⭐ Advanced/⭐⭐⭐⭐ Expert |
| Scenario | Mjolnir Training [Environment] |

## Learning Objectives
1. ...
2. ...

## Prerequisites
- ...

## Lab Instructions

### Part 1: [Section]

[Instructions with code blocks]

### Part 2: [Section]

[Instructions with code blocks]

## Flags

| Flag | Points |
|------|--------|
| flag_name | X |

## Summary

[Key takeaways]
```

---

## Submitting Changes

### Pull Request Process

1. **Fork the repository**

```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR_USERNAME/vulnot.git
git remote add upstream https://github.com/mjolnirsecurity/vulnot.git
```

2. **Create a branch**

```bash
git checkout -b feature/your-feature-name
# or: git checkout -b fix/issue-description
```

3. **Make changes**

```bash
# Make your changes
git add .
git commit -m "feat(scope): description"
```

4. **Keep up to date**

```bash
git fetch upstream
git rebase upstream/main
```

5. **Push and create PR**

```bash
git push origin feature/your-feature-name
# Create PR on GitHub
```

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactoring

## Related Issues
Closes #123

## Testing
- [ ] Unit tests added/updated
- [ ] Manual testing completed
- [ ] All tests passing

## Checklist
- [ ] Code follows project standards
- [ ] Documentation updated
- [ ] No sensitive data in commits
- [ ] PR title follows conventional commits
```

### Review Process

1. Automated checks must pass (linting, tests)
2. At least one maintainer review required
3. Address review feedback
4. Maintainer merges when approved

---

## Questions?

- GitHub Issues: Technical questions
- Email: training@mjolnirsecurity.com (Training-related)
- Security: security@mjolnirsecurity.com

---

*Thank you for contributing to VULNOT!*

*Developed by Milind Bhargava at Mjolnir Security*
