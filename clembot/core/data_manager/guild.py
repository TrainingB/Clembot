import discord
from clembot.core.data_manager.dbi import DatabaseInterface

class GuildManager:

    def __init__(self, dbi: DatabaseInterface, guild):
        self.dbi = dbi
        if isinstance(guild, discord.Guild):
            self.guild_id = guild.id
        else:
            self.guild_id = int(guild)

    async def settings(self, key=None, value=None, *, delete=False):
        try:
            config_table = self.dbi.table('guild_config')

            if delete:
                if key:
                    return await config_table.delete(guild_id=self.guild_id, config_name=str(key))
                else:
                    return None

            if key is not None:
                if value is not None:

                    existing_configs = await self.settings()
                    config_id_list = list(map(lambda cid: cid['id'] , filter(lambda cn : cn['config_name'] == key, existing_configs)))
                    if config_id_list and len(config_id_list) > 0:
                        update_query = config_table.update(config_name=str(key), config_value=str(value), guild_id=self.guild_id).where(id=config_id_list[0])
                        return await update_query.commit()
                    else:
                        insert_query = config_table.insert(config_name=str(key), config_value=str(value), guild_id=self.guild_id)
                        return await insert_query.commit()

                else:
                    return await self.dbi.settings_stmt.fetchval(self.guild_id, str(key))
            else:
                return await config_table.query().select().where(guild_id=self.guild_id).getjson()
        except:
            raise Exception("Operation Failed!")


    async def channel_settings(self, channel_id, key=None, value=None, *, delete=False):
        try:
            channel_config_table = self.dbi.table('guild_channel_config')
            if channel_id is None:
                raise ValueError("missing channel_id")
            if delete:
                if key:
                    return await channel_config_table.delete(guild_id=self.guild_id, channel_id=channel_id, config_name=str(key))
                else:
                    return None

            if key is not None:
                if value is not None:

                    existing_configs = await self.channel_settings(channel_id)
                    config_id_list = list(map(lambda cid: cid['id'] , filter(lambda cn : cn['config_name'] == key, existing_configs)))
                    if config_id_list and len(config_id_list) > 0:
                        update_query = channel_config_table.update(config_name=str(key), config_value=str(value), guild_id=self.guild_id, channel_id=channel_id).where(id=config_id_list[0])
                        return await update_query.commit()
                    else:
                        insert_query = channel_config_table.insert(config_name=str(key), config_value=str(value), guild_id=self.guild_id, channel_id=channel_id)
                        return await insert_query.commit()

                else:
                    return await self.dbi.channel_settings_stmt.fetchval(self.guild_id, channel_id, str(key))
            else:
                return await channel_config_table.query().select().where(guild_id=self.guild_id, channel_id=channel_id).getjson()
        except:
            raise Exception("Operation Failed!")





    async def prefix(self, new_prefix: str = None):
        """Add, remove and change custom guild prefix.

        Get current prefix by calling without args.
        Set new prefix by calling with the new prefix as an arg.
        Reset prefix to default by calling 'reset' as an arg.
        """
        pfx_tbl = self.dbi.table('guild')
        pfx_tbl.query.where(guild_id=self.guild_id)
        if new_prefix:
            if new_prefix.lower() == "reset":
                return await pfx_tbl.query.delete()
            pfx_tbl.insert(guild_id=self.guild_id, prefix=new_prefix)
            pfx_tbl.insert.primaries('guild_id')
            return await pfx_tbl.insert.commit(do_update=True)
        else:
            return await pfx_tbl.query.get_value('prefix')
