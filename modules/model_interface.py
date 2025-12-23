from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from modules.app_tools import turn_into_logic
from modules.logger import Logger
from modules.time_decorators import timer
class ModelInterface:
    outputs = {}
    # initializes the model interface with the specified model and prompt
    # defaults to qwen2.5:7b from ollama with temperature 0
    @timer
    def __init__(self , model_name: str = "qwen2.5:7b", model_provider_: str = "ollama", temperature: int = 0):
        self.llm = init_chat_model(
            model=model_name, 
            model_provider=model_provider_, 
            temperature=0
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", turn_into_logic()),
            ("user", "{statement}")
        ])

        self.chain = self.prompt | self.llm | StrOutputParser()
    
    # returns the llm output
    # prints the output in green as it streams
    @timer
    def process_statement(self, statement: str) -> str:
        result = ""
        for chunk in self.chain.stream({"statement": statement}):
            Logger.log(chunk, end="");   
            result += chunk
        return result
    # extracts and returns only the logic form expression from the llm output
    def get_expression(self, statement: str) -> str:
        if(statement in self.outputs):
            return self.outputs[statement].split("Logic Form Expression:", 1)[1].strip()
        else:
            self.outputs[statement] = self.process_statement(statement)
        return self.outputs[statement].split("Logic Form Expression:", 1)[1].strip()
    # extracts and returns only the definitions
    # if it is already in database, it will return the existing definitions
    def get_definitions(self, statement: str) -> str:
        if(statement in self.outputs):
            return self.outputs[statement].split("Logic Form Expression:", 1)[0].strip()
        else:
            self.outputs[statement] = self.process_statement(statement)
        return self.outputs[statement].split("Logic Form Expression:", 1)[0].strip()