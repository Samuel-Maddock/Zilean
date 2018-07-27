import json

from disco.bot import Plugin

from league_api.helpers.league_helper import LeagueHelper
from league_api.helpers.live_data_helper import LiveDataHelper
from plugins.game_info_plugin import GameInfo

class GameTracker(Plugin):
    def load(self,ctx):
        super(GameTracker, self).load(ctx)
        self.league_helper = LeagueHelper()
        self.tracker = self.load_tracker()

    def load_tracker(self):
        with open("league_api/live_data/tracker.json") as tracker_file:
            return json.load(tracker_file)

    def update_tracker(self, tracker):
        self.tracker = tracker

    @Plugin.command("add", '<region:str> <summoner_name:str...>', group="tracker")
    def on_track(self, event, region, summoner_name):
        '''Adds a summoner for Zilean to track whether they are in a live game'''
        region = LeagueHelper.validate_region(region)

        if region is None:
            event.msg.reply("Please enter a valid **region**: *EUW, NA, EUN, JP, LAN, LAS, OCE, TR, RU, KR* :warning:")
            return

        summoner = self.league_helper.user_exists(region, summoner_name)

        if summoner is False:
            event.msg.reply("This summoner does not exist on " + region + ". Maybe try another region!")
            return

        self._add_summoner(event, region, summoner)

    @Plugin.command("list", group="tracker")
    def on_list(self, event):
        '''Displays a list of all summoners that Zilean is tracking to see if they are in a live game'''
        msg_content = ""
        guild_id = str(event.guild.id)

        if not self._guild_is_tracked(self.tracker, guild_id):
            event.msg.reply("You are currently not tracking any players! Try ~tracker add <region> <summoner_name> to begin...")
            return

        summoner_list = self.tracker[guild_id]
        for index, summoner in enumerate(summoner_list):
                msg_content += str(index+1) + " - " + summoner[1] + " " + summoner[2] + "\n"
        event.msg.reply(msg_content)

    @Plugin.command("remove", '<region:str> <summoner_name:str...>', group="tracker")
    def on_remove(self, event, region, summoner_name):
        '''Removes a summoner that is being tracked by Zilean'''
        region = LeagueHelper.validate_region(region)

        if region is None:
            event.msg.reply("Please enter a valid **region**: *EUW, NA, EUN, JP, LAN, LAS, OCE, TR, RU, KR* :warning:")
            return
        if not self._summoner_is_tracked(self.tracker, event.guild.id, summoner_name, region):
            event.msg.reply("This summoner is not being tracked. Track them by ~tracker add <region> <summoner_name>")
            return

        self._remove_summoner(event, region, summoner_name)

    @Plugin.schedule(600, init=False) # 5 minute schedule
    def on_schedule_track(self):
        tracker = self.load_tracker()
        channel_binds = LiveDataHelper.load_guild_binds()
        game_info = GameInfo()

        if len(tracker) == 0:
            return

        for guild_id in channel_binds.keys():
            game_found = False
            summoner_list = tracker[guild_id]
            channel = self.bot.client.state.channels.get(channel_binds[guild_id])
            channel.send_message(":eye: Tracking live games... :eye:")
            has_live_games = False

            for summoner in summoner_list:
                spectate_info = self.league_helper.user_in_game(summoner[2], summoner[0])
                if spectate_info:
                    game_info = GameInfo()
                    game_info.display(channel, summoner[2], spectate_info)
                    has_live_games = True
                else:
                    pass

            if not has_live_games:
                channel.send_message("No one is currently in a live game")

    def _guild_is_tracked(self, tracker, guild_id):
        try:
            print(tracker[str(guild_id)])
            return True
        except KeyError as err:
            return False

    def _summoner_is_tracked(self, tracker, guild_id, summoner_name, region):
        summoner_info_list = tracker[str(guild_id)]
        for summoner_tuple in summoner_info_list:
            if summoner_name.lower() == summoner_tuple[1] and region == summoner_tuple[2]:
                return True
        return False

    def _add_summoner(self, event, region, summoner):
        guild_id = str(event.guild.id)
        data = (summoner["id"], summoner["name"].lower(), region)
        tracker = self.load_tracker()
        summoner_list = list()

        if self._guild_is_tracked(tracker, guild_id):
            if self._summoner_is_tracked(tracker, guild_id, summoner["name"], region):
                event.msg.reply("This summoner is already being tracked: `" + summoner["name"] + "`")
                return
            else:
                summoner_list = tracker[guild_id]

        summoner_list.append(data)
        tracker[guild_id] = summoner_list

        with open("league_api/live_data/tracker.json", "w") as tracker_file:
            json.dump(tracker, tracker_file)

        event.msg.reply("The summoner `" + summoner["name"] + "` is now being tracked :eye:")

        channel_binds = LiveDataHelper.load_guild_binds()

        if LiveDataHelper.guild_is_binded(channel_binds, guild_id):
            channel = self.bot.client.state.channels.get(channel_binds[guild_id])
            event.msg.reply("You will receive track alerts on the current bound text channel: `#" + channel.name + "`")
        else:
            channel = event.msg.channel
            event.msg.reply("No text channel is bound to Zilean")
            channel_binds[str(guild_id)] = channel.id
            LiveDataHelper.save_guild_binds(channel_binds)
            event.msg.reply("The tracker messages are now bound to the following text channel: `#" + channel.name + "`")

        self.update_tracker(tracker)

    def _remove_summoner(self, event, region, summoner_name):
        tracker = self.load_tracker()
        guild_id = str(event.guild.id)
        summoner_list = tracker[guild_id]

        for index, summoner_tuple in enumerate(summoner_list):
            if summoner_tuple[1] == summoner_name.lower():
                del summoner_list[index]

        tracker[guild_id] = summoner_list

        with open("league_api/live_data/tracker.json", "w") as tracker_file:
            json.dump(tracker, tracker_file)

        event.msg.reply("This summoner is no longer being tracked.")
        self.update_tracker(tracker)
