from disco.bot import Plugin
from disco.types.message import MessageEmbed
from datetime import datetime
from disco.types.user import GameType, Game, Status


class HelpPlugin(Plugin):
    def load(self, ctx):
        super(HelpPlugin, self).load(ctx)
        for command in self.commands:
            command.description = "test"

    @Plugin.command("info")
    def on_info(self, event):
        """Displays information about the bot"""
        print("Test")
        embed = MessageEmbed()
        embed.title = "Zilean Bot Info"
        embed.set_author(name="Zilean", icon_url="https://i.imgur.com/JreyU9y.png", url="https://github.com/Samuel-Maddock/Zilean")
        embed.description = "A discord bot that tracks time spent playing league and other statistics :hourglass_flowing_sand: https://github.com/Samuel-Maddock/Zilean"
        embed.add_field(name="Developed using:", value="https://github.com/pseudonym117/Riot-Watcher https://github.com/b1naryth1ef/disco")
        embed.add_field(name="Use ~help for a list of commands!", value=":wave:")
        embed.color = "444751"
        embed.timestamp = datetime.utcnow().isoformat()
        embed.set_footer(text="Bot Information")
        event.msg.reply(embed=embed)

    @Plugin.command("help")
    def on_help(self, event):
        """Displays a list of all of commands"""

        embed = MessageEmbed()
        embed.title = "Zilean Command List"
        embed.set_author(name="Zilean", icon_url="https://i.imgur.com/JreyU9y.png", url="https://github.com/Samuel-Maddock/Zilean")
        embed.description = "A list of Zilean's commands"
        embed.color = "444751"
        embed.timestamp = datetime.utcnow().isoformat()
        embed.set_footer(text="Zilean Commands")

        for command in self.bot.commands:
            prefix = self.bot.config.commands_prefix
            description = command.get_docstring()
            cmd_name = ""

            if command.group:
                prefix += command.group + " "

            if len(command.triggers) > 1:
                for trigger in command.triggers:
                    cmd_name += prefix + trigger + " | "
            else:
                cmd_name = prefix + command.name

            embed.add_field(name=cmd_name, value=description)

        event.msg.reply(embed=embed)

    @Plugin.command("ping")
    def on_ping(self, event):
        """A basic ping command"""
        event.msg.reply("Pong!")

    @Plugin.listen("Ready")
    def on_ready(self, event):
        self.client.update_presence(Status.ONLINE, Game(type=GameType.watching, name="you waste time"))
