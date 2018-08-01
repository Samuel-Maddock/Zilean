import json
from datetime import datetime
from disco.bot import Plugin
from disco.types.message import MessageEmbed
from league_api.helpers.league_helper import LeagueHelper
from league_api.helpers.live_data_helper import LiveDataHelper
from plugins.game_info_plugin import GameInfo

TRACKER_SCHEDULE = 600 # Every 10 minutes

class GameTracker(Plugin):
    def load(self,ctx):
        super(GameTracker, self).load(ctx)
        self.league_helper = LeagueHelper()
        self.tracker = self.load_tracker()

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
        if event.msg.channel.is_dm:
            return event.msg.reply("You must use this command in a guild!")

        tracker = self.tracker

        if not self._guild_is_tracked(str(event.msg.guild.id)):
            event.msg.reply("You are currently not tracking any players! Try ~tracker add <region> <summoner_name> to begin...")
            return

        self._display_track(tracker[str(event.msg.guild.id)], event.msg.channel)

    @Plugin.command("add", '<region:str> <summoner_name:str...>', group="tracker")
    def on_track(self, event, region, summoner_name):
        '''Adds a summoner for Zilean to track whether they are in a live game'''
        if event.msg.channel.is_dm:
            return event.msg.reply("You must use this command in a guild!")

        region = LeagueHelper.validate_region(region)

        if region is None:
            event.msg.reply("Please enter a valid **region**: *EUW, NA, EUN, JP, LAN, LAS, OCE, TR, RU, KR* :warning:")
            return

        summoner = self.league_helper.user_exists(region, summoner_name)

        if summoner is False:
            event.msg.reply("This summoner does not exist on " + region + ". Maybe try another region!")
            return

        self._add_summoner(event, region, summoner)

    @Plugin.command("remove", '<region:str> <summoner_name:str...>', group="tracker")
    def on_remove(self, event, region, summoner_name):
        '''Removes a summoner that is being tracked by Zilean'''
        if event.msg.channel.is_dm:
            return event.msg.reply("You must use this command in a guild!")

        region = LeagueHelper.validate_region(region)

        if region is None:
            event.msg.reply("Please enter a valid **region**: *EUW, NA, EUN, JP, LAN, LAS, OCE, TR, RU, KR* :warning:")
            return
        if not self._summoner_is_tracked(event.guild.id, summoner_name, region):
            event.msg.reply("This summoner is not being tracked. Track them by ~tracker add <region> <summoner_name>")
            return

        self._remove_summoner(event, region, summoner_name)

    @Plugin.command("reset", group="tracker")
    def on_reset(self, event):
        '''Removes all of the summoner that are being tracked by Zilean'''
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
                summoner_list[index][3] = (not summoner_tuple[3]) # Invert the current bool
                if summoner_list[index][3]:
                    auto_message = "now being auto-displayed :white_check_mark:"

        tracker[guild_id] = summoner_list
        self.update_tracker(tracker)
        event.msg.reply("The summoner `" + summoner_name + "` is " + auto_message)

    @Plugin.schedule(TRACKER_SCHEDULE, init=False)
    def on_schedule_track(self):
        tracker = self.tracker
        channel_binds = LiveDataHelper.load_guild_binds()
        game_info = GameInfo()

        if len(tracker) == 0:
            return

        for guild_id in channel_binds.keys():
            guild_id = str(guild_id)
            channel = self.bot.client.state.channels.get(channel_binds[guild_id])
            summoner_list = tracker[guild_id]
            if len(summoner_list) != 0:
                self._display_track(tracker[guild_id], channel)

    def _display_track(self, summoner_list, channel):
            game_found = False
            has_live_games = False
            summoner_names = ""
            regions = ""
            in_game = ""
            footer = ""

            for summoner in summoner_list:
                auto_display = summoner[3]
                summoner_names += summoner[1] + "\n"
                regions += summoner[2] + "\n"

                spectate_info = self.league_helper.user_in_game(summoner[2], summoner[0])
                if spectate_info:
                    in_game += "**Yes** | " + self.boolMsg(auto_display) + "\n"
                    if auto_display:
                        game_info = GameInfo()
                        game_info.display(channel, summoner[2], spectate_info)
                    has_live_games = True
                else:
                    in_game += "No | " + self.boolMsg(auto_display) + "\n"

            if not has_live_games:
                footer = "No one is currently in a live game :("
            else:
                footer = "To view a summoner in game use ~game_info <region> <summoner_name>"

            embed = MessageEmbed()
            embed.title = ":eye: Tracking Live Games... :eye:"

            embed.description = "This message is automatically displayed every " + str(int(TRACKER_SCHEDULE/60)) + " minutes!" + \
                                "\n If auto-display is turned on for a summoner their game is automatically displayed"

            embed.set_author(name="Zilean", icon_url="https://i.imgur.com/JreyU9y.png", url="https://github.com/Samuel-Maddock/Zilean")
            embed.add_field(name="Summoner Name", value=summoner_names, inline=True)
            embed.add_field(name="Region", value=regions, inline=True)
            embed.add_field(name="In Game | Auto-Display", value=in_game, inline=True)
            embed.color = "444751"
            embed.timestamp = datetime.utcnow().isoformat()
            embed.set_footer(text=footer)
            channel.send_message(embed=embed)

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
        tracker = self.tracker
        summoner_info_list = tracker[str(guild_id)]
        for summoner_tuple in summoner_info_list:
            if summoner_name.lower() == summoner_tuple[1] and region == summoner_tuple[2]:
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

        summoner_list.append(data)
        tracker[guild_id] = summoner_list
        self.update_tracker(tracker)

        event.msg.reply("The summoner `" + summoner["name"] + "` is now being tracked, tracking messages will be displayed every " + str(int(TRACKER_SCHEDULE/60)) + " minutes :eye:")
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
                del summoner_list[index]

        tracker[guild_id] = summoner_list
        self.update_tracker(tracker)
        event.msg.reply("This summoner is no longer being tracked.")
