import os

from disco.bot import Plugin

from league_api.graphs.champion_mastery import ChampionMasteryGraph
from league_api.graphs.champion_wins import ChampionWinsGraph
from league_api.graphs.games_per_month import GamesPerMonthGraph
from league_api.graphs.kill_participation import KillParticipationGraph
from league_api.helpers.league_helper import LeagueHelper
from league_api.helpers.cache_helper import CacheHelper
from league_api.helpers.live_data_helper import LiveDataHelper


class GraphCommands(Plugin):
    def load(self,ctx):
        super(GraphCommands, self).load(ctx)
        self.league_helper = LeagueHelper()

    @Plugin.pre_command()
    def on_command_event(self, command, event, args, kwargs):
        CacheHelper.log_command(command, event)
        return event

    @Plugin.command('games_per_month', "[summoner_name:str] [region:str]", group="graph", aliases=["gpm"])
    def on_gpm_graph(self, event, summoner_name=None, region=None):
        """Displays a graph of the league games played per month per year"""
        region = LeagueHelper.validate_region(region, event)
        if region:
            gpm_graph = GamesPerMonthGraph(self.league_helper.watcher, region)
            if summoner_name is not None:
                filepath = "gpm-" + summoner_name + ".png"
            else:
                filepath = "gpm-default.png"
            self._graph_renderer(event, gpm_graph, summoner_name, region, filepath, match_validation=True)

    @Plugin.command("champion_mastery", "[summoner_name:str] [region:str]", group="graph", aliases=["cm"])
    def on_cm_graph(self, event, summoner_name=None, region=None):
        """Displays a graph of the summoners top 5 champions by mastery"""
        region = LeagueHelper.validate_region(region, event)
        if region:
            cm_graph = ChampionMasteryGraph(self.league_helper.watcher, region, LeagueHelper.get_champion_data())
            if summoner_name is not None:
                filepath = "cm-" + summoner_name + ".png"
            else:
                filepath = "cm-default.png"
            self._graph_renderer(event, cm_graph, summoner_name, region, filepath)

    @Plugin.command("champion_wins", "[summoner_name:str] [region:str]", group="graph", aliases=["cw"])
    def on_cw_graph(self, event, summoner_name=None, region=None):
        """Displays a graph of your wins per individual champion over the last 20 games played"""
        region = LeagueHelper.validate_region(region, event)

        if region:
            cw_graph = ChampionWinsGraph(self.league_helper.watcher, region, LeagueHelper.get_champion_data())
            if summoner_name is not None:
                filepath = "cw-" + summoner_name + ".png"
            else:
                filepath = "cw-default.png"
            self._graph_renderer(event, cw_graph, summoner_name, region, filepath, match_validation=True)

    @Plugin.command("kill_participation", "[summoner_name:str] [region:str]", group="graph", aliases=["kp"])
    def on_kp_graph(self, event, summoner_name=None, region=None):
        """Displays a graph of your kill participation percentage over the last 20 games played"""
        region = LeagueHelper.validate_region(region, event)
        if region:
            kp_graph = KillParticipationGraph(self.league_helper.watcher, region, LeagueHelper.get_champion_data())
            if summoner_name is not None:
                filepath = "kp-" + summoner_name + ".png"
            else:
                filepath = "kp-default.png"
            self._graph_renderer(event, kp_graph, summoner_name, region, filepath, match_validation=True)

    '''
    @Plugin.command("living_time_vs_gold", "<region:str> <summoner_name:str...>", group="graph", aliases=["ltg"])
    def on_ltg_graph(self, event, region, summoner_name):
        """Displays a scatter graph of your longest living time against your total gold earned for 100 recent games"""
        region = LeagueHelper.validate_region(region)
        if self._validate_region(event, region):
            ltg_graph = LivingTimeGold(self.league_helper.watcher, region, LeagueHelper.get_champion_data())
            filepath = "ltg-" + summoner_name + ".png"
            self._graph_renderer(event, ltg_graph, summoner_name, region, filepath, match_validation=True) 
    '''

    def _graph_renderer(self, event, graph, summoner_name, region, filepath, match_validation=False):

        if summoner_name is None and LiveDataHelper.user_is_bound(LiveDataHelper.load_summoner_binds(), str(event.msg.author.id)):
            summoner_tuple = LiveDataHelper.load_summoner_binds()[str(event.msg.author.id)]
            summoner_name = summoner_tuple[0]
            region = summoner_tuple[1]
            graph.set_region(region)

        if not self.league_helper.has_match_history(region, summoner_name) and match_validation:
            event.msg.reply("The summoner `" + summoner_name + "` does not exist on the region `" + region + "` or does not have enough games in their match history. Try again with a different summoner!")
            return
        elif self.league_helper.user_exists(region, summoner_name, event):
            event.msg.reply("Loading " + summoner_name + "'s data... :hourglass_flowing_sand:")
            result = graph.render(summoner_name, filepath)
            event.msg.reply(attachments=[(filepath, open(filepath, "rb"))])

            if result is not None:
                event.msg.reply(result)

            os.remove(filepath)
