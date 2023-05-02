from typing import Union

import discord

from bots.discord.slash_message import MessageSession
from core.logger import Logger
from core.parser.message import parser
from core.types import MsgInfo, Session


def ctx_to_session(ctx: Union[discord.ApplicationContext, discord.AutocompleteContext]):
    target = "Discord|Channel"
    if isinstance(ctx, discord.ApplicationContext):
        if isinstance(ctx.channel, discord.DMChannel):
            target = "Discord|DM|Channel"
        targetId = f"{target}|{ctx.channel.id}"
        senderId = f"Discord|Client|{ctx.author.id}"
    else:
        if isinstance(ctx.interaction.channel, discord.PartialMessage):
            target = "Discord|DM|Channel"
            targetId = f"{target}|{ctx.interaction.channel.id}"
        else:
            targetId = f"{target}|{ctx.interaction.channel_id}"
        senderId = f"Discord|Client|{ctx.interaction.user.id}"
    return MessageSession(
        target=MsgInfo(
            targetId=targetId,
            senderId=senderId,
            senderName=ctx.author.name if isinstance(
                ctx,
                discord.ApplicationContext) else ctx.interaction.user.name,
            targetFrom=target,
            senderFrom="Discord|Client",
            clientName='Discord|Slash',
            messageId=0),
        session=Session(
            message=ctx,
            target=ctx.channel if isinstance(
                ctx,
                discord.ApplicationContext) else ctx.interaction.channel,
            sender=ctx.author if isinstance(
                ctx,
                discord.ApplicationContext) else ctx.interaction.user))


async def slash_parser(ctx: discord.ApplicationContext, command: str):
    await ctx.defer()
    session = ctx_to_session(ctx)
    session.command = f'/{str(ctx.command).split(" ")[0]} {command}'
    Logger.info(f'parsing..')
    await parser(session, prefix=['~', '/'], require_enable_modules=False)
