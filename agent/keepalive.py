"""
ServiceNow PDI keep-alive agent.

Authenticates against the instance and performs a short sequence of REST API
calls to register activity and prevent the PDI from being hibernated or flagged
for deletion (ServiceNow hibernates instances after ~10 days of inactivity).
"""

import logging
import os
import sys
from datetime import datetime, timezone

from servicenow_client import ServiceNowClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger(__name__)


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise EnvironmentError(f"Required environment variable '{name}' is not set")
    return value


def run() -> None:
    instance_url = _require_env("SN_INSTANCE_URL")
    username = _require_env("SN_USERNAME")
    password = _require_env("SN_PASSWORD")

    logger.info("Starting ServiceNow PDI keep-alive")
    logger.info("Instance: %s", instance_url)
    logger.info("User:     %s", username)

    client = ServiceNowClient(instance_url, username, password)

    # 1 — verify credentials and register a session
    display_name = client.verify_auth()
    logger.info("Authenticated as: %s", display_name)

    # 2 — browse a couple of tables to pad out activity
    for table, label in [
        ("incident", "Incidents"),
        ("sys_update_set", "Update Sets"),
        ("sys_app", "Scoped Applications"),
    ]:
        result = client.get(
            f"/api/now/table/{table}",
            params={"sysparm_limit": "1", "sysparm_fields": "sys_id"},
        )
        count = len(result.get("result", []))
        logger.info("Browsed %s — %d record(s) returned", label, count)

    # 3 — write a heartbeat entry to syslog so there is a visible audit trail
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    client.post("/api/now/table/syslog", {
        "level": "information",
        "source": "keepalive-agent",
        "message": f"PDI keep-alive ping — {ts}",
    })
    logger.info("Heartbeat written to syslog")

    logger.info("Keep-alive complete — instance is active")


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        logger.error("Keep-alive failed: %s", exc, exc_info=True)
        sys.exit(1)
