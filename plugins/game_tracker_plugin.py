from disco.bot import Plugin
from league_api.helper import LeagueHelper
import json

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

    @Plugin.command('add', '<region:str> <summoner_name:str...>', group="tracker")
    def on_track(self, event, region, summoner_name):
        '''In Development'''
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
        msg_content = ""
        for index, key in enumerate(self.tracker.keys()):
            data = self.tracker[key]
            msg_content += str(index+1) + " - " + data[1] + " " + data[2] + "\n"
        event.msg.reply(msg_content)

    @Plugin.command("remove", '<region:str> <summoner_name:str...>', group="tracker")
    def on_remove(self, event, region, summoner_name):
        region = LeagueHelper.validate_region(region)

        if region is None:
            event.msg.reply("Please enter a valid **region**: *EUW, NA, EUN, JP, LAN, LAS, OCE, TR, RU, KR* :warning:")
            return
        if not self._summoner_is_tracked(self.tracker, summoner_name, region):
            event.msg.reply("This summoner is not being tracked. Track them by ~tracker add <region> <summoner_name>")
            return

        self._remove_summoner(event, region, summoner_name)

    @Plugin.schedule(5)
    def on_track(self):
        pass


    def _is_tracked(self, tracker, summoner_id):
        try:
            print(tracker[str(summoner_id)])
            return True
        except KeyError as err:
            return False

    def _summoner_is_tracked(self, tracker, summoner_name, region):
        for key, value in tracker.items():
            if value[1] == summoner_name and value[2] == region:
                return True
        return False

    def _add_summoner(self, event, region, summoner):

        data = (summoner["id"], summoner["name"].lower(), region)
        tracker = self.load_tracker()

        if self._is_tracked(tracker, summoner["id"]):
            event.msg.reply("This summoner is already being tracked. Use ~tracker list to see a list of all summoners")
            return

        tracker[str(summoner["id"])] = data

        with open("league_api/live_data/tracker.json", "w") as tracker_file:
            json.dump(tracker, tracker_file)

        event.msg.reply("This summoner is now being tracked :eye:")
        self.update_tracker(tracker)

    def _remove_summoner(self, event, region, summoner):
        tracker = self.load_tracker()

        for key, value in list(tracker.items()):
            if value[1] == summoner:
                del tracker[key]

        with open("league_api/live_data/tracker.json", "w") as tracker_file:
            json.dump(tracker, tracker_file)

        event.msg.reply("This summoner is no longer being tracked.")
        self.update_tracker(tracker)
