import json
import time
import urllib
import logging
from datetime import datetime
from disco.types.message import MessageEmbed

class CacheHelper:

    @staticmethod
    def get_logger(log_name):
        ZILEAN = 20
        logging.addLevelName(ZILEAN, "ZILEAN")

        # Should probably just subclass this logger TODO

        def zilean_cache(self, message, *args, **kws):
            self._log(ZILEAN, message, args, **kws)

        logging.Logger.zilean = zilean_cache
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(log_name)

    @staticmethod
    def log_command(command, event):
        logger = CacheHelper.get_logger(command.name)
        logger.zilean("Guild: " + event.guild.name + " Message: " + event.msg.content + " User: " + str(event.author))

    @staticmethod
    def update_static_data():
        current_timestamp = time.time()
        logger = CacheHelper.get_logger("StaticCache")

        with open("league_api/data/static/cache_info.json") as update_info:
            info = json.load(update_info)

        cache_version = info["version"]
        cache_timestamp = info["timestamp"]
        version_endpoint = "http://ddragon.leagueoflegends.com/realms/euw.json"

        if current_timestamp - int(cache_timestamp) >= 21600: # Update static data every 6 hours

            with urllib.request.urlopen(version_endpoint) as url:
                data = json.loads(url.read().decode())

            server_version = data["v"] # The most recent live version
            logger.zilean("Checking for static data version difference...")
            if server_version != cache_version:
                logger.zilean("Version difference detected. detected version: " + cache_version + " live version: " + server_version)
                logger.zilean("Current static data out of date - Updating now...")
                CacheHelper.update_cache(server_version, current_timestamp)
                logger.zilean("Static data hs been updated to version: " + server_version)
            else:
                CacheHelper._update_cache_timestamp(server_version, current_timestamp)
                logger.zilean("Version up to date: " + server_version)
        else:

            logger.zilean("Static data is up to date (within 6 hours) - version: " + cache_version)

    @staticmethod
    def _update_cache_timestamp(server_version, current_timestamp):
        update_info = dict()
        update_info["version"] = server_version
        update_info["timestamp"] = current_timestamp

        with open("league_api/data/static/cache_info.json", "w") as cache_info:
            json.dump(update_info, cache_info)

    @staticmethod
    def update_cache(server_version, current_timestamp):
        endpoint_url = "http://ddragon.leagueoflegends.com/cdn/" + server_version + "/data/en_GB/"
        file_path = "league_api/data/static/"

        static_file_list = ["championFull.json", "item.json"]

        for filename in static_file_list:
            with urllib.request.urlopen(endpoint_url + filename) as url:
                raw_json = json.loads(url.read().decode())

            with open(file_path + filename, "w") as file:
                json.dump(raw_json, file)

        CacheHelper._update_cache_timestamp(server_version, current_timestamp) # Update the version and timestamp in cache_info.json

    @staticmethod
    def get_guilds():
        with open("league_api/data/guilds.json") as data_file:
            return json.load(data_file)

    @staticmethod
    def save_guilds(guild_list):
        with open("league_api/data/guilds.json", "w") as data_file:
            json.dump(guild_list, data_file)

    @staticmethod
    def getZileanEmbed(title="Zilean Bot", footer="Zilean Bot", description="Zilean Bot"):
        embed = MessageEmbed()

        embed.title = title
        embed.description = description
        embed.set_footer(text=footer)

        embed.set_author(name="Zilean", icon_url="https://i.imgur.com/JreyU9y.png", url="https://samuel-maddock.github.io/Zilean/#commands")
        embed.color = 0x59fff9
        embed.timestamp = datetime.utcnow().isoformat()
        return embed