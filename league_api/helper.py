from riotwatcher import RiotWatcher
from requests import HTTPError
import json
import time

# A class that initialises the riot api and provides a set of utility methods for accessing it.
class LeagueHelper:
    def __init__(self):
        with open("config.json") as data_file:
            data = json.load(data_file)
        watcher = RiotWatcher(data["riot_api_key"])
        self.watcher = watcher

    def user_exists(self, region, summoner_name):
        try:
            a = self.watcher.summoner.by_name(region, summoner_name)
        except HTTPError as err:
            if err.response.status_code == 404:
                return False
        return True

    def has_match_history(self, region, summoner_name):
        try:
            summoner = self.watcher.summoner.by_name(region, summoner_name)
            history = self.watcher.match.matchlist_by_account(region, summoner["accountId"])
        except HTTPError as err:
            if err.response.status_code == 404:
                return False
        return True

    def update_static_data(self):
        current_timestamp = time.time()

        with open("league_api/static_data/cache_info.json") as update_info:
            info = json.load(update_info)

        cache_version = info["version"]
        cache_timestamp = info["timestamp"]

        if current_timestamp - int(cache_timestamp) >= 21600: # Update static data every 6 hours
            server_version = self.watcher.static_data.versions("EUW1")[1] # The most recent live version
            print("[LEAGUE-API] Checking for static data version difference...")
            if (server_version != cache_version):
                print("[LEAGUE-API] Version difference detected. detected version: " + cache_version + " live version: " + server_version)
                print("[LEAGUE-API] Current static data out of date - Updating now...")
                self._update_cache(server_version, current_timestamp)
            else:
                self._update_cache_timestamp(server_version, current_timestamp)
                print("[LEAGUE-API] Version up to date: " + server_version)

        else:
            print("[LEAGUE-API] Static data is up to date (within 6 hours) - version: " + cache_version)

    def _update_cache_timestamp(self, server_version, current_timestamp):

        update_info = dict()
        update_info["version"] = server_version
        update_info["timestamp"] = current_timestamp

        with open("league_api/static_data/cache_info.json", "w") as cache_info:
            json.dump(update_info, cache_info)

    def _update_cache(self, server_version, current_timestamp):
        tags = set()

        tags.add("all")

        champions = self.watcher.static_data.champions(region="EUW1", tags=tags)
        with open("league_api/static_data/champions.json", "w") as champion_file:
            json.dump(champions, champion_file)

        items = self.watcher.static_data.items(region="EUW1", tags=tags)
        with open("league_api/static_data/items.json", "w") as item_file:
            json.dump(items, item_file)

        self._update_cache_timestamp(server_version, current_timestamp) # Update the version and timestamp in cache_info.json
        print("[LEAGUE-API] Static data has been updated to version: " + server_version)

    @staticmethod
    def get_champion_data():
        with open("league_api/static_data/champions.json") as data_file:
            data = json.load(data_file)
        return data

    @staticmethod
    def validate_region(region):
        region = region.upper()
        if region in ["EUW", "NA", "EUN", "JP", "LAN", "OCE", "TR", "RU"]:
            region += "1"
        elif region == "KR":
            pass
        elif region == "LAS":
            region += "2"
        elif region == "EU":
            region = "EUW1"
        else:
            region = None
        return region