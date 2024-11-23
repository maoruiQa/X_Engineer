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

def determine_project_structure(goal):
    """
    Determines the project directory structure based on the user's goal.

    Parameters:
        goal (str): The user's goal description.

    Returns:
        dict: A dictionary representing the project structure.
    """
    system_message = {
        'role': 'system',
        'content': (
            'You are Grok, an AI assistant specializing in software development. '
            'Your capabilities include designing project directory structures based on user goals. '
            'Provide a clear and reasonable project directory structure for the given goal.'
        )
    }
    user_message = {
        'role': 'user',
        'content': f'Based on the following goal, please provide a reasonable project directory structure:\n\n"{goal}"\n\n'
                   'Provide the structure in a tree format.'
    }
    messages = [system_message, user_message]
    response = call_grok_api(messages)
    project_structure = parse_project_structure(response)
    return project_structure

def parse_project_structure(response):
    """
    Parses the project directory structure from the Grok-2 API response.

    Parameters:
        response (str): The raw response from the Grok-2 model.

    Returns:
        dict: A dictionary representing the project structure.
    """
    structure = {}
    lines = response.strip().split('\n')
    current_path = []
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue
        indent_level = len(line) - len(line.lstrip())
        depth = indent_level // 4  # Assuming 4 spaces per indent
        item = stripped_line.strip('/')

        # Update the current path based on depth
        current_path = current_path[:depth]
        current_path.append(item)

        # Build the nested dictionary
        d = structure
        for part in current_path[:-1]:
            d = d.setdefault(part, {})
        d[current_path[-1]] = {}
    return structure

def provide_example_subtasks(goal, project_structure):
    """
    Provides an example list of reasonable subtasks based on the goal and project structure.

    Parameters:
        goal (str): The user's goal description.
        project_structure (dict): The project directory structure.

    Returns:
        str: An example of reasonable subtasks.
    """
    example_subtasks = (
        f'Example based on the goal "{goal}":\n\n'
        '1. Create the project directory structure:\n'
        f'{format_structure(project_structure)}\n'
        '2. For each script or module in the structure, write code in manageable parts, ensuring that each part is complete and functional.\n'
        '3. Integrate the parts into complete scripts or modules.\n'
        '4. Write a README.md with installation and usage instructions.\n'
        '5. Create a requirements.txt file with necessary dependencies.\n'
        'Note: When generating code, control the amount to ensure it can be fully written with minimal errors.'
    )
    return example_subtasks

def format_structure(structure, indent=0):
    """
    Formats the project structure dictionary into a string.

    Parameters:
        structure (dict): The project directory structure.
        indent (int): Current indentation level.

    Returns:
        str: A formatted string representing the structure.
    """
    lines = []
    for key, value in structure.items():
        lines.append('    ' * indent + key + '/')
        if isinstance(value, dict):
            lines.extend(format_structure(value, indent + 1))
    return '\n'.join(lines)

def decompose_goal(goal, project_structure):
    """
    Decomposes the user's goal into a list of subtasks using the Grok-2 model.

    Parameters:
        goal (str): The user's goal description.
        project_structure (dict): The project directory structure.

    Returns:
        list: A list of subtasks extracted from the model's response.
    """
    example_subtasks = provide_example_subtasks(goal, project_structure)
    system_message = {
        'role': 'system',
        'content': (
            'You are Grok, an AI assistant specializing in software development. '
            'Your capabilities include decomposing goals into actionable subtasks. '
            'When generating code for a script, write code in manageable, complete parts, and then integrate them into a complete script. '
            'Control the code amount to ensure you can fully write it with minimal errors. '
            'First, determine the project directory structure before setting subtasks.'
        )
    }
    user_message = {
        'role': 'user',
        'content': (
            f'Based on the following goal and project directory structure, please decompose the goal into a list of actionable subtasks. '
            f'Ensure that the code amount in each subtask is manageable.\n\n'
            f'Goal:\n"{goal}"\n\n'
            f'Project Directory Structure:\n{format_structure(project_structure)}\n\n'
            f'{example_subtasks}\n\n'
            'Provide the subtasks in a numbered list.'
        )
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
            match = re.match(r'^\d+(\.\d+)*\.?\s*(.*)', task)
            if match:
                task = match.group(2).strip()
            subtasks.append(task)
    return subtasks

def execute_subtasks(subtasks, project_folder):
    """
    Executes the list of subtasks.

    Parameters:
        subtasks (list): A list of subtasks to execute.
        project_folder (str): The path to the project folder.

    Returns:
        list: A log of execution details for each subtask.
    """
    logs = []
    for subtask in subtasks:
        logs.extend(execute_subtask(subtask, project_folder))
    return logs

def execute_subtask(subtask, project_folder):
    """
    Executes a single subtask.

    Parameters:
        subtask (str): The subtask description.
        project_folder (str): The path to the project folder.

    Returns:
        list: A log of execution details for this subtask.
    """
    logs = []
    print(f"\nExecuting subtask: {subtask}")
    logs.append(f"Executing subtask: {subtask}")

    # Determine the action from the subtask
    action = determine_action(subtask)

    if action == 'model_interaction':
        try:
            result = execute_subtask_with_model(subtask, project_folder)
            logs.append(f"Result: {result}")
        except Exception as e:
            logs.append(f"Failed to execute subtask: {e}")
            print(f"Failed to execute subtask: {e}")
    elif action == 'file_operation':
        try:
            result = execute_file_operation(subtask, project_folder)
            logs.append(f"Result: {result}")
        except Exception as e:
            logs.append(f"Failed to execute subtask: {e}")
            print(f"Failed to execute subtask: {e}")
    else:
        try:
            result = execute_subtask_directly(subtask, project_folder)
            logs.append(f"Result: {result}")
        except Exception as e:
            logs.append(f"Failed to execute subtask: {e}")
            print(f"Failed to execute subtask: {e}")

    return logs

def determine_action(subtask):
    """
    Determines the action type required for the subtask.

    Parameters:
        subtask (str): The subtask description.

    Returns:
        str: 'model_interaction', 'file_operation', or 'direct_execution'
    """
    # Check for file operations
    file_operations = ['create', 'write', 'read', 'delete']
    for op in file_operations:
        if op in subtask.lower():
            return 'file_operation'
    # Check for code generation tasks
    code_keywords = ['generate code', 'implement', 'develop', 'write code', 'create script']
    for keyword in code_keywords:
        if keyword in subtask.lower():
            return 'model_interaction'
    return 'direct_execution'

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
    for root, dirs, files in os.walk(project_folder):
        for filename in files:
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, project_folder)
            if os.path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_files[rel_path] = f.read()

    context = ""
    if existing_files:
        context = "Here are the current files in the project:\n"
        for filename, content in existing_files.items():
            context += f"\nFilename: {filename}\nContent:\n```\n{content}\n```\n"

    system_message = {
        'role': 'system',
        'content': (
            'You are Grok, an AI assistant specializing in software development. '
            'Your capabilities include generating source code. '
            'When generating code for a script, write code in manageable, complete parts, and then integrate them into a complete script. '
            'Control the code amount to ensure you can fully write it with minimal errors. '
            'Avoid splitting functions or code sections into separate files unless they are meant to be standalone modules. '
            'Ensure that the code is complete and functional. '
            'When providing code, output it within markdown code blocks and specify the filename with its relative path.'
        )
    }
    user_message = {
        'role': 'user',
        'content': f'Please assist with the following task:\n\n"{subtask}"\n\n{context}'
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
    code_pattern = r'```(?:\w*\n)?(.*?)```'
    code_blocks = re.findall(code_pattern, response, re.DOTALL)
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
        filename = os.path.normpath(filename)
        if filename.startswith('..'):
            print(f"Invalid filename: {filename}")
            continue

        full_path = os.path.join(project_folder, filename)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        # Append code to the file
        with open(full_path, 'a', encoding='utf-8') as f:
            f.write(code)
        print(f"Saved code to {full_path}")

def execute_file_operation(subtask, project_folder):
    """
    Executes file operations like create, write, read, or delete files.

    Parameters:
        subtask (str): The subtask description.
        project_folder (str): The path to the project folder.

    Returns:
        str: Confirmation message after execution.
    """
    subtask_lower = subtask.lower()
    filename = extract_filename(subtask)

    if 'delete' in subtask_lower:
        if filename:
            file_path = os.path.join(project_folder, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
                return f"Deleted file: {filename}"
            else:
                return f"File {filename} does not exist."
        else:
            return "No filename specified for deletion."

    elif 'create' in subtask_lower:
        if filename:
            file_path = os.path.join(project_folder, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            open(file_path, 'w').close()
            print(f"Created empty file: {file_path}")
            return f"Created file: {filename}"
        else:
            return "No filename specified for creation."

    elif 'write' in subtask_lower or 'append' in subtask_lower:
        # For write operations, we may need model interaction
        return execute_subtask_with_model(subtask, project_folder)

    elif 'read' in subtask_lower:
        if filename:
            file_path = os.path.join(project_folder, filename)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"Content of {filename}:\n{content}")
                return f"Read content of {filename}"
            else:
                return f"File {filename} does not exist."
        else:
            return "No filename specified to read."

    else:
        return "File operation not recognized."

def extract_filename(subtask):
    """
    Extracts the filename from the subtask description.

    Parameters:
        subtask (str): The subtask description.

    Returns:
        str: The extracted filename, or None if not found.
    """
    match = re.search(r'file\s+([^\s]+)', subtask.lower())
    if match:
        return match.group(1)
    return None

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
    print("\nDetermining project directory structure...")
    # Determine project structure
    project_structure = determine_project_structure(goal)
    print("\nProject Directory Structure:")
    print(format_structure(project_structure))
    # Decompose goal into subtasks
    print("\nDecomposing goal into subtasks...")
    subtasks = decompose_goal(goal, project_structure)
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
