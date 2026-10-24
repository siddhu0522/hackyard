import asyncio
import datetime
import hashlib
import hmac
import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.models.monitoring import MonitoringConfiguration, BackgroundJob, NotificationRecord
from backend.app.models.specification import ApiSpecification
from backend.app.models.scan import Scan
from backend.app.models.detected_change import DetectedChange
from backend.app.services.openapi_diff import OpenAPIDiffEngine

logger = logging.getLogger(__name__)

class MonitoringService:
    """
    Scheduled API monitoring, webhook validation, and notification dispatcher.
    Runs background jobs safely with SQLite transaction boundaries.
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            self.is_running = True
            logger.info("Monitoring AsyncIOScheduler started successfully.")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Monitoring AsyncIOScheduler shut down.")

    def add_or_update_schedule(self, config_id: int, interval_minutes: int, cron_expr: Optional[str] = None):
        job_id = f"monitor_{config_id}"
        # Remove existing if present
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        if cron_expr:
            # Cron trigger
            trigger = CronTrigger.from_crontab(cron_expr)
        else:
            trigger = IntervalTrigger(minutes=max(1, interval_minutes))

        self.scheduler.add_job(
            self._execute_monitor_wrapper,
            trigger=trigger,
            id=job_id,
            args=[config_id],
            replace_existing=True
        )
        logger.info(f"Registered schedule for monitor config {config_id} (interval={interval_minutes}m)")

    def pause_schedule(self, config_id: int):
        job_id = f"monitor_{config_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.pause_job(job_id)

    def resume_schedule(self, config_id: int):
        job_id = f"monitor_{config_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.resume_job(job_id)

    def remove_schedule(self, config_id: int):
        job_id = f"monitor_{config_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

    @classmethod
    async def _execute_monitor_wrapper(cls, config_id: int):
        """Wrapper to provide clean db session for background job."""
        db = SessionLocal()
        try:
            service = cls()
            await service.run_monitor_job(config_id, db)
        finally:
            db.close()

    async def run_monitor_job(self, config_id: int, db: Session) -> BackgroundJob:
        config = db.query(MonitoringConfiguration).filter(MonitoringConfiguration.id == config_id).first()
        if not config:
            raise ValueError(f"MonitoringConfiguration {config_id} not found.")

        job = BackgroundJob(
            monitoring_id=config.id,
            job_type="scheduled_scan",
            status="running",
            started_at=datetime.datetime.utcnow(),
            logs=f"Starting monitor run for {config.name} at {config.api_spec_url}\n"
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        try:
            # 1. Fetch remote specification
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(config.api_spec_url)
                if resp.status_code != 200:
                    raise Exception(f"Failed to fetch remote OpenAPI spec: HTTP {resp.status_code}")
                content = resp.text

            # 2. Parse spec
            engine = OpenAPIDiffEngine()
            new_spec_dict = engine.parse_spec(content)
            version = new_spec_dict.get("info", {}).get("version", "unknown")

            # 3. Save new spec record
            new_spec = ApiSpecification(
                name=config.name,
                version=version,
                content_json=json.dumps(new_spec_dict),
                format="json" if content.strip().startswith("{") else "yaml",
                source_type="url",
                source_url=config.api_spec_url
            )
            db.add(new_spec)
            db.commit()
            db.refresh(new_spec)

            # 4. Compare with latest previous spec for this repo/name
            prev_spec = (
                db.query(ApiSpecification)
                .filter(ApiSpecification.name == config.name, ApiSpecification.id != new_spec.id)
                .order_by(ApiSpecification.created_at.desc())
                .first()
            )

            if prev_spec:
                old_spec_dict = json.loads(prev_spec.content_json)
                changes = engine.compare_specs(old_spec_dict, new_spec_dict)
                
                breaking = [c for c in changes if c["severity"] == "BREAKING"]
                warnings = [c for c in changes if c["severity"] == "WARNING"]
                infos = [c for c in changes if c["severity"] == "INFO"]

                scan = Scan(
                    repository_id=config.repository_id,
                    previous_spec_id=prev_spec.id,
                    current_spec_id=new_spec.id,
                    status="succeeded",
                    total_changes=len(changes),
                    breaking_changes=len(breaking),
                    warnings=len(warnings),
                    infos=len(infos),
                    completed_at=datetime.datetime.utcnow()
                )
                db.add(scan)
                db.commit()
                db.refresh(scan)

                for c in changes:
                    detected = DetectedChange(
                        scan_id=scan.id,
                        change_type=c["change_type"],
                        severity=c["severity"],
                        path=c["path"],
                        http_method=c["http_method"],
                        description=c["description"],
                        rule_code=c["rule_code"],
                        old_value=c.get("old_value"),
                        new_value=c.get("new_value"),
                        evidence_json=json.dumps(c.get("evidence", {})),
                        status="detected"
                    )
                    db.add(detected)
                db.commit()

                # Dispatch notification if breaking changes detected
                if breaking:
                    notif = NotificationRecord(
                        event_type="BREAKING_CHANGE_DETECTED",
                        title=f"{len(breaking)} Breaking Change(s) in {config.name}",
                        message=f"Monitoring detected {len(breaking)} breaking changes in OpenAPI version {version}.",
                        severity="error",
                        metadata_json=json.dumps({"scan_id": scan.id, "breaking_count": len(breaking)})
                    )
                    db.add(notif)
                    db.commit()

                job.logs += f"Scan completed: {len(changes)} total changes ({len(breaking)} breaking).\n"
            else:
                job.logs += "First version recorded. Baseline established for future diffs.\n"

            job.status = "succeeded"
            job.finished_at = datetime.datetime.utcnow()
            config.last_run_at = datetime.datetime.utcnow()
            db.commit()
            return job

        except Exception as e:
            logger.error(f"Monitoring job {job.id} failed: {e}")
            job.status = "failed"
            job.error_message = str(e)
            job.finished_at = datetime.datetime.utcnow()
            job.logs += f"Error: {str(e)}\n"
            db.commit()
            return job

    @staticmethod
    def verify_webhook_signature(payload_bytes: bytes, signature_header: Optional[str], secret: Optional[str]) -> bool:
        """Verifies HMAC SHA-256 signature for GitHub or API webhooks."""
        if not secret:
            return True  # If no secret configured, accept
        if not signature_header:
            return False

        prefix = "sha256="
        sig = signature_header[len(prefix):] if signature_header.startswith(prefix) else signature_header
        mac = hmac.new(secret.encode("utf-8"), msg=payload_bytes, digestmod=hashlib.sha256)
        expected_sig = mac.hexdigest()
        return hmac.compare_digest(sig, expected_sig)

monitoring_service = MonitoringService()
