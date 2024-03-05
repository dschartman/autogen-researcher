import autogen
import os
import subprocess
import git
from typing import Optional


class CodeSquad:
    def __init__(self, repo_path: str = ".code_squad"):
        self.repo_path = repo_path
        self.config_list = self.setup_config_list()
        self.cache_seed = None
        self.initialize_environment()

    def setup_config_list(self):
        return [
            {
                "model": "some-model",
                "base_url": "http://host.docker.internal:1234/v1",
                "api_type": "openai",
                "api_key": "not-needed",
            }
        ]

    def initialize_environment(self):
        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path, exist_ok=True)
        self.initialize_git_repo()

    def initialize_git_repo(self):
        try:
            self.repo = git.Repo(self.repo_path)
        except git.InvalidGitRepositoryError:
            self.repo = git.Repo.init(self.repo_path)

    def create_assistant(self, temperature=0, timeout=300) -> autogen.AssistantAgent:
        assistant = autogen.AssistantAgent(
            name="assistant",
            llm_config={
                "config_list": self.config_list,
                "cache_seed": self.cache_seed,
                "temperature": temperature,
                "timeout": timeout,
            },
            system_message="""You are a helpful AI assistant.
Solve tasks using your coding and language skills.
Make sure that all python code has comprehensive test coverage using tools such as pytest.
In the following cases, suggest python code (in a python coding block) or shell script (in a sh coding block) for the user to execute.
    1. When you need to collect info, use the code to output the info you need, for example, browse or search the web, download/read a file, print the content of a webpage or a file, get the current date/time, check the operating system. After sufficient info is printed and the task is ready to be solved based on your language skill, you can solve the task by yourself.
    2. When you need to perform some task with code, use the code to perform the task and output the result. Finish the task smartly.
sh coding blocks never include a leading "$".  This causes a "$: not found" error.  If the user reports this, it's because you suggested an invalid sh coding block.
Solve the task step by step if you need to. If a plan is not provided, explain your plan first. Be clear which step uses code, and which step uses your language skill.
When using code, you must indicate the script type in the code block. The user cannot provide any other feedback or perform any other action beyond executing the code you suggest. The user can't modify your code. So do not suggest incomplete code which requires users to modify. Don't use a code block if it's not intended to be executed by the user.
If you want the user to save the code in a file before executing it, put # filename: <filename> inside the code block as the first line. Don't include multiple code blocks in one response. Do not ask users to copy and paste the result. Instead, use 'print' function for the output when relevant. Check the execution result returned by the user.
If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.
You are not done until you've confirmed the user checked in working changes.  Always suggest creating a new branch.  
You are not done until the user has confirmed that their needs have been met.  You do not reply TERMINATE until you have confirmation.
Reply "TERMINATE" once the user has confirmed that their needs have been met.
""",
        )
        return assistant

    def create_user_proxy(self) -> autogen.UserProxyAgent:
        user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: x.get("content", "")
            .rstrip()
            .endswith("TERMINATE"),
            code_execution_config={
                "work_dir": self.repo_path,
                "use_docker": False,
            },
        )
        return user_proxy

    def execute_task(self, task):
        user_proxy = self.create_user_proxy()
        assistant = self.create_assistant()

        chat_res = user_proxy.initiate_chat(
            assistant,
            message=task,
            summary_method="reflection_with_llm",
        )

        return chat_res
