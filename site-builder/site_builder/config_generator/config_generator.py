"""Configuration generator using Jinja2 templates."""

from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader


class ConfigGenerator:
    """Generates configuration files using Jinja2 templates."""

    def __init__(self, template_path: Path):
        self.env = Environment(loader=FileSystemLoader(template_path))

    def render_nginx_config(self, site: Dict[str, Any], template_vars: Dict[str, Any]) -> str:
        """Render nginx configuration using Jinja2 template."""
        template = self.env.get_template("nginx.conf.tpl")
        return template.render(site=site, **template_vars)

    def render_docker_compose(self, sites: List[Dict[str, Any]], template_vars: Dict[str, Any]) -> str:
        """Render docker-compose configuration using Jinja2 template."""
        template = self.env.get_template("docker-compose.yml.tpl")
        return template.render(sites=sites, **template_vars)

    def render_mariadb_config(self, template_vars: Dict[str, Any]) -> str:
        """Render MariaDB configuration using Jinja2 template."""
        template = self.env.get_template("my.cnf.tpl")
        return template.render(**template_vars)

    def render_postgresql_config(self, template_vars: Dict[str, Any]) -> str:
        """Render PostgreSQL configuration using Jinja2 template."""
        template = self.env.get_template("postgresql.conf.tpl")
        return template.render(**template_vars)
