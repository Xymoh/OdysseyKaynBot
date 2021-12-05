"""Special additional class which is a part of Cogs for bot. It contains
commands for only bot owner usage.
"""
import discord

from discord.ext import commands


def is_it_owner(ctx):
    """Method for returning the bot owner ID

    :param ctx: object: A command must always have at least one parameter
    ctx, which is the Context as the first one
    :return: returns the bot author ID
    """
    return ctx.author.id == 156483073880489985


class Example(commands.Cog):
    """Class responsible for special bot commands only usable by the bot
     owner

     :param commands.Cog: object: Connector with the main class
     """
    def __init__(self, client):
        """"""
        self.client = client

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        """When loaded displays the message

        :return: printing console message for notify
        """
        print('example cogs loaded.')

    # Commands
    @commands.command()
    async def pong(self, ctx):
        """Checking the reaction from the bot to see if the cogs loaded
         properly

        :param ctx: object: A command must always have at least one parameter
        ctx, which is the Context as the first one
        :return: returns the message send by the bot
        """
        await ctx.send('Pong!')

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.check(is_it_owner)
    async def clear(self, ctx, amount: int):
        """Command responsible for deleting last messages on the discord text
        chat

        :param ctx: object: A command must always have at least one parameter
        ctx, which is the Context as the first one
        :param amount: specifying amount of the messages to be deleted
        :return: returns the message send by the bot
        """
        if amount > 0:
            amount = amount + 1
            await ctx.channel.purge(limit=amount)
        else:
            await ctx.send("Please insert number bigger than 0.")

    @clear.error
    async def clear_error(self, ctx, error):
        """special error message for clear command

        :param ctx: object: A command must always have at least one parameter
        ctx, which is the Context as the first one
        :param error: catching the error invoked withing clear command
        :return: returns the message send by the bot
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please put the command in correct way to execute"
                           " the command. ex: $clear [number]")
        if isinstance(error, commands.BadArgument):
            await ctx.send("Please put the command in correct way to execute"
                           " the command. ex: $clear [number]")

    @commands.command()
    @commands.check(is_it_owner)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Command responsible for kicking the user from discord server

        :param ctx: object: A command must always have at least one parameter
        ctx, which is the Context as the first one
        :param member: Specifying the name of the member to be kicked
        :param reason: Giving the reason for kicking. Can be empty.
        :return: returns the message send by the bot
        """
        await member.kick(reason=reason)
        await ctx.send(f'Kicked {member.mention}')

    @commands.command()
    @commands.check(is_it_owner)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Command responsible for banning the user from discord server

        :param ctx: object: A command must always have at least one parameter
        ctx, which is the Context as the first one
        :param member: Specifying the name of the member to be banned
        :param reason: Giving the reason for banning. Can be empty.
        :return: returns the message send by the bot
        """
        await member.ban(reason=reason)
        await ctx.send(f'Banned {member.mention}')

    @commands.command()
    @commands.check(is_it_owner)
    async def unban(self, ctx, *, member):
        """Command responsible for unbanning the user from the current server

        :param ctx: object: A command must always have at least one parameter
        ctx, which is the Context as the first one
        :param member: Specifying the name of the member to be unbanned
        :return: returns the message send by the bot
        """
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')

        for ban_entry in banned_users:
            user = ban_entry.user

            if (user.name, user.discriminator) == \
                    (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'Unbanned {user.mention}')
                return


def setup(client):
    """Method responsible for adding the cogs commands into the rest of methods

    :param client: request from the client
    """
    client.add_cog(Example(client))
