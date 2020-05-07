import click
import importlib
import pkgutil
import time
from pulpcore.client.pulpcore import (
    Configuration,
    ApiClient,
    TasksApi,
)


class PulpContext:
    def wait_for_task(self, task_href, timeout=120):
        while timeout:
            timeout -= 1
            task = self.tasks_api.read(task_href)
            if task.state == "completed":
                return
            if task.state == "failed":
                raise Exception("Task failed")
            time.sleep(1)
            timeout -= 1
            click.echo(".", nl=False)
        raise Exception("Task timed out")


@click.group()
@click.version_option(prog_name="pulp3 command line interface")
@click.option("--base-url", default="http://localhost", help="Api base url")
@click.option("--user", default="admin", help="Username on pulp server")
# @click.option("--password", prompt=True, hide_input=True, help="Password on pulp server")
@click.option("--password", default="password", help="Password on pulp server")
@click.option("--verify-ssl", is_flag=True, default=True, help="Verify SSL connection")
@click.pass_context
def main(ctx, base_url, user, password, verify_ssl):
    ctx.ensure_object(PulpContext)
    ctx.obj.api_config = Configuration()
    ctx.obj.api_config.host = base_url
    ctx.obj.api_config.username = user
    ctx.obj.api_config.password = password
    ctx.obj.api_config.verify_ssl = verify_ssl
    ctx.obj.api_config.safe_chars_for_path_param = '/'
    ctx.obj.core_client = ApiClient(ctx.obj.api_config)
    ctx.obj.tasks_api = TasksApi(ctx.obj.core_client)


# Load plugins from the pulpcore.cli namespace
# https://packaging.python.org/guides/creating-and-discovering-plugins/#using-namespace-packages
discovered_plugins = {
    name: importlib.import_module(name)
    for _finder, name, _ispkg in pkgutil.iter_modules(__path__, __name__ + ".")
}
