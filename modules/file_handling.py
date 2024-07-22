import os
import zipfile
from pathlib import Path
from business_logic import generate_business_logic
from test_generation import generate_unit_tests, generate_integration_tests, extract_tests, save_summaries

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