import numpy as np
import datetime
import matplotlib.pyplot as plt
from .base_graph import Graph

class KillParticipationGraph(Graph):

    def __init__(self, api_watcher, region, champion_json):
        super(KillParticipationGraph, self).__init__(api_watcher, region)
        self.champion_json = champion_json


    def render(self, summoner_name="SamuelTheRandom", filepath="kp-summoner.png"):
        summoner = self.api_watcher.summoner.by_name(self.region, summoner_name)
        history = self.api_watcher.match.matchlist_by_account(self.region, summoner["accountId"], end_index=20) # Get the most recent 20 games played

        dataset = list()
        for match_reference in history["matches"]:
            total_kills = 0
            summoner_kills = 0
            champion_id = match_reference["champion"]
            match = self.api_watcher.match.by_id(self.region, match_reference["gameId"])

            team_kills = dict()
            team_id = "100"
            for participant in match["participants"]:
                if participant["teamId"] not in team_kills.keys():
                    team_kills[participant["teamId"]] = participant["stats"]["kills"]
                else:
                    team_kills[participant["teamId"]] += participant["stats"]["kills"]

                if participant["championId"] == champion_id:
                    team_id = participant["teamId"]
                    summoner_kills = participant["stats"]["kills"] + participant["stats"]["assists"]

            dataset.append(summoner_kills / team_kills[team_id])

        plt.clf()
        x = range(1,21) # 0 to 20
        y = dataset

        ind = np.arange(len(x))
        width = 0.5

        p = plt.bar(ind, y, width, color='#d62728', )

        plt.ylabel('Kill Participation')
        plt.xlabel("Game Number")
        plt.title('Kill Participation over 20 games for ' + summoner["name"])
        plt.xticks(ind, x)
        plt.savefig(filepath, bbox_inches='tight')

        mean = 0
        for data in dataset:
            mean += data
        return "Average Kill Participation: " + str(round(mean/len(dataset) * 100)) + "%"