from model import *
from file_handling import process_zip_file
from test_execution import run_tests_and_generate_report

def main():
    zip_file_path = '/Users/nboddu/Desktop/Desktop-Assistant-using-Python-main.zip'
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
