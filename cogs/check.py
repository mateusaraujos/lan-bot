import os
import datetime
import discord
from discord import app_commands
from discord.ext import commands

class InteractionTracker(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # Dicionário para armazenar a última interação de cada usuário.
        # Chave: user_id; Valor: (timestamp, descrição da interação)
        self.last_interactions = {}

    async def cog_load(self):
        guild = discord.Object(id=int(os.getenv("GUILD_ID")))
        self.bot.tree.add_command(self.check, guild=guild)
    
    # Listener para mensagens: regsitra quando o usuário envia uma mensagem.
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        description = f"Sent a message: [Here]({message.jump_url})"
        self.last_interactions[message.author.id] = (timestamp, description)
    
    # Listener para atualizações do estado de voz: resgistra quando um membro entra em um canal de voz.
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return
        
        # Considera apenas a entrada em um canal (quando after.channel é diferente de None e diferente de before.channel)
        if after.channel is not None and after.channel != (before.channel if before else None):
            timestamp = datetime.datetime.now(datetime.timezone.utc)
            description = f"Joined voice channel '{after.channel.name}'"
            self.last_interactions[member.id] = (timestamp, description)
    
    # Listener para reações: resgistra quando um usuário adiciona uma reação.
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # Se a reação for adicionada por um bot, ignora
        if payload.member is None or payload.member.bot:
            return
        
        # Tenta obter o canal onde a reação foi adicionada
        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(payload.channel_id)
            except Exception:
                return
        
        # Tenta buscar a mensagem para obter o link de jump_url
        try:
            message = await channel.fetch_message(payload.message_id)
        except Exception:
            return
        
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        description = f"Added reaction {payload.emoji} on [this message]({message.jump_url})"
        self.last_interactions[payload.user_id] = (timestamp, description)
    
    @app_commands.command(
        name="check",
        description="Verifica a última interação de um usuário no servidor."
    )
    async def check(self, interaction: discord.Interaction, member: discord.Member):
        if member.id in self.last_interactions:
            timestamp, description = self.last_interactions[member.id]

            # Formata o timestamp para o formato relativo do Discord, ex: <t:TIMESTAMP:R>
            time_str = f"<t:{int(timestamp.timestamp())}:R>"
            response = (
                f"{member.mention} - Last interaction: {time_str}\n"
                f"Interaction: {description}"
            )
        else:
            response = f"{member.mention} has no recorded interactions."
        await interaction.response.send_message(response, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(InteractionTracker(bot))
