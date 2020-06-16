import json

from clembot.core.logs import Logger

class BingoCardManager:

    def __init__(self, dbi):
        self.dbi = dbi

    async def find_bingo_card(self, guild_id, user_id, event):

        try:
            Logger.info(f"find_bingo_card({guild_id}, {user_id}, {event})")

            guild_user_event_bingo_card_table = self.dbi.table('guild_user_event_bingo_card')

            bingo_card_query = guild_user_event_bingo_card_table.query().select().where(guild_id=guild_id, user_id=user_id, event=event)

            bingo_record = await bingo_card_query.get_first()
            if bingo_record:
                return bingo_record
        except Exception as error:
            Logger.info(error)

        return None

    async def save_bingo_card(self, guild_id, user_id, event, bingo_card, bingo_card_url, generated_at):
        Logger.info(f"save_bingo_card ({guild_id}, {user_id}, {event})")
        try:

            guild_user_event_bingo_card_record = {
                "guild_id": guild_id,
                "user_id": user_id,
                "event":event,
                "bingo_card": json.dumps(bingo_card),
                "bingo_card_url": bingo_card_url,
                "generated_at": generated_at
            }

            table = self.dbi.table('guild_user_event_bingo_card')

            existing_bingo_card = await table.query().select().where(guild_id=guild_id, user_id=user_id, event=event).get_first()

            if existing_bingo_card:
                update_query = table.update(bingo_card=json.dumps(bingo_card), bingo_card_url=bingo_card_url, generated_at=generated_at).where(user_id=user_id, guild_id=guild_id, event=event)
                await update_query.commit()
            else:
                insert_query = table.insert(**guild_user_event_bingo_card_record)
                await insert_query.commit()

        except Exception as error:
            print(error)

        return

