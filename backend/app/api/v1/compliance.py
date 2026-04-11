"""Compliance audit endpoints — license status and CVE findings."""

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_db, require_permission
from app.models.compliance import (
    ComplianceRecord,
    ComplianceResourceType,
    ComplianceStatus,
)
from app.models.dataset import Dataset
from app.models.llm_model import LLMModel
from app.models.user import User
from app.services.compliance_scanner import (
    evaluate_license_policy,
    fetch_hub_license,
    scan_image_cves_async,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/records")
async def list_compliance_records(
    resource_type: ComplianceResourceType | None = None,
    license_status: ComplianceStatus | None = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = require_permission("reports.read"),
):
    """List compliance records, optionally filtered by type or status.

    Joins the record against its source resource (model or dataset) so
    the UI can show the display name without a second round-trip.
    """
    stmt = select(ComplianceRecord)
    if resource_type is not None:
        stmt = stmt.where(ComplianceRecord.resource_type == resource_type)
    if license_status is not None:
        stmt = stmt.where(ComplianceRecord.license_status == license_status)
    stmt = stmt.order_by(col(ComplianceRecord.created_at).desc())
    records = (await session.exec(stmt)).all()

    out: list[dict] = []
    for r in records:
        resource_name = ""
        if r.resource_type == ComplianceResourceType.model:
            m = await session.get(LLMModel, r.resource_id)
            if m:
                resource_name = m.name
        elif r.resource_type == ComplianceResourceType.dataset:
            d = await session.get(Dataset, r.resource_id)
            if d:
                resource_name = d.name
        out.append(
            {
                "id": str(r.id),
                "resource_type": r.resource_type.value,
                "resource_id": str(r.resource_id),
                "resource_name": resource_name,
                "license_spdx": r.license_spdx,
                "license_status": r.license_status.value,
                "cve_findings": json.loads(r.cve_findings_json or "[]"),
                "notes": r.notes,
                "last_scanned_at": (
                    r.last_scanned_at.isoformat() if r.last_scanned_at else None
                ),
            }
        )
    return out


@router.post("/scan")
async def scan_resource(
    resource_type: ComplianceResourceType,
    resource_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = require_permission("reports.export"),
):
    """Rescan a resource and upsert its compliance record.

    Resolution:
    - `model`: pull `source_model_id` + provider; call
      `fetch_hub_license` and optionally CVE-scan the vllm image.
    - `dataset`: look up the hub repo from the dataset's `source_uri`
      and read license metadata the same way.
    """
    source_label = ""
    repo = ""
    image_ref = ""
    hf_token = getattr(current_user, "hf_token", "") or ""

    if resource_type == ComplianceResourceType.model:
        model = await session.get(LLMModel, resource_id)
        if not model:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "模型未找到")
        source_label = model.model_type.value if model.model_type else ""
        repo = model.source_model_id or model.model_name or ""
        image_ref = model.vllm_deployment_name or ""
    elif resource_type == ComplianceResourceType.dataset:
        dataset = await session.get(Dataset, resource_id)
        if not dataset:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "数据集未找到")
        source_label = dataset.source_type.value if dataset.source_type else ""
        repo = getattr(dataset, "source_ref", "") or getattr(
            dataset, "source_uri", ""
        )

    license_spdx = ""
    notes = ""
    if source_label in ("huggingface", "modelscope") and repo:
        hub_result = await fetch_hub_license(source_label, repo, hf_token=hf_token)
        if hub_result.get("ok"):
            license_spdx = hub_result.get("license_spdx", "")
        else:
            notes = f"Hub 查询失败: {hub_result.get('error', '')}"
    else:
        notes = "无法从 Hub 查询 license — 非 HF/MS 来源"

    status_str = evaluate_license_policy(license_spdx)
    cve_findings: list[dict] = []
    if resource_type == ComplianceResourceType.model and image_ref:
        cve_findings = await scan_image_cves_async(image_ref)

    # Upsert — one row per (type, resource_id).
    existing_stmt = select(ComplianceRecord).where(
        ComplianceRecord.resource_type == resource_type,
        ComplianceRecord.resource_id == resource_id,
    )
    existing = (await session.exec(existing_stmt)).first()
    if existing is None:
        record = ComplianceRecord(
            resource_type=resource_type,
            resource_id=resource_id,
            license_spdx=license_spdx,
            license_status=ComplianceStatus(status_str),
            cve_findings_json=json.dumps(cve_findings),
            notes=notes,
            last_scanned_at=datetime.now(timezone.utc),
        )
        session.add(record)
    else:
        existing.license_spdx = license_spdx
        existing.license_status = ComplianceStatus(status_str)
        existing.cve_findings_json = json.dumps(cve_findings)
        existing.notes = notes
        existing.last_scanned_at = datetime.now(timezone.utc)
        record = existing

    await session.commit()
    await session.refresh(record)

    return {
        "id": str(record.id),
        "license_spdx": record.license_spdx,
        "license_status": record.license_status.value,
        "cve_findings": cve_findings,
        "notes": record.notes,
    }


@router.get("/policy")
async def get_compliance_policy(
    current_user: User = require_permission("reports.read"),
):
    """Return the current license policy table so the UI can show users
    which license identifiers count as compliant / restricted."""
    from app.services.compliance_scanner import (
        _COMPLIANT_LICENSES,
        _RESTRICTED_LICENSES,
    )

    return {
        "compliant": sorted(_COMPLIANT_LICENSES),
        "restricted": sorted(_RESTRICTED_LICENSES),
    }


__all__ = ["router"]
