# Import necessary libraries
import os
import zipfile
from pathlib import Path
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.schema import SystemMessage
from autogen.coding import CodeBlock, LocalCommandLineCodeExecutor
from crewai import Agent, Task, Crew, Process

from model import *
from prompts import *

# Define prompts
business_logic = ChatPromptTemplate.from_messages([
        SystemMessage(content=business_logic_generation_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{human_input}"),
    ])

unit_tests = ChatPromptTemplate.from_messages([
        SystemMessage(content=unit_tests_generation_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{human_input}"),
    ])

integration_tests = ChatPromptTemplate.from_messages([
        SystemMessage(content=integration_tests_generation_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{human_input}"),
    ])

# Handling the input
def extract_zip(zip_file_path, extract_to):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def read_file(file_path):
    print(f"Reading file: {file_path}")  # Debug statement
    encodings = ['utf-8', 'latin-1', 'iso-8859-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
                if content:
                    print(f"Successfully read file: {file_path}")  # Debug statement
                return content
        except UnicodeDecodeError:
            continue
    print(f"Failed to read file with available encodings: {file_path}")  # Debug statement
    raise UnicodeDecodeError(f"Failed to decode {file_path} with available encodings.")

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

# Tests generation and saving them in files
def process_python_files(python_files, files_for_unit_tests, model):
    all_content = {}
    all_unit_tests = {}

    extracted_files_path = Path("extracted_files")
    unit_tests_folder = extracted_files_path / "tests/unit"
    integration_tests_folder = extracted_files_path / "tests/integration"
    unit_tests_folder.mkdir(parents=True, exist_ok=True)
    integration_tests_folder.mkdir(parents=True, exist_ok=True)

    for file_path in python_files:
        print(f"Processing file: {file_path}")  # Debug statement
        
        file_content = read_file(file_path)
        if not file_content:
            print(f"File content is empty for: {file_path}")  # Debug statement
            continue

        file_summary = generate_business_logic(file_content, model)
        all_content[file_path] = {"summary": file_summary}

        file_name = Path(file_path).name
        if file_name in files_for_unit_tests:
            unit_tests_content = generate_unit_tests(file_content, file_path, model)
            unit_tests_content = extract_tests(unit_tests_content)
            test_file_name = f"test_{file_name}"
            test_file_path = unit_tests_folder / test_file_name

            # Add sys.path modification to the test file content
            relative_path = Path(file_path).parent.relative_to(extracted_files_path)
            unit_test_content = f"import sys\nsys.path.insert(0, '{extracted_files_path / relative_path}')\n\n" + unit_tests_content

            with open(test_file_path, 'w', encoding='utf-8') as test_file:
                test_file.write(unit_test_content)
            all_content[file_path]["unit_tests"] = unit_test_content

            # Store unit tests for report generation
            all_unit_tests[file_path] = unit_tests_content

    integration_tests_content = generate_integration_tests(file_content, file_path, model)
    integration_tests_content = extract_tests(integration_tests_content)
    integration_test_file_path = integration_tests_folder / "test_integration.py"

    # Add sys.path modification to the integration test file content
    relative_path = Path(file_path).parent.relative_to(extracted_files_path)
    integration_tests_content = f"import sys\nsys.path.insert(0, '{extracted_files_path / relative_path}')\n\n" + integration_tests_content

    with open(integration_test_file_path, 'w', encoding='utf-8') as test_file:
        test_file.write(integration_tests_content)

    all_content[file_path]["integration_tests"] = integration_tests_content

    print(f"ALL UNIT TEST CASES: \n{all_unit_tests}")
    print(f"INTEGRATION TEST CASES: \n{integration_tests_content}")

    return all_content, all_unit_tests, integration_tests_content

def save_summaries(all_content, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    context_path = os.path.join(output_folder, "context.txt")
    with open(context_path, 'w', encoding='utf-8') as context_file:
        for file_path, content in all_content.items():
            context_file.write(f"File: {file_path}\n")
            context_file.write(f"Summary: {content['summary']}\n")
            context_file.write("="*40 + "\n")

def process_zip_file(zip_file_path, model, files_for_unit_tests=[]):
    extract_to = "extracted_files"
    extract_zip(zip_file_path, extract_to)
    extracted_files_path = Path(extract_to)

    # Extract base name of zip file without extension
    zip_file_base_name = Path(zip_file_path).stem
    path = extracted_files_path / zip_file_base_name
    print("PATH: ", path)

    # Set the PYTHONPATH dynamically
    os.environ["PYTHONPATH"] = str(path)

    # Exclude _MACOSX files
    python_files = [os.path.join(root, file) for root, _, files in os.walk(extracted_files_path) for file in files if file.endswith(".py") and "_MACOSX" not in root]
    
    if not files_for_unit_tests:
        files_for_unit_tests = [Path(f).name for f in python_files]
    
    all_content, all_unit_tests, integration_tests_content = process_python_files(python_files, files_for_unit_tests, model)
    save_summaries(all_content, "outputs")
    
    return zip_file_base_name, all_content, all_unit_tests, integration_tests_content

def run_tests_and_generate_report(model, zip_file_base_name, all_unit_tests, integration_tests_content):
    # Add a conftest.py file for setting up the path
    extracted_files_path = Path("extracted_files")
    conftest_path = extracted_files_path / "conftest.py"
    with open(conftest_path, 'w', encoding='utf-8') as conftest_file:
        conftest_file.write(f"import sys\nsys.path.insert(0, '{extracted_files_path.parent}')\n")

    work_dir = Path("/Users/nboddu/Desktop/Experiment/python/")
    work_dir.mkdir(exist_ok=True)

    requirements_command = f"pip install -r extracted_files/{zip_file_base_name}/requirements.txt"
    unit_test_command = "pytest --cov=extracted_files --cov-report=term-missing extracted_files/tests/unit -vv -r a --disable-warnings > unit_test_coverage.txt"
    integration_test_command = "pytest --cov=extracted_files --cov-report=term-missing extracted_files/tests/integration -vv -r a --disable-warnings > integration_test_coverage.txt"
    
    # Install the dependencies
    requirements_code_block = CodeBlock(language="sh", code=requirements_command)
    requirements_executor = LocalCommandLineCodeExecutor(work_dir=work_dir)
    requirements_coverage = requirements_executor.execute_code_blocks(code_blocks=[requirements_code_block])

    # Execute unit tests
    unit_code_block = CodeBlock(language="sh", code=unit_test_command)
    unit_executor = LocalCommandLineCodeExecutor(work_dir=work_dir)
    unit_coverage = unit_executor.execute_code_blocks(code_blocks=[unit_code_block])

    # Execute integration tests
    integration_code_block = CodeBlock(language="sh", code=integration_test_command)
    integration_executor = LocalCommandLineCodeExecutor(work_dir=work_dir)
    integration_coverage = integration_executor.execute_code_blocks(code_blocks=[integration_code_block])

    # Read the coverage report from the file
    print(requirements_coverage)

    unit_coverage_report_path = work_dir / "unit_test_coverage.txt"
    with open(unit_coverage_report_path, 'r', encoding='utf-8') as unit_coverage_file:
        unit_coverage = unit_coverage_file.read()

    integration_coverage_report_path = work_dir / "integration_test_coverage.txt"
    with open(integration_coverage_report_path, 'r', encoding='utf-8') as integration_coverage_file:
        integration_coverage = integration_coverage_file.read()

    print(f"unit test coverage report :\n {unit_coverage}")
    print("*" * 150)
    print(f"integration test coverage report :\n {integration_coverage}")
    
    # Generate unit test report
    unit_report_generation_agent = Agent(
        role='Technical analyst',
        goal='Generate an execution report based on the coverage report.',
        backstory=generate_unit_report_prompt(all_unit_tests, unit_coverage),
        verbose=True,
        llm=openai_model,
        allow_delegation=False
    )
    
    unit_report_generation_task = Task(
        description=("You are a technical analyst, so generate the report in an understandable format."),
        expected_output=(
            "Business level unit test report"
        ),
        async_execution=False,
        agent=unit_report_generation_agent,
        output_file='outputs/report_unit.txt'
    )

    # Generate integration test report
    integration_report_generation_agent = Agent(
        role='Technical analyst',
        goal='Generate an execution report based on the coverage report.',
        backstory=generate_integration_report_prompt(integration_tests_content, integration_coverage),
        verbose=True,
        llm=openai_model,
        allow_delegation=False
    )
    
    integration_report_generation_task = Task(
        description=("You are a technical analyst, so generate the report in an understandable format."),
        expected_output=(
            "Business level integration test report"
        ),
        async_execution=False,
        agent=integration_report_generation_agent,
        output_file='outputs/report_integration.txt'
    )

    my_crew = Crew(
        agents=[unit_report_generation_agent, integration_report_generation_agent],
        tasks=[unit_report_generation_task, integration_report_generation_task],
        process=Process.sequential,
        full_output=True,
        memory=True,
        verbose=True
        # output_log_file=True
    )
    
    my_crew.kickoff()
    # print(result)

# Main execution
def main():
    zip_file_path = '/Users/nboddu/Desktop/zip_files/HTML_Table_to_List.zip'
    files_for_unit_tests = []
    model_name = 'claude_model'  
    # model_name = 'openai_model' 
    model = globals()[model_name]  

    zip_file_base_name, file_summaries, all_unit_tests, integration_tests_content = process_zip_file(zip_file_path, model, files_for_unit_tests)

    # Print the summaries and generated unit tests
    for file_path, content in file_summaries.items():
        print(f"File: {file_path}")
        print(f"Summary: {content['summary']}")
        if 'unit_tests' in content:
            print(f"Unit Tests: {content['unit_tests']}")
        if 'integration_tests' in content:
            print(f"Integration Tests: {content['integration_tests']}")
        print("="*40)

    run_tests_and_generate_report(model, zip_file_base_name, all_unit_tests, integration_tests_content)

if __name__ == "__main__":
    main()




# export PYTHONPATH=$(pwd)/extracted_files