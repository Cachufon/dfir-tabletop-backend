# Tools (Local Workflow Launchers)

This folder provides convenience launchers so you do not have to memorize commands.

## macOS: Double-click launcher
- tools/TTX_Launcher.command

NOTE:
- After git checkout, you may need to mark the launcher executable:
  - chmod +x tools/TTX_Launcher.command
- On macOS Gatekeeper, you may need to right-click -> Open the first time.

## What it does
- Creates a local Python virtualenv in .venv (if missing)
- Installs requirements (best effort):
  - dfir_backend/ttx/scripts/requirements.txt
  - dfir_backend/ttx/ui/requirements.txt (if it exists)
- Opens a simple menu to run common TTX workflows.

## Safety defaults
- Workflows should write client-tailored outputs to secure storage OUTSIDE git.
- The launcher will warn if you try to write outputs inside the repo unless you explicitly confirm.

End.
