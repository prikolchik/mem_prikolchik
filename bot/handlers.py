import asyncio
import os
import html
import aiohttp
import random
import urllib.parse
import yt_dlp

from telethon import events
from telethon import types
from datetime import datetime
from groq import AsyncGroq

from .client import client
from utils.logger import logger 
from .config import WEATHER_API_KEY
from .config import GROQ_API_KEY
from .config import PIXABAY_KEY
from .config import GIPHY_KEY

COMMAND_HANDLERS = {}
SELF_USER = "me"
groq_client = AsyncGroq(api_key=GROQ_API_KEY)

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': '%(title)s.%(ext)s', 
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'quiet': True,
    'noplaylist': True,
    'ffmpeg_location': 'ffmpeg.exe' , 
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'nocheckcertificate': True,
    'geo_bypass': True
}

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
<code>.magic</code> - magic effect 
<code>.qweather</code> - quick weather
<code>.weather</code> - regular weather
<code>.gpt</code> - reply to messages
<code>.cat</code> - send random cat image
<code>.fox</code> - send random fox image
<code>.coffee</code> - send random coffee image
<code>.duck</code> - send random duck image
<code>.dog</code> - send random dog image
<code>.panda</code> - send random panda image
<code>.redpanda</code> - send random redpanda image
<code>.birb</code> - send random birb image
<code>.koala</code> - send random koala image
<code>.shark</code> - send random shark image
<code>.radish</code> - send random radish image
<code>.find</code> - search photo
<code>.song</code> - send a song
<code>.gif</code> - send gif

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
    
@command(".magic")
async def handle_magic(event, *args):
    text = ' '.join(args) or "Abracadabra!"    
    frames = [text, "...", "..", ".", "✨", " "]
    
    for frame in frames:
        await event.edit(f"<code>{html.escape(frame)}</code>", parse_mode="html")
        await asyncio.sleep(0.4)
    await event.delete()
    
@command(".qweather")
async def handle_qweather(event, *args):
    city = args[0] if args else "Landschut"
    full_mode = "full" in args
    
    if full_mode:
        url = f"https://wttr.in/{city}?m&n&T&0"    
    else:
        url = f"https://wttr.in/{city}?format=%l:+%c+%t+%w+%h"
        
    await event.edit(f"<b>Receive data for {city}...</b> ", parse_mode='html')
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    await event.edit("Server error or City not found")
                    return
                text = await response.text()
                
                if full_mode:
                    await event.edit(f"<code>{text}</code>", parse_mode='html')
                else:
                    await event.edit(f"<b>Weather:</b>\n<code>{text}</code>", parse_mode='html')
        except Exception as e:
            logger.error(f"[qweather] Error {e}")
            await event.edit(f"Could not contact the service")
            
            
@command(".weather")

async def handle_weather(event, *args):
    """
    Weather via OpenWeatherMap API.
    Usage: .weather London
    """
    
    API_KEY =  WEATHER_API_KEY
    
    city = " ".join(args) if args else "Landshut"
    
    # URL: units=metric (Celsius), lang=en (English)
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=en"

    await event.edit(f"☁️ Fetching data for <b>{city}</b>...", parse_mode="html")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 401:
                    await event.edit("❌ <b>Error:</b> API key is not active yet. Please wait about an hour.")
                    return

                if response.status != 200:
                    await event.edit(f"❌ City <b>{city}</b> not found.")
                    return

                data = await response.json()
                temp = round(data['main']['temp'])
                feels_like = round(data['main']['feels_like'])
                desc = data['weather'][0]['description'].capitalize()
                humidity = data['main']['humidity']
                wind = data['wind']['speed']
                city_name = data['name']
                country = data['sys'].get('country', '')
                
                # Emoji mapping based on weaher icon
                
                icon = data['weather'][0]['icon']
                emoji_map = {
                    "01": "☀️", "02": "⛅", "03": "☁️", "04": "☁️",
                    "09": "🌧️", "10": "🌦️", "11": "⛈️", "13": "❄️", "50": "🌫️"
                }
                
                emoji = emoji_map.get(icon[:2], "🌡️")
                
                res = (
                    f"{emoji} <b>Weather in {city_name}, {country}</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"📝 <b>Status:</b> {desc}\n"
                    f"🌡 <b>Temp:</b> <code>{temp}°C</code>\n"
                    f"🤔 <b>Feels like:</b> <code>{feels_like}°C</code>\n"
                    f"💧 <b>Humidity:</b> <code>{humidity}%</code>\n"
                    f"💨 <b>Wind:</b> <code>{wind} m/s</code>"
                )

                await event.edit(res, parse_mode="html")
                
        except Exception as e:
            logger.error(f"[weather] Error: {e}")
            await event.edit("❌ An internal error occurred while processing the request.")
            



@command(".gpt")
async def handle_gpt(event, *args):
    user_args = " ".join(args).strip()
    reply = await event.get_reply_message()
    reply_text = reply.raw_text.strip() if reply and reply.raw_text else ""

    if user_args and reply_text:
        full_prompt = f"{user_args}\n\nКонтекст:\n{reply_text}"
    elif user_args:
        full_prompt = user_args
    elif reply_text:
        full_prompt = reply_text
    else:
        await event.edit("<b>Напишіть запит або зробіть реплай!</b>", parse_mode="html")
        return

    await event.edit("<b>Groq думає...</b>", parse_mode="html")

    try:
        chat_completion = await groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Ти — швидкий та лаконічний асистент. Відповідай мовою якою ти отримав запит. наприклад якщо мова - українська, то відповідай українською і тд"
                },
                {
                    "role": "user",
                    "content": full_prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
        )

        answer = chat_completion.choices[0].message.content
        
        header = f"<b>Запит:</b> <i>{html.escape(full_prompt[:50])}...</i>\n\n"
        await event.edit(f"{header}{answer}", parse_mode="html")

    except Exception as e:
        logger.error(f"[groq] Error: {e}")
        await event.edit(f"<b>Помилка Groq:</b>\n<code>{html.escape(str(e))}</code>", parse_mode="html")
        
        
@command(".taksa")
async def handle_taksa(event):
    taksa_text = """\n
<code>\n 
                             .-.
(___________________________()6 `-,
(   ______________________   /''"`
//\\                      //\\
" ""                     "" ""
</code> 

    """
    await event.reply(taksa_text, parse_mode="html")
    
@command(".cat")
async def handle_cat(event):
    await event.edit("<b>Meow!</b>", parse_mode="html")
    url = '''https://api.thecatapi.com/v1/images/search'''
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            cat_url = data[0]["url"]
            await client.send_file(
                event.chat_id, 
                cat_url, 
                force_document=False
            )
    await event.delete()
    
@command(".fox")
async def handle_fox(event):
    await event.edit("<b>Hhhh!</b>", parse_mode="html")
    url = '''https://randomfox.ca/floof/'''
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            
            await client.send_file(
                event.chat_id, 
                data["image"], 
                force_document=False
            )
    await event.delete()
    
@command(".coffee")
async def handle_coffee(event):
    await event.edit("<b>yumi!</b>", parse_mode="html")
    url = '''https://coffee.alexflipnote.dev/random.json'''
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            
            await client.send_file(
                event.chat_id, 
                data["file"], 
                force_document=False
            )
    await event.delete()
    
@command(".duck")
async def handle_duck(event):
    await event.edit("<b>krya!</b>", parse_mode="html")
    url = '''https://random-d.uk/api/v2/random'''
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            
            await client.send_file(
                event.chat_id, 
                data["url"], 
                force_document=False
            )
    await event.delete()
    
@command(".dog")
async def handle_dog(event):
    await event.edit("<b>gaf!</b>", parse_mode="html")
    url = '''https://dog.ceo/api/breeds/image/random'''
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            
            await client.send_file(
                event.chat_id, 
                data["message"], 
                force_document=False
            )
    await event.delete()
    
@command(".panda")
async def handle_panda(event):
    await event.edit("<b>BEEEEEEE!</b>", parse_mode="html")
    url = '''https://some-random-api.com/img/panda'''
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            
            await client.send_file(
                event.chat_id, 
                data["link"], 
                force_document=False
            )
    await event.delete()
    
@command(".redpanda")
async def handle_redpanda(event):
    await event.edit("<b>BEEEEEEE!</b>", parse_mode="html")
    url = '''https://some-random-api.com/img/red_panda'''
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            
            await client.send_file(
                event.chat_id, 
                data["link"], 
                force_document=False
            )
    await event.delete()
    
@command(".birb")
async def handle_birb(event):
    await event.edit("<b>z z z!</b>", parse_mode="html")
    url = '''https://some-random-api.com/img/birb'''
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            
            await client.send_file(
                event.chat_id, 
                data["link"], 
                force_document=False
            )
    await event.delete()
    
@command(".koala")
async def handle_koala(event):
    await event.edit("<b>😪😴!</b>", parse_mode="html")
    url = '''https://some-random-api.com/img/koala'''
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            
            await client.send_file(
                event.chat_id, 
                data["link"], 
                force_document=False
            )
    await event.delete()
    
async def get_pixabay_photo(query):
    encoded_query = urllib.parse.quote(query)
    url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q={encoded_query}&image_type=photo&safesearch=true&per_page=30"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as r:
                data = await r.json()
                if data.get("hits"):
                    return random.choice(data["hits"])["largeImageURL"]
                return None
        except Exception as e:
            logger.error(f"pixabay error: {e}")
            return None
        
@command(".shark")
async def handle_shark(event):
    await event.edit("<b>🦈🦈!</b>", parse_mode="html")
    photo = await get_pixabay_photo("shark")
    if photo:
        await client.send_file(
                event.chat_id, 
                photo, 
                force_document=False
            )
        await event.delete()
    else:
        await event.edit("SHARK NOT FOUND")
            
            
@command(".radish")
async def handle_shark(event):
    await event.edit("<b>🍅🍅!</b>", parse_mode="html")
    photo = await get_pixabay_photo("radish")
    if photo:
        await client.send_file(
                event.chat_id, 
                photo, 
                force_document=False
            )
        await event.delete()
    else:
        await event.edit("radish NOT FOUND")
        
        
@command(".find")
async def handle_find_photo(event, *args):
    query = " ".join(args).strip()
    if not query:
        await event.edit("<b>usage: .find animal/object</b>", parse_mode="html")
        
    await event.edit(f"finding... {query}")
    photo = await get_pixabay_photo(query)
    if photo:
        await client.send_file(
                event.chat_id, 
                photo, 
                force_document=False
            )
        await event.delete()
    else:
        await event.edit("PHOTO NOT FOUND")
        
            
@command(".song")
async def handle_song(event, *args):
    query = " ".join(args).strip()
    if not query:
        await event.edit("<b>enter song name </b>", parse_mode="html")
        return
        
    await event.edit(f"finding song... {query}")
    try:
        loop = asyncio.get_event_loop()
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=True)
                entry = info['entries'][0]
                filename = ydl.prepare_filename(entry).rsplit('.', 1)[0] + ".mp3"
                return filename, entry['title'], entry.get('uploader', 'Unknown')

        file_path, title, artist = await loop.run_in_executor(None, download)

        if os.path.exists(file_path):
            await event.edit("<b>sending song </b>", parse_mode="html")
            
            await client.send_file(
                event.chat_id, 
                file_path,
                caption=f"{title}", 
                attributes=[types.DocumentAttributeAudio(
                    duration=0,
                    title=title,
                    performer=artist
                )]
            )
            
            os.remove(file_path)
            await event.delete()
        else:
            await event.edit("file not found")
    except Exception  as e:
        await event.edit(f"<b>error: </b> <code>{str(e)[:100]}</code>", parse_mode="html")
        
@command(".gif")
async def handle_gif(event, *args):
    query = " ".join(args).strip()
    
    await event.edit("We are finding gif")
    async with aiohttp.ClientSession() as session:
        try:
            if query:
                encoded_query = urllib.parse.quote(query)
                url = f"https://api.giphy.com/v1/gifs/search?api_key={GIPHY_KEY}&q={encoded_query}&limit=200&rating=g"
                async with session.get(url) as r:
                    data = await r.json()
                    if not data["data"]:
                        await event.edit("gif not found")
                        return 
                    gif_url = random.choice(data["data"])["images"]["original"]["url"]
            else:
                url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_KEY}&rating=g"
                async with session.get(url) as r:
                    data = await r.json()
                    gif_url = data["data"]["images"]["original"]["url"]
                    
            await client.send_file(
                event.chat_id, 
                gif_url, 
                parse_mode="html"
            )
            await event.delete()
            
        except Exception as e:
            logger.error(f"giphy error: {e}")
            return None