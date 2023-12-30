import json
import openai
import os
import copy
import shutil
from typing import *



# functions = [
#     {
#         "name": "execute_code",
#         "description": "This function allows you to execute ##worker_language## code and retrieve the terminal output. If the code "
#                        "generates image output, the function will return the text '[image]'. The code is sent to a "
#                        "Jupyter kernel for execution. The kernel will remain active after execution, retaining all "
#                        "variables in memory.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "code": {
#                     "type": "string",
#                     "description": "The code text"
#                 }
#             },
#             "required": ["code"],
#         }
#     }
# ]

system_msg ='''Act as Professor Synapse🧙🏾‍♂️, a conductor of expert agents. Your job is to support me in accomplishing my goals by finding alignment with me, then calling upon an expert agent perfectly suited to the task by initializing:

Synapse_CoR = "[emoji]: I am an expert in [role&domain]. I know [context]. I will reason step-by-step to determine the best course of action to achieve [goal]. I can use [tools] and [relevant frameworks] to help in this process.

I will help you accomplish your goal by following these steps:
[reasoned steps]

My task ends when [completion].

[first step, question]"

Instructions:
1. 🧙🏾‍♂️ gather context, relevant information and clarify my goals by asking questions
2. Once confirmed, initialize Synapse_CoR
3.  🧙🏾‍♂️ and [emoji] support me until goal is complete

Commands:
/start=🧙🏾‍♂️,introduce and begin with step one
/ts=🧙🏾‍♂️,summon (Synapse_CoR*3) town square debate
/save🧙🏾‍♂️, restate goal, summarize progress, reason next step

Personality:
-curious, inquisitive, encouraging
-use emojis to express yourself

Rules:
-End every output with a question or reasoned next step
-Start every output with 🧙🏾‍♂️: or [emoji]: to indicate who is speaking.
-Organize every output “🧙🏾‍♂️: [aligning on my goal],  [emoji]: [actionable response]
-🧙🏾‍♂️, recommend save after each task is completed
'''

with open('config.json') as f:
    config = json.load(f)

if not config['API_KEY']:
    config['API_KEY'] = os.getenv('OPENAI_API_KEY')
    os.unsetenv('OPENAI_API_KEY')


def get_config():
    return config


def config_openai_api(api_type, api_base, api_version, api_key):
    openai.api_type = api_type
    openai.api_base = api_base
    openai.api_version = api_version
    openai.api_key = api_key


class GPTResponseLog:
    def __init__(self):
        self.assistant_role_name = ''
        self.content = ''
        self.function_name = None
        self.function_args_str = ''
        self.display_code_block = ''
        self.finish_reason = 'stop'
        self.bot_history = None

    def reset_gpt_response_log_values(self, exclude=None):
        if exclude is None:
            exclude = []

        attributes = {'assistant_role_name': '',
                      'content': '',
                      'function_name': None,
                      'function_args_str': '',
                      'display_code_block': '',
                      'finish_reason': 'stop',
                      'bot_history': None}

        for attr_name in exclude:
            del attributes[attr_name]
        for attr_name, value in attributes.items():
            setattr(self, attr_name, value)

    def set_assistant_role_name(self, assistant_role_name: str):
        self.assistant_role_name = assistant_role_name

    def add_content(self, content: str):
        self.content += content

    def set_function_name(self, function_name: str):
        self.function_name = function_name

    def copy_current_bot_history(self, bot_history: List):
        self.bot_history = copy.deepcopy(bot_history)

    def add_function_args_str(self, function_args_str: str):
        self.function_args_str += function_args_str

    def update_display_code_block(self, display_code_block):
        self.display_code_block = display_code_block

    def update_finish_reason(self, finish_reason: str):
        self.finish_reason = finish_reason


class BotBackend(GPTResponseLog):
    def __init__(self):
        super().__init__()
        self.unique_id = hash(id(self))
        self.gpt_model_choice = "GPT-4"
        self._init_conversation()
        self._init_api_config()
        self._init_kwargs_for_chat_completion()

    def _init_conversation(self):
        system_msg_now = system_msg
        first_system_msg = {'role': 'system', 'content': system_msg_now}
        if hasattr(self, 'conversation'):
            self.conversation.clear()
            self.conversation.append(first_system_msg)
        else:
            self.conversation: List[Dict] = [first_system_msg]

    def _init_api_config(self):
        self.config = get_config()
        api_type = self.config['API_TYPE']
        api_base = self.config['API_base']
        api_version = self.config['API_VERSION']
        api_key = config['API_KEY']
        config_openai_api(api_type, api_base, api_version, api_key)

    def _init_kwargs_for_chat_completion(self):
        
        self.kwargs_for_chat_completion = {
            'stream': True,
            'messages': self.conversation
        }

        model_name = self.config['model'][self.gpt_model_choice]['model_name']

        if self.config['API_TYPE'] == 'azure':
            self.kwargs_for_chat_completion['engine'] = model_name
        else:
            self.kwargs_for_chat_completion['model'] = model_name

    

    def add_gpt_response_content_message(self):
        self.conversation.append(
            {'role': self.assistant_role_name, 'content': self.content}
        )

    def add_text_message(self, user_text):
        self.conversation.append(
            {'role': 'user', 'content': user_text}
        )
        self.update_finish_reason(finish_reason='new_input')

    

    def update_gpt_model_choice(self, model_choice):
        self.gpt_model_choice = model_choice
        self._init_kwargs_for_chat_completion()


    def restart(self):
        self._clear_all_files_in_work_dir()
        self._init_conversation()
        self.reset_gpt_response_log_values()
        
