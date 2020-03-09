import bot
import daemon

with daemon.DaemonContext():
    Bot = bot.MyBotHandler()
    Bot.client.call_on_each_message(Bot.get_msg)
