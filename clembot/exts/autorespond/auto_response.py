class AutoResponse:

    by_respond_to = dict()

    def __init__(self, bot, guild_id, channel_id, respond_to, respond_with, image=False, auto_respond_id=None):
        self.bot = bot
        self.id = auto_respond_id
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.respond_to = respond_to
        self.respond_with = respond_with
        self.image = image

    @property
    def key(self):
        return f"{self.guild_id}___{self.channel_id}___{self.respond_to}"

    def get_state(self):
        db_dict = {
            'guild_id' : self.guild_id,
            'channel_id' : self.channel_id,
            'respond_to' : self.respond_to,
            'respond_with' : self.respond_with,
            'image' : self.image
        }
        return db_dict

    @classmethod
    def from_db_dict(cls, bot, db_dict):
        p_id, p_guild_id, p_channel_id, p_respond_to, p_respond_with, p_image = ([db_dict.get(key) for key in ['id', 'guild_id', 'channel_id', 'respond_to', 'respond_with', 'image']])

        return cls(bot, p_guild_id, p_channel_id, p_respond_to, p_respond_with, p_image, p_id)

    @classmethod
    def from_cache(cls, guild_id, channel_id, respond_to):

        key = f"{guild_id}___{channel_id}___{respond_to}"
        if key in cls.by_respond_to.keys():
            return cls.by_respond_to[key]

        return None


    @classmethod
    def cache(cls, bot, auto_response):
        cls.by_respond_to[auto_response.key] = auto_response
        bot.auto_responses[auto_response.key] = auto_response.respond_with


    @classmethod
    def evict(cls, bot, auto_response):
        cls.by_respond_to.pop(auto_response.key, None)
        bot.auto_responses.pop(auto_response.key, None)

    @staticmethod
    async def find_auto_responses(bot):
        auto_response_table = bot.dbi.table('auto_responses')
        auto_response_query = auto_response_table.query().select()
        auto_response_list = await auto_response_query.getjson()
        return auto_response_list

    async def insert(self):
        auto_response_table = self.bot.dbi.table('auto_responses')
        auto_response_table_insert = auto_response_table.insert(**self.get_state())
        await auto_response_table_insert.commit()
        AutoResponse.cache(auto_response=self)


    async def update(self):
        auto_response_table = self.bot.dbi.table('auto_responses')
        auto_response_table_update = auto_response_table.update(**self.get_state()).where(id=self.id)
        await auto_response_table_update.commit()
        AutoResponse.cache(auto_response=self)

    async def delete(self):
        """Deletes the raid record from DB and evicts from cache."""
        auto_response_table = self.bot.dbi.table('auto_responses')
        auto_response_table_delete = auto_response_table.query().where(id=self.id)
        await auto_response_table_delete.delete()
        AutoResponse.evict(auto_response=self)