import json
import urllib.request
import urllib3
from league_api.helpers.cache_helper import CacheHelper
from league_api.helpers.league_helper import LeagueHelper
from PIL import Image
import numpy as np
import io

''' This class handles the championGG API that is used to display champion builds and their statistics'''

class ChampionGGHelper:
    def __init__(self):
        with open("config.json") as data_file:
            data = json.load(data_file)
        self.key = data["champion_gg_token"]

    def parse_item_hash(self, hash, items, generate_image=False):
        item_image_url = "http://ddragon.leagueoflegends.com/cdn/" + items["version"] + "/img/item/"
        item_message = ""
        item_urls = []
        for item_id in hash.split("-"):
            item_name = items["data"][item_id]["name"]
            image_name = items["data"][item_id]["image"]["full"]
            item_urls.append(item_image_url + image_name)
            item_message += "*" + item_name + "*  | "

        if generate_image:
            return item_message, item_urls
        else:
            return item_message

    def parse_rune_hash(self, hash, runes):
        rune_message = ""
        rune_path = ""
        rune_image_url = "http://ddragon.leagueoflegends.com/cdn/img/"
        rune_image_urls = []

        for rune_id in hash.split("-"):
            if rune_id in ["8000", "8100", "8200", "8300", "8400"]:
                rune_path = [rune for rune in runes if str(rune.get('id')) == rune_id][0]
                rune_message += "$**" + rune_path["name"] + "**: "
                rune_image_urls.append(rune_image_url + rune_path["icon"])
            else:
                rune_arr = []
                # Get all possible runes for the current rune path
                for slot in rune_path["slots"]:
                    rune_arr = rune_arr + slot["runes"]

                # Select the specific rune and add its image url and name
                for rune in rune_arr:
                    if str(rune.get("id")) == str(rune_id):
                        specific_rune = rune

                rune_image_urls.append(rune_image_url + specific_rune["icon"])
                rune_message += "*" + specific_rune["name"] + "*  |  "

        rune_message = rune_message.split("$")
        return rune_message[1], rune_message[2], rune_image_urls

    def generate_build_image(self, build_urls, filename, vertical=False):
        images = []

        for item_url in build_urls:
            with urllib.request.urlopen(item_url) as url:
                img = io.BytesIO(url.read())
                images.append(Image.open(img))

        min_shape = sorted( [(np.sum(i.size), i.size ) for i in images])[0][1]

        if vertical:
            final_build_image = np.vstack((np.asarray(i.resize(min_shape)) for i in images))
        else:
            final_build_image = np.hstack((np.asarray(i.resize(min_shape)) for i in images))

        final_build_image = Image.fromarray(final_build_image)
        final_build_image.save(filename)


    def generate_build(self, event, champion, version):
        # For ChampionGG API Documentation: http://api.champion.gg/docs/#api-Champions-GetChampion
        # This sends a GET request to the championGG API and retrieves the champions highest winrate build

        champion_id = champion["key"]
        embed = CacheHelper.getZileanEmbed(title="Champion Build", description=champion["name"] + " " + champion["title"])
        api_url = "http://api.champion.gg/v2/champions/" + champion_id + "?champData=hashes&api_key=" + self.key
        response = urllib.request.urlopen(api_url)
        build_info = json.loads(response.read().decode("utf-8"))[0] # Decode the byte response to json object
        # The above also stores the json dict and not the array of the dict

        # Retrieve hashes for the highest winrate build
        hashes = build_info["hashes"]
        skill_order = hashes["skillorderhash"]["highestWinrate"]["hash"].strip("skill-")
        start_items = hashes["firstitemshash"]["highestWinrate"]["hash"].strip("first-")
        final_items = hashes["finalitemshashfixed"]["highestWinrate"]["hash"].strip("items-")
        rune_hash = hashes["runehash"]["highestWinrate"]["hash"]

        # Convert hashes into viewable strings
        items = LeagueHelper.get_item_data()
        runes = LeagueHelper.get_rune_data()

        start_items, start_build_urls = self.parse_item_hash(start_items, items, True)
        final_items, final_build_urls = self.parse_item_hash(final_items, items, True)
        rune_message_1, rune_message_2, rune_path_urls = self.parse_rune_hash(rune_hash, runes)
        skill_order = skill_order.replace("-", ">")

        # Generate the final build image
        self.generate_build_image(final_build_urls, "finalbuild.png")
        self.generate_build_image(start_build_urls, "startbuild.png")
        self.generate_build_image(rune_path_urls[0:5], "runepath1.png")
        self.generate_build_image(rune_path_urls[5:8], "runepath2.png")

        # Append and send message embed and images
        image_url = "http://ddragon.leagueoflegends.com/cdn/" + version + "/img/champion/"
        embed.set_thumbnail(url=image_url + champion["image"]["full"])
        embed.add_field(name="ProBuilds: " + champion["name"], value="https://www.probuilds.net/champions/details/" + champion["name"])
        embed.add_field(name="In-Depth Builds:", value="https://www.mobafire.com/league-of-legends/" + champion["name"] + "-guide?sort=patch&order=ascending&author=all&page=1")
        embed.add_field(name="Skill Order", value=skill_order)
        event.msg.reply(embed=embed)
        event.msg.reply("**Recommended Starting Items:**\n" + start_items, attachments=[("startbuild.png", open("startbuild.png", "rb"))])
        event.msg.reply("**Recommended Final Build:**\n" + final_items, attachments=[("finalbuild.png", open("finalbuild.png", "rb"))])
        event.msg.reply("**Recommended Runes:**\n" + rune_message_1, attachments=[("runepath1.png", open("runepath1.png", "rb"))])
        event.msg.reply(rune_message_2, attachments=[("runepath2.png", open("runepath2.png", "rb"))])

