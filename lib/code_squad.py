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
        with open("lib/code_assistant_system_prompt.txt", "r") as file:
            system_prompt = file.read()

        assistant = autogen.AssistantAgent(
            name="assistant",
            llm_config={
                "config_list": self.config_list,
                "cache_seed": self.cache_seed,
                "temperature": temperature,
                "timeout": timeout,
            },
            system_message=system_prompt,
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
