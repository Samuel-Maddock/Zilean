import py_gg
import json
import urllib.request

''' This class handles the championGG API that is used to display champion builds and statistics'''

class ChampionGGHelper:
    def __init__(self):
        with open("config.json") as data_file:
            data = json.load(data_file)
        self.key = data["champion_gg_token"]

    def generate_build(self, champion):
        champion_id = champion["key"]
        api_url = "http://api.champion.gg/v2/champions/" + champion_id + "?champData=hashes&api_key=" + self.key
        contents = urllib.request.urlopen(api_url).read()
        print(contents)
