import os

from disco.bot import Plugin
from disco.types.user import GameType, Game, Status
from disco.types.message import  MessageAttachment

from league_api.graphs.games_per_month import GamesPerMonthGraph
from league_api.graphs.champion_mastery import ChampionMasteryGraph
from league_api.helper import LeagueHelper


class CorePlugin(Plugin):
    def load(self,ctx):
        super(CorePlugin, self).load(ctx)
        self.league_helper = LeagueHelper()

    @Plugin.command('games_per_month', '<summoner_name:str...>', group="graph", aliases=["gpm"])
    def on_gpm_graph(self, event, summoner_name):
        """Displays a graph of the league games played per month per year"""
        gpm_graph = GamesPerMonthGraph(self.league_helper.watcher)
        event.msg.reply("Loading " + summoner_name + "'s data...")

        if self.league_helper.user_exists(summoner_name):
            filepath = "gpm-" + summoner_name + ".png"
            gpm_graph.render(summoner_name, filepath)
            event.msg.reply(attachments=[("wow.png", open(filepath, "rb"))])
            os.remove(filepath)
        else:
            event.msg.reply(":warning: This summoner does not exist :warning:")

    @Plugin.command("champion_mastery", "<summoner_name:str...>", group="graph", aliases=["cm"])
    def on_cm_graph(self, event, summoner_name):
        """Displays a graph of the summoners top 5 champions by mastery"""
        cm_graph = ChampionMasteryGraph(self.league_helper.watcher, self.league_helper.get_champion_data())

        if self.league_helper.user_exists(summoner_name):
            filepath = "cm-" + summoner_name + ".png"
            cm_graph.render(summoner_name, filepath)
            event.msg.reply(attachments=[("wow.png", open(filepath, "rb"))])
            os.remove(filepath)
        else:
            event.msg.reply("This summoner does not exist")

    @Plugin.command("ping")
    def on_ping(self, event):
        """A basic ping command"""
        event.msg.reply("Pong!")

    @Plugin.listen("Ready")
    def on_ready(self, event):
        self.client.update_presence(Status.ONLINE, Game(type=GameType.watching, name="you waste time"))

