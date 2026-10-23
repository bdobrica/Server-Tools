"""Database storage configuration and rendering checks."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jinja2 import Environment, FileSystemLoader
from site_builder import __main__ as cli
from site_builder.core.config_persistence import load_config, save_config


class DatabaseDatadirTests(unittest.TestCase):
    def test_cli_config_roundtrip_and_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            argv = ['site-builder', '--site-builder-config-path', directory]
            with patch('sys.argv', argv):
                args = cli.parse_arguments()
            self.assertIsNone(args.mysql_datadir)
            self.assertIsNone(args.postgres_datadir)
            args.mysql_datadir = Path('/srv/mysql')
            args.postgres_datadir = Path('/srv/postgres')
            save_config(Path(directory), args)
            saved = load_config(Path(directory))
            self.assertEqual(saved['mysql_datadir'], args.mysql_datadir)
            self.assertEqual(saved['postgres_datadir'], args.postgres_datadir)
            with patch('sys.argv', argv + ['--mysql-datadir', '/other/mysql']):
                parsed = cli.parse_arguments()
            self.assertEqual(parsed.mysql_datadir, Path('/other/mysql'))
            self.assertEqual(parsed.postgres_datadir, args.postgres_datadir)

    def test_native_and_docker_rendering(self):
        env = Environment(loader=FileSystemLoader(Path(cli.__file__).parent / 'templates'))
        for custom in (False, True):
            values = dict(DB_MODE='native', MYSQL_CONFIG_PATH='/config/mysql',
                          POSTGRES_CONFIG_PATH='/config/postgres',
                          ENABLE_MYSQL_DATABASE=True, ENABLE_POSTGRES_DATABASE=True,
                          MYSQL_DATADIR='/srv/mysql' if custom else None,
                          POSTGRES_DATADIR='/srv/postgres' if custom else None)
            mysql = env.get_template('my.cnf.tpl').render(values)
            postgres = env.get_template('postgresql.conf.tpl').render(values)
            self.assertIn('datadir = "' + ('/srv/mysql' if custom else '/var/lib/mysql') + '"', mysql)
            self.assertEqual("data_directory = '/srv/postgres'" in postgres, custom)
            values['DB_MODE'] = 'docker'
            self.assertNotIn('data_directory =', env.get_template('postgresql.conf.tpl').render(values))
            compose = env.get_template('docker-compose.yml.tpl').render(values)
            for db in ('mysql', 'postgres'):
                source = '/srv/' + db if custom else '/config/' + db + '/data'
                self.assertIn('source: "' + source + '"', compose)
