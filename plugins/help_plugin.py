from disco.bot import Plugin
from disco.types.message import MessageEmbed
from datetime import datetime


class HelpPlugin(Plugin):
    @Plugin.command("info")
    def on_info(self, event):
        print("Test")
        embed = MessageEmbed()
        embed.title = "Zilean Bot Info"
        embed.set_author(name="Zilean", icon_url="https://i.imgur.com/JreyU9y.png", url="https://github.com/Samuel-Maddock/Zilean")
        embed.description = "Test embed"
        embed.color = "444751"
        embed.timestamp = datetime.utcnow().isoformat()
        embed.set_footer(text="Bot Information")
        event.msg.reply(embed=embed)
