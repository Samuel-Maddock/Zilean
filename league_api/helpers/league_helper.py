from riotwatcher import RiotWatcher
from requests import HTTPError
import json
import urllib
import time
from requests.exceptions import ConnectionError
from league_api.helpers.cache_helper import CacheHelper
from league_api.helpers.live_data_helper import LiveDataHelper

# A class that initialises the riot api and provides a set of utility methods for accessing it.
class LeagueHelper:
    API_ENDPOINTS = ["EUW1", "NA1", "EUN1", "KR", "LA1", "LA2", "JP1", "OC1", "TR1", "RU", "BR1"]

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

    @staticmethod
    def get_champion_data():
        with open("league_api/data/static/championFull.json") as data_file:
            data = json.load(data_file)
        return data

    @staticmethod
    def get_item_data():
        with open("league_api/data/static/item.json") as data_file:
            data = json.load(data_file)
        return data

    @staticmethod
    def validate_region(region, event=None):
        region = region.upper()

        region_binds = LiveDataHelper.load_region_binds()
        if region is None and event is not None:
            if LiveDataHelper.guild_has_region(region_binds, str(event.guild.id)):
                region = region_binds[str(event.guild.id)]

        if region in LeagueHelper.API_ENDPOINTS:
            pass
        elif region in ["EUW", "NA", "EUN", "JP", "TR", "BR"]:
            region += "1"
        elif region == "LAN":
            region = "LA1"
        elif region == "LAS":
            region = "LA2"
        elif region == "EU":
            region = "EUW1"
        elif region == "EUNE":
            region = "EUN1"
        elif region == "OCE":
            region = "OC1"
        else:
            region = None

        if event is not None and region is None:
            event.msg.reply("Please enter a valid **region**: *EUW, NA, EUN, JP, LAN, LAS, OCE, TR, RU, KR, BR* :warning:")

        return region