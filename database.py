import sqlite3

conn = sqlite3.connect('blackjack.db')
c = conn.cursor()

c.execute('''CREATE TABLE users(
            userID text,
            name text,
            discriminator text,
            tokens integer,
            guildID text,
            PRIMARY KEY (userID, guildID))''')

conn.commit()
conn.close()