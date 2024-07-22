from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.schema import SystemMessage
from prompts import business_logic_generation_prompt

business_logic = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=business_logic_generation_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{human_input}"),
    ]
)

# Business logic generation
def generate_business_logic(file_content, model):
    if not file_content:
        raise ValueError("file_content is empty")
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    chat_llm_chain = LLMChain(
        llm=model,
        prompt=business_logic,
        verbose=True,
        memory=memory
    )
    response = chat_llm_chain.predict(human_input=file_content)
    return response
