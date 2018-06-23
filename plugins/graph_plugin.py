import os

from disco.bot import Plugin
from league_api.graphs.games_per_month import GamesPerMonthGraph
from league_api.graphs.champion_mastery import ChampionMasteryGraph
from league_api.helper import LeagueHelper


class GraphPlugin(Plugin):
    def load(self,ctx):
        super(GraphPlugin, self).load(ctx)
        self.league_helper = LeagueHelper()

    @Plugin.command('games_per_month', '<region:str> <summoner_name:str...>', group="graph", aliases=["gpm"])
    def on_gpm_graph(self, event, region, summoner_name):
        """Displays a graph of the league games played per month per year"""

        region = LeagueHelper.validate_region(region)

        if region is None:
            event.msg.reply("Please enter a valid **region**: *EUW, NA, EUN, JP, LAN, LAS, OCE, TR, RU, KR* :warning:")
            return

        gpm_graph = GamesPerMonthGraph(self.league_helper.watcher, region)
        event.msg.reply("Loading " + summoner_name + "'s data... :hourglass_flowing_sand:")

        if not self.league_helper.has_match_history(region, summoner_name):
            event.msg.reply("W0W this summoner doesn't have a recent match history :(")
            return
        elif self.league_helper.user_exists(region, summoner_name):
            filepath = "gpm-" + summoner_name + ".png"
            gpm_graph.render(summoner_name, filepath)
            event.msg.reply(attachments=[(filepath, open(filepath, "rb"))])
            os.remove(filepath)
        else:
            event.msg.reply("This summoner does not exist on " + region + ". Maybe try another region!")

    @Plugin.command("champion_mastery", "<region:str> <summoner_name:str...>", group="graph", aliases=["cm"])
    def on_cm_graph(self, event, region, summoner_name):
        """Displays a graph of the summoners top 5 champions by mastery"""
        region = LeagueHelper.validate_region(region)

        if region is None:
            event.get.msg.reply("Please enter a valid **region**: *EUW, NA, EUN, JP, LAN, LAS, OCE, TR, RU, KR* :warning:")
            return

        cm_graph = ChampionMasteryGraph(self.league_helper.watcher, LeagueHelper.get_champion_data(), region)
        event.msg.reply("Loading " + summoner_name + "'s data... :hourglass_flowing_sand:")

        if self.league_helper.user_exists(region, summoner_name):
            filepath = "cm-" + summoner_name + ".png"
            cm_graph.render(summoner_name, filepath)
            event.msg.reply(attachments=[(filepath, open(filepath, "rb"))])
            os.remove(filepath)
        else:
            event.msg.reply("This summoner does not exist on " + region + ". Maybe try another region!")
