import discord

from clembot.config.constants import GUILD_METADATA_KEY, GUILD_CONFIG_KEY
from clembot.core.data_manager.dbi import DatabaseInterface
from clembot.utilities.utils.embeds import Embeds


class GuildManager:

    def __init__(self, dbi: DatabaseInterface, guild):
        self.dbi = dbi
        if isinstance(guild, discord.Guild):
            self.guild_id = guild.id
        else:
            self.guild_id = int(guild)

    async def timezone(self, ctx):
        timezone = await self.guild_profile('timezone')
        if timezone:
            return timezone

        await Embeds.error_notification(ctx, "Missing Guild Configuration", "Contact an admin and ask them to setup timezone using `!config timezone`.")


    async def guild_profile(self, key=None, value=None, *, delete=False):

        config_value = await self.dbi.guild_config_stmt.fetchrow(self.guild_id)

        # TODO: Just in case if the guild_config data is missing, insert a blank row with default prefix.
        if not config_value:
            guild_metadata_table = self.dbi.table('guild_config')
            d = {
                'guild_id': self.guild_id,
                'prefix': '!'
            }
            guild_metadata_table_insert = guild_metadata_table.insert.row(**d)
            await guild_metadata_table_insert.commit()

        guild_metadata_table = self.dbi.table('guild_metadata')
        guild_config_table = self.dbi.table('guild_config')

        if delete:
            if key in GUILD_METADATA_KEY:
                return await guild_metadata_table.query().where(guild_id=self.guild_id, config_name=str(key)).delete()
            else:
                return None

        if key is not None:
            if key in GUILD_CONFIG_KEY:
                if value is not None:
                    d = { key : value }
                    update_query = guild_config_table.update(**d).where(guild_id=self.guild_id)
                    await update_query.commit()
                else:
                    config_value = await self.dbi.guild_config_stmt.fetchrow(self.guild_id)
                    return config_value[key]
            else:
                if value is not None:
                    guild_metadata = await guild_metadata_table.query().select().where(guild_id=self.guild_id).getjson()
                    config_id_list = list(map(lambda cid: cid['id'] , filter(lambda cn : cn['config_name'] == key, guild_metadata)))
                    if config_id_list and len(config_id_list) > 0:
                        update_query = guild_metadata_table.update(config_name=str(key), config_value=str(value), guild_id=self.guild_id).where(id=config_id_list[0])
                        await update_query.commit()
                    else:
                        insert_query = guild_metadata_table.insert(config_name=str(key), config_value=str(value), guild_id=self.guild_id)
                        return await insert_query.commit()
                else:
                    return await self.dbi.guild_metadata_stmt.fetchval(self.guild_id, str(key))
        else:
            metadata_dict = await guild_metadata_table.query().select().where(guild_id=self.guild_id).getjson()
            guild_metadata = {k['config_name']: k['config_value'] for k in metadata_dict}
            guild_config = await self.dbi.guild_config_stmt.fetchrow(self.guild_id)
            guild_metadata['city'] = guild_config['city']
            guild_metadata['timezone'] = guild_config['timezone']
            guild_metadata['prefix'] = guild_config['prefix']
            return guild_metadata


    async def channel_profile(self, channel_id, key=None, value=None, *, delete=False):
        try:
            channel_config_table = self.dbi.table('channel_metadata')
            if channel_id is None:
                raise ValueError("missing channel_id")

            channel_profile = await self.dbi.channel_profile_select_stmt.fetchrow(self.guild_id, channel_id)
            # TODO: Just in case if the guild_config data is missing, insert a blank row with default prefix.
            if channel_profile is None:

                channel_metadata_table = self.dbi.table('channel_metadata')
                d = {
                    'guild_id': self.guild_id,
                    'channel_id': channel_id
                }
                channel_metadata_table_insert = channel_metadata_table.insert.row(**d)
                await channel_metadata_table_insert.commit()

            if delete:
                if key:
                    d = {f'{key}' : None}
                    update_query = channel_config_table.update(**d).where(guild_id=self.guild_id, channel_id=channel_id)
                    await update_query.commit()
                else:
                    return None

            if key is not None:
                if value is not None:
                    d = {f'{key}': value}
                    update_query = channel_config_table.update(**d).where(guild_id=self.guild_id, channel_id=channel_id)
                    await update_query.commit()
                else:
                    channel_profile = await self.dbi.channel_profile_select_stmt.fetchrow(self.guild_id, channel_id)
                    if channel_profile:
                        return channel_profile[key]
                    return None
            else:
                return await channel_config_table.query().select().where(guild_id=self.guild_id, channel_id=channel_id).get_first_json()

        except Exception as error:
            raise Exception(error)


    async def prefix(self, new_prefix: str = None):
        """Add, remove and change custom guild prefix.

        Get current prefix by calling without args.
        Set new prefix by calling with the new prefix as an arg.
        Reset prefix to default by calling 'reset' as an arg.
        """
        pfx_tbl = self.dbi.table('guild_config')
        pfx_tbl.query.select('prefix').where(guild_id=self.guild_id)
        if new_prefix:
            if new_prefix.lower() == "reset":
                return await pfx_tbl.query.delete()
            pfx_tbl.insert(guild_id=self.guild_id, prefix=new_prefix)
            pfx_tbl.insert.primaries('guild_id')
            return await pfx_tbl.insert.commit(do_update=True)
        else:
            return await pfx_tbl.query.get_value('prefix')
