import openai
from webex_bot.models.command import Command
from webex_bot.models.response import Response
class gpt(Command):
    messages = []
    messages.append({"role" : "system", "content" : "I am webexGPT ask me any question, I'll be able to answer"})
    def __init__(self):
        super().__init__()
    def execute(self, message, attachment_actions, activity):
        openai.api_key = ("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")
        self.messages.append({"role" :"user","content":message})
        completion = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages=self.messages)
        gpt_res = completion.choices[0].message.content
        self.messages.append({"role":"assistant","content": message})
        return gpt_res