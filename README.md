# Automating Software Testing Using GenAI

This project automates the generation, and execution of unit and integration tests for Python projects, followed by generating detailed test coverage reports.


## Project Structure

- `file_handling.py`: Handles file extraction, reading, processing of Python files, and test case generation.
- `business_logic.py`: Defines the logic for generating business summaries of Python files using LLM.
- `test_generation.py`: Defines the logic for generating unit and integration tests for the Python files using the LLM.
- `test_execution.py`: Responsible for executing the generated tests and generating a report.
- `main.py`: The main script that orchestrates the workflow.
- `prompts.py`: Contains the prompts used for generating business logic, test cases and report.
- `model.py`: Defines the LLMs used for generating summaries and test cases (`openai_model` and `claude_model`).


## Setup and Usage

### Extract Files, Generate Tests, Execute Tests and Generate Report
1. Ensure your Python project zip file path is specified correctly in `main.py`.
2. Run `main.py`. This will:
   - Extract the zip file to `extracted_files` directory.
   - Generate business logic summaries for each Python file.
   - Generate unit tests for specified files.
   - Generate an integration test for the project.
   - Save the summaries and test cases in the `outputs` directory.
   - Execute the generated unit and integration tests.
   - Test results and coverage reports will be saved in the `outputs` directory.


## Requirements

Ensure you have the following prerequisites before using the application:

- Python 3.x
- Claude API key
- OpenAI API Key
- Required Python libraries (specified in Requirements.txt)


## Getting Started

1. Clone this repository to your local machine.
2. Install the required Python libraries using `pip install -r requirements.txt`.
3. Obtain an API key for Claude and OpenAI model and set it as an environment variable (`ANTHROPIC_API_KEY` and `OPENAI_API_KEY`).
4. Run the application from the root folder using the command `python modules/main.py`.


## Output

- Business logic file: `outputs/context.txt`
- Unit Test Coverage Report: `outputs/report_unit.txt`
- Integration Test Coverage Report: `outputs/report_integration.txt`

Adjust paths as necessary to fit your local setup.
