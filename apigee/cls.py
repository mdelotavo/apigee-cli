import click


class AliasedGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        cmd = super().get_command(ctx, cmd_name)
        if cmd:
            return cmd

        matches = [name for name in self.list_commands(ctx) if name.startswith(cmd_name)]

        if not matches:
            return None

        if len(matches) == 1:
            return super().get_command(ctx, matches[0])

        ctx.fail(f"Too many matches: {', '.join(sorted(matches))}")