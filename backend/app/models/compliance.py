"""Compliance audit records for models and datasets.

Tracks license metadata (resolved from HF / ModelScope cardData) and an
optional CVE findings list (populated by an external container scanner
if one is available at deploy time). One row per (resource_type,
resource_id); updates rewrite the row rather than append history.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class ComplianceResourceType(str, enum.Enum):
    model = "model"
    dataset = "dataset"


class ComplianceStatus(str, enum.Enum):
    compliant = "compliant"
    restricted = "restricted"
    unknown = "unknown"


class ComplianceRecord(SQLModel, table=True):
    __tablename__ = "compliance_records"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    resource_type: ComplianceResourceType = Field(
        sa_column=Column(
            SAEnum(
                ComplianceResourceType,
                name="complianceresourcetype",
                create_constraint=False,
            ),
            nullable=False,
        )
    )
    resource_id: uuid.UUID = Field(index=True)
    license_spdx: str = Field(default="", max_length=128)
    license_status: ComplianceStatus = Field(
        sa_column=Column(
            SAEnum(
                ComplianceStatus, name="compliancestatus", create_constraint=False
            ),
            nullable=False,
            default=ComplianceStatus.unknown,
        )
    )
    cve_findings_json: str = Field(default="[]")
    # JSON array of {id, severity, description} — populated when
    # an image scanner (trivy / grype) is available; empty otherwise.

    notes: str = Field(default="")
    last_scanned_at: datetime | None = Field(
        default=None, sa_type=DateTime(timezone=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
    )
