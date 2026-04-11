"""Tests for dcgm_queries PromQL formatting helpers."""

import unittest

from app.services.dcgm_queries import (
    DCGM_GPU_MEM_PEAK,
    DCGM_GPU_POWER_AVG,
    DCGM_GPU_UTIL_AVG,
    build_gpu_regex,
    format_query,
)


class TestBuildGpuRegex(unittest.TestCase):
    def test_multiple_ids(self):
        self.assertEqual(build_gpu_regex("0,1,2"), "0|1|2")

    def test_single_id(self):
        self.assertEqual(build_gpu_regex("3"), "3")

    def test_whitespace_tolerated(self):
        self.assertEqual(build_gpu_regex(" 0 , 1 "), "0|1")

    def test_empty_string_becomes_wildcard(self):
        self.assertEqual(build_gpu_regex(""), ".*")

    def test_none_becomes_wildcard(self):
        self.assertEqual(build_gpu_regex(None), ".*")

    def test_only_commas_becomes_wildcard(self):
        self.assertEqual(build_gpu_regex(",,,"), ".*")


class TestFormatQuery(unittest.TestCase):
    def test_util_query_with_ids(self):
        q = format_query(DCGM_GPU_UTIL_AVG, "0,1")
        self.assertEqual(q, 'avg(DCGM_FI_DEV_GPU_UTIL{gpu=~"0|1"})')

    def test_mem_query_no_ids(self):
        q = format_query(DCGM_GPU_MEM_PEAK, None)
        self.assertEqual(q, 'max(DCGM_FI_DEV_FB_USED{gpu=~".*"})')

    def test_power_query(self):
        q = format_query(DCGM_GPU_POWER_AVG, "7")
        self.assertEqual(q, 'avg(DCGM_FI_DEV_POWER_USAGE{gpu=~"7"})')


if __name__ == "__main__":
    unittest.main()
