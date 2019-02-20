import discord
from discord import ChannelType
import asyncio
from threading import Thread
from PIL import Image
import requests
from io import BytesIO
import os
from sys import exit, maxsize

SERVER = "342430559697502219"
TOKEN = open("token.txt").readlines()[0].rstrip() # I am lazy
LIMIT = maxsize # some ungodly number
client = discord.Client(max_messages=LIMIT) 

@client.event
async def on_ready():
    print('Logged in as ' + client.user.name)

async def get_images_from_channels():
    await client.wait_until_ready()
    server = client.get_server(SERVER)
    channels = [x for x in server.channels if x.type == ChannelType.text]
    # if just flumblezone content
    flumblezone = [client.get_channel("422924857555288064")]
    tasks = [collect_channel(c) for c in channels]
    print("before gather")
    return await asyncio.gather(*tasks)

async def collect_channel(c):
    urls = []
    async for l in client.logs_from(c, limit=LIMIT):
        # ugly workaround for BetterDiscord users
        for item in l.embeds:
            if 'description' in item.keys():
                l.embeds = []

        # handle directly attached images and embeds
        items = l.attachments + l.embeds

        # uglier workaround for gifs and mp4s
        for i in items:
            fname = i['url'].split("/")[-1]
            extension = fname.split('.')[-1]
            # duck typing means != 'png' or 'jpg' == 'jpg'
            if extension == 'png' or extension == 'jpg':
                pass
            else:
                items = []

        if items != []:
            urls += [i['url'] for i in items]
    print("scraped pictures from #" + c.name)
    return urls

async def download_image(url):
    try:
        # save image with some pil+bytesio boilerplate
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        fname = url.split('/')[-1]
        img.save('dataset/' + fname)
    except OSError:
        print("Warning: Failed to write " + url) # one of the jpgs is pngs.

async def main_loop():
    tasks = []
    for urls in await get_images_from_channels():
        tasks.extend([download_image(url) for url in urls])
    await asyncio.wait(tasks)
    print("done!")
    client.logout()
    exit(0)

if __name__ == "__main__":
    if not os.path.exists('dataset/'):
        os.mkdir('dataset')

    task = client.loop.create_task(main_loop())
    client.run(TOKEN)