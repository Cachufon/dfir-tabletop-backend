# Endpoint Scope Area Workflow (Stub)

This document outlines the high-level workflow for running the Endpoint scope area within a Compromise Assessment. It can be used:

- As an Endpoint-only compromise assessment, or
- Combined with Identity and SaaS scope areas.

## High-Level Steps (v1 Stub)

1. Confirm in-scope endpoints or endpoint groups (e.g., specific users, critical systems) and time window.
2. Collect endpoint data:
   - EDR alerts/detections (minimum), and/or
   - Host triage bundles from selected endpoints.
3. Normalize and prepare endpoint data for analysis.
4. Apply endpoint-focused detection logic (e.g., persistence, suspicious binaries, EDR tampering, potential lateral movement).
5. Triage and investigate notable endpoint activity.
6. Summarize endpoint-related findings, including suspected compromised hosts and persistence mechanisms.
7. When combined with other scope areas, correlate endpoint findings with suspect identities and SaaS activity.

This file will be expanded with more detailed steps, queries, and mappings to specific detection rules.

## Endpoint Scope Area Detection Categories (v1)

The Endpoint scope area focuses on detecting malicious or suspicious activity on endpoints using EDR telemetry, triage bundles, or host-level artifacts. These behaviors help identify persistence, lateral movement, malware execution, or attempts to evade security controls.

### 1. Persistence Mechanisms

Goal: Detect mechanisms attackers use to maintain local access.

Examples:
- macOS: Suspicious LaunchAgents/LaunchDaemons, login items, TCC manipulation, cron jobs, system extensions.
- Windows: Registry Run keys, scheduled tasks, new or modified services, WMI persistence.
- Cross-platform: Unexpected auto-start entries created shortly before suspicious activity.

### 2. Suspicious Process Execution

Goal: Detect anomalous or malicious process behavior.

Examples:
- Execution of known malicious binaries (YARA hits).
- Abuse of LOLBins (osascript, curl, python, PowerShell, bitsadmin, certutil, etc.).
- Unusual command-line flags for exfiltration or evasion.
- Unexpected remote execution tools (PsExec, WinRM, Apple Remote Desktop, SSH misuse).

### 3. Privilege Escalation Attempts

Goal: Detect attempts to obtain elevated privileges.

Examples:
- macOS/Linux: sudo misuse, privilege escalation binaries.
- Windows: UAC bypass attempts, LSASS access patterns.
- Creation or modification of local admin groups.
- Credential dumping behavior.

### 4. Lateral Movement Indicators

Goal: Detect attempts to move across systems.

Examples:
- Remote authentication via SSH, SMB, RDP, WMI.
- Use of tunneling tools (e.g., SSH tunnels, ngrok, chisel).
- Remote process execution frameworks (PsExec, WinRM, ARD).
- Unusual remote access tools (TeamViewer, AnyDesk, Chrome Remote Desktop).

### 5. EDR Tampering & Security Control Evasion

Goal: Detect attempts to evade or disable defenses.

Examples:
- EDR sensor stop/uninstall attempts.
- Clearing or tampering with endpoint logs.
- Kernel extension or OS security framework tampering (macOS Gatekeeper bypass).
- Attempts to disable security products.

### 6. Suspicious Network Behavior

Goal: Detect abnormal network connections originating from endpoints.

Examples:
- Regular beaconing to suspicious external IPs.
- DNS anomalies or algorithmically generated domains.
- Outbound connections to VPS/cloud hosting providers.
- Use of unexpected ports or protocols.

### 7. Host-Based Exfiltration Indicators

Goal: Detect data exfiltration originating from endpoints.

Examples:
- Large file archiving (zip/tar/rar) followed by network upload.
- Use of exfiltration-capable CLI tools (scp, curl/wget, aws s3 cp).
- Mass file reads from sensitive directories.
- Use of removable media or unexpected USB activity.

### 8. Endpoint Hygiene & Risk Indicators

Goal: Identify endpoint misconfigurations or gaps that elevate compromise risk.

Examples:
- Missing or unhealthy EDR sensor.
- Unsupported or outdated OS versions.
- Unencrypted macOS volumes.
- Overprivileged local accounts or insecure endpoint policies.

These categories guide detection rule selection, triage workflows, and CA findings classification within the Endpoint scope area.
