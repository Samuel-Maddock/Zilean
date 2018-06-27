import numpy as np

from .base_graph import Graph
from riotwatcher import RiotWatcher
import matplotlib.pyplot as plt
from matplotlib import rcParams


class ChampionWinsGraph(Graph):
    def __init__(self, api_watcher, region, champion_json):
        super(ChampionWinsGraph, self).__init__(api_watcher, region)
        self.champion_json = champion_json

    def render(self, summoner_name="SamuelTheRandom", filepath="cw-summoner.png"):
        summoner = self.api_watcher.summoner.by_name(self.region, summoner_name)
        history = self.api_watcher.match.matchlist_by_account(self.region, summoner["accountId"], end_index=20) # Get the most recent 20 games played

        champ_match_dict = dict()
        for match in history["matches"]:
            champion_id_dict = self.champion_json["keys"]
            champion_name = champion_id_dict[str(match["champion"])] # Uses the champion id and retrieves the champions name

            if champion_name not in champ_match_dict:
                match_list = list()
            else:
                match_list = champ_match_dict[champion_name]

            match_list.append(match["gameId"])
            champ_match_dict[champion_name] = match_list
        
        dataset = dict()
        for champion in champ_match_dict:
            games_played = len(champ_match_dict[champion])
            games_won = 0

            for match_id in champ_match_dict[champion]:
                match = self.api_watcher.match.by_id(self.region, match_id)

                for participant in match["participants"]:
                    if self.champion_json["keys"][str(participant["championId"])] == champion:
                        team_id = participant["teamId"]

                for team in match["teams"]:
                    if team["teamId"] == team_id:
                        if team["win"] == "Win":
                            games_won+= 1

            dataset[champion] = (games_played, games_won)

        x = dataset.keys() # The x axis of champion names
        y1,y2 = zip(*dataset.values()) #Unpack the total games played, and games won

        ind = np.arange(len(x))
        width = 0.35

        fig, ax = plt.subplots(1)

        p1 = ax.bar(ind, y1, width, color='#d62728')
        p2 = ax.bar(ind, y2, width)

        plt.ylabel('Number of Games')
        plt.title('Champion wins over the past 20 games played for ' + summoner["name"])
        plt.xticks(ind, x)
        plt.yticks(np.arange(0, 21, 1))
        plt.legend((p1[0], p2[0]), ('Number of Games Played', 'Number of Games Won'))
        fig.autofmt_xdate()
        plt.savefig(filepath, bbox_inches='tight')