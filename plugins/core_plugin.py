import os

from disco.bot import Plugin
from disco.types.user import GameType, Game, Status

import league_api.graphs.games_per_month as gpm_graph
from league_api.helper import LeagueHelper


class CorePlugin(Plugin):
    def load(self,ctx):
        super(CorePlugin, self).load(ctx)
        self.league_helper = LeagueHelper()

    @Plugin.command('graph', '<summoner_name:str...>')
    def on_graph(self, event, summoner_name):
        league_helper = self.league_helper
        event.msg.reply("Loading " + summoner_name +  " data...")

        if summoner_name != "":
            if league_helper.user_exists(summoner_name):
                gpm_graph.render(league_helper.watcher, summoner_name)
                event.msg.reply(attachments=[("wow.png", open(summoner_name + ".png", "r"))])
                os.remove(summoner_name+".png")
            else:
                event.msg.reply(":warning: This summoner does not exist :warning:")

    @Plugin.command("ping")
    def on_ping(self, event):
        event.msg.reply("Pong!")

    @Plugin.listen("Ready")
    def on_ready(self, event):
        self.client.update_presence(Status.ONLINE, Game(type=GameType.watching, name="you waste time"))

