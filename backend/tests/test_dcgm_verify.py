"""Tests for verify_dcgm_exporter — mock k8s AppsV1 client."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.k8s_manager import verify_dcgm_exporter


def _mk_ds(name, desired, ready):
    ds = SimpleNamespace()
    ds.metadata = SimpleNamespace(name=name)
    ds.status = SimpleNamespace(
        desired_number_scheduled=desired,
        number_ready=ready,
    )
    return ds


class TestVerifyDcgmExporter(unittest.TestCase):
    def test_daemonset_found(self):
        apps_v1 = MagicMock()
        apps_v1.list_namespaced_daemon_set.return_value = SimpleNamespace(
            items=[_mk_ds("dcgm-exporter", desired=4, ready=4)]
        )
        with patch(
            "app.services.k8s_manager.create_apps_v1", return_value=apps_v1
        ):
            result = verify_dcgm_exporter("dummy-kubeconfig", "gpu-operator")

        self.assertTrue(result["found"])
        self.assertEqual(result["daemonset_name"], "dcgm-exporter")
        self.assertEqual(result["desired"], 4)
        self.assertEqual(result["ready"], 4)
        self.assertEqual(result["namespace"], "gpu-operator")

    def test_daemonset_not_found(self):
        apps_v1 = MagicMock()
        apps_v1.list_namespaced_daemon_set.return_value = SimpleNamespace(items=[])
        with patch(
            "app.services.k8s_manager.create_apps_v1", return_value=apps_v1
        ):
            result = verify_dcgm_exporter("dummy", "kube-system")

        self.assertFalse(result["found"])
        self.assertIsNone(result["daemonset_name"])
        self.assertEqual(result["desired"], 0)
        self.assertEqual(result["ready"], 0)
        self.assertEqual(result["namespace"], "kube-system")

    def test_api_error_returns_fail_soft(self):
        apps_v1 = MagicMock()
        apps_v1.list_namespaced_daemon_set.side_effect = RuntimeError("forbidden")
        with patch(
            "app.services.k8s_manager.create_apps_v1", return_value=apps_v1
        ):
            result = verify_dcgm_exporter("dummy", "gpu-operator")

        self.assertFalse(result["found"])
        self.assertIn("forbidden", result["error"])

    def test_partial_ready(self):
        apps_v1 = MagicMock()
        apps_v1.list_namespaced_daemon_set.return_value = SimpleNamespace(
            items=[_mk_ds("dcgm-exporter", desired=8, ready=5)]
        )
        with patch(
            "app.services.k8s_manager.create_apps_v1", return_value=apps_v1
        ):
            result = verify_dcgm_exporter("dummy", "gpu-operator")

        self.assertTrue(result["found"])
        self.assertEqual(result["desired"], 8)
        self.assertEqual(result["ready"], 5)


if __name__ == "__main__":
    unittest.main()
