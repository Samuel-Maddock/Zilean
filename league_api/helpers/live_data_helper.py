import json

class LiveDataHelper():
    @staticmethod
    def load_guild_binds():
        with open("league_api/data/live/guild_channel_binds.json") as bind_file:
            return json.load(bind_file)

    @staticmethod
    def save_guild_binds(channel_binds):
        with open("league_api/data/live/guild_channel_binds.json", "w") as bind_file:
            json.dump(channel_binds, bind_file)

    @staticmethod
    def guild_is_binded(channel_binds, guild_id):
        try:
            channel_binds[guild_id]
            return True
        except KeyError as err:
            return False

    @staticmethod
    def load_region_binds():
        with open("league_api/data/live/region_binds.json") as bind_file:
            return json.load(bind_file)

    @staticmethod
    def save_region_binds(region_binds):
        with open("league_api/data/live/region_binds.json", "w") as bind_file:
            json.dump(region_binds, bind_file)

    @staticmethod
    def guild_has_region(region_binds, guild_id):
        try:
            region_binds[guild_id]
            return True
        except KeyError as err:
            return False