import json

class LiveDataHelper():
    @staticmethod
    def load_guild_binds():
        with open("league_api/live_data/guild_channel_binds.json") as bind_file:
            return json.load(bind_file)

    @staticmethod
    def save_guild_binds(channel_binds):
        with open("league_api/live_data/guild_channel_binds.json", "w") as bind_file:
            json.dump(channel_binds, bind_file)

    @staticmethod
    def guild_is_binded(channel_binds, guild_id):
        try:
            channel_binds[guild_id]
            return True
        except KeyError as err:
            return False