import math
import json
import atexit
from datetime import datetime

from disco.bot import Plugin
from disco.types.message import MessageEmbed
from disco.types.user import GameType, Game, Status

from league_api.helpers.live_data_helper import LiveDataHelper
from league_api.helpers.cache_helper import CacheHelper


CACHE_SCHEDULE = 21600

class UtilityCommands(Plugin):
    def load(self, ctx):
        super(UtilityCommands, self).load(ctx)

        with open("league_api/data/version.json") as data_file:
            data = json.load(data_file)

        self.version = data["version"]
        self.guild_list = dict()

    @Plugin.command("info")
    def on_info(self, event):
        """Displays information about the bot"""
        guild_list = self.client.state.guilds
        user_list = self.client.state.users
        channel_list = self.client.state.channels

        embed = CacheHelper.getZileanEmbed(title="Zilean Bot Info", footer="Bot Information", description="A discord bot that tracks time spent playing league and other statistics :hourglass_flowing_sand: https://samuel-maddock.github.io/Zilean/")
        embed.add_field(name="Version:", value=self.version)
        embed.add_field(name="Developed using:", value="https://github.com/pseudonym117/Riot-Watcher https://github.com/b1naryth1ef/disco")
        embed.add_field(name="Guilds Connected: ", value=len(guild_list), inline=True)
        embed.add_field(name="Users Connected: ", value=len(user_list), inline=True)
        embed.add_field(name="Channels Connected: ", value=len(channel_list), inline=True)
        embed.add_field(name="If you enjoy the bot please upvote it below:heart_exclamation:", value="https://discordbots.org/bot/459139146544578571")
        embed.add_field(name="If you have feature suggestions/spotted some bugs", value="Join the support server: https://discord.gg/ZjAyh7N")
        embed.add_field(name="Use ~help for a list of commands!", value=":wave:")
        event.msg.reply(embed=embed)

    @Plugin.command("help")
    def on_help(self, event):
        """Displays a list of all of commands"""
        embed = CacheHelper.getZileanEmbed(title="Zilean Command List", footer="Zilean Commands", description="Note that [arg] is a required argument and (arg) is an optional argument")
        embed.add_field(name="Zilean Commands", value="You can view the commands by following the link below" + "\nhttps://samuel-maddock.github.io/Zilean/#command-section")
        embed.add_field(name="If you enjoy the bot please upvote it below:heart_exclamation:", value="https://discordbots.org/bot/459139146544578571")
        embed.add_field(name="If you have feature suggestions/spotted some bugs", value="Join the support server: https://discord.gg/ZjAyh7N")
        event.msg.reply(embed=embed)

    @Plugin.command("commands", aliases=["cmd", "cmds", "command"])
    def on_commands(self, event):
        """Displays the link to the commands"""
        event.msg.reply("Zilean Commands: https://samuel-maddock.github.io/Zilean/#command-section :hourglass_flowing_sand:")

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
        self.client.update_presence(Status.ONLINE, Game(type=GameType.watching, name="you play League of Legends"))
        command_list = self.generate_command_list()
        self.update_command_list(command_list)
        atexit.register(self.on_bot_shutdown)  # Register bot shutdown hook

    @Plugin.schedule(CACHE_SCHEDULE)
    def on_cache_update(self):
        CacheHelper.update_static_data()

    @Plugin.listen("GuildCreate")
    def on_guild_create(self, event):
        self.guild_list[str(event.guild.id)] = (event.guild.name, event.guild.id)
        logger = CacheHelper.get_logger("GuildCreate")
        logger.zilean("New Guild Created: " + event.guild.name + " " + str(event.guild.id))

    @Plugin.listen("GuildDelete")
    def on_guild_remove(self, event):
        guild_list = self.guild_list
        guild = guild_list[str(event.id)]
        guild_list.pop(str(event.id))

        logger = CacheHelper.get_logger("GuildRemove")
        logger.zilean("Guild Removed: " + guild[0] + " " + str(guild[1]))

        channel_binds = LiveDataHelper.load_guild_binds()
        channel_bind = channel_binds.pop(str(event.id), None)

        if channel_bind:
            logger.zilean("Guild-Channel bind has been removed for " + guild[0] + " " + str(guild[1]))

        LiveDataHelper.save_guild_binds(channel_binds)

    @Plugin.listen("MessageCreate")
    def on_message_create(self, event):
        content = event.message.content
        if content == "<@459139146544578571>":
            event.message.reply("Type ~help and ~info to get started!")

    @Plugin.pre_command()
    def on_command_event(self, command, event, args, kwargs):
        CacheHelper.log_command(command, event)
        return event

    def on_bot_shutdown(self):
        CacheHelper.save_guilds(self.guild_list)
        logger = CacheHelper.get_logger("ShutdownHook")
        logger.zilean("Bot Shutdown - Guild List saved successfully")

        # Send restart messages to those who have bound the bot to a channel
        channel_binds = LiveDataHelper.load_guild_binds()
        for guild_id in channel_binds.keys():
            guild_id = str(guild_id)
            channel = self.bot.client.state.channels.get(channel_binds[guild_id])
            channel.send_message("Zilean is restarting - The bot is updating, please be patient... :recycle:")

    def generate_command_list(self):
        command_list = dict()
        for name, plugin in self.bot.plugins.items():
            command_list[name] = list()
            for command in plugin.commands:
                prefix = self.bot.config.commands_prefix
                cmd_description = command.get_docstring()
                cmd_usage = list()
                args = ""

                if command.group:
                    prefix += command.group + " "

                if command.args:
                    for arg in command.args.args:
                        if arg.required:
                            args += "[" + arg.name + "] "
                        else:
                            args += "(" + arg.name + ")"

                if len(command.triggers) > 1:
                    for trigger in command.triggers:
                        cmd_usage.append(prefix + trigger + " " + args)
                else:
                    cmd_usage.append(prefix + command.name + " " + args)

                cmd_name = prefix + command.name

                command_list.setdefault(name, []).append((cmd_name, cmd_usage, cmd_description))

        return command_list

    def update_command_list(self, command_list):
        with open("docs/commandList.json", "w") as data_file:
            json.dump(command_list, data_file)
        logger = CacheHelper.get_logger("CommandList")
        logger.zilean("Command List Generated")
