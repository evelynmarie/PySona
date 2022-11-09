import arrow
import disnake
from disnake import ApplicationCommandInteraction, Member
from disnake.ext import commands

from client import Client


class Spotify(commands.Cog):
    """A set of commands for interacting with Spotify."""

    def __init__(self, client: Client) -> None:
        self.client = client

    @commands.slash_command()
    async def spotify(self, inter: ApplicationCommandInteraction) -> None:
        """Provides access to retrieving data from the Spotify API."""
        del inter
        pass

    @spotify.sub_command()
    async def album(self, inter: ApplicationCommandInteraction, album: str, artist: str = None, year: int = None, market: str = None) -> None:
        """Retrieves a specific album from Spotify.

        Parameters
        ----------
        album: The album to search for. Required.
        artist: The artist who recorded the album. Optional.
        year: The year the album was recorded. Optional.
        market: The region to be searched, as a two-character country code. Optional.
        """

        if artist is not None and year is None:
            search_string = f"album: {album} artist: {artist}"
        elif artist is None and year is not None:
            search_string = f"album: {album} year: {year}"
        elif artist is not None and year is not None:
            search_string = f"album: {album} artist: {artist} year: {year}"
        else:
            search_string = f"album: {album}"

        results = self.client.spotify.search(q=search_string, type="album", limit=1, market=market)
        items = results["albums"]["items"]

        if len(items) > 0:
            album = self.client.spotify.album(items[0]["id"], market=market)
            tracks = self.client.spotify.album_tracks(album_id=items[0]["id"], market=market)

            id = album["id"]
            name = album["name"]
            released = arrow.get(album["release_date"]).format("MMM D, YYYY")
            type = album["album_type"].title()
            artists = list()
            tracklist = list()
            duration: int = 0

            if type == "single" and len(tracks["items"]) > 1 and len(tracks["items"]) <= 6:
                type = "Extended Play (EP)"

            for artist in album["artists"]:
                name = artist["name"]
                url = artist["external_urls"]["spotify"]
                artists.append(f"[{name}]({url})")

            for track in tracks["items"]:
                title = track["name"]
                track_number = track["track_number"]
                url = track["external_urls"]["spotify"]
                length = arrow.get((track["duration_ms"]) / 1000).format("m [min] s [sec]")

                if track["duration_ms"] / 1000 > 3600:
                    length = arrow.get((track["duration_ms"]) / 1000).format("h [hr] m [min] s [sec]")

                if track["explicit"]:
                    tracklist.append(f"**{track_number}**. [{title}]({url}) **E** - {length}")
                else:
                    tracklist.append(f"**{track_number}**. [{title}]({url}) - {length}")

                duration += track["duration_ms"] / 1000

            embed = disnake.Embed(colour=0x1DB954)
            embed.title = name
            embed.url = f"https://open.spotify.com/album/{id}"
            embed.description = "\n".join(tracklist)
            embed.set_thumbnail(album["images"][0]["url"])
            embed.add_field(name="Type", value=type, inline=True)
            embed.add_field(name="Released", value=released, inline=True)
            embed.add_field(name="Artists", value=", ".join(artists), inline=True)
            embed.add_field(name="Tracks", value=album["total_tracks"], inline=True)

            if duration > 3600:
                embed.add_field(name="Length", value=arrow.get(duration).format("h [hr] m [min] s [sec]"), inline=True)
            else:
                embed.add_field(name="Length", value=arrow.get(duration).format("m [min] s [sec]"), inline=True)

            try:
                embed.add_field(name="Markets", value=len(album["available_markets"]), inline=True)
            except KeyError:
                # if we get a key error, its because the user provided a market,
                # which removes the available_markets array from the returned album
                # object for some reason.
                pass

            if len(embed.fields) < 6 and len(embed.fields) <= 5:
                embed.insert_field_at(4, name="\u200B", value="\u200B", inline=True)

            embed.set_footer(text="Powered by the Spotify Web API.")

            return await inter.send(embed=embed)

        await inter.send("No album could be found matching this criteria. Please try again.")

    @spotify.sub_command()
    async def status(self, inter: ApplicationCommandInteraction, member: Member = None) -> None:
        """Retrieves a given user's Spotify status. Defaults to your own."""

        if inter.guild_id is None:
            # due to the way discord activities work, they cannot be accessed from direct
            # messages for some reason, so disallow the command from being used in guilds
            # to avoid it breaking.
            return await inter.send("This command cannot be used from DMs.")

        if member is None:
            member = inter.author
        elif member.bot:
            return await inter.send("Bots can't listen to music, silly.")

        name = member.name.title()
        activity = member.activity

        if isinstance(activity, disnake.Spotify):
            title = activity.title
            artist = activity.artist
            album = activity.album

            if member is inter.author:
                message = f"You are currently listening to **{title}** by **{artist}** on **{album}**."
            else:
                message = f"**{name}** is currently listening to **{title}** by **{artist}** on **{album}**."

            return await inter.send(message)

        if member is inter.author:
            return await inter.send("You aren't currently istening to anything.")

        await inter.send(f"**{name}** isn't currently listening to anything.")
        pass


def setup(client: Client):
    client.add_cog(Spotify(client))
    pass
