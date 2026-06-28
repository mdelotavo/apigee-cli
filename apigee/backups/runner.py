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

        console.echo("Starting async backup...\n")

        tasks = []

        for name in self.config.api_choices:
            handler_cls = RESOURCE_REGISTRY.get(name)

            if not handler_cls:
                console.echo(f"[WARN] No handler for {name}")
                continue

            console.echo(f"▶ {name}")
            handler = handler_cls(self.config)
            tasks.append(asyncio.create_task(handler.run()))

        await asyncio.gather(*tasks)

        completed = getattr(self.config, "completed", 0)
        total = getattr(self.config, "total_items", "unknown")

        console.echo("\nBackup complete.")
        console.echo(f"Completed: {completed} items")
        console.echo(f"Expected: {total}")
