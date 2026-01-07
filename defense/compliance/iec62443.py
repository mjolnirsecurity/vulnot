"""
VULNOT IEC 62443 Compliance Assessment Framework
Automated assessment against IEC 62443 security requirements

IEC 62443 Structure:
- Part 2: Policies & Procedures
- Part 3: System Security Requirements
- Part 4: Component Security Requirements

Security Levels (SL):
- SL 1: Protection against casual or coincidental violation
- SL 2: Protection against intentional violation using simple means
- SL 3: Protection against sophisticated attack with moderate resources
- SL 4: Protection against state-sponsored attack with extensive resources
"""

import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime


class SecurityLevel(Enum):
    SL0 = 0  # No requirements
    SL1 = 1  # Low
    SL2 = 2  # Medium
    SL3 = 3  # High
    SL4 = 4  # Critical


class ComplianceStatus(Enum):
    NOT_ASSESSED = "not_assessed"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    COMPLIANT = "compliant"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class Requirement:
    """Single compliance requirement"""
    id: str
    name: str
    description: str
    category: str
    security_level: SecurityLevel
    status: ComplianceStatus = ComplianceStatus.NOT_ASSESSED
    evidence: str = ""
    notes: str = ""
    last_assessed: Optional[str] = None
    

@dataclass
class ControlFamily:
    """Family of related controls"""
    id: str
    name: str
    description: str
    requirements: List[Requirement] = field(default_factory=list)
    
    @property
    def compliance_score(self) -> float:
        if not self.requirements:
            return 0.0
        compliant = sum(1 for r in self.requirements 
                       if r.status in [ComplianceStatus.COMPLIANT, ComplianceStatus.NOT_APPLICABLE])
        return (compliant / len(self.requirements)) * 100


# =============================================================================
# IEC 62443-3-3 SYSTEM SECURITY REQUIREMENTS
# =============================================================================

IEC_62443_REQUIREMENTS = {
    "FR1": ControlFamily(
        id="FR1",
        name="Identification and Authentication Control",
        description="Identify and authenticate all users before allowing access",
        requirements=[
            Requirement(
                id="SR 1.1",
                name="Human user identification and authentication",
                description="The control system shall provide the capability to identify and authenticate all human users",
                category="Authentication",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 1.2",
                name="Software process and device identification",
                description="The control system shall provide the capability to identify and authenticate all software processes and devices",
                category="Authentication",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 1.3",
                name="Account management",
                description="The control system shall provide the capability to support the management of all accounts",
                category="Account Management",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 1.4",
                name="Identifier management",
                description="The control system shall provide the capability to support the management of identifiers",
                category="Identity Management",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 1.5",
                name="Authenticator management",
                description="The control system shall provide the capability to manage authenticators",
                category="Authentication",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 1.6",
                name="Wireless access management",
                description="The control system shall provide the capability to identify and authenticate all wireless users",
                category="Wireless Security",
                security_level=SecurityLevel.SL2
            ),
            Requirement(
                id="SR 1.7",
                name="Strength of password-based authentication",
                description="The control system shall provide the capability to enforce configurable password strength",
                category="Authentication",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 1.8",
                name="Public key infrastructure certificates",
                description="The control system shall support PKI certificates for authentication",
                category="PKI",
                security_level=SecurityLevel.SL2
            ),
            Requirement(
                id="SR 1.9",
                name="Strength of public key authentication",
                description="The control system shall provide capability to validate the strength of PKI authentication",
                category="PKI",
                security_level=SecurityLevel.SL2
            ),
            Requirement(
                id="SR 1.10",
                name="Authenticator feedback",
                description="The control system shall obscure feedback of authentication information during authentication",
                category="Authentication",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 1.11",
                name="Unsuccessful login attempts",
                description="The control system shall enforce a limit of consecutive invalid login attempts",
                category="Authentication",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 1.12",
                name="System use notification",
                description="The control system shall provide the capability to display a configurable system use notification",
                category="Access Control",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 1.13",
                name="Access via untrusted networks",
                description="The control system shall provide the capability to monitor and control access via untrusted networks",
                category="Network Security",
                security_level=SecurityLevel.SL1
            ),
        ]
    ),
    
    "FR2": ControlFamily(
        id="FR2",
        name="Use Control",
        description="Enforce assigned privileges of an authenticated user",
        requirements=[
            Requirement(
                id="SR 2.1",
                name="Authorization enforcement",
                description="The control system shall provide the capability to enforce authorizations assigned to all human users",
                category="Authorization",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 2.2",
                name="Wireless use control",
                description="The control system shall provide the capability to authorize and monitor the use of wireless devices",
                category="Wireless Security",
                security_level=SecurityLevel.SL2
            ),
            Requirement(
                id="SR 2.3",
                name="Use control for portable and mobile devices",
                description="The control system shall provide the capability to authorize and monitor portable devices",
                category="Mobile Security",
                security_level=SecurityLevel.SL2
            ),
            Requirement(
                id="SR 2.4",
                name="Mobile code",
                description="The control system shall provide the capability to enforce restrictions on the use of mobile code",
                category="Application Security",
                security_level=SecurityLevel.SL2
            ),
            Requirement(
                id="SR 2.5",
                name="Session lock",
                description="The control system shall provide the capability to prevent further access through session lock",
                category="Session Management",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 2.6",
                name="Remote session termination",
                description="The control system shall provide the capability to terminate a remote session",
                category="Session Management",
                security_level=SecurityLevel.SL2
            ),
            Requirement(
                id="SR 2.7",
                name="Concurrent session control",
                description="The control system shall provide the capability to enforce limits on concurrent sessions",
                category="Session Management",
                security_level=SecurityLevel.SL2
            ),
            Requirement(
                id="SR 2.8",
                name="Auditable events",
                description="The control system shall provide the capability to generate audit records for auditable events",
                category="Audit",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 2.9",
                name="Audit storage capacity",
                description="The control system shall provide the capability to allocate audit record storage capacity",
                category="Audit",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 2.10",
                name="Response to audit processing failures",
                description="The control system shall provide the capability to alert on audit processing failures",
                category="Audit",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 2.11",
                name="Timestamps",
                description="The control system shall provide the capability to provide timestamps for use in audit records",
                category="Audit",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 2.12",
                name="Non-repudiation",
                description="The control system shall provide the capability to determine that a message was sent by an authorized source",
                category="Non-Repudiation",
                security_level=SecurityLevel.SL3
            ),
        ]
    ),
    
    "FR3": ControlFamily(
        id="FR3",
        name="System Integrity",
        description="Ensure the integrity of the control system",
        requirements=[
            Requirement(
                id="SR 3.1",
                name="Communication integrity",
                description="The control system shall provide the capability to protect the integrity of transmitted information",
                category="Communication Security",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 3.2",
                name="Malicious code protection",
                description="The control system shall provide the capability to employ malicious code protection mechanisms",
                category="Malware Protection",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 3.3",
                name="Security functionality verification",
                description="The control system shall provide the capability to verify the intended operation of security functions",
                category="Security Testing",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 3.4",
                name="Software and information integrity",
                description="The control system shall provide the capability to detect and protect against unauthorized software modifications",
                category="Integrity",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 3.5",
                name="Input validation",
                description="The control system shall validate the syntax and content of inputs",
                category="Input Validation",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 3.6",
                name="Deterministic output",
                description="The control system shall provide the capability for deterministic process outputs",
                category="Output Control",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 3.7",
                name="Error handling",
                description="The control system shall provide the capability to manage errors appropriately",
                category="Error Handling",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 3.8",
                name="Session integrity",
                description="The control system shall provide the capability to protect session integrity",
                category="Session Security",
                security_level=SecurityLevel.SL2
            ),
            Requirement(
                id="SR 3.9",
                name="Protection of audit information",
                description="The control system shall protect audit information from unauthorized modifications",
                category="Audit Protection",
                security_level=SecurityLevel.SL1
            ),
        ]
    ),
    
    "FR4": ControlFamily(
        id="FR4",
        name="Data Confidentiality",
        description="Ensure the confidentiality of information on communication channels and in data repositories",
        requirements=[
            Requirement(
                id="SR 4.1",
                name="Information confidentiality",
                description="The control system shall provide the capability to protect information at rest from unauthorized disclosure",
                category="Data Protection",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 4.2",
                name="Information persistence",
                description="The control system shall provide the capability to purge memory resources of their information content",
                category="Data Protection",
                security_level=SecurityLevel.SL2
            ),
            Requirement(
                id="SR 4.3",
                name="Use of cryptography",
                description="The control system shall use cryptographic mechanisms to protect the integrity and confidentiality of information",
                category="Cryptography",
                security_level=SecurityLevel.SL1
            ),
        ]
    ),
    
    "FR5": ControlFamily(
        id="FR5",
        name="Restricted Data Flow",
        description="Segment the control system via zones and conduits",
        requirements=[
            Requirement(
                id="SR 5.1",
                name="Network segmentation",
                description="The control system shall provide the capability to logically segment networks",
                category="Network Segmentation",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 5.2",
                name="Zone boundary protection",
                description="The control system shall provide the capability to monitor and control communications at zone boundaries",
                category="Network Security",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 5.3",
                name="General purpose person-to-person communication restrictions",
                description="The control system shall provide the capability to prevent general purpose person-to-person messaging",
                category="Network Security",
                security_level=SecurityLevel.SL2
            ),
            Requirement(
                id="SR 5.4",
                name="Application partitioning",
                description="The control system shall provide the capability to partition applications and data in a secure manner",
                category="Application Security",
                security_level=SecurityLevel.SL2
            ),
        ]
    ),
    
    "FR6": ControlFamily(
        id="FR6",
        name="Timely Response to Events",
        description="Respond to security violations by notifying the proper authority and taking corrective action",
        requirements=[
            Requirement(
                id="SR 6.1",
                name="Audit log accessibility",
                description="The control system shall provide the capability for authorized humans to access audit logs",
                category="Audit",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 6.2",
                name="Continuous monitoring",
                description="The control system shall provide the capability to continuously monitor all security mechanisms",
                category="Monitoring",
                security_level=SecurityLevel.SL1
            ),
        ]
    ),
    
    "FR7": ControlFamily(
        id="FR7",
        name="Resource Availability",
        description="Ensure the availability of the control system against degradation or denial of essential services",
        requirements=[
            Requirement(
                id="SR 7.1",
                name="Denial of service protection",
                description="The control system shall provide the capability to operate in degraded mode during a denial of service event",
                category="Availability",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 7.2",
                name="Resource management",
                description="The control system shall provide the capability to limit the use of resources by security functions",
                category="Resource Management",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 7.3",
                name="Control system backup",
                description="The control system shall provide the capability to support backups of user-level and system-level information",
                category="Backup",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 7.4",
                name="Control system recovery and reconstitution",
                description="The control system shall provide the capability to recover and reconstitute to a known secure state",
                category="Recovery",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 7.5",
                name="Emergency power",
                description="The control system shall provide the capability to maintain an emergency power supply",
                category="Power Management",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 7.6",
                name="Network and security configuration settings",
                description="The control system shall provide the capability to store current security and network configuration settings",
                category="Configuration",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 7.7",
                name="Least functionality",
                description="The control system shall support the principle of least functionality",
                category="Hardening",
                security_level=SecurityLevel.SL1
            ),
            Requirement(
                id="SR 7.8",
                name="Control system component inventory",
                description="The control system shall provide the capability to support asset inventory management",
                category="Asset Management",
                security_level=SecurityLevel.SL1
            ),
        ]
    ),
}


# =============================================================================
# ASSESSMENT ENGINE
# =============================================================================

class ComplianceAssessment:
    """IEC 62443 Compliance Assessment Engine"""
    
    def __init__(self, target_sl: SecurityLevel = SecurityLevel.SL2):
        self.target_sl = target_sl
        self.frameworks = {
            "IEC 62443": IEC_62443_REQUIREMENTS.copy()
        }
        self.assessment_date = datetime.now().isoformat()
        
    def assess_requirement(self, family_id: str, req_id: str, 
                          status: ComplianceStatus, evidence: str = "", notes: str = ""):
        """Update assessment for a specific requirement"""
        if family_id in self.frameworks["IEC 62443"]:
            family = self.frameworks["IEC 62443"][family_id]
            for req in family.requirements:
                if req.id == req_id:
                    req.status = status
                    req.evidence = evidence
                    req.notes = notes
                    req.last_assessed = datetime.now().isoformat()
                    return True
        return False
        
    def get_compliance_summary(self) -> dict:
        """Get overall compliance summary"""
        total_reqs = 0
        compliant = 0
        partial = 0
        non_compliant = 0
        not_assessed = 0
        
        for family in self.frameworks["IEC 62443"].values():
            for req in family.requirements:
                if req.security_level.value <= self.target_sl.value:
                    total_reqs += 1
                    if req.status == ComplianceStatus.COMPLIANT:
                        compliant += 1
                    elif req.status == ComplianceStatus.PARTIALLY_COMPLIANT:
                        partial += 1
                    elif req.status == ComplianceStatus.NON_COMPLIANT:
                        non_compliant += 1
                    else:
                        not_assessed += 1
                        
        score = ((compliant + partial * 0.5) / total_reqs * 100) if total_reqs > 0 else 0
        
        return {
            "framework": "IEC 62443-3-3",
            "target_security_level": self.target_sl.name,
            "assessment_date": self.assessment_date,
            "total_requirements": total_reqs,
            "compliant": compliant,
            "partially_compliant": partial,
            "non_compliant": non_compliant,
            "not_assessed": not_assessed,
            "compliance_score": round(score, 1),
            "families": {
                fid: {
                    "name": f.name,
                    "score": round(f.compliance_score, 1)
                }
                for fid, f in self.frameworks["IEC 62443"].items()
            }
        }
        
    def get_gaps(self) -> List[dict]:
        """Get list of compliance gaps"""
        gaps = []
        for family in self.frameworks["IEC 62443"].values():
            for req in family.requirements:
                if req.security_level.value <= self.target_sl.value:
                    if req.status in [ComplianceStatus.NON_COMPLIANT, 
                                      ComplianceStatus.PARTIALLY_COMPLIANT,
                                      ComplianceStatus.NOT_ASSESSED]:
                        gaps.append({
                            "requirement_id": req.id,
                            "name": req.name,
                            "category": req.category,
                            "status": req.status.value,
                            "security_level": req.security_level.name,
                            "family": family.name,
                            "description": req.description,
                        })
        return gaps
        
    def generate_report(self) -> dict:
        """Generate full compliance report"""
        return {
            "summary": self.get_compliance_summary(),
            "gaps": self.get_gaps(),
            "requirements": {
                fid: {
                    "name": f.name,
                    "requirements": [asdict(r) for r in f.requirements]
                }
                for fid, f in self.frameworks["IEC 62443"].items()
            }
        }
        
    def to_json(self) -> str:
        """Export assessment as JSON"""
        return json.dumps(self.generate_report(), indent=2, default=str)


# =============================================================================
# AUTO-ASSESSMENT FROM VULNOT FINDINGS
# =============================================================================

def auto_assess_from_vulnot(assessment: ComplianceAssessment, vulnot_findings: dict):
    """Automatically assess based on VULNOT security findings"""
    
    # Map VULNOT findings to IEC 62443 requirements
    if vulnot_findings.get("no_authentication"):
        assessment.assess_requirement("FR1", "SR 1.1", ComplianceStatus.NON_COMPLIANT,
            evidence="VULNOT detected unauthenticated access to OT systems")
        assessment.assess_requirement("FR1", "SR 1.2", ComplianceStatus.NON_COMPLIANT,
            evidence="VULNOT detected unauthenticated protocol access")
            
    if vulnot_findings.get("weak_passwords"):
        assessment.assess_requirement("FR1", "SR 1.7", ComplianceStatus.NON_COMPLIANT,
            evidence="VULNOT detected default/weak credentials")
            
    if vulnot_findings.get("no_network_segmentation"):
        assessment.assess_requirement("FR5", "SR 5.1", ComplianceStatus.NON_COMPLIANT,
            evidence="VULNOT detected flat network without segmentation")
        assessment.assess_requirement("FR5", "SR 5.2", ComplianceStatus.NON_COMPLIANT,
            evidence="VULNOT detected no zone boundary protection")
            
    if vulnot_findings.get("no_encryption"):
        assessment.assess_requirement("FR4", "SR 4.3", ComplianceStatus.NON_COMPLIANT,
            evidence="VULNOT detected unencrypted OT communications")
        assessment.assess_requirement("FR3", "SR 3.1", ComplianceStatus.NON_COMPLIANT,
            evidence="VULNOT detected no communication integrity protection")
            
    if vulnot_findings.get("no_logging"):
        assessment.assess_requirement("FR2", "SR 2.8", ComplianceStatus.NON_COMPLIANT,
            evidence="VULNOT detected insufficient audit logging")
        assessment.assess_requirement("FR6", "SR 6.1", ComplianceStatus.NON_COMPLIANT,
            evidence="VULNOT detected no audit log accessibility")
            
    if vulnot_findings.get("ids_alerts"):
        assessment.assess_requirement("FR6", "SR 6.2", ComplianceStatus.COMPLIANT,
            evidence="VULNOT IDS providing continuous monitoring")
            
    return assessment


if __name__ == "__main__":
    # Example usage
    assessment = ComplianceAssessment(target_sl=SecurityLevel.SL2)
    
    # Simulate VULNOT findings
    findings = {
        "no_authentication": True,
        "weak_passwords": True,
        "no_network_segmentation": True,
        "no_encryption": True,
        "no_logging": True,
        "ids_alerts": True,
    }
    
    auto_assess_from_vulnot(assessment, findings)
    
    # Print summary
    summary = assessment.get_compliance_summary()
    print(f"IEC 62443 Compliance Score: {summary['compliance_score']}%")
    print(f"Gaps: {len(assessment.get_gaps())}")
