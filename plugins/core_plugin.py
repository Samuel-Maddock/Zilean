import math
import json
from datetime import datetime

from disco.bot import Plugin
from disco.types.message import MessageEmbed
from disco.types.user import GameType, Game, Status

from league_api.helpers.live_data_helper import LiveDataHelper


class UtilityPlugin(Plugin):
    def load(self, ctx):
        super(UtilityPlugin, self).load(ctx)

        with open("league_api/data/version.json") as data_file:
            data = json.load(data_file)

        self.version = data["version"]

    @Plugin.command("info")
    def on_info(self, event):
        """Displays information about the bot"""
        embed = MessageEmbed()
        embed.title = "Zilean Bot Info"
        embed.set_author(name="Zilean", icon_url="https://i.imgur.com/JreyU9y.png", url="https://github.com/Samuel-Maddock/Zilean")
        embed.description = "A discord bot that tracks time spent playing league and other statistics :hourglass_flowing_sand: https://github.com/Samuel-Maddock/Zilean"
        embed.add_field(name="Version:", value=self.version)
        embed.add_field(name="Developed using:", value="https://github.com/pseudonym117/Riot-Watcher https://github.com/b1naryth1ef/disco")
        embed.add_field(name="Use ~help for a list of commands!", value=":wave:")
        embed.color = "444751"
        embed.timestamp = datetime.utcnow().isoformat()
        embed.set_footer(text="Bot Information")
        event.msg.reply(embed=embed)

    @Plugin.command("help")
    def on_help(self, event):
        """Displays a list of all of commands"""

        if not event.msg.channel.is_dm:
            event.msg.reply("Check your DMs... :cyclone:")

        user = event.msg.author

        embed = MessageEmbed()
        embed.title = "Zilean Command List"

        for name, plugin in self.bot.plugins.items():
            embed = MessageEmbed()
            embed.title = "Zilean Commands: " + name
            embed.set_author(name="Zilean", icon_url="https://i.imgur.com/JreyU9y.png", url="https://github.com/Samuel-Maddock/Zilean")
            embed.description = "Note that <arg> is a required argument, and [arg] is an optional argument"
            embed.color = "444751"
            embed.timestamp = datetime.utcnow().isoformat()
            embed.set_footer(text="Zilean Commands")
            for command in plugin.commands:
                prefix = self.bot.config.commands_prefix
                description = command.get_docstring()
                cmd_name = ""
                args = ""

                if command.group:
                    prefix += command.group + " "

                if command.args:
                    for arg in command.args.args:
                        if arg.required:
                            args += "<" + arg.name + "> "
                        else:
                            args += "[" + arg.name + "] "

                if len(command.triggers) > 1:
                    for trigger in command.triggers:
                        cmd_name += prefix + trigger + " " + args + " | "
                else:
                    cmd_name = prefix + command.name + " " + args

                embed.add_field(name=cmd_name, value=description)

            user.open_dm().send_message(embed=embed)

    @Plugin.command("ping")
    def on_ping(self, event):
        """A basic ping command, returns the latency in milliseconds"""
        delta = datetime.now() - event.msg.timestamp
        delta_tuple = math.modf(delta.total_seconds())
        ms = round(delta_tuple[0] * 1000)
        event.msg.reply("Pong! " + str(ms) + "ms")

    @Plugin.command("bind")
    def on_bind(self, event):
        '''Binds Zilean to the current text channel to be used during live game alerts'''

        if event.msg.channel.is_dm:
            return event.msg.reply("You must use this command in a guild!")

        guild = event.guild
        channel = event.channel
        channel_binds = LiveDataHelper.load_guild_binds()

        if LiveDataHelper.guild_is_binded(channel_binds, str(guild.id)):
            if channel_binds[str(guild.id)] == channel.id:
                event.msg.reply("Zilean is already bound to this channel: `#" + channel.name + "`")
                return

        channel_binds[str(guild.id)] = channel.id
        LiveDataHelper.save_guild_binds(channel_binds)
        event.msg.reply("The tracker messages are now bound to the following text channel: `#" + channel.name + "`")

    @Plugin.listen("Ready")
    def on_ready(self, event):
        self.client.update_presence(Status.ONLINE, Game(type=GameType.watching, name="you waste time"))
