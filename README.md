# ServiceNow PDI Keep-Alive Agent

Automatically pings your ServiceNow Personal Developer Instance (PDI) every 5 days
via the REST API to prevent hibernation or deletion due to inactivity.

## How it works

A GitHub Actions workflow runs on a cron schedule and executes `agent/keepalive.py`, which:

1. Authenticates against the PDI using Basic Auth
2. Browses a few tables (Incidents, Update Sets, Scoped Apps) to register activity
3. Writes a timestamped heartbeat entry to the instance's `syslog` table

ServiceNow flags PDIs for deletion after ~10 days of inactivity. Running every 5 days
provides a comfortable buffer.

## Setup

### 1. Add GitHub repository secrets

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret name | Value |
|---|---|
| `SN_INSTANCE_URL` | `https://devXXXXXX.service-now.com/` |
| `SN_USERNAME` | `admin` |
| `SN_PASSWORD` | your PDI password |

### 2. Enable GitHub Actions

If not already enabled, go to the **Actions** tab and enable workflows.

### 3. Manual trigger

You can trigger a run at any time from **Actions → ServiceNow PDI Keep-Alive → Run workflow**.

## Local testing

```bash
pip install -r requirements.txt
export SN_INSTANCE_URL=https://devXXXXXX.service-now.com/
export SN_USERNAME=admin
export SN_PASSWORD=yourpassword
cd agent && python keepalive.py
```

## Schedule

The workflow runs at 08:00 UTC on days 1, 6, 11, 16, 21, 26, and 31 of each month —
never more than 5 days apart.
