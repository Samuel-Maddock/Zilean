import json
from datetime import datetime
from disco.bot import Plugin
from disco.types.message import MessageEmbed
from disco.api.http import APIException
from league_api.helpers.league_helper import LeagueHelper
from league_api.helpers.live_data_helper import LiveDataHelper
from league_api.helpers.cache_helper import CacheHelper
from plugins.game_info_plugin import GameInfo
from requests.exceptions import ConnectionError

TRACKER_SCHEDULE = 600 # Every 10 minutes

''' TODO: Add subscribe command to DM auto-display games'''

class GameTrackerCommands(Plugin):
    def load(self,ctx):
        super(GameTrackerCommands, self).load(ctx)
        self.league_helper = LeagueHelper()
        self.tracker = self.load_tracker()

    @Plugin.pre_command()
    def on_command_event(self, command, event, args, kwargs):
        CacheHelper.log_command(command, event)
        return event

    def load_tracker(self):
        with open("league_api/data/live/tracker.json") as tracker_file:
            return json.load(tracker_file)

    def update_tracker(self, tracker):
        with open("league_api/data/live/tracker.json", "w") as tracker_file:
            json.dump(tracker, tracker_file)

        self.tracker = tracker

    @Plugin.command("tracker")
    def on_tracker(self, event):
        '''Displays the list of tracked summoners and whether they are in game'''

        if len(event.args) >= 1:
            return;

        if event.msg.channel.is_dm:
            return event.msg.reply("You must use this command in a guild!")

        tracker = self.tracker

        if not self._guild_is_tracked(str(event.msg.guild.id)):
            event.msg.reply("You are currently not tracking any players! Try ~tracker add <region> <summoner_name> to begin...")
            return

        self._display_track(tracker[str(event.msg.guild.id)], event.msg.channel)

    @Plugin.command("add", '[summoner_name:str] [region:str]', group="tracker")
    def on_track(self, event, summoner_name=None, region=None):
        '''Adds a summoner for Zilean to track whether they are in a live game'''
        if event.msg.channel.is_dm:
            return event.msg.reply("You must use this command in a guild!")

        if region is None and summoner_name is None and LiveDataHelper.user_is_bound(LiveDataHelper.load_summoner_binds(), str(event.msg.author.id)):
            region = LiveDataHelper.get_user_bound_region(str(event.msg.author.id))

        region = LeagueHelper.validate_region(region, event)
        if region is None:
            return

        summoner = self.league_helper.user_exists(region, summoner_name, author_id=event.msg.author.id)

        if summoner is False:
            event.msg.reply("This summoner `" + summoner_name + "` does not exist on `" + region + "` Maybe try another region!")
            return

        self._add_summoner(event, region, summoner)

    @Plugin.command("remove", '[summoner_name:str] [region:str]', group="tracker")
    def on_remove(self, event, summoner_name=None, region=None):
        '''Removes a summoner that is being tracked by Zilean'''
        if event.msg.channel.is_dm:
            return event.msg.reply("You must use this command in a guild!")

        if region is None and summoner_name is None and LiveDataHelper.user_is_bound(LiveDataHelper.load_summoner_binds(), str(event.msg.author.id)):
            region = LiveDataHelper.get_user_bound_region(str(event.msg.author.id))
            summoner_name = LiveDataHelper.get_user_bound_name(str(event.msg.author.id))

        region = LeagueHelper.validate_region(region, event, send_event_msg=False)

        if not self._summoner_is_tracked(event.guild.id, summoner_name, region):
            event.msg.reply("This summoner `" + summoner_name + " " + region + "` is not being tracked. Track them by ~tracker add <region> <summoner_name>")
            return

        self._remove_summoner(event, region, summoner_name)

    @Plugin.command("reset", group="tracker")
    def on_reset(self, event):
        '''Removes all of the summoners that are being tracked by Zilean'''
        if event.msg.channel.is_dm:
            return event.msg.reply("You must use this command in a guild!")

        if self._guild_is_tracked(event.msg.guild.id):
            event.msg.reply("The tracker list for this guild has been reset :sparkles:")
            self.tracker[str(event.msg.guild.id)] = list()
            self.update_tracker(self.tracker)
        else:
            event.msg.reply("The tracker list for this guild is empty! Use ~tracker add <region> <summoner_name> to get started...")

    @Plugin.command("auto", "<region:str> <summoner_name:str...>", group="tracker")
    def on_auto(self, event, region, summoner_name):
        '''Toggles a summoner that is being tracked to auto-display there game'''

        # Need to rework this command!
        event.msg.reply("This command is currently being rehauled. For more information join the support server: https://discord.gg/ZjAyh7N")
        return
        # TODO: Rework this command

        if event.msg.channel.is_dm:
            return event.msg.reply("You must use this command in a guild!")

        region = LeagueHelper.validate_region(region)

        if not self._summoner_is_tracked(event.guild.id, summoner_name, region):
            event.msg.reply("This summoner is not being tracked. Track them by ~tracker add <region> <summoner_name>")
            return

        tracker = self.tracker
        guild_id = str(event.guild.id)
        summoner_list = tracker[guild_id]
        auto_message = "no longer being auto-displayed :x:"

        for index, summoner_tuple in enumerate(summoner_list):
            if summoner_tuple[1] == summoner_name.lower() and region == summoner_tuple[2]:
                summoner_tuple = summoner_list[index]
                summoner_list[index] = (summoner_tuple[0], summoner_tuple[1], summoner_tuple[2], not summoner_tuple[3]) # Invert the current bool
                if summoner_list[index][3]:
                    auto_message = "now being auto-displayed :white_check_mark:"

        tracker[guild_id] = summoner_list
        self.update_tracker(tracker)
        event.msg.reply("The summoner `" + summoner_name + "` is " + auto_message)

    @Plugin.schedule(TRACKER_SCHEDULE, init=False)
    def on_schedule_track(self):
        tracker = self.tracker
        channel_binds = LiveDataHelper.load_guild_binds()
        game_info = GameInfo(self.league_helper)

        if len(tracker) == 0:
            return

        for guild_id in channel_binds.keys():
            guild_id = str(guild_id)
            if self._guild_is_tracked(guild_id):
                channel = self.bot.client.state.channels.get(channel_binds[guild_id])
                if channel is not None: # Prevents errors if the bot has left a guild, but the guild id still persits in the binds
                    summoner_list = tracker[guild_id]
                    logger = CacheHelper.get_logger("TrackerMessage")
                    self._display_track(tracker[guild_id], channel)
                    logger.zilean("Tracker: " + guild_id + " " + self.bot.client.state.guilds.get(int(guild_id)).name)

    def _display_track(self, summoner_list, channel):
            game_found = False
            has_live_games = False
            summoner_names = ""
            regions = ""
            in_game = ""
            footer = ""

            connection_failure = False
            for summoner in summoner_list:
                summoner_failed = False
                auto_display = summoner[3]
                summoner_names += summoner[1] + "\n"
                regions += summoner[2] + "\n"

                try:
                    spectate_info = self.league_helper.user_in_game(summoner[2], summoner[0])
                except ConnectionError as e:
                    logger = CacheHelper.get_logger("TrackerError")
                    logger.zilean("Could not connect to the Riot API. Summoner: " + summoner[1] + "Channel: " + channel.name)
                    summoner_failed = True
                    connection_failure = True

                if spectate_info and not summoner_failed:
                    in_game += "**Yes** | " + self.boolMsg(auto_display) + "\n"
                    if auto_display:
                        game_info = GameInfo(self.league_helper)
                        game_info.display_live_game(channel, summoner[2], spectate_info)
                    has_live_games = True
                elif not summoner_failed:
                    in_game += "No | " + self.boolMsg(auto_display) + "\n"
                else:
                    in_game += "Summoner info cannot be retrieved at this time\n"

            if connection_failure:
                footer = "Error retrieving one or more summoners info"
            if not has_live_games:
                footer = "No one is currently in a live game :("
            else:
                footer = "To view a summoner in game use ~game_info <region> <summoner_name>"


            description = "This message is automatically displayed every " + str(int(TRACKER_SCHEDULE/60)) + " minutes!" + \
                                "\n If auto-display is turned on for a summoner their game is automatically displayed"

            embed = CacheHelper.getZileanEmbed(title=":eye: Tracking Live Games... :eye:", description=description, footer=footer)
            embed.add_field(name="Summoner Name", value=summoner_names, inline=True)
            embed.add_field(name="Region", value=regions, inline=True)
            embed.add_field(name="In Game | Auto-Display", value=in_game, inline=True)

            if connection_failure:
                embed.add_field(name="Connection Issue", value="One or more summoners info could not be retrieved. Please try again in a few minutes.")

            try:
                channel.send_message(embed=embed)
            except ConnectionError as e:
                logger = CacheHelper.get_logger("TrackerError")
                logger.zilean("Tracker message failed to send. Could not connect to the Discord API")
            except APIException as e:
                logger = CacheHelper.get_logger("TrackerError")
                logger.zilean(e.status_code)

    def boolMsg(self, bool):
        if bool:
            return "**Yes**"
        else:
            return "No"

    def _guild_is_tracked(self, guild_id):
        tracker = self.tracker
        try:
            a = tracker[str(guild_id)]
            if len(a) == 0:
                return False
            else:
                return True
        except KeyError as err:
            return False

    def _summoner_is_tracked(self, guild_id, summoner_name, region):
        if not self._guild_is_tracked(guild_id):
            return False

        tracker = self.tracker
        summoner_info_list = tracker[str(guild_id)]
        for summoner_tuple in summoner_info_list:
            if summoner_name.lower() == summoner_tuple[1].replace(" ", "").lower() and region == summoner_tuple[2]:
                return True
        return False

    def _add_summoner(self, event, region, summoner, is_auto=False):
        guild_id = str(event.guild.id)
        data = (summoner["id"], summoner["name"].lower(), region, is_auto)
        tracker = self.tracker
        summoner_list = list()

        if self._guild_is_tracked(guild_id):
            if self._summoner_is_tracked(guild_id, summoner["name"], region):
                event.msg.reply("This summoner is already being tracked: `" + summoner["name"] + "`")
                return
            else:
                summoner_list = tracker[guild_id]

        if len(summoner_list) >= 10:
            event.msg.reply("You are already tracking the maximum number (10) of summoners! Use ~tracker remove [region] [summoner_name] to remove a summoner")
            return

        summoner_list.append(data)
        tracker[guild_id] = summoner_list
        self.update_tracker(tracker)

        event.msg.reply("The summoner `" + summoner["name"] + " " + region + "` is now being tracked, tracking messages will be displayed every " + str(int(TRACKER_SCHEDULE/60)) + " minutes :eye:")
        channel_binds = LiveDataHelper.load_guild_binds()

        if LiveDataHelper.guild_is_binded(channel_binds, guild_id):
            channel = self.bot.client.state.channels.get(channel_binds[guild_id])
            event.msg.reply("You will receive track alerts on the current bound text channel: `#" + channel.name + "`")
        else:
            channel = event.msg.channel
            channel_binds[str(guild_id)] = channel.id
            LiveDataHelper.save_guild_binds(channel_binds)
            event.msg.reply("The tracker messages are now bound to the following text channel: `#" + channel.name + "`" + "\n" + "Use ~bind to change the bound text channel")

    def _remove_summoner(self, event, region, summoner_name):
        tracker = self.tracker
        guild_id = str(event.guild.id)
        summoner_list = tracker[guild_id]

        for index, summoner_tuple in enumerate(summoner_list):
            if summoner_tuple[1] == summoner_name.lower() and summoner_tuple[2] == region:
                summoner_name = summoner_tuple[1]
                del summoner_list[index]

        tracker[guild_id] = summoner_list
        self.update_tracker(tracker)
        event.msg.reply("The summoner `" + summoner_name + " " + region + "` is no longer being tracked.")
