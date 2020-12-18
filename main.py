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
            
            # create embedded message
            embed = discord.Embed(
                title = 'Blackjack Account',
                colour = discord.Colour.orange()
            )
            embed.add_field(name='User \U0001F9CD', value=user.mention, inline=False)
            embed.add_field(name='Account Balance \U0001F4B0', value='\U0001FA99 1000', inline=False)
            embed.set_footer(text='Type !help for a list of commands.')
            await message.channel.send('New account created!\n', embed=embed)
            
            # commit insert to database
            conn.commit()
            return
        else:
            embed = discord.Embed(
                title = 'Blackjack Account',
                colour = discord.Colour.orange()
            )
            embed.add_field(name='User \U0001F9CD', value=user.mention, inline=False)
            embed.add_field(name='Account Balance \U0001F4B0', value=f'\U0001FA99 {rows[0][0]}', inline=False)
            embed.set_footer(text='Type !help for a list of commands.')
            await message.channel.send('You already have an account!\n', embed=embed)
            return
    elif msg.startswith('!play'):
        msg = msg[5:]
        if len(msg) > 0 and msg[1:].isnumeric():
            msg = msg[1:]
            bet = int(msg)
            
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
            #print(card_mapping)
            
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
            
            embed = discord.Embed(
                title = 'Blackjack!',
                colour = discord.Colour.green()
            )
            embed.add_field(name='User \U0001F9CD', value=user.mention, inline=False)
            embed.add_field(name='Your Hand', value=f'{playerHand[0]} - {playerHand[1]}', inline=False)
            embed.add_field(name="Dealer's Hand", value=f'{dealerHand[0]} - \U0001F0CF', inline=True)
            embed.add_field(name='Next Move', value=f'!hit or !stand', inline=False)
            embed.set_footer(text='Type !help for a list of commands.')
            await message.channel.send(embed=embed)
            print(message.author.name, playerHand, dealerHand, len(cardsArr))
            return
        else:
            embed = discord.Embed(
                title = 'Blackjack Error',
                description = 'Wrong usage of !play.\nCorrect usage: !play <bet amount>.',
                colour = discord.Colour.red()
            )
            embed.set_footer(text='Type !help for a list of commands.')
            await message.channel.send(embed=embed)
            return
    elif msg == '!help':
        embed = discord.Embed(
            title = 'Blackjack Help',
            colour = discord.Colour.red()
        )
        embed.add_field(name='!create', value='Create new blackjack account.', inline=False)
        embed.add_field(name='!play <bet amount>', value='Start a round of blackjack.')
        await message.channel.send(embed=embed)
        return

client.run(bot_token)
c.close()