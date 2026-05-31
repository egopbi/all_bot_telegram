import asyncio
import logging
import os

from dotenv import load_dotenv
from telethon import TelegramClient, events, utils
from telethon.tl.functions.bots import (
    SetBotCommandsRequest,
    SetBotMenuButtonRequest,
)
from telethon.tl.types import (
    BotCommand,
    BotCommandScopeDefault,
    BotMenuButtonCommands,
)

from markets import (
    crypto,
    currencies,
    markets_main,
    metals_sber,
    stocks,
    stocks_rus,
)


DEFAULT_RETRY_DELAY = 10
DEFAULT_MAX_RETRY_DELAY = 300

logger = logging.getLogger(__name__)


def get_required_env(name):
    value = os.getenv(name)
    if not value or not value.strip():
        raise RuntimeError(f"{name} environment variable is required")
    return value.strip().strip("'\"")


def get_int_env(name, default):
    value = os.getenv(name)
    if not value or not value.strip():
        return default
    return int(value)


def create_client(session_name, api_id, api_hash, *, retry_delay):
    return TelegramClient(
        session_name,
        api_id,
        api_hash,
        auto_reconnect=True,
        connection_retries=None,
        retry_delay=retry_delay,
    )


async def set_bot_commands(client):
    commands = [
        BotCommand(command="start", description="Start bot"),
        BotCommand(command="all", description="Mention all of participants"),
        BotCommand(command="markets", description="Prices for all markets"),
        # BotCommand(command="crypto", description="Prices for cryptocurrencies"),
        # BotCommand(command="stocks", description="Prices for stocks"),
        BotCommand(
            command="rus_stocks", description="Prices for MOEX russian stocks"
        ),
        BotCommand(command="metals", description="Prices for precious metals"),
        BotCommand(command="currencies", description="Prices for currencies"),
        BotCommand(command="help", description="Info about commands"),
        BotCommand(command="info", description="Info about bot"),
    ]

    await client(
        SetBotCommandsRequest(
            scope=BotCommandScopeDefault(), lang_code="en", commands=commands
        )
    )
    await client(
        SetBotMenuButtonRequest(user_id="self", button=BotMenuButtonCommands())
    )


def register_handlers(client):
    @client.on(events.NewMessage(pattern="/all"))
    async def mention_all(event):
        if event.is_group:
            chat = await event.get_chat()
            participants = await client.get_participants(chat)

            max_mentions_per_message = 10

            mentions = []
            for p in participants:
                if not p.bot:
                    mentions.append(
                        f"[{utils.get_display_name(p)}](tg://user?id={p.id})"
                    )

            for i in range(0, len(mentions), max_mentions_per_message):
                await event.reply(
                    " ".join(mentions[i : i + max_mentions_per_message])
                )
        else:
            await event.reply(
                "Ahahaha lol🤣\nUsing this command in dialog with me is pointless  Use it in chat!"
            )

    @client.on(events.NewMessage(pattern="/start"))
    async def start_command(event):
        await event.reply(
            "Hello! I am a bot for mentioning all group members. Use /help to see available commands."
        )

    @client.on(events.NewMessage(pattern="/info"))
    async def info_command(event):
        await event.reply(
            "This bot is created to mention all group members. Developer: @egopbi a.k.a Eeee Gorka"
        )

    @client.on(events.NewMessage(pattern="/help"))
    async def help_command(event):
        help_text = (
            "Available commands:\n"
            "/all - mention all group members\n"
            "/info - get information about the bot\n"
            "/markets - get information about **Crypto, Stocks, Metals & Currencies**\n"
            "NOT AVAILABLE /crypto - get information about **Crypto**\n"
            "NOT AVAILABLE /stocks - get information about **Stocks**\n"
            "/rus_stocks - get information about **Russian Stocks**\n"
            "/metals - get information about **Metals**\n"
            "/currencies - get information about **Currencies**\n"
            "/help - list of commands"
        )
        await event.reply(help_text)

    @client.on(events.NewMessage(pattern="/markets"))
    async def markets(event):
        text = await markets_main()
        text = str(text)
        await client.send_message(event.chat_id, text)

    @client.on(events.NewMessage(pattern="/crypto"))
    async def crypto_market(event):
        text = await crypto()
        text = str(text)
        await client.send_message(event.chat_id, text)

    @client.on(events.NewMessage(pattern="/stocks"))
    async def stocks_market(event):
        text = await stocks()
        text = str(text)
        await client.send_message(event.chat_id, text)

    @client.on(events.NewMessage(pattern="/rus_stocks"))
    async def rus_stocks(event):
        text = await stocks_rus()
        text = str(text)
        await client.send_message(event.chat_id, text)

    @client.on(events.NewMessage(pattern="/metals"))
    async def metals_market(event):
        text = await metals_sber()
        text = str(text)
        await client.send_message(event.chat_id, text)

    @client.on(events.NewMessage(pattern="/currencies"))
    async def curencies_market(event):
        text = await currencies()
        text = str(text)
        await client.send_message(event.chat_id, text)

    @client.on(events.NewMessage)
    async def bot_mention(event):
        if event.message.mentioned:
            await event.reply(
                "You mentioned me! Use /all to mention all of participants. If you want to see all my functions, use /help"
            )


async def run_client_forever(
    client,
    bot_token,
    set_commands,
    *,
    retry_delay=DEFAULT_RETRY_DELAY,
    max_retry_delay=DEFAULT_MAX_RETRY_DELAY,
    sleep=asyncio.sleep,
):
    delay = retry_delay
    while True:
        try:
            if not client.is_connected():
                await client.start(bot_token=bot_token)
                await set_commands()
                logger.info("Connected to Telegram")
                delay = retry_delay

            await client.run_until_disconnected()
            logger.warning(
                "Telegram client disconnected; reconnecting in %s second(s)",
                delay,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "Telegram client failed; reconnecting in %s second(s)",
                delay,
            )
        finally:
            if client.is_connected():
                await client.disconnect()

        await sleep(delay)
        delay = min(delay * 2, max_retry_delay)


async def main():
    load_dotenv()
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    api_id = int(get_required_env("API_ID"))
    api_hash = get_required_env("API_HASH")
    bot_token = get_required_env("BOT_TOKEN")
    retry_delay = get_int_env("TELEGRAM_RETRY_DELAY", DEFAULT_RETRY_DELAY)
    max_retry_delay = get_int_env(
        "TELEGRAM_MAX_RETRY_DELAY", DEFAULT_MAX_RETRY_DELAY
    )
    session_name = os.getenv("TELEGRAM_SESSION", "bot")

    client = create_client(
        session_name,
        api_id,
        api_hash,
        retry_delay=retry_delay,
    )
    register_handlers(client)

    await run_client_forever(
        client,
        bot_token,
        lambda: set_bot_commands(client),
        retry_delay=retry_delay,
        max_retry_delay=max_retry_delay,
    )


if __name__ == "__main__":
    asyncio.run(main())
