import os
from discord import Interaction, app_commands
from discord.app_commands import CheckFailure

# Carregar IDs do .env
LEADER_ID = int(os.getenv("ROLE_ADMIN"))  # ID do líder (você)
MASTER_ROLE_ID = int(os.getenv("ROLE_MEMBER_MASTER"))  # ID do cargo Master

def is_allowed():
    async def predicate(interaction: Interaction):
        if LEADER_ID in [role.id for role in interaction.user.roles]:
            return True
        
        if MASTER_ROLE_ID in [role.id for role in interaction.user.roles]:
            return True
        
        # Levanta a exceção de verificação
        raise CheckFailure(f"Member {interaction.user} cannot use the /{interaction.command.name} command.")
    
    return app_commands.check(predicate)
