import os

from disco.bot import Plugin
from disco.types.user import GameType, Game, Status
from disco.types.message import  MessageAttachment

from league_api.graphs.games_per_month import GamesPerMonthGraph
from league_api.helper import LeagueHelper


class CorePlugin(Plugin):
    def load(self,ctx):
        super(CorePlugin, self).load(ctx)
        self.league_helper = LeagueHelper()

    @Plugin.command('games_per_month', '<summoner_name:str...>', group="graph", aliases=["gpm"])
    def on_graph(self, event, summoner_name):
        """Displays a graph of the league games played per month per year"""
        gpm_graph = GamesPerMonthGraph(self.league_helper.watcher)
        event.msg.reply("Loading " + summoner_name + "'s data...")

        if summoner_name != "":
            if self.league_helper.user_exists(summoner_name):
                gpm_graph.render(summoner_name)
                filepath = summoner_name + ".png"

                event.msg.reply(attachments=[("wow.png", open(filepath, "rb"))])
                os.remove(summoner_name + ".png")
            else:
                event.msg.reply(":warning: This summoner does not exist :warning:")

    @Plugin.command("ping")
    def on_ping(self, event):
        """A basic ping command"""
        event.msg.reply("Pong!")

    @Plugin.listen("Ready")
    def on_ready(self, event):
        self.client.update_presence(Status.ONLINE, Game(type=GameType.watching, name="you waste time"))

