import os
import datetime
import discord
from discord.ext import commands
from discord import app_commands
from utils.checks import is_allowed

class Status(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Dicionário para armazenar o horário da última interação de cada usuário
        self.user_last_interaction = {}
    
    async def cog_load(self):
        # Adiciona o comando à árvore, definindo o guild para que ele seja registrado imediatamente
        guild = discord.Object(id=int(os.getenv("GUILD_ID")))
        self.bot.tree.add_command(self.status, guild=guild)
    
    @app_commands.command(
        name="status",
        description="Verifique o status atual do bot e quando você interagiu com ele."
    )
    @is_allowed()
    async def status(self, interaction: discord.Interaction):
        # Usa .now() com timezone-aware para consistência
        current_time = datetime.datetime.now(datetime.timezone.utc)
        user_id = interaction.user.id

        # Recupera a última interação do usuário, se houver; senão, usa o horário atual
        last_interaction = self.user_last_interaction.get(user_id, current_time)
        self.user_last_interaction[user_id] = current_time

        # Usa o horário de início do bot para calcular o uptime
        bot_start_time = getattr(self.bot, "start_time", current_time)

        # Cria timestamps relativos (o Discord renderiza de forma dinâmica)
        uptime_relative = f"<t:{int(bot_start_time.timestamp())}:R>"
        inactivity_relative = f"<t:{int(last_interaction.timestamp())}:R>"

        response = (
            f"🟢 Online: {uptime_relative}\n"
            f"Sua última interação com o bot foi: {inactivity_relative}"
        )
        await interaction.response.send_message(response)

async def setup(bot: commands.Bot):
    await bot.add_cog(Status(bot))
