
import json
import re
import random
from datetime import datetime
from disco.bot import Plugin
from disco.types.message import MessageEmbed
from league_api.helpers.league_helper import LeagueHelper

class GameInfoPlugin(Plugin):
    def load(self,ctx):
        super(GameInfoPlugin, self).load(ctx)
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
                game_info = GameInfo(self.league_helper)
                game_info.display(event.msg.channel, region, spectate_info)
            else:
                event.msg.reply("This summoner is not currently in a game!")
        else:
            event.msg.reply("This summoner does not exist on the region: `" + region + "`")

    @Plugin.command("game", "<region:str> <summoner_name:str> [game_number:int]")
    def on_recent_game(self, event, region, summoner_name, game_number=0):
        '''[IN DEVELOPMENT] Displays the most recent game in the summoners match history'''

        if game_number < 0:
            game_number = 0

        region = LeagueHelper.validate_region(region)

        if region is None:
            event.msg.reply("Please enter a valid **region**: *EUW, NA, EUN, JP, LAN, LAS, OCE, TR, RU, KR* :warning:")
            return

        # TODO: has_match_history returns false if history < 20, need to change this...
        if not self.league_helper.has_match_history(region, summoner_name):
            event.msg.reply("This summoner has no valid match history at this time...")
            return

        summoner = self.league_helper.user_exists(region, summoner_name)

        if not summoner:
            event.msg.reply("This summoner does not exist on the region: `" + region + "`")
            return

        matchlist = self.league_helper.watcher.match.matchlist_by_account(region, summoner["id"])

        if game_number > len(matchlist):
            event.msg.reply("The game number entered has exceeded the number of games available (100 max)")
            return
        else:
            game_info = GameInfo()
            match = self.league_helper.watcher.match.by_id(region, matchlist["matches"][game_number]["gameId"])
            print(match)
            game_info.display(event.msg.channel, region, match)
            pass

    @Plugin.command("item", "<item_name:str...>")
    def on_item(self, event, item_name):
        '''Searches and displays the corresponding league of legends item'''
        items = LeagueHelper.get_item_data()
        game_info = GameInfo(self.league_helper)
        item_found = False

        for key, value in items["data"].items():
            if item_name.lower() in value["name"].lower() and len(item_name) > 3:
                game_info.display_item(event.msg.channel, items["version"], items["data"][key])
                item_found = True

        if not item_found:
            event.msg.reply("This item does not exist...")

    @Plugin.command("champion", "<champion_name:str...>")
    def on_champion(self, event, champion_name):
        '''Searches and displays the corresponding league of legends champion'''
        champions = LeagueHelper.get_champion_data()
        game_info = GameInfo(self.league_helper)
        champ_found = False

        for key, name in champions["keys"].items():
            if champion_name.lower() == name.lower():
                game_info.display_champ(event.msg.channel, champions["version"], champions["data"][name])
                champ_found = True

        if not champ_found:
            event.msg.reply("This champ does not exist...")


class GameInfo():
    def __init__(self, league_helper):
        self.league_helper = league_helper

    def _get_queue_data(self):
        with open("league_api/data/static/queue.json") as data_file:
            data = json.load(data_file)
        return data

    def _get_rank_by_queue(self,queue_name, is_ranked, ranked_positions):
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

    def display(self, channel, region, spectate_info):
        channel.send_message("Game found generating live info...")

        if spectate_info["gameType"] == "CUSTOM_GAME":
            channel.send_message("Custom game spectating is not supported SOONtm")
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
        # Currently the CDragon json needs to be updated manually -> TODO
        description, queue_name, pick_type, is_ranked = self._get_queue_info(region, spectate_info)

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
        channel.send_message(embed=embed)

    def display_item(self, channel, version, item):
        image_url = "http://ddragon.leagueoflegends.com/cdn/" + version + "/img/item/"

        embed = MessageEmbed()
        embed.title = item["name"]
        embed.set_author(name="Zilean", icon_url="https://i.imgur.com/JreyU9y.png", url="https://github.com/Samuel-Maddock/Zilean")
        embed.description = item["plaintext"]
        embed.set_thumbnail(url=image_url + item["image"]["full"])
        embed.color = "4390911" # Decimal representation of hex code
        description = re.sub('<[^<]+?>', '\n ', item["description"])
        description = re.sub(r'(\n\s*)+\n+', '\n\n', description)
        embed.add_field(name="Item Description", value=description, inline=True)
        embed.add_field(name ="Buy Price", value=str(item["gold"]["total"]) + " gold", inline=True)
        embed.add_field(name="Sell Price", value=str(item["gold"]["sell"]) + " gold", inline=True)

        channel.send_message(embed=embed)

    def display_champ(self, channel, version, champion):
        image_url = "http://ddragon.leagueoflegends.com/cdn/" + version + "/img/champion/"
        spells = ""
        for spell in champion["spells"]:
            ability = spell["id"].strip(champion["name"])
            name = spell["name"]
            description = spell["description"]
            spells += "**" + ability + ":** " + name + "\n" + description + "\n\n"

        spells += "**Passive:** " + champion["passive"]["name"] + "\n" + champion["passive"]["description"]

        embed = MessageEmbed()
        embed.title = "Champion Info"
        embed.set_author(name="Zilean", icon_url="https://i.imgur.com/JreyU9y.png", url="https://github.com/Samuel-Maddock/Zilean")
        embed.description = champion["name"] + " " + champion["title"]
        embed.set_thumbnail(url=image_url + champion["image"]["full"])
        embed.color = "4390911" # Decimal representation of hex code

        embed.add_field(name="Lore", value=champion["lore"])
        embed.add_field(name="Abilities", value=spells)

        skin_num = random.randint(0, len(champion["skins"])-1)
        embed.set_image(url="http://ddragon.leagueoflegends.com/cdn/img/champion/splash/" + champion["name"] +"_" + str(skin_num) + ".jpg")
        embed.set_footer(text="Splash art: " + str(champion["skins"][skin_num]["name"]))

        channel.send_message(embed=embed)

    # TODO
    def display_past_game(self, channel, region, match):
        pass