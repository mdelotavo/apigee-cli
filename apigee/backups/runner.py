import asyncio
from apigee import console

from .registry import RESOURCE_REGISTRY


class BackupRunner:

    def __init__(self, config):
        self.config = config

    async def run(self):
        if not self.config.api_choices:
            console.echo("No resources selected.")
            return

        tasks = []

        for name in self.config.api_choices:
            handler_cls = RESOURCE_REGISTRY.get(name)

            if not handler_cls:
                console.echo(f"[WARN] No handler for {name}")
                continue

            console.echo(f"Processing {name}...")
            handler = handler_cls(self.config)
            tasks.append(handler.run())

        await asyncio.gather(*tasks)

        if self.config.progress_bar:
            self.config.progress_bar.close()

        console.echo("Backup complete.")