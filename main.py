
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from modules.app_tools import turn_into_logic

llm = init_chat_model(
    model="qwen2.5:7b", 
    model_provider="ollama", 
    temperature=0
)


prompt = ChatPromptTemplate.from_messages([
    ("system", turn_into_logic()),
    ("user", "{statement}")
])


chain = prompt | llm | StrOutputParser()


input_text = "1. Never Outshine the Master Avoid displaying your talents too brightly; it creates insecurity in those above you. Make your masters appear more brilliant than they are."

print("Processing...")

for chunk in chain.stream({"statement": input_text}):
    print(chunk, end="", flush=True)

print()