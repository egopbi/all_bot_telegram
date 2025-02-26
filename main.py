import os

from telethon import TelegramClient, events, utils
from dotenv import load_dotenv

from markets import markets_main, crypto, stocks, metals_sber, currencies


load_dotenv()

# Input your API data to .env file
api_id = int(os.getenv('API_ID'))
api_hash = str(os.getenv('API_HASH')).strip("'")
bot_token = str(os.getenv('BOT_TOKEN')).strip("'")

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

@client.on(events.NewMessage(pattern='/all'))
async def mention_all(event):
    if event.is_group:  # Check that command was used in a group
        chat = await event.get_chat()
        participants = await client.get_participants(chat)

        max_mentions_per_message = 10 

        mentions = []
        for p in participants:
            # Pass bots
            if not p.bot: 
                mentions.append(f"[{utils.get_display_name(p)}](tg://user?id={p.id})")

        # Split mentions for a few messages if more than max
        for i in range(0, len(mentions), max_mentions_per_message):
            await event.reply(' '.join(mentions[i:i + max_mentions_per_message]))
    else:
        await event.reply("Ahahaha lol🤣\nUsing this command in dialog with me is pointless  Use it in chat!")

@client.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    await event.reply("Hello! I am a bot for mentioning all group members. Use /help to see available commands.")

@client.on(events.NewMessage(pattern='/info'))
async def info_command(event):
    await event.reply("This bot is created to mention all group members. Developer: @egopbi a.k.a Eeee Gorka")

@client.on(events.NewMessage(pattern='/help'))
async def help_command(event):
    help_text = (
        "Available commands:\n"
        "/all - mention all group members\n"
        "/info - get information about the bot\n"
        "/markets - get information about **Crypto, Stocks, Metals & Currencies**\n"
        "/crypto - get information about **Crypto**\n"
        "/stocks - get information about **Stocks**\n"
        "/metals - get information about **Metals**\n"
        "/currencies - get information about **Currencies**\n"
        "/help - list of commands"
    )
    await event.reply(help_text)

@client.on(events.NewMessage(pattern='/markets'))
async def markets(event):
    text = await markets_main()
    text = str(text)
    await client.send_message(event.chat_id, text)

@client.on(events.NewMessage(pattern='/crypto'))
async def crypto_market(event):
    text = await crypto()
    text = str(text)
    await client.send_message(event.chat_id, text)

@client.on(events.NewMessage(pattern='/stocks'))
async def stocks_market(event):
    text = await stocks()
    text = str(text)
    await client.send_message(event.chat_id, text)

@client.on(events.NewMessage(pattern='/metals'))
async def metals_market(event):
    text = await metals_sber()
    text = str(text)
    await client.send_message(event.chat_id, text)

@client.on(events.NewMessage(pattern='/currencies'))
async def curencies_market(event):
    text = await currencies()
    text = str(text)
    await client.send_message(event.chat_id, text)

@client.on(events.NewMessage)
async def bot_mention(event):
    if event.message.mentioned:
        await event.reply("You mentioned me! Use /all to mention all of participants. If you want to see all my functions, use /help")

client.run_until_disconnected()
