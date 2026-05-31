import asyncio
import importlib
import sys
import types
import unittest
from unittest.mock import AsyncMock


_MISSING = object()


class FakeTelegramClient:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def on(self, _event):
        def decorator(func):
            return func

        return decorator


class RestartingClient:
    def __init__(self, outcomes):
        self._outcomes = list(outcomes)
        self.connected = False
        self.starts = 0
        self.disconnects = 0

    def is_connected(self):
        return self.connected

    async def start(self, *, bot_token):
        self.starts += 1
        self.connected = True

    async def disconnect(self):
        self.disconnects += 1
        self.connected = False

    async def run_until_disconnected(self):
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class MainResilienceTests(unittest.IsolatedAsyncioTestCase):
    def import_main_with_fakes(self):
        module_names = [
            "main",
            "markets",
            "telethon",
            "telethon.tl",
            "telethon.tl.functions",
            "telethon.tl.functions.bots",
            "telethon.tl.types",
        ]
        saved_modules = {
            name: sys.modules.get(name, _MISSING) for name in module_names
        }

        fake_markets = types.ModuleType("markets")

        async def market_response():
            return "market"

        fake_markets.crypto = market_response
        fake_markets.currencies = market_response
        fake_markets.markets_main = market_response
        fake_markets.metals_sber = market_response
        fake_markets.stocks = market_response
        fake_markets.stocks_rus = market_response

        fake_telethon = types.ModuleType("telethon")
        fake_telethon.TelegramClient = FakeTelegramClient
        fake_telethon.utils = types.SimpleNamespace(
            get_display_name=lambda user: "User"
        )
        fake_telethon.events = types.SimpleNamespace(
            NewMessage=lambda *args, **kwargs: ("NewMessage", args, kwargs)
        )

        fake_tl = types.ModuleType("telethon.tl")
        fake_tl_functions = types.ModuleType("telethon.tl.functions")
        fake_bots = types.ModuleType("telethon.tl.functions.bots")
        fake_types = types.ModuleType("telethon.tl.types")

        class SimpleType:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

        fake_bots.SetBotCommandsRequest = SimpleType
        fake_bots.SetBotMenuButtonRequest = SimpleType
        fake_types.BotCommand = SimpleType
        fake_types.BotCommandScopeDefault = SimpleType
        fake_types.BotMenuButtonCommands = SimpleType

        sys.modules["markets"] = fake_markets
        sys.modules["telethon"] = fake_telethon
        sys.modules["telethon.tl"] = fake_tl
        sys.modules["telethon.tl.functions"] = fake_tl_functions
        sys.modules["telethon.tl.functions.bots"] = fake_bots
        sys.modules["telethon.tl.types"] = fake_types
        sys.modules.pop("main", None)

        def restore_modules():
            for name, module in saved_modules.items():
                if module is _MISSING:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module

        self.addCleanup(restore_modules)
        return importlib.import_module("main")

    async def test_create_client_uses_infinite_telethon_reconnects(self):
        main = self.import_main_with_fakes()

        client = main.create_client("bot", 12345, "hash", retry_delay=17)

        self.assertEqual(client.args, ("bot", 12345, "hash"))
        self.assertIsNone(client.kwargs["connection_retries"])
        self.assertEqual(client.kwargs["retry_delay"], 17)
        self.assertTrue(client.kwargs["auto_reconnect"])

    async def test_run_client_forever_restarts_after_connection_failure(self):
        main = self.import_main_with_fakes()
        client = RestartingClient(
            [
                ConnectionError("Connection to Telegram failed 5 time(s)"),
                asyncio.CancelledError(),
            ]
        )
        set_commands = AsyncMock()
        sleeps = []

        async def sleep(delay):
            sleeps.append(delay)

        with self.assertLogs("main", level="ERROR") as logs:
            with self.assertRaises(asyncio.CancelledError):
                await main.run_client_forever(
                    client,
                    "bot-token",
                    set_commands,
                    retry_delay=3,
                    max_retry_delay=60,
                    sleep=sleep,
                )

        self.assertEqual(client.starts, 2)
        self.assertEqual(set_commands.await_count, 2)
        self.assertEqual(sleeps, [3])
        self.assertIn("Telegram client failed", logs.output[0])
