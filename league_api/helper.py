from riotwatcher import RiotWatcher
from requests import HTTPError
import json
import urllib
import time

# A class that initialises the riot api and provides a set of utility methods for accessing it.
class LeagueHelper:
    def __init__(self):
        with open("config.json") as data_file:
            data = json.load(data_file)
        watcher = RiotWatcher(data["riot_api_key"])
        self.watcher = watcher

    def user_in_game(self, region, summoner_id):
        spectate_info = None
        try:
            spectate_info = self.watcher.spectator.by_summoner(region, summoner_id)
        except HTTPError as err:
            if err.response.status_code == 404:
                return False
        return spectate_info

    def user_exists(self, region, summoner_name):
        summoner = None
        try:
            summoner = self.watcher.summoner.by_name(region, summoner_name)
        except HTTPError as err:
            if err.response.status_code == 404:
                return False
        return summoner

    def has_match_history(self, region, summoner_name):
        try:
            summoner = self.watcher.summoner.by_name(region, summoner_name)
            history = self.watcher.match.matchlist_by_account(region, summoner["accountId"])
            if len(history["matches"]) < 20:
                return False
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
        version_endpoint = "http://ddragon.leagueoflegends.com/realms/euw.json"

        if current_timestamp - int(cache_timestamp) >= 21600: # Update static data every 6 hours

            with urllib.request.urlopen(version_endpoint) as url:
                data = json.loads(url.read().decode())

            server_version = data["v"] # The most recent live version
            print(server_version)
            print("[ZILEAN] Checking for static data version difference...")
            if (server_version != cache_version):
                print("[ZILEAN] Version difference detected. detected version: " + cache_version + " live version: " + server_version)
                print("[ZILEAN] Current static data out of date - Updating now...")
                self._update_cache(server_version, current_timestamp)
            else:
                self._update_cache_timestamp(server_version, current_timestamp)
                print("[ZILEAN] Version up to date: " + server_version)
        else:
            print("[ZILEAN] Static data is up to date (within 6 hours) - version: " + cache_version)

    def _update_cache_timestamp(self, server_version, current_timestamp):

        update_info = dict()
        update_info["version"] = server_version
        update_info["timestamp"] = current_timestamp

        with open("league_api/static_data/cache_info.json", "w") as cache_info:
            json.dump(update_info, cache_info)

    def _update_cache(self, server_version, current_timestamp):
        endpoint_url = "http://ddragon.leagueoflegends.com/cdn/" + server_version + "/data/en_GB/"
        file_path = "league_api/static_data/"

        static_file_list = ["championFull.json", "item.json"]

        for filename in static_file_list:
            with urllib.request.urlopen(endpoint_url + filename) as url:
                raw_json = json.loads(url.read().decode())

            with open(file_path + filename, "w") as file:
                json.dump(raw_json, file)

        self._update_cache_timestamp(server_version, current_timestamp) # Update the version and timestamp in cache_info.json
        print("[ZILEAN] Static data has been updated to version: " + server_version)

    @staticmethod
    def get_champion_data():
        with open("league_api/static_data/championFull.json") as data_file:
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