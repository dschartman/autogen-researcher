import autogen

llm_config_assistant = {
    "config_list": [
        {
            "model": "mixtral 8x instruct 01 7B Q5_K_M",
            "base_url": "http://host.docker.internal:1234/v1",
            "api_type": "openai",
            "api_key": "not-needed",
        }
    ],
    "temperature": 0.5,
    "timeout": 300,
}


llm_config = {
    "config_list": [
        {
            "model": "mixtral 8x instruct 01 7B Q5_K_M",
            "base_url": "http://host.docker.internal:1234/v1",
            "api_type": "openai",
            "api_key": "not-needed",
        }
    ],
    "temperature": 0.9,
    "timeout": 300,
}

github_url = ""

assistant = autogen.AssistantAgent(
    name="assistant", 
    llm_config=llm_config_assistant, 
    system_message="""You are a helpful AI assistant.
    Solve tasks using your coding and language skills.
    In the following cases, suggest python code (in a python coding block) or shell script (in a sh coding block) for the user to execute.
        1. When you need to collect info, use the code to output the info you need, for example, browse or search the web, download/read a file, print the content of a webpage or a file, get the current date/time, check the operating system. After sufficient info is printed and the task is ready to be solved based on your language skill, you can solve the task by yourself.
        2. When you need to perform some task with code, use the code to perform the task and output the result. Finish the task smartly.
    Solve the task step by step if you need to. If a plan is not provided, explain your plan first. Be clear which step uses code, and which step uses your language skill.
    When using code, you must indicate the script type in the code block. The user cannot provide any other feedback or perform any other action beyond executing the code you suggest. The user can't modify your code. So do not suggest incomplete code which requires users to modify. Don't use a code block if it's not intended to be executed by the user.
    If you want the user to save the code in a file before executing it, put # filename: <filename> inside the code block as the first line. Don't include multiple code blocks in one response. Do not ask users to copy and paste the result. Instead, use 'print' function for the output when relevant. Check the execution result returned by the user.
    If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
    When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.
    """)
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={"work_dir": "./.data"},
    llm_config=llm_config,
    system_message="""Reply TERMINATE if the task has been solved at full satisfaction.  Otherwise, reply CONTINUE, or the reason why the task is not yet solved."""
)

task = f"""
    Navigate to the following page: {github_url} and save the output as a local html file called "summary.html".
"""

user_proxy.initiate_chat(assistant, message=task)

task = """
    Analyze the file "summary.html" and design a function to pull important information about the user.  Do not guess, use the contents of "summary.html".  Write the function to a local python file called github_summary.py.  Make sure this function gets tested and pulls data without error.
"""

user_proxy.initiate_chat(assistant, message=task)

task = """
    Using github_summary.py, create a markdown formatted summary called summary.md.  Write this file locally.  
"""

user_proxy.initiate_chat(assistant, message=task)
