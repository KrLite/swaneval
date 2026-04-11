"""PromQL templates for the three DCGM GPU metrics used in reports.

The placeholder ``{gpu_regex}`` lets callers narrow the query to a specific
subset of GPUs (matching ``task.gpu_ids``). If the task has no gpu_ids the
regex defaults to ``.*`` and matches every GPU visible to DCGM.
"""

from __future__ import annotations

# Average GPU utilization (%) over the task window.
DCGM_GPU_UTIL_AVG = 'avg(DCGM_FI_DEV_GPU_UTIL{{gpu=~"{gpu_regex}"}})'

# Peak framebuffer memory used (MiB) during the task window.
DCGM_GPU_MEM_PEAK = 'max(DCGM_FI_DEV_FB_USED{{gpu=~"{gpu_regex}"}})'

# Average power draw (W) during the task window.
DCGM_GPU_POWER_AVG = 'avg(DCGM_FI_DEV_POWER_USAGE{{gpu=~"{gpu_regex}"}})'


def build_gpu_regex(gpu_ids: str | None) -> str:
    """Convert a comma-separated GPU id list into a PromQL regex.

    ``"0,1,2"`` → ``"0|1|2"``; empty / None → ``".*"``.
    """
    if not gpu_ids:
        return ".*"
    parts = [p.strip() for p in gpu_ids.split(",") if p.strip()]
    if not parts:
        return ".*"
    return "|".join(parts)


def format_query(template: str, gpu_ids: str | None) -> str:
    return template.format(gpu_regex=build_gpu_regex(gpu_ids))
