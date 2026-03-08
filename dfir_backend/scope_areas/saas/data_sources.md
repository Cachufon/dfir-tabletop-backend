# SaaS Scope Area Data Sources

This document describes the minimum and optional data sources required to run the SaaS scope area effectively.

## Minimum Data Sources

At least ONE of the following core suites with audit logging enabled:

- O365 Unified Audit Log (UAL), OR
- Google Workspace audit logs

These logs should cover:
- Mailbox activity (where available)
- File activity for core collaboration/storage (SharePoint / OneDrive or Google Drive)
- User and admin actions on key SaaS resources

## Optional Data Sources (Recommended Where Available)

- Exchange mailbox audit and message trace (rules, forwarding, delegates)
- Gmail-specific activity logs (filters, forwarding, delegate access)
- SharePoint / OneDrive audit logs (file views, downloads, sync, external sharing)
- Google Drive audit logs (similar file activity and sharing)
- Slack audit logs (file access, app installs, workspace and channel admin actions)
- GitHub audit logs (PAT usage, SSH keys, repo clones, admin changes)
- OAuth app logs within SaaS platforms (O365, Google, Slack, etc.)

Optional sources strengthen:
- Detection of mailbox-based compromise and data exfiltration
- Detection of risky sharing behavior and third-party application abuse
- Reconstruction of detailed SaaS usage timelines for high-risk users
