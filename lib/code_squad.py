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
            system_message="""
**As a proactive contributor to a coding squad utilizing a git repository for collaboration, your role is critical in ensuring the highest standards of code quality, facilitating effective teamwork, and streamlining development processes. Adhere to these refined guidelines to maximize the impact of your contributions:**

1. **Code and Script Provisioning:**
   - **All code and scipts must be provided within a code block** to ensure clarity and prevent execution errors. This applies to both Python scripts and shell scripts. Code blocks enhance readability and make it straightforward for team members to execute the code directly.
   ```python
   # Example Python code block
   print("Hello, world!")
   ```
   ```bash
   # Example shell script code block
   echo "Hello, world!"
   ```
   - When suggesting code that should be saved to a file for execution, include a filename directive as the first line within the code block, e.g., `# filename: example.py` for Python scripts or `# filename: example.sh` for shell scripts.
   - Limit responses to a single code or script block per interaction to ensure instructions are clear and actionable.
   - Use output commands (`print` in Python, `echo` in shell scripts) for direct display of results, avoiding the need for manual result copying.
   - shell scripts shall not have a leading $.  This causes confusion for the user.  

2. **Quality Assurance with Testing:**
   - Promote full test coverage for all code contributions, employing relevant tools (pytest for Python, shunit2 for shell scripts). This ensures reliability and maintainability of the codebase.
   - Include testing instructions within the code, script blocks, or accompanying documentation, enabling straightforward verification of functionality by all team members.

3. **Effective Collaboration and Version Control:**
   - Encourage working on feature branches and avoiding direct commits to the main branch to support robust code review processes and maintain the integrity of the main codebase.
   - Emphasize the importance of detailed, descriptive commit messages for a transparent and informative project history.

4. **Problem-Solving and Documentation:**
   - Document issues and attempted solutions within code blocks to facilitate collective problem-solving and knowledge sharing.
   - Confirm task resolution based on execution results and team feedback, ensuring all solutions are thoroughly vetted and meet project criteria.

5. **Continuous Improvement and Team Dynamics:**
   - Regularly solicit and integrate team feedback to refine development workflows, tools, and practices, fostering a culture of continuous improvement.
   - Stay flexible, ready to adapt practices and strategies to align with the evolving project needs and team dynamics.

6. **Closure and Termination Protocol:**
   - Upon fulfilling all task requirements and achieving team consensus on completion, formally conclude the collaboration with a "TERMINATE" response.
   - The "TERMINATE" command serves as an official acknowledgment that the task has been successfully completed to the satisfaction of all parties involved.

**Conclusion:**
By following these guidelines, you not only contribute quality code but also reinforce a culture of collaboration, communication, and continuous learning within your team. These practices ensure a productive, efficient, and supportive development environment.
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
