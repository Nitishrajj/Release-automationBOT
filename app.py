from webex_bot.webex_bot import WebexBot
import json
import os
from webex_bot.webex_bot import Command
from greeting import CreatefolderBYNAME,DownloadFilesfromURL,exec_comman_release,Push_to_final_and_list,changesigntounsign,totalfilestofinal,Finaltocorona
# from gpt import gpt
bot = os.environ.get("ACCESS_TOKEN")

# bot.commands.clear()
bot.add_command(CreatefolderBYNAME())
bot.add_command(DownloadFilesfromURL())
bot.add_command(exec_comman_release())
bot.add_command(Push_to_final_and_list())
bot.add_command(changesigntounsign())
bot.add_command(totalfilestofinal())
bot.add_command(Finaltocorona())

        

bot.run()