import os
import requests
import json
import time
import re

def call_grok_api(messages):
    """
    Calls the Grok-2 API with the given messages.

    Parameters:
        messages (list): A list of message dictionaries for the API.

    Returns:
        str: The content of the response from the Grok-2 model.
    """
    api_key = 'YOUR_API_KEY'  # Replace with your actual API key
    url = 'https://api.x.ai/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    data = {
        'messages': messages,
        'model': 'grok-beta',
        'stream': False,
        'temperature': 0
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content']
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")

def decompose_goal(goal):
    """
    Decomposes the user's goal into a list of subtasks using the Grok-2 model.

    Parameters:
        goal (str): The user's goal description.

    Returns:
        list: A list of subtasks extracted from the model's response.
    """
    system_message = {
        'role': 'system',
        'content': (
            'You are Grok, an AI assistant specializing in software development. '
            'Your capabilities include decomposing goals into subtasks, generating source code, '
            'creating and writing to files, and reading existing files. You do not perform compilation or deployment tasks. '
            'Your workflow involves generating code step by step, ensuring all code for a single script stays in one file, '
            'and writing a README with installation and deployment instructions.'
        )
    }
    user_message = {
        'role': 'user',
        'content': f'Please decompose the following software development goal into a list of actionable subtasks. '
                   f'Exclude any compilation or deployment tasks. Include the creation of a README with instructions.\n\n"{goal}"\n\n'
                   'Provide the subtasks in a numbered list.'
    }
    messages = [system_message, user_message]
    response = call_grok_api(messages)
    subtasks = parse_subtasks(response)
    return subtasks

def parse_subtasks(response):
    """
    Parses the subtasks from the Grok-2 API response.

    Parameters:
        response (str): The raw response from the Grok-2 model.

    Returns:
        list: A list of parsed subtasks.
    """
    subtasks = []
    lines = response.strip().split('\n')
    for line in lines:
        if line.strip():
            # Remove numbering if present
            task = line.strip()
            match = re.match(r'^\d+\.?\s*(.*)', task)
            if match:
                task = match.group(1).strip()
            subtasks.append(task)
    return subtasks

def execute_subtasks(subtasks, project_folder):
    """
    Executes the list of subtasks step by step.

    Parameters:
        subtasks (list): A list of subtasks to execute.
        project_folder (str): The path to the project folder.

    Returns:
        list: A log of execution details for each subtask.
    """
    logs = []
    for i, subtask in enumerate(subtasks):
        print(f"\nExecuting subtask {i+1}/{len(subtasks)}: {subtask}")
        logs.append(f"Subtask {i+1}: {subtask}")
        # Determine if the subtask needs model interaction
        needs_model_interaction = determine_model_interaction(subtask)
        if needs_model_interaction:
            try:
                result = execute_subtask_with_model(subtask, project_folder)
                logs.append(f"Result: {result}")
            except Exception as e:
                logs.append(f"Failed to execute subtask: {e}")
                print(f"Failed to execute subtask {i+1}: {e}")
                continue
        else:
            try:
                result = execute_subtask_directly(subtask, project_folder)
                logs.append(f"Result: {result}")
            except Exception as e:
                logs.append(f"Failed to execute subtask: {e}")
                print(f"Failed to execute subtask {i+1}: {e}")
    return logs

def determine_model_interaction(subtask):
    """
    Determines if the subtask requires model interaction.

    Parameters:
        subtask (str): The subtask description.

    Returns:
        bool: True if model interaction is needed, False otherwise.
    """
    # Assume that all code generation and documentation tasks require model interaction
    keywords = ['generate', 'create', 'write', 'implement', 'develop', 'code', 'design', 'readme', 'documentation']
    for keyword in keywords:
        if keyword in subtask.lower():
            return True
    return False

def execute_subtask_with_model(subtask, project_folder):
    """
    Executes a subtask that requires model interaction.

    Parameters:
        subtask (str): The subtask description.
        project_folder (str): The path to the project folder.

    Returns:
        str: Confirmation message after execution.
    """
    # Prepare the context by reading any existing files if needed
    existing_files = {}
    for filename in os.listdir(project_folder):
        file_path = os.path.join(project_folder, filename)
        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_files[filename] = f.read()

    context = ""
    if existing_files:
        context = "Here are the current files in the project:\n"
        for filename, content in existing_files.items():
            context += f"\nFilename: {filename}\nContent:\n```\n{content}\n```\n"

    system_message = {
        'role': 'system',
        'content': (
            'You are Grok, an AI assistant specializing in software development. '
            'Your capabilities include generating source code, creating and writing to files, and reading existing files. '
            'You do not perform compilation or deployment tasks. '
            'Ensure all code for a single script stays in one file, and write a README with installation and deployment instructions. '
            'When providing code, output it within markdown code blocks and specify the filename. '
            'Use temporary filenames with a "_temp" suffix if the code is incomplete and will be completed in later steps.'
        )
    }
    user_message = {
        'role': 'user',
        'content': f'Please assist with the following subtask:\n\n"{subtask}"\n\n{context}'
    }
    messages = [system_message, user_message]
    response = call_grok_api(messages)
    print(f"Subtask result:\n{response}")
    save_code_from_response(response, project_folder)
    return "Subtask executed with model assistance."

def save_code_from_response(response, project_folder):
    """
    Parses code blocks from the model's response and saves them as files in the project folder.

    Parameters:
        response (str): The response from the Grok-2 model.
        project_folder (str): The path to the project folder.
    """
    code_blocks = re.findall(r'```(?:\w*\n)?(.*?)```', response, re.DOTALL)
    filenames = re.findall(r'Filename:\s*(.+)', response)

    if not code_blocks:
        print("No code blocks found in the response.")
        return

    for i, code in enumerate(code_blocks):
        # Determine the filename
        if i < len(filenames):
            filename = filenames[i].strip()
        else:
            # Default filename if not specified
            filename = f"file_{i+1}.py"

        # Ensure filename does not traverse directories
        filename = os.path.basename(filename)

        # Handle temporary files
        if '_temp' in filename:
            full_path = os.path.join(project_folder, filename)
            # Append code to the temp file
            with open(full_path, 'a', encoding='utf-8') as f:
                f.write(code)
            print(f"Appended code to temporary file: {full_path}")
        else:
            full_path = os.path.join(project_folder, filename)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(code)
            print(f"Saved code to {full_path}")

def execute_subtask_directly(subtask, project_folder):
    """
    Executes a subtask that does not require model interaction.

    Parameters:
        subtask (str): The subtask description.
        project_folder (str): The path to the project folder.

    Returns:
        str: A confirmation message after execution.
    """
    print(f"Directly executing subtask: {subtask}")
    # Simulate execution time
    time.sleep(1)
    return f"Executed subtask directly: {subtask}"

def create_project_folder(goal):
    """
    Creates a project folder in the current directory based on the goal.

    Parameters:
        goal (str): The user's goal description.

    Returns:
        str: The path to the created project folder.
    """
    # Create a safe folder name from the goal
    folder_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', goal)[:50]
    project_folder = os.path.join(os.getcwd(), folder_name)
    os.makedirs(project_folder, exist_ok=True)
    print(f"Created project folder at: {project_folder}")
    return project_folder

def main():
    """
    Main function to run the autonomous AI agent.
    """
    # Receive user goal
    goal = input("Please enter your software development goal:\n")
    # Create project folder
    project_folder = create_project_folder(goal)
    print("\nDecomposing goal into subtasks...")
    # Decompose goal into subtasks
    subtasks = decompose_goal(goal)
    print("\nSubtasks:")
    for i, subtask in enumerate(subtasks):
        print(f"{i+1}. {subtask}")
    # Execute subtasks
    logs = execute_subtasks(subtasks, project_folder)
    # Provide final result
    print("\nAll subtasks executed.")
    print("\nExecution logs:")
    for log in logs:
        print(log)
    print(f"\nYour project files are located in: {project_folder}")

if __name__ == "__main__":
    main()
