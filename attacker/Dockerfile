FROM kalilinux/kali-rolling:latest

LABEL maintainer="Mjolnir Security"
LABEL description="VULNOT Attacker Workstation - OT Security Tools"

ENV DEBIAN_FRONTEND=noninteractive

# Update and install base tools
RUN apt-get update && apt-get install -y \
    # Network tools
    nmap \
    netcat-openbsd \
    tcpdump \
    wireshark-common \
    tshark \
    hping3 \
    arp-scan \
    masscan \
    net-tools \
    iproute2 \
    iputils-ping \
    dnsutils \
    curl \
    wget \
    # Development tools
    python3 \
    python3-pip \
    python3-venv \
    git \
    vim \
    nano \
    tmux \
    # Metasploit
    metasploit-framework \
    # Additional utilities
    jq \
    tree \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install Python OT security tools
RUN pip3 install --break-system-packages \
    # Modbus tools
    pymodbus \
    modbus-cli \
    # Network analysis
    scapy \
    impacket \
    # OT-specific
    cpppo \
    # Utilities
    requests \
    colorama \
    tabulate \
    rich \
    click

# Create workspace directory
WORKDIR /root/workspace

# Copy custom VULNOT tools
COPY tools/ /root/tools/
COPY scripts/ /root/scripts/

# Make tools executable
RUN chmod +x /root/tools/* /root/scripts/* 2>/dev/null || true

# Add tools to PATH
ENV PATH="/root/tools:/root/scripts:${PATH}"

# Create aliases for common operations
RUN echo 'alias ll="ls -la"' >> /root/.bashrc && \
    echo 'alias scan-modbus="nmap -p 502 --script modbus-discover"' >> /root/.bashrc && \
    echo 'alias plc1="modbus-cli read 10.0.1.10 -p 502"' >> /root/.bashrc && \
    echo 'alias plc2="modbus-cli read 10.0.1.11 -p 502"' >> /root/.bashrc && \
    echo 'alias plc3="modbus-cli read 10.0.1.12 -p 502"' >> /root/.bashrc

# Welcome message
RUN echo '' >> /root/.bashrc && \
    echo 'echo ""' >> /root/.bashrc && \
    echo 'echo "╔═══════════════════════════════════════════════════════════╗"' >> /root/.bashrc && \
    echo 'echo "║     VULNOT - OT Security Training Attacker Workstation    ║"' >> /root/.bashrc && \
    echo 'echo "╠═══════════════════════════════════════════════════════════╣"' >> /root/.bashrc && \
    echo 'echo "║  Target Network: 10.0.1.0/24                              ║"' >> /root/.bashrc && \
    echo 'echo "║  PLCs: 10.0.1.10-12 (Modbus TCP port 502)                 ║"' >> /root/.bashrc && \
    echo 'echo "║                                                           ║"' >> /root/.bashrc && \
    echo 'echo "║  Quick Commands:                                          ║"' >> /root/.bashrc && \
    echo 'echo "║    vulnot-scan     - Discover OT devices                  ║"' >> /root/.bashrc && \
    echo 'echo "║    vulnot-read     - Read PLC registers                   ║"' >> /root/.bashrc && \
    echo 'echo "║    vulnot-write    - Write to PLC registers               ║"' >> /root/.bashrc && \
    echo 'echo "║    vulnot-monitor  - Live process monitoring              ║"' >> /root/.bashrc && \
    echo 'echo "║                                                           ║"' >> /root/.bashrc && \
    echo 'echo "║  ⚠️  FOR TRAINING PURPOSES ONLY                           ║"' >> /root/.bashrc && \
    echo 'echo "╚═══════════════════════════════════════════════════════════╝"' >> /root/.bashrc && \
    echo 'echo ""' >> /root/.bashrc

CMD ["/bin/bash"]
