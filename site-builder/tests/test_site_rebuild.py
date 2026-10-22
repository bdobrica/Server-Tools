"""Checks for explicit runtime rebuilds and failure handling."""

import subprocess
import unittest
from pathlib import Path
from unittest.mock import call, patch

from site_builder import __main__ as cli
from site_builder.docker.site_rebuild import rebuild_site_containers


class SiteRebuildTests(unittest.TestCase):
    @patch("site_builder.docker.site_rebuild.subprocess.run")
    def test_build_failure_preserves_running_containers(self, run):
        run.side_effect = subprocess.CalledProcessError(1, "build")
        with self.assertRaises(subprocess.CalledProcessError):
            rebuild_site_containers([{"slug": "example-com"}], Path("compose.yml"))
        self.assertEqual(run.call_count, 1)

    @patch("site_builder.docker.site_rebuild.subprocess.run")
    def test_recreation_failure_propagates(self, run):
        run.side_effect = [None, subprocess.CalledProcessError(1, "up")]
        with self.assertRaises(subprocess.CalledProcessError):
            rebuild_site_containers([{"slug": "example-com"}], Path("compose.yml"))

    @patch("site_builder.docker.site_rebuild.subprocess.run")
    def test_only_discovered_sites_are_recreated_after_build(self, run):
        compose = ["docker", "compose", "-f", str(Path("compose.yml").resolve())]
        services = ["web-example-com", "web-other-com"]
        rebuild_site_containers([{"slug": "example-com"}, {"slug": "other-com"}], Path("compose.yml"))
        self.assertEqual(run.call_args_list, [
            call(compose + ["build", "--pull", "--no-cache"] + services, check=True),
            call(compose + ["up", "-d", "--no-deps", "--force-recreate"] + services, check=True),
        ])

    @patch("site_builder.docker.site_rebuild.subprocess.run")
    def test_empty_sites_never_invokes_compose(self, run):
        rebuild_site_containers([], Path("compose.yml"))
        run.assert_not_called()

    @patch.object(cli, "load_config", return_value={})
    def test_cli_rebuild_preserves_saved_and_explicit_skip_restart(self, load):
        with patch("sys.argv", ["site-builder"]):
            self.assertFalse(cli.parse_arguments().rebuild_containers)
        with patch("sys.argv", ["site-builder", "--rebuild-containers"]):
            self.assertTrue(cli.parse_arguments().rebuild_containers)
        for config, argv in (
            ({}, ["site-builder", "--rebuild-containers", "--skip-service-restart"]),
            ({"skip_service_restart": True}, ["site-builder", "--rebuild-containers"]),
        ):
            load.return_value = config
            with patch("sys.argv", argv):
                args = cli.parse_arguments()
            self.assertTrue(args.rebuild_containers)
            self.assertTrue(args.skip_service_restart)
