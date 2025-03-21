import os
import datetime
import logging
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

# Criar diretório de logs se não existir
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configurar logging
logging.basicConfig( 
    level=logging.INFO, 
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'), # Salvar logs no arquivo bot.log
        logging.StreamHandler() # Mostrar logs no console
    ]
)

# Configurar intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Criação do bot
bot = commands.Bot(command_prefix="/", intents=intents)

# on_app_command_completion é chamado automaticamente quando um comando é concluído sem erros
@bot.event
async def on_app_command_completion(interaction: discord.Interaction, command: discord.app_commands.Command):
    #Registra o uso bem-sucedido do comando
    logging.info(f"Member {interaction.user} successfully used the /{command.name} command.")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    # Se for erro de permissão, responde com a mensagem desejada
    if isinstance(error, discord.app_commands.CheckFailure):
        if interaction.response.is_done():
            await interaction.followup.send(
                "🚫 Você não tem permissão para usar este comando.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "🚫 Você não tem permissão para usar este comando.",
                ephemeral=True
            )
        # Registra apenas uma linha de erro sem traceback
        logging.error(f"CheckFailure: {error}", exc_info=False)
    else:
        # Para outros erros, responda de forma genérica
        if interaction.response.is_done():
            await interaction.followup.send(
                "❌ Ocorreu um erro ao executar este comando.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Ocorreu um erro ao executar este comando.",
                ephemeral=True
            )
        logging.error(f"Error in command: {error}", exc_info=False)

@bot.event
async def on_ready():
    # Definir o horário de início com objeto timezone-aware
    bot.start_time = datetime.datetime.now(datetime.timezone.utc)

    # Sincronizar os slash commands para o servidor de testes
    guild = discord.Object(id=GUILD_ID)
    synced = await bot.tree.sync(guild=guild)

    logging.info(f"Synced Slash Commands: {synced}")
    logging.info(f"Bot connected as {bot.user}")

async def shutdown():
    """Função para desligamento seguro do bot."""
    logging.info("Shutting down the bot...")
    await bot.close()
    logging.info(f"{bot.user} successfully shut down.")

async def main():
    async with bot:
        # Carregar os cogs da pasta /cogs/
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                extension = f"cogs.{filename[:-3]}"
                try:
                    await bot.load_extension(extension)
                    logging.info(f"Cog '{extension}' loaded successfully.")
                except Exception as e:
                    logging.error(f"Error loading {extension}: {e}")
        
        try:
            await bot.start(TOKEN)
        except Exception as e:
            logging.error(f"Unexpected error 'bot.start': {e}", exc_info=True)
        finally:
            await shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot manually shut down.")
    except Exception as e:
        logging.error(f"Unexpected error 'asyncio.run': {e}")
