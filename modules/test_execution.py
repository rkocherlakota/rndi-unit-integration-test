from pathlib import Path
from autogen.coding import CodeBlock, LocalCommandLineCodeExecutor
from crewai import Agent, Task, Crew, Process
from prompts import generate_unit_report_prompt, generate_integration_report_prompt
from model import openai_model, claude_model

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