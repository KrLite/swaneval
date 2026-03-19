import json
import os
import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from sqlalchemy import func as sa_func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.dataset import Dataset, DatasetVersion, SourceType
from app.models.eval_result import EvalResult
from app.models.user import User
from app.schemas.dataset import DatasetMountRequest, DatasetResponse, PaginatedResponse
from app.services.dataset_deletion import cleanup_uploaded_file, delete_dataset_versions
from app.services.storage import StorageBackend, get_storage
from app.services.storage.utils import uri_to_key

router = APIRouter()


def _get_storage() -> StorageBackend:
    return get_storage()


async def _count_rows(storage: StorageBackend, source_uri: str) -> int:
    """Count rows in a JSON/JSONL file via the storage backend."""
    key = uri_to_key(source_uri)
    if key is None:
        # Mounted path — fall back to direct filesystem read
        if not os.path.exists(source_uri):
            return 0
        count = 0
        with open(source_uri) as f:
            if source_uri.endswith(".json"):
                data = json.load(f)
                return len(data) if isinstance(data, list) else 1
            for line in f:
                if line.strip():
                    count += 1
        return count

    if not await storage.exists(key):
        return 0

    text = await storage.read_text(key)
    if key.endswith(".json"):
        data = json.loads(text)
        return len(data) if isinstance(data, list) else 1

    return sum(1 for line in text.splitlines() if line.strip())


@router.post("/upload", response_model=DatasetResponse, status_code=201)
async def upload_dataset(
    file: UploadFile,
    name: str = Form(""),
    description: str = Form(""),
    tags: str = Form(""),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage: StorageBackend = Depends(_get_storage),
):
    if not name:
        name = file.filename or "untitled"

    ext = os.path.splitext(file.filename or "")[1].lower()
    fmt = ext.lstrip(".") or "jsonl"

    content = await file.read()
    file_id = uuid.uuid4()
    key = f"uploads/{file_id}{ext}"
    uri = await storage.write_file(key, content)

    row_count = await _count_rows(storage, uri)

    # Check if dataset with same name exists (auto-version)
    stmt = (
        select(Dataset).where(Dataset.name == name).order_by(Dataset.version.desc())
    )
    existing = (await session.exec(stmt)).first()
    version = (existing.version + 1) if existing else 1

    ds = Dataset(
        name=name,
        description=description,
        source_type=SourceType.upload,
        source_uri=uri,
        format=fmt,
        tags=tags,
        version=version,
        size_bytes=len(content),
        row_count=row_count,
        created_by=current_user.id,
    )
    session.add(ds)
    await session.commit()
    await session.refresh(ds)

    # Create version record
    dv = DatasetVersion(
        dataset_id=ds.id,
        version=version,
        file_path=uri,
        changelog="Initial upload" if version == 1 else f"Version {version}",
        row_count=row_count,
    )
    session.add(dv)
    await session.commit()
    await session.refresh(ds)

    return ds


@router.post("/mount", response_model=DatasetResponse, status_code=201)
async def mount_dataset(
    body: DatasetMountRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage: StorageBackend = Depends(_get_storage),
):
    # Mount always operates on local filesystem paths
    if not os.path.exists(body.server_path):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Server path does not exist"
        )

    row_count = await _count_rows(storage, body.server_path)
    size = os.path.getsize(body.server_path)

    ds = Dataset(
        name=body.name,
        description=body.description,
        source_type=SourceType.server_path,
        source_uri=body.server_path,
        format=body.format,
        tags=body.tags,
        version=1,
        size_bytes=size,
        row_count=row_count,
        created_by=current_user.id,
    )
    session.add(ds)
    await session.commit()
    await session.refresh(ds)
    return ds


@router.get("", response_model=PaginatedResponse)
async def list_datasets(
    page: int = 1,
    page_size: int = 20,
    tag: str | None = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base = select(Dataset)
    if tag:
        base = base.where(Dataset.tags.contains(tag))

    count_stmt = select(sa_func.count()).select_from(base.subquery())
    total = (await session.exec(count_stmt)).one()

    offset = (page - 1) * page_size
    items_stmt = (
        base.order_by(Dataset.created_at.desc()).offset(offset).limit(page_size)
    )
    result = await session.exec(items_stmt)
    return PaginatedResponse(
        items=result.all(), total=total, page=page, page_size=page_size
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds = await session.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dataset not found")
    return ds


@router.get("/{dataset_id}/preview")
async def preview_dataset(
    dataset_id: uuid.UUID,
    limit: int = 50,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage: StorageBackend = Depends(_get_storage),
):
    ds = await session.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dataset not found")

    key = uri_to_key(ds.source_uri)

    # Determine if we can read via storage or must fall back to local FS
    if key is not None:
        if not await storage.exists(key):
            return {"rows": [], "total": 0}
        text = await storage.read_text(key)
    else:
        if not os.path.exists(ds.source_uri):
            return {"rows": [], "total": 0}
        with open(ds.source_uri, encoding="utf-8") as f:
            text = f.read()

    rows: list[dict] = []
    if ds.source_uri.endswith(".json") or (key and key.endswith(".json")):
        data = json.loads(text)
        items = data if isinstance(data, list) else [data]
        rows = items[:limit]
    else:
        for line in text.splitlines():
            if len(rows) >= limit:
                break
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    return {"rows": rows, "total": ds.row_count}


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage: StorageBackend = Depends(_get_storage),
):
    ds = await session.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dataset not found")

    # Delete eval_results referencing this dataset
    stmt = select(EvalResult).where(EvalResult.dataset_id == dataset_id)
    results = (await session.exec(stmt)).all()
    for r in results:
        await session.delete(r)

    # Delete dataset versions (must flush before deleting parent)
    await delete_dataset_versions(session, ds.id)
    await session.flush()

    await cleanup_uploaded_file(storage, ds)
    await session.delete(ds)
    await session.commit()
