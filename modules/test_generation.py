from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.schema import SystemMessage
from pathlib import Path
import os
from prompts import unit_tests_generation_prompt, integration_tests_generation_prompt

unit_tests = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=unit_tests_generation_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{human_input}"),
    ]
)

integration_tests = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=integration_tests_generation_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{human_input}"),
    ]
)

def generate_unit_tests(file_content, file_path, model):
    if not file_content or not file_path:
        raise ValueError("file_content or file_path is empty")
    combined_input = f"File path: {file_path}\n\n{file_content}"
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    chat_llm_chain = LLMChain(
        llm=model,
        prompt=unit_tests,
        verbose=True,
        memory=memory
    )
    response = chat_llm_chain.predict(human_input=combined_input)
    return response

def generate_integration_tests(file_content, file_path, model):
    if not file_content or not file_path:
        raise ValueError("file_content or file_path is empty")
    combined_input = f"File path: {file_path}\n\n{file_content}"
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    chat_llm_chain = LLMChain(
        llm=model,
        prompt=integration_tests,
        verbose=True,
        memory=memory
    )
    response = chat_llm_chain.predict(human_input=combined_input)
    return response

# Filtering the test cases
def extract_tests(tests_content):
    start_index = tests_content.find("```python") + len("```python")
    end_index = tests_content.find("```", start_index)
    filtered_test_cases = tests_content[start_index:end_index].strip()

    return filtered_test_cases

def save_summaries(all_content, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    context_path = os.path.join(output_folder, "context.txt")
    with open(context_path, 'w', encoding='utf-8') as context_file:
        for file_path, content in all_content.items():
            context_file.write(f"File: {file_path}\n")
            context_file.write(f"Summary: {content['summary']}\n")
            context_file.write("="*40 + "\n")
