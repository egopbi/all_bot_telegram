import asyncio
import os

from telethon import TelegramClient, events, utils
from dotenv import load_dotenv

load_dotenv()

# Input your API data to .env file
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')
 
print('API ID is: ', api_id)
print('API_HASH is: ', api_hash)
print('BOT TOKEN is: ', bot_token)
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
        "/help - list of commands"
    )
    await event.reply(help_text)

@client.on(events.NewMessage)
async def bot_mention(event):
    if event.message.mentioned:
        await event.reply("You mentioned me! Use /all to mention all of participants. If you want to see all my functions, use /help")


client.run_until_disconnected()
