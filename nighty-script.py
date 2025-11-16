import discord
import requests
import xml.etree.ElementTree as ET
from discord.ext import commands


@nightyScript(
    name="dblookup",
    author="jermate industries",
    description="data breach lookup developed by jerkmate industires using neuralink bypass found in aws backdoor",
    usage="Command: [Prefix]dblookup <tags>"
)
def dblookup1():
    post_cache = {}

    @bot.command()
    async def dblookup(ctx, *, tags: str):
        import requests
        import json
        import io
        import datetime

        if not tags:
            return await ctx.send("❌ **Usage:** `[Prefix]dblookup <tags>")

        try:
            await ctx.message.add_reaction('🔍')

            cache_key = tags

            loading_msg = await ctx.send(f"🔍 **Searching...**\n**Tags:** `{tags}`")

            api_url = "http://127.0.0.1:8080/search"
            params = {
                'search_string': tags,
                'extensions': 'txt,csv,sql'
            }

            response = requests.get(api_url, params=params)
            response.raise_for_status()

            print(f"Response status: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response content (first 500 chars): {response.text[:500]}")

            try:
                data = response.json()
            except:
                pass

            # Extract matches from JSON response
            posts_to_show = data.get('matches', [])

            # Print the matches to console for debugging
            print(f"=== MATCHES FOUND ===")
            print(f"Number of matches: {len(posts_to_show)}")
            print(f"Matches content: {json.dumps(posts_to_show, indent=2)}")
            print(f"=====================")

            if not posts_to_show:
                await loading_msg.edit(content=f"❌ **No results found for:** `{tags}`")
                return

            # Initialize cache for this search if it doesn't exist
            if cache_key not in post_cache:
                post_cache[cache_key] = []

            for post in posts_to_show:
                # Extract post ID - adjust based on your JSON structure
                post_id = post.get('id')
                if post_id:
                    post_cache[cache_key].append(post_id)

            # Create text file with matches
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"matches_{tags.replace(' ', '_')}_{timestamp}.txt"

            # Prepare file content
            file_content = f"Search Results for: {tags}\n"
            file_content += f"Search Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            file_content += f"Total Matches: {len(posts_to_show)}\n"
            file_content += "=" * 50 + "\n\n"

            # Add all matches to file
            for i, match in enumerate(posts_to_show, 1):
                file_content += f"Match #{i}:\n"
                file_content += json.dumps(match, indent=2)
                file_content += "\n" + "-" * 30 + "\n\n"

            # Create file object
            file_obj = io.StringIO(file_content)

            # Build response message
            response_msg = f"🔍 **Search Results**\n"
            response_msg += f"**Tags:** `{tags}`\n"
            response_msg += f"**Found:** `{len(posts_to_show)}` posts\n"
            response_msg += f"**File:** `{filename}`\n\n"

            # Edit loading message and send file
            await loading_msg.edit(content=response_msg)
            await ctx.send(file=discord.File(fp=io.BytesIO(file_content.encode('utf-8')), filename=filename))

            try:
                await ctx.message.remove_reaction('🔍', ctx.me)
                await ctx.message.add_reaction('✅')
            except:
                pass

        except requests.RequestException as e:
            await loading_msg.edit(content=f"❌ **API connection error:** {str(e)}")
        except Exception as e:
            await loading_msg.edit(content=f"❌ **Unexpected error:** {str(e)}")


dblookup1()
