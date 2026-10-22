"""Regression checks for loading renewed certificates without container restarts."""

import subprocess
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import call, patch

from site_builder.docker.site_reload import reload_site_containers
from site_builder.ssl_certificate_manager import SSLCertificateManager
from site_builder import __main__ as cli


class CertificateRenewalTests(unittest.TestCase):
    def test_reports_forced_automatic_and_key_renewal_but_not_unchanged_certificates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manager = SSLCertificateManager(root, root / "ca.crt", root / "ca.key", "")
            self.assertTrue(manager.generate_certificates("example.com", "example.com"))
            cert_path = root / "example.com/example.com/client.crt"
            original = cert_path.read_bytes()
            self.assertFalse(manager.generate_certificates("example.com", "example.com"))
            self.assertEqual(original, cert_path.read_bytes())
            self.assertTrue(manager.generate_certificates("example.com", "example.com", renew_crts=True))
            self.assertNotEqual(original, cert_path.read_bytes())
            with patch.object(manager, "_certificate_needs_renewal", return_value=True):
                self.assertTrue(manager.generate_certificates("example.com", "example.com"))
            self.assertTrue(manager.generate_certificates("example.com", "example.com", renew_keys=True))
            self.assertTrue(manager.generate_certificates("example.com", "example.com", renew_csrs=True))


class ContainerReloadTests(unittest.TestCase):
    @patch("site_builder.docker.site_reload.subprocess.run")
    def test_only_reloads_changed_running_sites_after_config_test(self, run):
        run.return_value.stdout = "site-example-com\nsite-unchanged-com\n"
        reload_site_containers([{"slug": "example-com"}, {"slug": "stopped-com"}])
        self.assertEqual(run.call_args_list, [
            call(["docker", "ps", "--format", "{{.Names}}"],
                 check=True, capture_output=True, text=True),
            call(["docker", "exec", "site-example-com", "nginx", "-t"], check=True),
            call(["docker", "exec", "site-example-com", "nginx", "-s", "reload"], check=True),
        ])

    @patch("site_builder.docker.site_reload.subprocess.run")
    def test_no_docker_access_when_nothing_changed(self, run):
        reload_site_containers([])
        run.assert_not_called()

    @patch("site_builder.docker.site_reload.subprocess.run")
    def test_failed_config_test_prevents_reload(self, run):
        run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout="site-example-com\n"),
            subprocess.CalledProcessError(1, "nginx -t"),
        ]
        with self.assertRaises(subprocess.CalledProcessError):
            reload_site_containers([{"slug": "example-com"}])
        self.assertEqual(run.call_count, 2)

    @patch("site_builder.docker.site_reload.subprocess.run")
    def test_reload_failure_is_reported(self, run):
        run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout="site-example-com\n"),
            subprocess.CompletedProcess([], 0),
            subprocess.CalledProcessError(1, "nginx -s reload"),
        ]
        with self.assertRaises(subprocess.CalledProcessError):
            reload_site_containers([{"slug": "example-com"}])


class RenewalWorkflowTests(unittest.TestCase):
    def test_changed_sites_reload_before_proxy_and_skip_flag_is_respected(self):
        for skip, rebuild in ((False, False), (True, False), (False, True)):
            with self.subTest(skip=skip, rebuild=rebuild), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                with patch.object(cli, "load_config", return_value={}), patch("sys.argv", ["site-builder"]):
                    args = cli.parse_arguments()
                args.docker_compose_path = Path(directory) / "docker-compose.yml"
                args.skip_service_restart = skip
                args.rebuild_containers = rebuild
                mocks = {}
                for name in ("parse_arguments", "save_config", "validate_paths", "get_ca_password",
                             "create_ssl_manager", "ConfigGenerator", "create_nginx_manager",
                             "create_database_managers", "discover_sites", "reload_site_containers", "rebuild_site_containers"):
                    mocks[name] = stack.enter_context(patch.object(cli, name))
                mocks["parse_arguments"].return_value = args
                sites = [{"name": "example.com", "domain": "example.com", "slug": "example-com", "use_ssl": True},
                         {"name": "other.com", "domain": "other.com", "slug": "other-com", "use_ssl": True}]
                mocks["discover_sites"].return_value = sites
                mocks["create_ssl_manager"].return_value.generate_certificates.side_effect = [True, False]
                mocks["create_database_managers"].return_value = {}
                mocks["ConfigGenerator"].return_value.render_docker_compose.return_value = "services: {}"
                events = []
                mocks["reload_site_containers"].side_effect = lambda changed: events.append(("sites", changed))
                mocks["rebuild_site_containers"].side_effect = lambda selected, path: events.append(("rebuild", selected))
                proxy = mocks["create_nginx_manager"].return_value
                proxy.is_running.return_value = True
                proxy.reload.side_effect = lambda: events.append(("proxy", None))
                cli.main()
                expected = [] if skip else [("rebuild", sites) if rebuild else ("sites", [sites[0]]), ("proxy", None)]
                self.assertEqual(events, expected)
                if rebuild:
                    mocks["reload_site_containers"].assert_not_called()
                    mocks["rebuild_site_containers"].assert_called_once_with(sites, args.docker_compose_path)
                else:
                    mocks["rebuild_site_containers"].assert_not_called()


if __name__ == "__main__":
    unittest.main()
