import os
from disco.bot import Plugin
from league_api.helper import LeagueHelper
from disco.types.message import MessageEmbed
from datetime import datetime

class LiveGamePlugin(Plugin):
    def load(self,ctx):
        super(LiveGamePlugin, self).load(ctx)
        self.league_helper = LeagueHelper()

    @Plugin.command('game_info', '<region:str> <summoner_name:str...>')
    def on_game_info(self, event, region, summoner_name):
        '''Test'''
        region = LeagueHelper.validate_region(region)
        if region is None:
            event.msg.reply("Please enter a valid **region**: *EUW, NA, EUN, JP, LAN, LAS, OCE, TR, RU, KR* :warning:")
            return

        summoner = self.league_helper.user_exists(region, summoner_name)

        if summoner:
            spectate_info = self.league_helper.user_in_game(region, summoner["id"])
            if spectate_info:
                self._send_game_info(event, spectate_info)
            else:
                event.msg.reply("This summoner is not currently in a game!")
        else:
            event.msg.reply("This summoner does not exist on: " + region)

    def _send_game_info(self, event, spectate_info):
        event.msg.reply("Game found generating live info...")
        champion_data = LeagueHelper.get_champion_data()

        teamInfo = list()
        for participant in spectate_info["participants"]:
            champInfo = (participant["teamId"], participant["summonerName"], champion_data["keys"][str(participant["championId"])])
            teamInfo.append(champInfo)

        team1Name = ""
        team1Champ = ""
        team2Name = ""
        team2Champ = ""

        for participant in teamInfo:
            if participant[0] == 100:
                team1Name += participant[1] + "\n"
                team1Champ += participant[2] + "\n"
            else:
                team2Name += participant[1] + "\n"
                team2Champ += participant[2] + "\n"

        embed = MessageEmbed()
        embed.title = "Live Game Info"
        embed.set_author(name="Zilean", icon_url="https://i.imgur.com/JreyU9y.png", url="https://github.com/Samuel-Maddock/Zilean")
        embed.description = "Displaying Live Game Info \n"
        embed.add_field(name=":large_blue_circle: Blue Team", value=team1Name, inline=True)
        embed.add_field(name="Rank", value="a", inline=True)
        embed.add_field(name="Champions:", value=team1Champ, inline=True)
        embed.add_field(name="Red Team", value=team2Name, inline=True)
        embed.add_field(name="Rank", value="a", inline=True)
        embed.add_field(name="Champions:", value=team2Champ, inline=True)
        embed.color = "444751"
        embed.timestamp = datetime.utcnow().isoformat()
        embed.set_footer(text="Live Game Info")
        event.msg.reply(embed=embed)

        #TODO
