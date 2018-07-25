import os
from disco.bot import Plugin
from league_api.graphs.games_per_month import GamesPerMonthGraph
from league_api.graphs.champion_mastery import ChampionMasteryGraph
from league_api.graphs.champion_wins import ChampionWinsGraph
from league_api.graphs.kill_participation import KillParticipationGraph
from league_api.graphs.living_time import LivingTimeGold
from league_api.helper import LeagueHelper

class GraphPlugin(Plugin):
    def load(self,ctx):
        super(GraphPlugin, self).load(ctx)
        self.league_helper = LeagueHelper()

    @Plugin.listen("Ready")
    def on_ready(self, event):
        self.league_helper.update_static_data()

    @Plugin.command('games_per_month', '<region:str> <summoner_name:str...>', group="graph", aliases=["gpm"])
    def on_gpm_graph(self, event, region, summoner_name):
        """Displays a graph of the league games played per month per year"""
        region = LeagueHelper.validate_region(region)
        if self._validate_region(event, region):
            gpm_graph = GamesPerMonthGraph(self.league_helper.watcher, region)
            filepath = "gpm-" + summoner_name + ".png"
            self._graph_renderer(event, gpm_graph, summoner_name, region, filepath, match_validation=True)

    @Plugin.command("champion_mastery", "<region:str> <summoner_name:str...>", group="graph", aliases=["cm"])
    def on_cm_graph(self, event, region, summoner_name):
        """Displays a graph of the summoners top 5 champions by mastery"""
        region = LeagueHelper.validate_region(region)
        if self._validate_region(event, region):
            cm_graph = ChampionMasteryGraph(self.league_helper.watcher, region, LeagueHelper.get_champion_data())
            filepath = "cm-" + summoner_name + ".png"
            self._graph_renderer(event, cm_graph, summoner_name, region, filepath)

    @Plugin.command("champion_wins", "<region:str> <summoner_name:str...>", group="graph", aliases=["cw"])
    def on_cw_graph(self, event, region, summoner_name):
        """Displays a graph of your wins per individual champion over the last 20 games played"""
        region = LeagueHelper.validate_region(region)
        if self._validate_region(event, region):
            cw_graph = ChampionWinsGraph(self.league_helper.watcher, region, LeagueHelper.get_champion_data())
            filepath = "cw-" + summoner_name + ".png"
            self._graph_renderer(event, cw_graph, summoner_name, region, filepath, match_validation=True)

    @Plugin.command("kill_participation", "<region:str> <summoner_name:str...>", group="graph", aliases=["kp"])
    def on_kp_graph(self, event, region, summoner_name):
        """Displays a graph of your kill participation percentage over the last 20 games played"""
        region = LeagueHelper.validate_region(region)
        if self._validate_region(event,region):
            kp_graph = KillParticipationGraph(self.league_helper.watcher, region, LeagueHelper.get_champion_data())
            filepath = "kp-" + summoner_name + ".png"
            self._graph_renderer(event, kp_graph, summoner_name, region, filepath, match_validation=True)

    @Plugin.command("living_time_vs_gold", "<region:str> <summoner_name:str...>", group="graph", aliases=["ltg"])
    def on_ltg_graph(self, event, region, summoner_name):
        """Displays a scatter graph of your longest living time against your total gold earned for 100 recent games"""
        region = LeagueHelper.validate_region(region)
        if self._validate_region(event, region):
            ltg_graph = LivingTimeGold(self.league_helper.watcher, region, LeagueHelper.get_champion_data())
            filepath = "ltg-" + summoner_name + ".png"
            self._graph_renderer(event, ltg_graph, summoner_name, region, filepath, match_validation=True)

    def _graph_renderer(self, event, graph, summoner_name, region, filepath, match_validation=False):
        event.msg.reply("Loading " + summoner_name + "'s data... :hourglass_flowing_sand:")

        if not self.league_helper.has_match_history(region, summoner_name) and match_validation:
            event.msg.reply("This summoner does not exist or has no/not enough games in their match history. Try again with a different summoner!")
            return
        elif self.league_helper.user_exists(region, summoner_name):
            result = graph.render(summoner_name, filepath)
            event.msg.reply(attachments=[(filepath, open(filepath, "rb"))])

            if result is not None:
                event.msg.reply(result)

            os.remove(filepath)
        else:
            event.msg.reply("This summoner does not exist on " + region + ". Maybe try another region!")

    def _validate_region(self, event, region):
        if region is None:
            event.msg.reply("Please enter a valid **region**: *EUW, NA, EUN, JP, LAN, LAS, OCE, TR, RU, KR* :warning:")
            return False
        else:
            return True
