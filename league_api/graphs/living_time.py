import datetime
import matplotlib.pyplot as plt
from .base_graph import Graph
from scipy.stats.stats import pearsonr

class LivingTimeGold(Graph):
    def __init__(self, api_watcher, region, champion_json):
        super(LivingTimeGold, self).__init__(api_watcher, region)
        self.champion_json = champion_json

    def render(self, summoner_name="SamuelTheRandom", filepath="test.png"):
        summoner = self.api_watcher.summoner.by_name(self.region, summoner_name)
        history = self.api_watcher.match.matchlist_by_account(self.region, summoner["accountId"]) # Plot 100 games worth of data

        dataset = list()
        for match_reference in history["matches"]:
            match = self.api_watcher.match.by_id(self.region, match_reference["gameId"])
            longest_living_time = 0
            total_damage_taken = 0

            for participant in match["participants"]:
                if participant["championId"] == match_reference["champion"]:
                    longest_living_time = participant["stats"]["longestTimeSpentLiving"]
                    total_damage_taken = participant["stats"]["goldEarned"]

            dataset.append((longest_living_time, total_damage_taken))

        x,y = zip(*dataset)
        plt.clf()
        plt.scatter(x,y)
        plt.xlabel("Longest time spent living (seconds)")
        plt.ylabel("Total Gold Earnt")
        plt.title("Over 100 games, the longest time spent living plotted against total gold earned " + summoner["name"])
        plt.savefig(filepath, bbox_inches='tight')
        return "Correlation: " + str(pearsonr(x,y)[0]) # Returns the correlation