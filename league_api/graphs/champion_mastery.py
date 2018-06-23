import numpy as np

from .base_graph import Graph
from riotwatcher import RiotWatcher
import matplotlib.pyplot as plt
import datetime


class ChampionMasteryGraph(Graph):

    def __init__(self, api_watcher, champion_json, region):
        super(ChampionMasteryGraph, self).__init__(api_watcher, region)
        self.champion_json = champion_json

    def render(self, summoner_name="SamuelTheRandom", filepath="cm-summoner.png"):
        api_watcher = self.api_watcher

        summoner = api_watcher.summoner.by_name(self.region, summoner_name)
        champion_mastery = api_watcher.champion_mastery.by_summoner(self.region, summoner["id"])
        cm_data = []

        for i in range(0,5):
            mastery = champion_mastery[i]
            champion_id = mastery["championId"]
            champion_name = ""

            for name, info in self.champion_json["data"].items():
                if info["key"] == str(champion_id):
                    champion_name = name

            champion_level = mastery["championLevel"]
            cm_data.append((champion_name, champion_level))

        cm_data = sorted(cm_data, reverse=True, key=lambda tup: tup[1])
        x,y = zip(*cm_data)
        plt.clf()
        y_pos = np.arange(len(y))

        barlist = plt.bar(y_pos, y, align="center", alpha=0.5)
        plt.xticks(y_pos, x)
        plt.title("Top 5 Champion Mastery for " + summoner["name"])

        plt.savefig(filepath, bbox_inches='tight')