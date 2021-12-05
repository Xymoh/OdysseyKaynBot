"""
Discord bot for League of Legends Responsible for making a ranking of solo que
among the friends from the same discord server.
"""
import os
import json
import urllib.request
import urllib.parse
import sqlite3
from random import choice
import discord
from dotenv import load_dotenv

from discord.ext import commands, tasks
from discord.ext.commands import has_permissions

load_dotenv()

status = ['The universe will be mine', 'Are they taunting us!?', '*Kayn Laughs*', 'Peekaboo']

# Secrets
api_key_secret = os.environ['API_KEY']
bot_token_secret = os.environ['BOT_TOKEN']

# Setting the riot api key
api_key = os.environ.get('API_KEY')

# Setting up the database
conn = sqlite3.connect('database/summoners.db')
_cursor = conn.cursor()


def is_it_owner(ctx):
    """Returns the bot author token

    Parameters:
        ctx: object: A command must always have at least one parameter,
        ctx, which is the Context as the first one

    Returns:
        int:Returning value
    """
    return ctx.author.id == 156483073880489985


# Upon joining a discord server bot automatically creates a prefix '$', it can be later changed to the whichever
# prefix user wants to.
def get_prefix(client, message):
    """Returns the prefix used by the certain discord server

    Parameters:
        client: object: request from the client
        message: object: Setting the prefix for commands

    Returns:
        str: discord server id converted into the string
    """
    _cursor.execute(f"SELECT * FROM server_config WHERE guild_id = :guild_id", {'guild_id': str(message.guild.id)})

    print(str(message.guild.id))
    server_prefix = _cursor.fetchone()[2]

    return server_prefix


def assigning_json_values(player_ranked_data, summoner_current_name, index, list_of_players, summoners):
    """Returns the custom made list which is created by the riot api data usage

    Parameters:
        :param index: index responsible for reading the certain keys
        :param player_ranked_data: Downloaded and decoded Riot Api data
        :param summoners: custom list creator
        :param list_of_players: custom list
        :param summoner_current_name:

    Returns:
        list: custom made list for bot purpose usage
    """
    summoner_name = summoner_current_name
    tier = player_ranked_data[index]['tier']
    rank = player_ranked_data[index]['rank']
    league_points = player_ranked_data[index]['leaguePoints']
    wins = player_ranked_data[index]['wins']
    losses = player_ranked_data[index]['losses']

    return list_of_players.append(summoners(summoner_name, tier, rank, league_points, wins, losses))


def check_if_name_changed(encrypted_summoner_id, guild_id):
    try:
        _cursor.execute("SELECT * FROM server_config WHERE guild_id = :guild_id", {'guild_id': guild_id})

        region = _cursor.fetchone()[1]

        api_check_name = f'https://{region}.api.riotgames.com/lol/summoner/v4/summoners/' \
                         f'{encrypted_summoner_id}?api_key={api_key}'

        if api_check_name == 0:
            return

        check_name = urllib.request.urlopen(api_check_name)

        check_name_data = json.loads(check_name.read())

        _cursor.execute("SELECT * FROM summoners WHERE riot_id = :riot_id", {'riot_id': check_name_data['id']})

        current_summoner_name = _cursor.fetchone()[0]

        if check_name_data['name'] != current_summoner_name:
            with conn:
                _cursor.execute("UPDATE summoners SET summoner_name = :new_name WHERE summoner_name = :summ_name",
                                {'new_name': check_name_data['name'], 'summ_name': current_summoner_name})
        else:
            pass
    except Exception as err:
        print(err)
        print("Something went wrong with refreshing the summoner name")


def check_if_riot_id_changed(summoner_name, guild_id):
    try:
        _cursor.execute("SELECT * FROM server_config WHERE guild_id = :guild_id", {'guild_id': guild_id})

        region = _cursor.fetchone()[1]

        parsed_summoner_name = urllib.parse.quote(summoner_name)

        api_check_riot_id = f'https://{region}.api.riotgames.com/lol/summoner/v4/summoners/' \
                            f'by-name/{parsed_summoner_name}?api_key={api_key}'

        if api_check_riot_id == 0:
            return

        check_riot_id = urllib.request.urlopen(api_check_riot_id)

        check_riot_id_data = json.loads(check_riot_id.read())

        _cursor.execute("SELECT * FROM summoners WHERE summoner_name = :summoner_name",
                        {'summoner_name': check_riot_id_data['name']})

        current_riot_id = _cursor.fetchone()[1]

        if check_riot_id_data['id'] != current_riot_id:
            with conn:
                _cursor.execute("UPDATE summoners SET riot_id = :new_riot_id WHERE riot_id = :riot_id",
                                {'new_riot_id': check_riot_id_data['id'], 'riot_id': current_riot_id})
        else:
            pass
    except Exception as err:
        print(err)
        print("Something went wrong with refreshing the riot id")


client = commands.Bot(command_prefix=get_prefix, help_command=None)


# client.event section
@client.event
async def on_guild_join(guild):
    """On joining the new discord server adds a new key into the json for the
    prefix and the region

    Parameters:
        guild: object: Responsible for reading discord server data
    """
    try:
        _cursor.execute("""CREATE TABLE summoners (
                    summoner_name text,
                    riot_id text,
                    discord_server text,
                    riot_region text
                )""")

        conn.commit()
    except sqlite3.OperationalError:
        print("Database already exists")
    try:
        _cursor.execute("""CREATE TABLE server_config (
                    guild_id text,
                    region text,
                    prefix text
                )""")

        conn.commit()
    except sqlite3.OperationalError:
        print("Database already exists")

    with conn:
        _cursor.execute("INSERT INTO server_config VALUES (:guild_id, :region, :prefix)",
                        {'guild_id': str(guild.id), 'region': 'eun1', 'prefix': '$'})


@client.event
async def on_guild_remove(guild):
    """On remove from the discord server, deletes a key value of prefix and
     region from the json

    Parameters:
        guild: object: Responsible for reading discord server data
    """
    with conn:
        _cursor.execute("DELETE FROM server_config WHERE guild_id = :guild_id", {'guild_id': str(guild.id)})


@client.event
async def on_ready():
    """Executing on bot startup. Setting base of the server."""
    await client.change_presence(status=discord.Status.online, activity=discord.Game('Python Project'), afk=False)
    change_status.start()
    print('Bot connected.')


# tasks.loop section
@tasks.loop(seconds=3600)
async def change_status():
    """Updates the bot status every hour"""
    await client.change_presence(activity=discord.Game(choice(status)))


# client.command section
@client.command()
async def ping(ctx):
    """Ping command which returns the message of the discord user ping"""
    await ctx.send(f'{round(client.latency * 1000)}ms')


@client.command()
async def help(ctx):
    """

    :param ctx:
    :return:
    """
    embed = discord.Embed(title='Commands', color=0x00ff00)
    embed.add_field(name='$prefix {ctx}', value='ONLY ADMIN Change the prefix of the bot on your server.', inline=False)
    embed.add_field(name='$region {ctx}', value='ONLY ADMIN Changes the region of your league ranking.', inline=False)
    embed.add_field(name='$showregion', value='Shows the currently chosen region for your bot.', inline=False)
    embed.add_field(name='$add {ctx}', value='ONLY ADMIN Adding the player to the ranking list.', inline=False)
    embed.add_field(name='$del {ctx}', value='ONLY ADMIN Deleting the player from the ranking list.', inline=False)
    embed.add_field(name='$delall', value='ONLY ADMIN Deletes all the players from your server list.', inline=False)
    embed.add_field(name='$showall', value='Shows all players from your server list.', inline=False)
    embed.add_field(name='$ranking solo/flex', value='Displays the ranking among the players '
                                                     'added to your server list.', inline=False)
    embed.add_field(name='$gamemode', value='If you dont know which gamemode to play why not to ask the bot?',
                    inline=False)
    embed.set_thumbnail(url="https://static.wikia.nocookie.net/leagueoflegends/images/a/a5/"
                            "Odyssey_Kayn_profileicon.png/revision/latest?cb=20180911213900")

    await ctx.send(embed=embed)


@client.command()
@has_permissions(administrator=True)
async def prefix(ctx, new_prefix):
    """Bot command for changing the prefix to invoke the bot commands

    Parameters:
        ctx: object: A command must always have at least one parameter,
        ctx, which is the Context as the first one
        new_prefix: object: a given new prefix for invoking the bot commands
    """
    with conn:
        _cursor.execute("UPDATE server_config SET prefix = :prefix", {'prefix': new_prefix})

        await ctx.send(f'Prefix changed to: \'{new_prefix}\'')


@client.command(aliases=['region', 'changeregion'])
@has_permissions(administrator=True)
async def change_region(ctx, new_region):
    """Bot command for changing the region for working with riot api

    Parameters:
        ctx: object: A command must always have at least one parameter,
        ctx, which is the Context as the first one
        new_region: object: a given new region for responding with the riot api
    """
    correct_region = False

    if new_region.lower() == 'eune':
        new_region = 'eun1'
        correct_region = True
        await ctx.send('Region changed to Europe North & East')
    elif new_region.lower() == 'euw':
        new_region = 'euw1'
        correct_region = True
        await ctx.send('Region changed to Europe West')
    elif new_region.lower() == 'ru':
        correct_region = True
        await ctx.send('Region changed to Russia')
    elif new_region.lower() == 'br':
        new_region = 'br1'
        correct_region = True
        await ctx.send('Region changed to Brazil')
    elif new_region.lower() == 'tr':
        new_region = 'tr1'
        correct_region = True
        await ctx.send('Region changed to Turkey')
    elif new_region.lower() == 'oce':
        new_region = 'oc1'
        correct_region = True
        await ctx.send('Region changed to Oceania')
    elif new_region.lower() == 'las':
        new_region = 'la2'
        correct_region = True
        await ctx.send('Region changed to Latin America South')
    elif new_region.lower() == 'lan':
        new_region = 'la1'
        correct_region = True
        await ctx.send('Region changed to Latin America North')
    elif new_region.lower() == 'kr':
        correct_region = True
        await ctx.send('Region changed to Korea')
    elif new_region.lower() == 'na':
        new_region = 'na1'
        correct_region = True
        await ctx.send('Region changed to North America')
    elif new_region.lower() == 'jp':
        new_region = 'jp1'
        correct_region = True
        await ctx.send('Region changed to Japan')
    else:
        await ctx.send("This region is not usable within my commands or it does not exist")

    if correct_region:
        with conn:
            _cursor.execute("UPDATE server_config SET region = :region", {'region': new_region})


@client.command(aliases=['showreg', 'showregion'])
async def show_reg(ctx):
    """Command for showing the current chosen region

    :param ctx: object: A command must always have at least one parameter,
    ctx, which is the Context as the first one
    :return: returns the message send by the bot
    """
    _cursor.execute("SELECT * FROM server_config WHERE guild_id = :guild_id", {'guild_id': str(ctx.guild.id)})

    region_text = _cursor.fetchone()[1]

    if region_text.lower() == 'eun1':
        region_text = 'EUNE'
    elif region_text.lower() == 'euw1':
        region_text = 'EUW'
    elif region_text.lower() == 'ru':
        region_text = 'RU'
    elif region_text.lower() == 'br1':
        region_text = 'BR'
    elif region_text.lower() == 'tr1':
        region_text = 'TR'
    elif region_text.lower() == 'oc1':
        region_text = 'OCE'
    elif region_text.lower() == 'la2':
        region_text = 'LAS'
    elif region_text.lower() == 'la1':
        region_text = 'LAN'
    elif region_text.lower() == 'kr':
        region_text = 'KR'
    elif region_text.lower() == 'na1':
        region_text = 'NA'
    elif region_text.lower() == 'jp1':
        region_text = 'JP'

    await ctx.send(f"Currently set region: {region_text}")


@client.command(aliases=['addplayer', 'add'])
@has_permissions(administrator=True)
async def add_player(ctx, *, member: str):
    """Bot command responsible for adding the players to the ranking list

    Parameters:
        ctx: object: A command must always have at least one parameter,
        ctx, which is the Context as the first one
        member: str: name of the player who gonna be considered by the bot for
        a potential ranking command participant
    """
    try:
        _cursor.execute(f"SELECT * FROM server_config WHERE guild_id = :guild_id", {'guild_id': str(ctx.guild.id)})

        region = _cursor.fetchone()[1]

        parsed_member = urllib.parse.quote(member)

        web_riot_api_id = f'https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{parsed_member}' \
                          f'?api_key={api_key}'
        data_id = urllib.request.urlopen(web_riot_api_id).read()
        summoner_data = json.loads(data_id)

        riot_id = summoner_data['id']

        _cursor.execute("SELECT * FROM summoners WHERE discord_server = :guild_id", {'guild_id': str(ctx.guild.id)})

        check_if_riot_id_changed(member, ctx.guild.id)

        summoners = _cursor.fetchall()

        copy_id = True

        for summoner in summoners:
            if summoner[1] == riot_id and summoner[3] == region:
                copy_id = False
        if copy_id:
            with conn:
                _cursor.execute("""INSERT INTO summoners 
                VALUES (:summoner_name, :riot_id, :discord_server, :riot_server)""",
                                {'summoner_name': member, 'riot_id': riot_id,
                                 'discord_server': str(ctx.guild.id), 'riot_server': region})

        if copy_id:
            await ctx.send(f'Player added to the ranking list: \'{member}\'')
        else:
            await ctx.send('Player is already added to the ranking')

    except Exception as err:
        if err:
            print(err)
            await ctx.send('Some data is incorrect. Check the user name or the region.')


@client.command(aliases=['delplayer', 'del'])
@has_permissions(administrator=True)
async def del_player(ctx, *, member: str):
    """Bot command responsible for deleting the players from the ranking list

    Parameters:
        ctx: object: A command must always have at least one parameter,
        ctx, which is the Context as the first one
        member: str: name of the player who gonna be considered by the bot for
        a potential ranking command participant
    """
    _cursor.execute(f"SELECT * FROM server_config WHERE guild_id = :guild_id", {'guild_id': str(ctx.guild.id)})

    region = _cursor.fetchone()[1]

    _cursor.execute("SELECT * FROM summoners WHERE discord_server = :guild_id", {'guild_id': str(ctx.guild.id)})

    data = _cursor.fetchall()

    player_deleted = False

    for elem in data:
        if elem[0].lower() == member.lower() and elem[2] == str(ctx.guild.id):
            with conn:
                _cursor.execute("""DELETE FROM summoners WHERE summoner_name = :summoner_name 
                AND riot_region = :riot_region""", {'summoner_name': member, 'riot_region': region})
                player_deleted = True
                break

    if not player_deleted:
        await ctx.send('Player couldn\'t be deleted from the ranking list')
    else:
        await ctx.send(f"Player \'{member}\' successfully deleted from the ranking list")


@client.command(aliases=['delall', 'delallplayers'])
@has_permissions(administrator=True)
async def del_all_players(ctx):
    """Bot command responsible for deleting all the players from the ranking
    list

    Parameters:
        ctx: object: A command must always have at least one parameter,
        ctx, which is the Context as the first one
    """

    _cursor.execute("SELECT * FROM summoners WHERE discord_server = :guild_id", {'guild_id': str(ctx.guild.id)})

    data = _cursor.fetchall()

    player_deleted = False

    if len(data) != 0:
        with conn:
            _cursor.execute("DELETE FROM summoners WHERE discord_server = :guild_id", {'guild_id': str(ctx.guild.id)})
            player_deleted = True

    if not player_deleted:
        await ctx.send('Players couldn\'t be deleted from the ranking list')
    else:
        await ctx.send("Players successfully deleted from the ranking list")


@client.command(aliases=['showplayers', 'showall'])
async def show_players(ctx):
    """Bot command responsible for showing all the potential ranking list
    players

    Parameters:
        ctx: object: A command must always have at least one parameter,
        ctx, which is the Context as the first one
    """
    _cursor.execute("SELECT * FROM summoners WHERE discord_server = :guild_id", {'guild_id': str(ctx.guild.id)})

    data = _cursor.fetchall()

    summoners_text = ''
    region = ''
    empty_list = True

    if len(data) != 0:
        for i, elem in enumerate(data):
            i += 1
            parsed_summoner_name = urllib.parse.quote(elem[0])
            check_if_name_changed(elem[1], str(ctx.guild.id))
            if elem[3].lower() == 'eun1':
                region = 'EUNE'
            elif elem[3].lower() == 'euw1':
                region = 'EUW'
            elif elem[3].lower() == 'ru':
                region = 'RU'
            elif elem[3].lower() == 'br1':
                region = 'BR'
            elif elem[3].lower() == 'tr1':
                region = 'TR'
            elif elem[3].lower() == 'oc1':
                region = 'OCE'
            elif elem[3].lower() == 'la2':
                region = 'LAS'
            elif elem[3].lower() == 'la1':
                region = 'LAN'
            elif elem[3].lower() == 'kr':
                region = 'KR'
            elif elem[3].lower() == 'na1':
                region = 'NA'
            elif elem[3].lower() == 'jp1':
                region = 'JP'
            empty_list = False
            summoners_text += f"{i}. Summoner name: [{elem[0]}](https://eune.op.gg/summoner/userName=" \
                              f"{parsed_summoner_name}) - Region: **{region}**\n"

    embed = discord.Embed(color=0x0080FF)
    embed.add_field(name='List of players', value=summoners_text, inline=False)

    if not empty_list:
        await ctx.send(embed=embed)
    else:
        await ctx.send("List of players is empty")


@client.command()
async def ranking(ctx, rankType: str):
    """Main bot command responsible for creating the ranking list from the
    previously added players

    Parameters:
        :param ctx: object: A command must always have at least one parameter, ctx, which is the
         Context as the first one
        :param rankType: specifying for the command which ranking we want to check
    """

    class Summoners:
        """Class responsible for creating the custom list which is helping us
        displaying the user data from league of legends
        """

        def __init__(self, summoner_name, tier, rank, league_points, wins, losses):
            self.summoner_name = summoner_name
            self.tier = tier
            self.rank = rank
            self.league_points = league_points
            self.wins = wins
            self.losses = losses

        def __repr__(self):
            return self.summoner_name + self.tier + self.rank + str(self.league_points) + self.wins + self.losses

    if rankType == "solo" or rankType == "flex":
        try:

            _cursor.execute("SELECT * FROM server_config WHERE guild_id = :guild_id", {'guild_id': str(ctx.guild.id)})

            region = _cursor.fetchone()[1]

            _cursor.execute("SELECT * FROM summoners WHERE discord_server = :guild_id", {'guild_id': str(ctx.guild.id)})

            data = _cursor.fetchall()

            list_of_players = []

            if data != 0:
                for summoners_data in data:
                    if summoners_data[2] == str(ctx.guild.id) and summoners_data[3] == region:

                        encrypted_summoner_id = summoners_data[1]

                        summoner_current_name = summoners_data[0]

                        # First we check if riot id hadn't changed on old nickname
                        check_if_riot_id_changed(summoner_current_name, str(ctx.guild.id))
                        # Now we check if the name of the summoner had changed
                        check_if_name_changed(encrypted_summoner_id, str(ctx.guild.id))
                        # We take new summoner name
                        summoner_current_name = summoners_data[0]
                        # Now on the new name we check if the riot id is still correct
                        check_if_riot_id_changed(summoner_current_name, str(ctx.guild.id))

                        # We download the League-V4 api to get the tier, rank and lp data
                        api_ranking = f'https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/' \
                                      f'{encrypted_summoner_id}?api_key={api_key}'

                        player_ranked = urllib.request.urlopen(api_ranking)

                        player_ranked_data = json.loads(player_ranked.read())

                        for i in range(len(player_ranked_data)):
                            if rankType == "solo" and player_ranked_data[i]['queueType'] == "RANKED_SOLO_5x5":
                                assigning_json_values(
                                    player_ranked_data,
                                    summoner_current_name,
                                    i,
                                    list_of_players,
                                    Summoners
                                )
                            elif rankType == "flex" and player_ranked_data[i]['queueType'] == "RANKED_FLEX_SR":
                                assigning_json_values(
                                    player_ranked_data,
                                    summoner_current_name,
                                    i,
                                    list_of_players,
                                    Summoners
                                )
                            else:
                                print("This player has no rank in this ranking category")
            else:
                await ctx.send("There are no players placed in the ranking")

            order = ["CHALLENGER", "GRANDMASTER", "MASTER", "DIAMOND", "PLATINUM", "GOLD", "SILVER", "BRONZE"]
            pos = {c: p for (p, c) in enumerate(order)}
            fully_sorted = sorted(list_of_players, key=lambda elem: (pos[elem.tier], elem.rank, -elem.league_points))

            display_text = ''
            increment_rank = 0

            for text in fully_sorted:
                increment_rank += 1
                win_ratio = round((text.wins * 100) / (text.wins + text.losses))
                parsed_summoner_name = urllib.parse.quote(text.summoner_name)

                if increment_rank == 1:
                    display_text += f"{increment_rank}. {text.summoner_name}" \
                                    f" :first_place: **{text.tier} {text.rank}" \
                                    f" {text.league_points} LP** - " \
                                    f"{text.wins}W {text.losses}L" \
                                    f" / Win Ratio {win_ratio}%\n\n"
                elif increment_rank == 2:
                    display_text += f"{increment_rank}. {text.summoner_name}" \
                                    f" :second_place: **{text.tier} {text.rank}" \
                                    f" {text.league_points} LP** - " \
                                    f"{text.wins}W {text.losses}L" \
                                    f" / Win Ratio {win_ratio}%\n\n"
                elif increment_rank == 3:
                    display_text += f"{increment_rank}. {text.summoner_name}" \
                                    f" :third_place: **{text.tier} {text.rank}" \
                                    f" {text.league_points} LP** - " \
                                    f"{text.wins}W {text.losses}L" \
                                    f" / Win Ratio {win_ratio}%\n\n"
                else:
                    display_text += f"{increment_rank}. {text.summoner_name}" \
                                    f" **{text.tier} {text.rank}" \
                                    f" {text.league_points} LP** -" \
                                    f" {text.wins}W {text.losses}L" \
                                    f" / Win Ratio {win_ratio}%\n\n"

                display_text = display_text.replace(text.summoner_name, f'[{text.summoner_name}]'
                                                                        f'(https://eune.op.gg/summoner/userName={parsed_summoner_name})')

            embed = discord.Embed(title=f'Ranked {rankType.capitalize()}', color=0x0080FF)
            embed.add_field(name='\u200b', value=display_text, inline=False)
            embed.set_thumbnail(url="https://i.pinimg.com/originals/09/2b/fa/092bfa54aad74ce9ab2de010031731f5.png")

            await ctx.send(embed=embed)

        except Exception as err:
            if err:
                print(err)
                await ctx.send("There might be no players for the ranking list")
    else:
        await ctx.send("Please put the command in this format ex.: ranking solo")


@ranking.error
async def ranking_error(ctx, error):
    """

    :param ctx:
    :param error:
    :return:
    """
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please put the command in this format ex.: ranking solo")


@client.command(aliases=['gamemode'])
async def game_mode(ctx):
    """Bot command responsible for generating the random answer from the bot
    about which game mode the player could play

    Parameters:
        ctx: object: A command must always have at least one parameter,
        ctx, which is the Context as the first one
    """
    responses = ['Normal Game', 'Flex 5v5', 'Ranked Solo/Duo', 'Aram']

    await ctx.send(f'{choice(responses)}')


# These lines below are responsible to load commands (cogs) for bot owner usage
@client.command()
@commands.check(is_it_owner)
async def load(extension):
    """Bot command responsible for loading the special owner only commands

    Parameters:
        extension: object: giving the command the extension of the file
    """
    client.load_extension(f'cogs.{extension}')


@client.command()
@commands.check(is_it_owner)
async def unload(extension):
    """Bot command responsible for unloading the special owner only commands

    Parameters:
        extension: object: giving the command the extension of the file
    """
    client.unload_extension(f'cogs.{extension}')


@client.command()
@commands.check(is_it_owner)
async def reload(extension):
    """Bot command responsible for reloading the special owner only commands

    Parameters:
        extension: object: giving the command the extension of the file
    """
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(f'cogs.{extension}')


for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')


@client.command()
@commands.check(is_it_owner)
async def example(ctx):
    """Bot command responsible for showing the author of the bot

    Parameters:
        ctx: object: A command must always have at least one parameter,
        ctx, which is the Context as the first one
    """
    await ctx.send(f'Hi im {ctx.author}')


client.run(os.environ.get('BOT_TOKEN'))
