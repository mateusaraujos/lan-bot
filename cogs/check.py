import os
import datetime
import discord
from discord import app_commands
from discord.ext import commands

class InteractionTracker(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_interactions = {}
        self.message_cache = {}

    async def cog_load(self):
        guild = discord.Object(id=int(os.getenv("GUILD_ID")))
        self.bot.tree.add_command(self.check, guild=guild)

    # Listener para mensagens: registra e guarda no cache
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        # Armazena a mensagem no cache com o ID como chave
        self.message_cache[message.id] = message
        
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        description = f"Enviou [esta mensagem]({message.jump_url})."
        self.last_interactions[message.author.id] = (timestamp, description)

    # Fallback: se a mensagem não estiver em cache, usa on_raw_message_delete
    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        # Tenta obter o canal para buscar a mensagem no cache próprio
        channel = self.bot.get_channel(payload.channel_id)
        jump_url = "Desconhecido"
        message = self.message_cache.get(payload.message_id)
    
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        if message is not None:
            jump_url = message.jump_url
            description = f"Apagou uma mensagem [neste canal]({jump_url})."

            # Registra a interação com base no autor da mensagem
            self.last_interactions[message.author.id] = (timestamp, description)
            self.message_cache.pop(payload.message_id, None)
        else:
            # Se a mensagem não estiver no cache, registra de forma genérica
            description = f"Apagou uma mensagem no canal <#{payload.channel_id}>."

            # Aqui você pode optar por registrar essa ação com uma chave especial ou ignorar
            # Por exemplo, registrar em um log global:
            self.last_interactions[payload.message_id] = (timestamp, description)
    
    # Listener para reações adicionadas (mesmo em mensagens antigas)
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
        description = f"Reagiu com o emoji {payload.emoji} nesta [mensagem]({message.jump_url})."
        self.last_interactions[payload.user_id] = (timestamp, description)
    
    # Listener para remoção de reação (mesmo em mensagens antigas)
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        # Tentar obter o objeto member
        user = self.bot.get_user(payload.user_id)
        if user is None or user.bot:
            return
        
        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(payload.channel_id)
            except Exception:
                return
        
        try:
            message = await channel.fetch_message(payload.message_id)
        except Exception:
            return
        
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        description = f"Tirou a reação {payload.emoji} nesta [mensagem]({message.jump_url})."
        self.last_interactions[payload.user_id] = (timestamp, description)
    
    # Listener para atualizações do estado de voz: registra quando um membro entra ou sai de um canal de voz.
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return
        
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        # Se entrou em uma call (after.channel não None e diferente de before)
        if after.channel is not None and after.channel != (before.channel if before else None):
            description = f"Entrou na call '{after.channel.name}'."
            self.last_interactions[member.id] = (timestamp, description)
        # Se saiu de uma call (after.channel é None, e antes havia um canal)
        elif before.channel is not None and after.channel is None:
            description = f"Saiu da call '{before.channel.name}'."
            self.last_interactions[member.id] = (timestamp, description)
    
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
                f"{member.mention} ({time_str})\n"
                f"{description}"
            )
        else:
            response = f"{member.mention} ainda não interagiu no servidor."
        await interaction.response.send_message(response, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(InteractionTracker(bot))
