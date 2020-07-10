import pkgutil

from clembot.core.bot import group
from clembot.core.commands import Cog


class CogManager(Cog):
    """Allows to load, unload and change extensions(cogs)"""

    def __init__(self, bot):
        self.bot = bot

    @property
    def available_extensions(self):
        return [i[1] for i in pkgutil.iter_modules([self.bot.ext_dir])]


    async def load_extension(self, ctx, name, extension):
        ext_loc, ext = extension.rsplit('.', 1)
        if ext not in self.available_extensions and ext_loc == 'clembot.exts':
            return await ctx.error(f'Extension {name} not found')
        was_loaded = extension in ctx.bot.extensions
        try:
            if was_loaded:
                ctx.bot.reload_extension(extension)
            else:
                ctx.bot.load_extension(extension)
        except Exception as e:
            await ctx.error(
                f'Error when loading extension {name}',
                f'{type(e).__name__}: {e} - {e.original}',
                log_level='critical')
        else:
            await ctx.success(
                f"Extension {name} {'reloaded' if was_loaded else 'loaded'}")


    @group(category="Owner", aliases=['ext'], invoke_without_command=True)
    async def extension(self, ctx):
        """Commands to manage extensions."""
        pass
        # await ctx.bot.send_cmd_help(ctx)

    @extension.group(invoke_without_command=True, aliases=['load'])
    async def cmd_ext_load(self, ctx, *extensions):
        if not extensions:
            return await ctx.send("No such extension.")

        for ext in extensions:
            name = ext.replace('_', ' ').title()
            await self.load_extension(ctx, name, f'clembot.exts.{ext}')


    @extension.command(aliases=['unload'])
    async def cmd_ext_unload(self, ctx, extension):

        ext_name = f'clembot.exts.{extension}'

        if ext_name in ctx.bot.extensions:
            ctx.bot.unload_extension(ext_name)
            await ctx.success(f'Extension {extension} unloaded')
        else:
            await ctx.error(f"Extension {extension} isn't loaded")


    @extension.group(name="list", invoke_without_command=True)
    async def _list(self, ctx):
        """List all available extension modules and their status."""
        all_exts = self.available_extensions
        not_emoji = "\N{BLACK SMALL SQUARE}"
        is_emoji = "\N{WHITE SMALL SQUARE}"
        status_list = []
        loaded = []
        for ext in ctx.bot.extensions:
            print(ext)

        for ext in all_exts:
            is_loaded = f"exts.{ext}" in ctx.bot.extensions
            if is_loaded:
                status = is_emoji
                loaded.append(ext)
            else:
                status = not_emoji
            status_list.append(f"{status} {ext}")
        await ctx.info(
            f'Available Extensions - {len(loaded)}/{len(all_exts)}',
            '\n'.join(status_list))

def setup(bot):
    bot.add_cog(CogManager(bot))