from riotwatcher import RiotWatcher
from requests import HTTPError
import json

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