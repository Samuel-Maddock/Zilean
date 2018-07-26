from disco.bot import Plugin
import json
from datetime import datetime

from disco.bot import Plugin
from disco.types.message import MessageEmbed

from league_api.helpers.league_helper import LeagueHelper


class LiveGamePlugin(Plugin):
    def load(self,ctx):
        super(LiveGamePlugin, self).load(ctx)
        self.league_helper = LeagueHelper()

    @Plugin.command('game_info', '<region:str> <summoner_name:str...>')
    def on_game_info(self, event, region, summoner_name):
        '''Displays the live game info if a summoner is in a game. Supports all game types and ranked modes'''
        region = LeagueHelper.validate_region(region)
        if region is None:
            event.msg.reply("Please enter a valid **region**: *EUW, NA, EUN, JP, LAN, LAS, OCE, TR, RU, KR* :warning:")
            return

        summoner = self.league_helper.user_exists(region, summoner_name)

        if summoner:
            spectate_info = self.league_helper.user_in_game(region, summoner["id"])
            if spectate_info:
                self._send_game_info(event, region, spectate_info)
            else:
                event.msg.reply("This summoner is not currently in a game!")
        else:
            event.msg.reply("This summoner does not exist on: " + region)

    def _get_queue_data(self):
        with open("league_api/static_data/queue.json") as data_file:
            data = json.load(data_file)
        return data

    def _get_rank_by_queue(self, queue_name, is_ranked, ranked_positions):
        rank_type = "N/A"
        if is_ranked:
            summoner_rank = "Unranked"
        else:
            summoner_rank = "N/A"

        for rank in ranked_positions:
            temp_rank = rank["tier"] + " " + rank["rank"] + " (" + str(rank["leaguePoints"]) + " lp)"
            if "FLEX_SR" in rank["queueType"] and "5v5" in queue_name and "Flex" in queue_name:
                summoner_rank = temp_rank
                rank_type = "5v5 Flex Queue"
            elif "SOLO_5x5" in rank["queueType"] and "5v5" in queue_name and "Solo" in queue_name:
                summoner_rank = temp_rank
                rank_type = "5v5 Solo/Duo Queue"
            elif "FLEX_TT" in rank["queueType"] and "3v3" in queue_name:
                summoner_rank = temp_rank
                rank_type = "3v3 Flex Queue"

        return (summoner_rank, rank_type)

    def _get_banned_champions(self, banned_champions, champion_data):
        blue_ban = ""
        red_ban = ""

        for banned_champ in banned_champions:
            if banned_champ["championId"] == -1:
                champion = "Missed Ban"
            else:
                champion = champion_data["keys"][str(banned_champ["championId"])]

            if banned_champ["teamId"] == 100:
                blue_ban += champion + "\n"
            else:
                red_ban += champion + "\n"
        return (blue_ban, red_ban)

    def _get_queue_info(self, region, spectate_info):
        queue_data = self._get_queue_data()
        description = ""
        rank_type = "N/A"
        is_ranked = False
        queue_name = "Unknown Queue Type" # Default value
        pick_type = ""
        for queue in queue_data:
            if queue["id"] == spectate_info["gameQueueConfigId"]:
                queue_name = queue["name"]
                description += queue["name"] + "\n"
                description += "**Queue Type:** " + queue["mapType"] + "\n"
                description += "**Game Mode:** " + queue["gameMode"] + "\n"
                description += "**Region:** " + region + "\n"
                pick_type = queue["pickType"]
                is_ranked = queue["ranked"]

        return (description, queue_name, pick_type, is_ranked)

    def _send_game_info(self, event, region, spectate_info):
        event.msg.reply("Game found generating live info...")

        if spectate_info["gameType"] == "CUSTOM_GAME":
            event.msg.reply("Custom game spectating is not supported SOONtm")
            return

        champion_data = LeagueHelper.get_champion_data()

        team_info = list()
        for participant in spectate_info["participants"]:
            champ_info = (participant["teamId"], participant["summonerName"], champion_data["keys"][str(participant["championId"])], participant["summonerId"])
            team_info.append(champ_info)

        blue_names = ""
        blue_champs = ""
        red_names = ""
        red_champs = ""
        blue_rank = ""
        red_rank = ""

        # Find the current game mode that is being played using a CDragon json
        # Currently this needs to be updated manually -> TODO
        description, queue_name, pick_type, is_ranked = self._get_queue_data(region, spectate_info)

        # Find the summoners names, champions and ranks on each team
        for participant in team_info:
            ranked_positions = self.league_helper.watcher.league.positions_by_summoner(region, participant[3])
            rank, rank_type = self._get_rank_by_queue(queue_name, is_ranked, ranked_positions)

            if participant[0] == 100:
                blue_names += participant[1] + "\n"
                blue_champs += participant[2] + "\n"
                blue_rank += rank + "\n"
            else:
                red_names += participant[1] + "\n"
                red_champs += participant[2] + "\n"
                red_rank += rank + "\n"

        # Find the list of banned champions for both teams
        blue_ban, red_ban = self._get_banned_champions(spectate_info["bannedChampions"], champion_data)

        if description == "":
            description = "Playing an unknown gamemode/map -> Please update queue.json "

        # Format all of the live game info using a discord embed message
        embed = MessageEmbed()
        embed.title = "Live Game Info"
        embed.set_author(name="Zilean", icon_url="https://i.imgur.com/JreyU9y.png", url="https://github.com/Samuel-Maddock/Zilean")
        description += "**Ranked Type Being Displayed:** " + rank_type + "\n"
        embed.description = description

        embed.add_field(name=":large_blue_circle: Blue Team", value=blue_names, inline=True)
        embed.add_field(name="Rank", value=blue_rank, inline=True)
        embed.add_field(name="Champions:", value=blue_champs, inline=True)
        embed.add_field(name=":red_circle: Red Team", value=red_names, inline=True)
        embed.add_field(name="Rank", value=red_rank, inline=True)
        embed.add_field(name="Champions:", value=red_champs, inline=True)

        if "DRAFT" in pick_type:
            embed.add_field(name=":no_entry_sign: Red Team Bans :no_entry_sign:", value=red_ban, inline=True)
            embed.add_field(name=":no_entry_sign: Blue Team Bans :no_entry_sign:", value=blue_ban, inline=True)

        embed.color = "444751"
        embed.timestamp = datetime.utcnow().isoformat()
        embed.set_footer(text="Live Game Info")
        event.msg.reply(embed=embed)
