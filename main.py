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

# value mapping
cardValueMap = {1: 'A', 2: 2, 3: 3, 4: 4, 5: 5,  6: 6, 7: 7, 8: 8, 9: 9, 10: 10, 11: 'J', 12: 'Q', 13: 'K'}

# returns round embedded message
def getRoundEmbed(playerHand, dealerHand, bet):
    # generates hand string for N cards in hand
    hand = str(cardValueMap[playerHand[0]])
    for i in range(1, len(playerHand)):
        hand += f' - {cardValueMap[playerHand[i]]}'
        
    embed = discord.Embed(
        title = 'Blackjack!',
        colour = discord.Colour.green()
    )
    embed.add_field(name='Current Bet', value=bet, inline=False)
    embed.add_field(name='Your Hand', value=hand, inline=True)
    embed.add_field(name="Dealer's Hand", value=f'{cardValueMap[dealerHand[0]]} - \U0001F0CF', inline=True)
    embed.add_field(name='Next Move', value=f'!hit or !stand', inline=False)
    embed.set_footer(text='Type !help for a list of commands.')
    return embed

# returns win embedded message
def getWinEmbed(bet, balance, playerHand, dealerHand):
    # generates hand string for N cards in hand
    playerHandStr = str(cardValueMap[playerHand[0]])
    for i in range(1, len(playerHand)):
        playerHandStr += f' - {cardValueMap[playerHand[i]]}'
        
    dealerHandStr = str(cardValueMap[dealerHand[0]])
    for i in range(1, len(dealerHand)):
        dealerHandStr += f' - {cardValueMap[dealerHand[i]]}'
    
    embed = discord.Embed(
        title = '\U0001F389 You won! \U0001F389',
        colour = discord.Colour.gold()
    )
    embed.add_field(name='Your Hand', value=playerHandStr, inline=True)
    embed.add_field(name="Dealer's Hand", value=dealerHandStr, inline=True)
    embed.add_field(name='Winnings', value=f'\U0001F4B0 {bet}', inline=False)
    embed.add_field(name='Account Balance', value=f'\U0001FA99 {balance}', inline=False)
    embed.set_footer(text='Type !help for a list of commands.')
    return embed

# returns lose embedded message
def getLoseEmbed(bet, balance, playerHand, dealerHand):
    # generates hand string for N cards in hand
    playerHandStr = str(cardValueMap[playerHand[0]])
    for i in range(1, len(playerHand)):
        playerHandStr += f' - {cardValueMap[playerHand[i]]}'
        
    dealerHandStr = str(cardValueMap[dealerHand[0]])
    for i in range(1, len(dealerHand)):
        dealerHandStr += f' - {cardValueMap[dealerHand[i]]}'
        
    embed = discord.Embed(
        title = '\U0001F622 You Lost! \U0001F614',
        colour = discord.Colour.gold()
    )
    embed.add_field(name='Your Hand', value=playerHandStr, inline=True)
    embed.add_field(name="Dealer's Hand", value=dealerHandStr, inline=True)
    embed.add_field(name='Amount Lost', value=f'\U0001F4B0 {bet}', inline=False)
    embed.add_field(name='Account Balance', value=f'\U0001FA99 {balance}', inline=False)
    embed.set_footer(text='Type !help for a list of commands.')
    return embed

# returns draw embedded message
def getDrawEmbed(balance, playerHand, dealerHand):
    # generates hand string for N cards in hand
    playerHandStr = str(cardValueMap[playerHand[0]])
    for i in range(1, len(playerHand)):
        playerHandStr += f' - {cardValueMap[playerHand[i]]}'
        
    dealerHandStr = str(cardValueMap[dealerHand[0]])
    for i in range(1, len(dealerHand)):
        dealerHandStr += f' - {cardValueMap[dealerHand[i]]}'

    embed = discord.Embed(
        title = '\U0001F0CF You Tied! \U0001F0CF',
        description = 'No money lost.',
        colour = discord.Colour.gold()
    )
    embed.add_field(name='Your Hand', value=playerHandStr, inline=True)
    embed.add_field(name="Dealer's Hand", value=dealerHandStr, inline=True)
    embed.add_field(name='Account Balance', value=f'\U0001FA99 {balance}', inline=False)
    embed.set_footer(text='Type !help for a list of commands.')
    return embed

# returns sum of cards in hand
def getHandSum(hand):
    count = 0
    numAces  = 0
    for card in hand:
        if card > 10:
            count += 10
        elif card == 1:
            numAces += 1
        else:
            count += card
    for _ in range(numAces):
        if count + 11 > 21:
            count += 1
        else:
            count += 11
    return count

# (userID, guildID): {cardArr: [], playerHand: [], dealerHand: [], bet: int}
# potential issue with async and updating global state??
userStates = {}
STARTING_TOKENS = 5000

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
            c.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?)', (user.id, user.name, user.discriminator, STARTING_TOKENS, user.guild.id,))
            
            await message.channel.send(f'{user.mention} New account created!\n', embed=getAccountEmbed(user.name, STARTING_TOKENS))
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
        
        userStates = (userID, guildID): {cardArr: [], playerHand: [], dealerHand: [], bet: int}
        '''
        userID = user.id 
        guildID = user.guild.id
        
        # Player must have account first
        c.execute('SELECT tokens FROM users WHERE userID = ? AND guildID = ?', (user.id, user.guild.id,))
        rows = c.fetchall()
        if len(rows) == 0:
            await message.channel.send(f'{user.mention}\n', embed=getErrorEmbed('You do not have an account! Create an account using !create.'))
            return
        
        # if Player is in a game and types !play again, send an error message
        if (userID, guildID) in userStates:
            await message.channel.send(f'{user.mention}\n', embed=getErrorEmbed('You have to finish your current game before you can play again.'))
            return
            
        msg = msg[5:]
        
        # user input validation
        if len(msg) > 0 and msg[1:].isnumeric():
            bet = int(msg[1:])
            
            cardsArr = []
            card = 1
            for _ in range(52):
                cardsArr.append(card)
                card += 1
                if card == 14:
                    card = 1
            
            # deals player hand
            playerHand = []
            cardIdx = random.randint(0, len(cardsArr)-1)
            playerHand.append(cardsArr[cardIdx])
            cardsArr.pop(cardIdx)
            cardIdx = random.randint(0, len(cardsArr)-1)
            playerHand.append(cardsArr[cardIdx])
            cardsArr.pop(cardIdx)
            
            # deals dealer hand
            dealerHand = []
            cardIdx = random.randint(0, len(cardsArr)-1)
            dealerHand.append(cardsArr[cardIdx])
            cardsArr.pop(cardIdx)
            # one dealer card should remain 'hidden'
            cardIdx = random.randint(0, len(cardsArr)-1)
            dealerHand.append(cardsArr[cardIdx])
            cardsArr.pop(cardIdx)
            
            # sets balance to tokens from db execute
            balance = rows[0][0]
            
            # player wins off the bat
            if getHandSum(playerHand) == 21:
                # update player balance in db
                c.execute('UPDATE users SET tokens = tokens + ? WHERE userID = ? AND guildID = ?', (bet, userID, guildID))
                conn.commit()
                
                await message.channel.send(f'{user.mention}\n', embed=getWinEmbed(bet, bet + balance, playerHand, dealerHand))
                return
            else: 
                userStates[(userID, guildID)] = {
                    'cardsArr': cardsArr,
                    'playerHand': playerHand,
                    'dealerHand': dealerHand,
                    'bet': bet}

                await message.channel.send(f'{user.mention}\n', embed=getRoundEmbed(playerHand, dealerHand, bet))
                # print(message.author.name, playerHand, dealerHand, len(cardsArr))
                return
        else: # doesnt pass input validation
            await message.channel.send(f'{user.mention}\n', embed=getErrorEmbed('Wrong usage of !play.\nCorrect usage: !play <bet amount>.'))
            return
    elif msg == '!hit':
        userID = user.id 
        guildID = user.guild.id
        
        # Player should only type !hit after starting a game instance with !play.
        if (userID, guildID) not in userStates:
            await message.channel.send(f'{user.mention}\n', embed=getErrorEmbed('You are currently not in a game. Type !play <bet amount> to start a game.'))
            return
        
        # gets user state
        state = userStates[(userID, guildID)]
        
        # deals card
        cardIdx = random.randint(0, len(state['cardsArr'])-1)
        state['playerHand'].append(state['cardsArr'][cardIdx])
        state['cardsArr'].pop(cardIdx)
        
        curHandSum = getHandSum(state['playerHand'])
        if curHandSum < 21:
            await message.channel.send(f'{user.mention}\n', embed=getRoundEmbed(state['playerHand'], state['dealerHand'], state['bet']))
            return
        elif curHandSum == 21: # blackjack
            # get account balance
            c.execute('SELECT tokens FROM users WHERE userID = ? AND guildID = ?', (user.id, user.guild.id,))
            rows = c.fetchall()
            
            # update player balance in db
            c.execute('UPDATE users SET tokens = tokens + ? WHERE userID = ? AND guildID = ?', (state['bet'], userID, guildID))
            conn.commit()
            
            await message.channel.send(f'{user.mention}\n', embed=getWinEmbed(state['bet'], state['bet'] + rows[0][0], state['playerHand'], state['dealerHand']))
            # when a player is done with a game, delete player state from userStates
            del userStates[(userID, guildID)]
            return  
        else: # busted
            # get account balance
            c.execute('SELECT tokens FROM users WHERE userID = ? AND guildID = ?', (user.id, user.guild.id,))
            rows = c.fetchall()
            balance = 0
            if rows[0][0] - state['bet'] < 0:
                balance = 0
            else:
                balance = rows[0][0] - state['bet']
            
            # update player balance in db
            c.execute('UPDATE users SET tokens = ? WHERE userID = ? AND guildID = ?', (balance, userID, guildID))
            conn.commit()
            
            await message.channel.send(f'{user.mention}\n', embed=getLoseEmbed(state['bet'], balance, state['playerHand'], state['dealerHand']))
            
            # when a player is done with a game, delete player state from userStates
            del userStates[(userID, guildID)]
            return
    elif msg == '!stand':
        userID = user.id 
        guildID = user.guild.id
        
        # Player should only type !stand after starting a game instance with !play.
        if (userID, guildID) not in userStates:
            await message.channel.send(f'{user.mention}\n', embed=getErrorEmbed('You are currently not in a game. Type !play <bet amount> to start a game.'))
            return

        # get account balance
        c.execute('SELECT tokens FROM users WHERE userID = ? AND guildID = ?', (user.id, user.guild.id,))
        rows = c.fetchall()
        
        # gets user state
        state = userStates[(userID, guildID)]
        playerHandSum = getHandSum(state['playerHand'])
        dealerHandSum = getHandSum(state['dealerHand'])
        
        # dealer plays
        # dealer must stand when it reaches 17
        while dealerHandSum <= 17:
            cardIdx = random.randint(0, len(state['cardsArr'])-1)
            state['dealerHand'].append(state['cardsArr'][cardIdx])
            state['cardsArr'].pop(cardIdx)
            dealerHandSum = getHandSum(state['dealerHand'])
        
        # dealer busts, player wins
        if dealerHandSum > 21 or dealerHandSum < playerHandSum:
            # update player balance in db
            c.execute('UPDATE users SET tokens = tokens + ? WHERE userID = ? AND guildID = ?', (state['bet'], userID, guildID))
            conn.commit()
            
            await message.channel.send(f'{user.mention}\n', embed=getWinEmbed(state['bet'], state['bet'] + rows[0][0], state['playerHand'], state['dealerHand']))
            
            # when a player is done with a game, delete player state from userStates
            del userStates[(userID, guildID)]
            return
        elif dealerHandSum == playerHandSum: # tie, player doesn't lose money
            await message.channel.send(f'{user.mention}\n', embed=getDrawEmbed(rows[0][0], state['playerHand'], state['dealerHand']))
            
            # when a player is done with a game, delete player state from userStates
            del userStates[(userID, guildID)]
            return
        elif dealerHandSum > playerHandSum: # player loses
            balance = 0
            if rows[0][0] - state['bet'] < 0:
                balance = 0
            else:
                balance = rows[0][0] - state['bet']
                
            # update player balance in db
            c.execute('UPDATE users SET tokens = ? WHERE userID = ? AND guildID = ?', (balance, userID, guildID))
            conn.commit()
            
            await message.channel.send(f'{user.mention}\n', embed=getLoseEmbed(state['bet'], balance, state['playerHand'], state['dealerHand']))
            
            # when a player is done with a game, delete player state from userStates
            del userStates[(userID, guildID)]
            return
        else: # shouldnt happen
            print('Error in !stand', state)
            return
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