from api.prompt import Prompt
import os
from openai import AzureOpenAI
import dotenv
dotenv.load_dotenv()

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://41241-maepdksw-eastus2.cognitiveservices.azure.com/")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "o3-mini")
subscription_key = os.getenv("AZURE_OPENAI_KEY")
api_version = os.getenv("OPENAI_API_VERSION", "2024-12-01-preview")

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

class ChatGPT:
    def __init__(self):
        self.prompt = Prompt()
        self.deployment_name = deployment
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", 0))
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", 2000))

    def get_response(self):
        response = client.chat.completions.create(
            messages=self.prompt.generate_prompt(),
            max_completion_tokens=self.max_tokens,
            model=self.deployment_name,
        )
        return response.choices[0].message.content

    def add_msg(self, text):
        self.prompt.add_msg(text)