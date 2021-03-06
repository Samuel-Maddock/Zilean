import json
import re
import random
import datetime
import urllib

from requests import HTTPError
from disco.bot import Plugin
from disco.types.message import MessageEmbed
from league_api.helpers.league_helper import LeagueHelper
from league_api.helpers.live_data_helper import LiveDataHelper
from league_api.helpers.cache_helper import CacheHelper
from league_api.helpers.championgg_helper import ChampionGGHelper

class GameInfoCommands(Plugin):
    def load(self,ctx):
        super(GameInfoCommands, self).load(ctx)
        self.league_helper = LeagueHelper()

    @Plugin.pre_command()
    def on_command_event(self, command, event, args, kwargs):
        CacheHelper.log_command(command, event)
        return event

    @Plugin.command("patch", "[version:str]")
    def on_patch(self, event, version=None):
        '''Displays the latest patch notes for League of Legends'''
        s = "."
        if not version:
            version = s.join(LeagueHelper.get_champion_data()["version"].split(".", 2)[:2])

        version_url = version.replace(".", "")
        patch_url = "http://na.leagueoflegends.com/en/news/game-updates/patch/patch-" + version_url + "-notes"
        version_url = "http://ddragon.leagueoflegends.com/api/versions.json"

        with urllib.request.urlopen(version_url) as url:
            raw_json = json.loads(url.read().decode())

        versionExists = False
        for patch in raw_json:
            if patch.startswith(version):
                versionExists = True

        if not versionExists:
            event.msg.reply("This is not a valid patch number. Try ~patch for the most recent patch notes!")
            return

        embed = CacheHelper.getZileanEmbed(title="League of Legends Patch Notes", description=version+ " Patch Notes", footer=version + " Patch Notes")
        embed.add_field(name="Notes", value=patch_url)
        event.msg.reply(embed=embed)

    @Plugin.command("status", "[region:str]")
    def on_status(self, event, region=None):
        '''Displays the status of the league of legends servers. Use ~status (region) for a more detailed breakdown'''

        if region:
            self._display_region_status(event, region)
            return

        embed = CacheHelper.getZileanEmbed(title="League of Legends Server Status", description="Use ~status [region] for a more detailed breakdown of server status! Displayed below is the game status", footer="League of Legends Server Status")
        for endpoint in LeagueHelper.API_ENDPOINTS:
            endpoint_status = self.league_helper.watcher.lol_status.shard_data(endpoint)
            embed.add_field(name=endpoint_status["name"] + " (" + endpoint_status["slug"].upper() + ")", value=self._emojify_status(endpoint_status["services"][0]["status"]),inline=True)

        event.msg.reply(embed=embed)

    def _emojify_status(self, status):
        if status == "online":
            return ":white_check_mark:"
        else:
            return ":no_entry_sign:"

    def _display_region_status(self, event, region):
        region = LeagueHelper.validate_region(region)

        if region is None:
            event.msg.reply("Please enter a valid **region**: *EUW, NA, EUN, JP, LAN, LAS, OCE, TR, RU, KR* :warning:")
            return

        embed = CacheHelper.getZileanEmbed(title="Zilean Bot", footer="League of Legends Server Status for " + region, description="Type ~status to see every regions status!")
        endpoint_status = self.league_helper.watcher.lol_status.shard_data(region)
        embed.add_field(name=endpoint_status["name"] + " (" + endpoint_status["slug"].upper() + ")", value="Server Status")

        services = endpoint_status["services"]
        for service in endpoint_status["services"]:
            embed.add_field(name=service["name"], value=self._emojify_status(service["status"]), inline=True)

            if len(service["incidents"]) != 0:
                embed.add_field(name="Incidents", value=str(len(service["incidents"])), inline=True)
                incident_msg = ""
                for incident in service["incidents"]:
                    if len(incident["updates"]) != 0:
                        recent_update = incident["updates"][0]
                        incident_msg += incident["created_at"][0:10] + " " + recent_update["severity"].upper() + ": " + recent_update["content"] + "\n"
                        embed.add_field(name="Incident Description", value= incident_msg, inline=True)
            else:
                embed.add_field(name="Incidents", value="No incidents!", inline=True)
                embed.add_field(name= "Incident Description", value="N/A", inline=True)

        event.msg.reply(embed=embed)

    @Plugin.command('live_game', '"[summoner_name:str] [region:str]"')
    def on_live_game(self, event, summoner_name=None, region=None):
        '''Displays the live game info if a summoner is in a game. Supports all game types and ranked modes'''

        # Prevent command quit on no region given if the discord user has bound a summoner to there account
        if region is None and summoner_name is None and LiveDataHelper.user_is_bound(LiveDataHelper.load_summoner_binds(), str(event.msg.author.id)):
            region = LiveDataHelper.get_user_bound_region(str(event.msg.author.id))

        region = LeagueHelper.validate_region(region, event)
        if region is None:
            return

        summoner = self.league_helper.user_exists(region, summoner_name, event, event.msg.author.id)

        if summoner:
            spectate_info = self.league_helper.user_in_game(region, summoner["id"])
            if spectate_info:
                game_info = GameInfo(self.league_helper)
                game_info.display_live_game(event.msg.channel, region, spectate_info)
            else:
                event.msg.reply("This summoner `" + summoner["name"] +  " " + region + "` is not currently in a game!")

    @Plugin.command("match_history", "[summoner_name:str] [region:str] [game_number:int]")
    def on_recent_game(self, event, summoner_name=None, region=None, game_number=0):
        '''Displays a match in the summoners match history, by default displays the most recent game'''

        game_number = game_number - 1

        if game_number < 0:
            game_number = 0

        # If we want users to have a summoner bound to them we have to deal with the game number being passed as the summoner_name...
        if region is None and LiveDataHelper.user_is_bound(LiveDataHelper.load_summoner_binds(), str(event.msg.author.id)):
            region = LiveDataHelper.get_user_bound_region(str(event.msg.author.id))
            try:
                game_number = int(summoner_name)
                game_number = game_number - 1
                if game_number < 0:
                    game_number = 0
                summoner_name = None
            except ValueError as err:
                pass
            except TypeError as err:
                pass

        # If we want users to choose a match history game and use the default region for the server
        # Then the game number is actually passed to the region variable
        # So we swap them or just leave it if the game number they has passed is not an int
        if LiveDataHelper.guild_has_region(LiveDataHelper.load_region_binds(), str(event.guild.id)) and region is not None:
            try:
                game_number = int(region)
                game_number = game_number - 1
                if game_number < 0:
                    game_number = 0
                region = None
            except ValueError as err:
                pass
            except TypeError as err:
                pass

        region = LeagueHelper.validate_region(region, event)
        if region is None:
            return

        summoner = self.league_helper.user_exists(region, summoner_name, event, event.msg.author.id)
        if not summoner:
            return

        # TODO: has_match_history returns false if history < 20, need to change this...
        if not self.league_helper.has_match_history(region, summoner["name"]):
            event.msg.reply("This summoner has no valid match history at this time `" + region + "`")
            return

        matchlist = self.league_helper.watcher.match.matchlist_by_account(region, summoner["accountId"])

        if game_number > len(matchlist["matches"]):
            event.msg.reply("The game number entered has exceeded the number of games available `Max Games: " + str(len(matchlist["matches"])) + "`")
            return
        else:
            game_info = GameInfo(self.league_helper)
            match = self.league_helper.watcher.match.by_id(region, matchlist["matches"][game_number]["gameId"])
            game_info.display_past_game(event.msg.channel, region, match, summoner["accountId"])

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
            event.msg.reply("This champion does not exist! Try ~champion Akali as an example...")

    @Plugin.command("ability", "<champion_name:str>, [ability:str]")
    def on_ability(self, event, champion_name, ability="all"):
        ''' Displays information about a specific champions ability '''
        champions = LeagueHelper.get_champion_data()
        game_info = GameInfo(self.league_helper)
        abilities = ["q", "w", "e", "r", "passive", "all"]
        champ_found = False

        if ability.lower() in ["ult", "ultimate"]:
            ability = "r"
        elif ability.lower() not in abilities:
            event.msg.reply("This is not a valid ability, Try from one of these " + str(abilities))
            return

        for key,name in champions["keys"].items():
            if champion_name.lower() == name.lower():
                champ_found = True
                if ability == "all":
                    game_info.display_champ(event.msg.channel, champions["version"], champions["data"][name])
                else:
                    game_info.display_ability(event.msg.channel, champions["version"], champions["data"][name], ability)

        if not champ_found:
            event.msg.reply("This champion does not exist! Try ~ability Akali Q as an example...")

    @Plugin.command("summoner", "[summoner_name:str] [region:str]")
    def on_summoner(self, event, summoner_name=None, region=None):
        '''Displays information about a League of Legends summoner'''
        # TODO: Tidy this up...

        # Prevent command quit on no region given if the discord user has bound a summoner to there account
        if region is None and summoner_name is None and LiveDataHelper.user_is_bound(LiveDataHelper.load_summoner_binds(), str(event.msg.author.id)):
            region = LiveDataHelper.get_user_bound_region(str(event.msg.author.id))

        region = LeagueHelper.validate_region(region, event)
        if region is None:
            return

        summoner = self.league_helper.user_exists(region, summoner_name, event, event.msg.author.id)
        if not summoner:
            return

        version = LeagueHelper.get_champion_data()["version"]
        embed = CacheHelper.getZileanEmbed(title="Summoner Profile: ", footer="Displaying summoner info for " + summoner["name"], description=summoner["name"] + " " + region)
        embed.set_thumbnail(url="http://ddragon.leagueoflegends.com/cdn/" + version + "/img/profileicon/" + str(summoner["profileIconId"]) + ".png")
        embed.add_field(name="Summoner Level", value=str(summoner["summonerLevel"]))
        ranked_positions = self.league_helper.watcher.league.positions_by_summoner(region, summoner["id"])

        ranks_array = ["RANKED SOLO 5x5", "RANKED FLEX TT", "RANKED FLEX SR"]
        for rank in ranked_positions:
            rank_name = rank["queueType"].replace("_", " ")
            embed.add_field(name="Queue Type", value=rank_name, inline=True)
            ranks_array.remove(rank_name)

            winrate = round((rank["wins"] / (rank["wins"] + rank["losses"])) * 100)
            rank_msg = rank["tier"] + " " + rank["rank"] + " (" + str(rank["leaguePoints"]) + "lp)"
            winrate_msg = " | " + str(winrate) + "%"
            winloss_msg = " | W:" + str(rank["wins"]) + " L:" + str(rank["losses"])

            embed.add_field(name="Rank | Wins/Losses | Winrate", value= rank_msg + winloss_msg + winrate_msg , inline=True)

        for rank in ranks_array:
            embed.add_field(name="Queue Type", value=rank, inline=True)
            embed.add_field(name="Rank | Wins/Losses | Winrate", value= "UNRANKED", inline=True)

        try:
            matchlist = self.league_helper.watcher.match.matchlist_by_account(region, summoner["accountId"])
            match = self.league_helper.watcher.match.by_id(region, matchlist["matches"][0]["gameId"])

            for participant in match["participantIdentities"]:
                if participant["player"]["currentAccountId"] == summoner["accountId"]:
                    target_player = participant

            for participant in match["participants"]:
                if participant["participantId"] == target_player["participantId"]:
                    target_champion_id = participant["championId"]
                    target_stats = str(participant["stats"]["kills"]) + "/" + str(participant["stats"]["deaths"]) + "/" + str(participant["stats"]["assists"])
                    target_team = participant["teamId"]

            for team in match["teams"]:
                if team["teamId"] == target_team:
                    match_outcome = team["win"]

            if match_outcome == "Fail":
                match_outcome = "Defeat :x:"
            else:
                match_outcome = "Victory :white_check_mark:"

            target_champion = LeagueHelper.get_champion_data()["keys"][str(target_champion_id)]
            embed.add_field(name="Last Game Played:", value= "**" + match_outcome + "**\n" + target_champion + " " + target_stats + " http://matchhistory.euw.leagueoflegends.com/en/#match-details/" + region + "/" + str(match["gameId"]) + "/" + str(summoner["accountId"]) + "?tab=overview")

        except HTTPError as err:
            if err.response.status_code == 404:
                embed.add_field(name="Last Game Played", value="This summoner has not recently played a game.")

        if not self.league_helper.user_in_game(region, summoner["id"]):
            embed.add_field(name="Live Game", value="This summoner is not currently in a live game.")
        else:
            embed.add_field(name="Live Game", value="This summoner is in a live game, type ~live_game " + region + " " + summoner_name + " for more info.")


        event.msg.reply(embed=embed)

    @Plugin.command("build", "<champion_name:str>")
    def on_build(self, event, champion_name):
        '''Displays the highest winrate championGG build for the given champion'''
        champions = LeagueHelper.get_champion_data()
        champ_found = False

        for key, name in champions["keys"].items():
            if champion_name.lower() == name.lower():
                champion_builder = ChampionGGHelper()
                champion_builder.generate_build(event, champions["data"][name], champions["version"])
                champ_found = True

        if not champ_found:
            event.msg.reply("This champion does not exist! Try ~champion Akali as an example...")

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

    def display_live_game(self, channel, region, spectate_info):
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
        embed = CacheHelper.getZileanEmbed(title="Live Game Info", description=description, footer="Live Game Info")

        embed.add_field(name=":large_blue_circle: Blue Team", value=blue_names, inline=True)
        embed.add_field(name="Rank", value=blue_rank, inline=True)
        embed.add_field(name="Champions:", value=blue_champs, inline=True)
        embed.add_field(name=":red_circle: Red Team", value=red_names, inline=True)
        embed.add_field(name="Rank", value=red_rank, inline=True)
        embed.add_field(name="Champions:", value=red_champs, inline=True)

        if "DRAFT" in pick_type:
            embed.add_field(name=":no_entry_sign: Red Team Bans :no_entry_sign:", value=red_ban, inline=True)
            embed.add_field(name=":no_entry_sign: Blue Team Bans :no_entry_sign:", value=blue_ban, inline=True)

        channel.send_message(embed=embed)

    def display_item(self, channel, version, item):
        image_url = "http://ddragon.leagueoflegends.com/cdn/" + version + "/img/item/"

        embed = CacheHelper.getZileanEmbed(title=item["name"], description=item["plaintext"])
        embed.set_thumbnail(url=image_url + item["image"]["full"])
        description = re.sub('<[^<]+?>', '\n ', item["description"])
        description = re.sub(r'(\n\s*)+\n+', '\n\n', description)
        embed.add_field(name="Item Description", value=description, inline=True)
        embed.add_field(name ="Buy Price", value=str(item["gold"]["total"]) + " gold", inline=True)
        embed.add_field(name="Sell Price", value=str(item["gold"]["sell"]) + " gold", inline=True)

        channel.send_message(embed=embed)

    def display_ability(self, channel, version, champion, ability):
        embed = CacheHelper.getZileanEmbed(title="Champion Ability", description=champion["name"] + " " + champion["title"])
        ability_list = ["Q", "W", "E", "R"]
        image_url = "http://ddragon.leagueoflegends.com/cdn/" + version + "/img/spell/"
        passive_url = "http://ddragon.leagueoflegends.com/cdn/" + version + "/img/passive/"

        if ability.lower() == "passive":
            embed.add_field(name="Passive - " + champion["passive"]["name"], value="\n" + champion["passive"]["description"])
            embed.set_thumbnail(url=passive_url + champion["passive"]["image"]["full"])
        else:
            spellIndex = 0
            for index, abilityTrigger in enumerate(ability_list):
                if abilityTrigger.lower() == ability.lower():
                    spellIndex = index

            spell = champion["spells"][spellIndex]
            name = spell["name"]
            description = spell["description"]
            embed.add_field(name=ability.upper() + "- " + name, value="\n" + description)
            embed.set_thumbnail(url=image_url + spell["image"]["full"])

        channel.send_message(embed=embed)

    def display_champ(self, channel, version, champion):
        image_url = "http://ddragon.leagueoflegends.com/cdn/" + version + "/img/champion/"
        spells = ""
        ability_list = ["Q", "W", "E", "R"]

        embed = CacheHelper.getZileanEmbed(title="Champion Info", description=champion["name"] + " " + champion["title"])
        embed.add_field(name="Lore", value=champion["lore"])
        embed.add_field(name="Passive - " + champion["passive"]["name"], value="\n" + champion["passive"]["description"])

        for index, spell in enumerate(champion["spells"]):
            ability = ability_list[index]
            name = spell["name"]
            description = spell["description"]
            embed.add_field(name=ability + "- " + name, value="\n" + description)

        embed.set_thumbnail(url=image_url + champion["image"]["full"])
        skin_num = random.randint(0, len(champion["skins"])-1)
        embed.set_image(url="http://ddragon.leagueoflegends.com/cdn/img/champion/splash/" + champion["name"] +"_" + str(skin_num) + ".jpg")
        embed.set_footer(text="Splash art: " + str(champion["skins"][skin_num]["name"]))
        channel.send_message(embed=embed)

    def display_past_game(self, channel, region, match, summoner_id):

        # Find the current game mode that is being played using a CDragon json
        match["gameQueueConfigId"] = match["queueId"]
        description, queue_name, pick_type, is_ranked = self._get_queue_info(region, match)

        game_epoch = match["gameCreation"]
        game_duration = datetime.timedelta(seconds=match["gameDuration"])
        game_date = datetime.datetime.fromtimestamp(game_epoch/1000).strftime('%d-%m-%Y')

        champion_data = LeagueHelper.get_champion_data()
        image_url = "http://ddragon.leagueoflegends.com/cdn/" + champion_data["version"] + "/img/champion/"

        for participant in match["participantIdentities"]:
            if participant["player"]["currentAccountId"] == summoner_id:
                target_player = participant

        for participant in match["participants"]:
            if participant["participantId"] == target_player["participantId"]:
                target_champion_id = participant["championId"]
                target_stats = str(participant["stats"]["kills"]) + "/" + str(participant["stats"]["deaths"]) + "/" + str(participant["stats"]["assists"])
                target_team = participant["teamId"]

        for team in match["teams"]:
            if team["teamId"] == target_team:
                match_outcome = team["win"]

        if match_outcome == "Fail":
            match_outcome = "Defeat"
            embed_color = 16711686
        else:
            match_outcome = "Victory"
            embed_color = 65286

        target_champion = champion_data["keys"][str(target_champion_id)]

        embed = CacheHelper.getZileanEmbed(title="Match History Game Info", description=queue_name)
        embed.set_thumbnail(url=image_url + target_champion + ".png")
        embed.color = embed_color
        embed.add_field(name="Summoner Name", value=target_player["player"]["summonerName"], inline=True)
        embed.add_field(name="Champion", value=target_champion, inline=True)
        embed.add_field(name="k/d/a", value=target_stats, inline=True)
        embed.add_field(name="Match Outcome", value=match_outcome, inline=True)
        embed.add_field(name="Game Duration:", value = str(game_duration), inline=True)
        embed.add_field(name="Game Date:", value=game_date, inline=True)
        embed.add_field(name="More Info", value="http://matchhistory.euw.leagueoflegends.com/en/#match-details/" + region + "/" + str(match["gameId"]) + "/" + str(summoner_id) + "?tab=overview")
        channel.send_message(embed=embed)