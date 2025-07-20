from ollama import chat, embed
from ollama import ChatResponse
import configparser
import base64

class ConfigLoader:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = None
    def load_config(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)
        return config

class ChatModel:
    def __init__(self, config_loader: ConfigLoader):
        self.config = config_loader.load_config()
        
    def get_response(self, messages):
        self.model_name = self.config['chat']['model_name']

        response: ChatResponse = chat(model=self.model_name, messages=messages)
        return response