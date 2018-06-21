from riotwatcher import RiotWatcher
from requests import HTTPError
import json


class LeagueHelper:
    def __init__(self):
        with open("config.json") as data_file:
            data = json.load(data_file)
        watcher = RiotWatcher(data["riot_api_key"])
        self.watcher = watcher

    def user_exists(self, summoner_name):
        result = True
        try:
            a = self.watcher.summoner.by_name("EUW1", summoner_name)
        except HTTPError as err:
            if err.response.status_code == 404:
                result = False
        return result
