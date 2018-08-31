import math
import json
import atexit
from datetime import datetime

from disco.bot import Plugin
from disco.types.message import MessageEmbed
from disco.types.user import GameType, Game, Status

from league_api.helpers.live_data_helper import LiveDataHelper
from league_api.helpers.league_helper import LeagueHelper
from league_api.helpers.cache_helper import CacheHelper


CACHE_SCHEDULE = 21600

class UtilityCommands(Plugin):
    def load(self, ctx):
        super(UtilityCommands, self).load(ctx)

        with open("league_api/data/version.json") as data_file:
            data = json.load(data_file)

        self.version = data["version"]
        self.guild_list = dict()
        self.league_helper = LeagueHelper()

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
        """Displays help and command information about Zilean"""
        embed = CacheHelper.getZileanEmbed(title="Zilean Command List", footer="Zilean Commands", description="Note that [arg] is a required argument and (arg) is an optional argument")
        embed.add_field(name="Zilean Commands", value="You can view the commands by following the link below" + "\nhttps://samuel-maddock.github.io/Zilean/#command-section")
        embed.add_field(name="If you enjoy the bot please upvote it below:heart_exclamation:", value="https://discordbots.org/bot/459139146544578571")
        embed.add_field(name="If you have feature suggestions/spotted some bugs", value="Join the support server: https://discord.gg/ZjAyh7N")
        event.msg.author.open_dm().send_message(embed=embed)
        event.msg.author.open_dm().send_message(embed=self.get_notification())
        event.msg.reply("Check your DMs for more information... :cyclone:")

    @Plugin.command("changelog")
    def on_changelog(self, event):
        '''Displays a list of recent changes to Zilean'''
        embed = self.get_notification()
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

    @Plugin.command("region", "[region:str]")
    def on_region(self, event, region=None):
        '''Sets the overall default region for League of Legends commands'''
        region_binds = LiveDataHelper.load_region_binds()
        endpoints = str(LeagueHelper.API_ENDPOINTS).replace("[","").replace("'","").replace("]", "")

        if region is None:
            if LiveDataHelper.guild_has_region(region_binds, str(event.guild.id)):
                event.msg.reply("The current default region for League of Legends commands is: `" + region_binds[str(event.guild.id)] + "`")
            else:
                event.msg.reply("This server does not currently have a default region for League of Legends commands.\nTry ~region [region] where the region is one of the following: `" + endpoints + "`")
        else:
            region = LeagueHelper.validate_region(region, event, send_event_msg=False)
            if region is None:
                event.msg.reply("You have entered an invalid region, please enter one of the following: `" + endpoints + "`")
                return

            region_binds = LiveDataHelper.load_region_binds()
            region_binds[str(event.guild.id)] = region
            LiveDataHelper.save_region_binds(region_binds)
            event.msg.reply("The default region for League of Legends commands is now `" + region + "`")

    @Plugin.command("iam", "[summoner_name:str] [region:str]")
    def on_iam(self, event, summoner_name=None, region=None):
        '''Set a default summoner for yourself that all league commands will use if you leave their summoner name and region arguments blank'''
        summoner_binds = LiveDataHelper.load_summoner_binds()
        author_id = str(event.author.id)

        if summoner_name is None and region is None:
            if LiveDataHelper.user_is_bound(summoner_binds, author_id):
                summoner_tuple = summoner_binds[author_id]
                event.msg.reply("You are `" + summoner_tuple[0] + " " + summoner_tuple[1] + "` If you want to change this type ~iam [summoner_name] [region]")
            else:
                event.msg.reply("You have not bound a summoner to your discord user! To do this type `~iam [summoner_name] [region]`")
        elif (summoner_name is not None) and (region is not None):
            region = LeagueHelper.validate_region(region, event)
            if region is None:
                return

            summoner = self.league_helper.user_exists(region, summoner_name, event)
            if summoner is False:
                return

            summoner_tuple = (summoner["name"], region)
            summoner_binds[author_id] = summoner_tuple
            LiveDataHelper.save_summoner_binds(summoner_binds)
            event.msg.reply("You have updated your summoner, You are `" + summoner["name"] + " " + region + "`")
        else:
            event.msg.reply("You must enter both a summoner name and region!")

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
        ''' channel_binds = LiveDataHelper.load_guild_binds()
        for guild_id in channel_binds.keys():
            try:
                channel = self.bot.client.state.channels[channel_binds[guild_id]]
                channel.send_message("Zilean is restarting - The bot is updating, please be patient... :recycle:")
            except KeyError as err:
                logger = CacheHelper.get_logger("GuildBindError")
                logger.zilean("Guild ID failed to be removed when the bot was offline: " + str(guild_id)) '''

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
                            args += "(" + arg.name + ") "

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

    def get_notification(self):
        embed = CacheHelper.getZileanEmbed(title="Recent Zilean Changes (" + self.version + ")", footer="Zilean Update", description=
            "For previous updates and changes go to the changelog here:\nhttps://samuel-maddock.github.io/Zilean/changelog.html\n\n" +
            "You can now bind a League of Legends summoner to your discord user by using the ~iam command. Try **~iam [summoner_name] [region]** to get started!\n\n" +
            "If you do this any command that requires a summoner name and region will work without writing those arguments eg ~match_history will display your own match history.\n\n" +
            "In order to support adding a default LoL region, the command structure for some commands have changed!"
            "\n\n"
            "For many LoL commands you used to state **[region] [summoner_name]** but now the order is **[summoner_name] (region)**."
            "\n\n"
            "The region is only optional if you set a default region for your server using **~region [league region]**"
            "\n\n**Note that you need to remove any spaces from a summoner name for the commands to work!**")
        embed.color = 0xFF3B73
        return embed
