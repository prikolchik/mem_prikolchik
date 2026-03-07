import asyncio

from  telethon import events
from datetime import datetime

from .client import client
from utils.logger import logger 

COMMAND_HANDLERS = {}
SELF_USER = "me"

def command(name):
    def wrapper(func):
        COMMAND_HANDLERS[name] = func
        return func 
    return wrapper

@client.on(events.NewMessage(from_users=SELF_USER))
async def handle_message(event):
    msg = (event.raw_text or "").strip()
    if not msg:
        return

    chat = await event.get_chat()
    chat_name = getattr(chat, "title", "Saved Messages")
    logger.info(f"[{chat_name}] Your message: {msg}")

    parts = msg.split()
    cmd = parts[0].lower()
    args = parts[1:]

    handler = COMMAND_HANDLERS.get(cmd)
    if handler:
        await handler(event, *args)
        
@command(".ping")
async def handle_ping(event):
    await event.reply("pong🗿")
    
@command(".help")
async def handle_help(event):
    help_text = """\n
<code>.ping</code> - check if the bot is alive
<code>.time</code> - send the curent time
<code>.reverse</code> - reverse the text
<code>.error</code> - big error 
    """
    await event.reply(help_text, parse_mode="html")
    
    
@command(".time")
async def handle_time(event):
    now = datetime.now()
    await event.reply(f"curent time <code>{now}</code>", parse_mode="html")
    
@command(".reverse")
async def handle_reverse(event, *args):
    text = " ".join(args)
    if not text: 
        reply = await event.get_reply_message()
        if reply:
            text = reply.raw_text
        else:
            return await event.edit("nothing to reverse")
    
    await event.edit(text[::-1])

@command(".error")
async def handle_error(event):
    error_text = (
        "<code>"
        " [ CRITICAL SYSTEM FAILURE ]\n"
        " ___________________________\n"
        " \n"
        "  ⚠  SYSTEM_THREAD_EXCEPTION\n"
        "  ID: 0x0000007E (FATAL)\n"
        " ___________________________\n"
        " \n"
        " CPU REGISTERS DUMP:\n"
        " EAX: 00000001  EBX: FFFFFFFF\n"
        " ECX: 00249F00  EDX: 00000000\n"
        " ESI: 804D7000  EDI: 804D7034\n"
        " \n"
        " PROCESS: tg_userbot.service\n"
        " STATUS: [██████████] 100%\n"
        " ACTION: MEMORY_DUMP_FAILED\n"
        "</code>\n"
        "🛑 <b>STOP: 0x0000001A (MEMORY_MANAGEMENT)</b>\n"
        "\n"
        "<b>A problem has been detected and the bot has been suspended to prevent damage to your Telegram account database.</b>\n"
        "\n"
        "<i>If this is the first time you've seen this stop error screen, contact the developer immediately.</i>\n"
        "\n"
        "🔍 <b>Technical information:</b>\n"
        "<code>*** STOP: 0x0000008E (0xC0000005, 0xBF86721A)</code>\n"
        "<code>*** tg_client.dll - Address BF86721A base at BF800000</code>"
    )
    await event.edit(error_text, parse_mode="html")