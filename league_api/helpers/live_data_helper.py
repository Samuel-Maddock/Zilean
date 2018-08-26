import json

class LiveDataHelper():

    # TODO: Lots of code duplication here, just use the same method but pass it the filename...

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

    @staticmethod
    def load_summoner_binds():
        with open("league_api/data/live/summoner_binds.json") as bind_file:
            return json.load(bind_file)

    @staticmethod
    def save_summoner_binds(summoner_binds):
        with open("league_api/data/live/summoner_binds.json", "w") as bind_file:
            json.dump(summoner_binds, bind_file)

    @staticmethod
    def user_is_bound(summoner_binds, user_id):
        try:
            summoner_binds[user_id]
            return True
        except KeyError as err:
            return False

    @staticmethod
    def get_user_bound_region(user_id):
        summoner_binds = LiveDataHelper.load_summoner_binds()
        return summoner_binds[str(user_id)][1]