import discord
import sqlite3
import random

bot_token = ''
with open('./secret.txt', 'r') as secret:
    for line in secret:
        bot_token = line
        
intents = discord.Intents.all()
client = discord.Client(intents=intents)

conn = sqlite3.connect('blackjack.db')
c = conn.cursor()

# returns account embedded message
def getAccountEmbed(name, tokens):
    embed = discord.Embed(
        title = f"{name}'s Account",
        colour = discord.Colour.orange()
    )
    embed.add_field(name='Account Balance', value=f'\U0001FA99 {tokens}', inline=False)
    embed.set_footer(text='Type !help for a list of commands.')
    return embed

# returns error embedded message
def getErrorEmbed(desc):
    embed = discord.Embed(
        title = 'Blackjack Error',
        description = desc,
        colour = discord.Colour.red()
    )
    embed.set_footer(text='Type !help for a list of commands.')
    return embed

# returns round embedded message
def getRoundEmbed(playerHand, dealerHand):
    embed = discord.Embed(
        title = 'Blackjack!',
        colour = discord.Colour.green()
    )
    embed.add_field(name='Your Hand', value=f'{playerHand[0]} - {playerHand[1]}', inline=True)
    embed.add_field(name="Dealer's Hand", value=f'{dealerHand[0]} - \U0001F0CF', inline=True)
    embed.add_field(name='Next Move', value=f'!hit or !stand', inline=False)
    embed.set_footer(text='Type !help for a list of commands.')
    return embed

# (userID, guildID): {state: '', cardArr: [], playerHand: [], dealerHand: [], bet: int}
userStates = {}

@client.event
async def on_ready():
    print(f'Logged on as {client.user}!')

@client.event
async def on_message(message):
    # ignore messages from the bot and messages with no content
    if message.author == client.user or len(message.content) == 0 or message.channel.name != 'blackjack':
        return

    user = message.author
    msg = message.content
    
    # user sends create new account command
    if msg == '!create':
        c.execute('SELECT tokens FROM users WHERE userID = ? AND guildID = ?', (user.id, user.guild.id,))
        rows = c.fetchall()
        
        # user has not created an account
        if len(rows) == 0: 
            # insert new user row into database, default 1000 tokens
            c.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?)', (user.id, user.name, user.discriminator, 1000, user.guild.id,))
            
            await message.channel.send(f'{user.mention} New account created!\n', embed=getAccountEmbed(user.name, 1000))
            conn.commit()
            return
        else:
            await message.channel.send(f'{user.mention} You already have an account!\n')
            return
    elif msg == '!balance': # get account balance
        c.execute('SELECT tokens FROM users WHERE userID = ? AND guildID = ?', (user.id, user.guild.id,))
        rows = c.fetchall()
        
        # user has not created an account
        if len(rows) == 0: 
            await message.channel.send(f'{user.mention}\n', embed=getErrorEmbed('You do not have an account! Create an account using !create.'))
            return
        else:
            await message.channel.send(f'{user.mention}\n', embed=getAccountEmbed(user.name, rows[0][0]))
            return
    elif msg.startswith('!play'):
        msg = msg[5:]
        if len(msg) > 0 and msg[1:].isnumeric():
            bet = int(msg[1:])
            
            '''
            Each user has their own game state
                - Multiple users can be playing the game at the same time
                - Commands issued by each user is handled independently of other users
            Example:
                - Player1: !play 300
                - Player2: !play 100
            
            In a game of blackjack:
                - Player places bet
                - Output 2 visible cards in Player's hand, 1 visible card in Dealer's hand.
                - Player either Hits or Stays
                - Continues until Player Stays, gets Blackjack, or Busts
            
            Can either have bag of 52 cards and take cards from bag everytime w/o replacement or just random value from 1-10
            '''
            
            cardsArr = []
            card = 1
            for i in range(52):
                cardsArr.append(card)
                card += 1
                if card == 14:
                    card = 1
            
            playerHand = []
            cardIdx = random.randint(0, len(cardsArr)-1)
            playerHand.append(cardsArr[cardIdx])
            cardsArr.pop(cardIdx)
            cardIdx = random.randint(0, len(cardsArr)-1)
            playerHand.append(cardsArr[cardIdx])
            cardsArr.pop(cardIdx)
            
            dealerHand = []
            cardIdx = random.randint(0, len(cardsArr)-1)
            dealerHand.append(cardsArr[cardIdx])
            cardsArr.pop(cardIdx)

            await message.channel.send(f'{user.mention}\n', embed=getRoundEmbed(playerHand, dealerHand))
            # print(message.author.name, playerHand, dealerHand, len(cardsArr))
            return
        else:
            await message.channel.send(f'{user.mention}\n', embed=getErrorEmbed('Wrong usage of !play.\nCorrect usage: !play <bet amount>.'))
            return
    elif msg == '!hit':
        pass
    elif msg == '!stand':
        pass
    elif msg == '!help':
        embed = discord.Embed(
            title = 'Blackjack Help',
            colour = discord.Colour.red()
        )
        embed.add_field(name='!create', value='Create new blackjack account.', inline=False)
        embed.add_field(name='!play <bet amount>', value='Start a round of blackjack.')
        await message.channel.send(f'{user.mention}\n', embed=embed)
        return

client.run(bot_token)
c.close()