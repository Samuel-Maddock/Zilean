from riotwatcher import RiotWatcher
import datetime
import matplotlib.pyplot as plt
from .base_graph import Graph


class GamesPerMonthGraph(Graph):

    def __init__(self, api_watcher, region):
        super(GamesPerMonthGraph, self).__init__(api_watcher, region)

    def retrieve_matchlist(self, summoner):
        canBeLoaded = True
        beginIndex = -100
        total = 0
        gameDateList = []

        # Retrieve a list of all game dates
        while canBeLoaded:
            beginIndex += 100
            history = self.api_watcher.match.matchlist_by_account(self.region, summoner["accountId"], begin_index=beginIndex)

            if len(history["matches"]) < 100:
                canBeLoaded = False

            for match in history["matches"]:
                gameDate = datetime.datetime.fromtimestamp(match["timestamp"]/1000).strftime('%Y-%m-%d %H:%M:%S.%f')
                gameDateList.append(gameDate)

            total += len(history["matches"])

        print("All Game Dates have been loaded for: " + summoner["name"])
        return gameDateList

    def render(self, summoner_name="SamuelTheRandom", filepath="gpm-summoner.png"):
        api_watcher = self.api_watcher
        summoner = api_watcher.summoner.by_name(self.region, summoner_name)
        gameDateList = self.retrieve_matchlist(summoner)

        # Format data into a dictionary of games played per month
        dateData = dict()
        yearSet = set()

        for gameDate in gameDateList:
            year = gameDate[0:4]
            month = gameDate[5:7]
            day = gameDate[8:10]

            key = year + "-" + month

            yearSet.add(year)

            if key not in dateData:
                dateData[key] = 1
            else:
                dateData[key] += 1

        # Formatting the Graph
        months = ["01", "02", "03", "04","05","06","07","08","09","10","11","12"]
        years = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        plt.clf()

        for year in sorted(yearSet):
            gamesPlayed = list()
            for month in months:
                key = year + "-" + month
                if key in dateData.keys():
                    gamesPlayed.append(dateData[key])
                else:
                    gamesPlayed.append(0)
            plt.plot(years, gamesPlayed, "o-", label=year)

        plt.title("League of Legends Games Played Per Month for: " + summoner["name"])
        plt.xlabel("Months of the Year")
        plt.ylabel("Number of Games Played")
        plt.legend(bbox_to_anchor=(1.05, 1),loc=2, borderaxespad=0.)
        plt.savefig(filepath, bbox_inches='tight')