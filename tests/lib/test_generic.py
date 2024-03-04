import pytest
import autogen
import os


@pytest.fixture()
def config_list():
    yield [
        {
            "model": "some-model",
            "base_url": "http://host.docker.internal:1234/v1",
            "api_type": "openai",
            "api_key": "not-needed",
        }
    ]


@pytest.fixture()
def cache_seed():
    yield None


@pytest.fixture()
def code_execution_config():
    yield {
        "work_dir": ".data",
        "use_docker": False,
    }


@pytest.fixture()
def create_assistant(config_list, cache_seed):
    def _create_assistant(temperature=0.2, timeout=300):
        return autogen.AssistantAgent(
            name="assistant",
            llm_config={
                "config_list": config_list,
                "cache_seed": cache_seed,
                "temperature": temperature,
                "timeout": timeout,
            },
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
Reply "TERMINATE" in the end when everything is done.
""",
        )

    yield _create_assistant


@pytest.fixture()
def create_user_proxy(config_list, cache_seed, code_execution_config):
    def _create_user_proxy(temperature=0.9, timeout=300):
        return autogen.UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: x.get("content", "")
            .rstrip()
            .endswith("TERMINATE"),
            code_execution_config=code_execution_config,
        )

    yield _create_user_proxy


def test_create_assistant(create_assistant):
    assistant = create_assistant()

    assert assistant


def test_create_user_proxy(create_user_proxy):
    user_proxy = create_user_proxy()

    assert user_proxy


def test_meta_tesla_ytd_stock(create_user_proxy, create_assistant):
    user_proxy = create_user_proxy()
    assistant = create_assistant()

    chat_res = user_proxy.initiate_chat(
        assistant,
        message="""What date is today? Compare the year-to-date gain for META and TESLA.""",
        summary_method="reflection_with_llm",
    )

    assert chat_res


def test_simple_function(create_user_proxy, create_assistant, code_execution_config):
    user_proxy = create_user_proxy()
    assistant = create_assistant()

    file_name = "adder.py"

    chat_res = user_proxy.initiate_chat(
        assistant,
        message=f"""create a python function that adds two numbers.  Write this function to a file called {file_name}""",
        summary_method="reflection_with_llm",
    )

    assert chat_res
    assert os.path.isfile(f"{code_execution_config['work_dir']}/{file_name}")


class PokerPlayer:
    def __init__(self, name, config_list):
        if not name or not isinstance(config_list, list):
            raise ValueError("Name must be a string and config_list must be a list.")
        self.name = name
        self.setup_agents(config_list)
        self.setup_group_chat(config_list)

    def setup_agents(self, config_list):
        self.user_proxy = autogen.UserProxyAgent(
            name=self.name,
            system_message="Your strategy should balance logic with emotion. After considering the game state, format your decision as follows: {'action': '<ACTION>', 'amount': <AMOUNT>, 'chat': '<MESSAGE>'}.",
            llm_config={"config_list": config_list},
        )
        self.logic = autogen.AssistantAgent(
            name="logic",
            system_message="Analyze the current hand and suggest a logical action. Consider the odds and other players' potential hands.",
            llm_config={"config_list": config_list},
        )
        self.emotion = autogen.AssistantAgent(
            name="emotion",
            system_message="Reflect on the game's emotional aspect. How does the current state affect your decision? Share your feelings.",
            llm_config={"config_list": config_list},
        )

    def setup_group_chat(self, config_list):
        self.groupchat = autogen.GroupChat(
            agents=[self.user_proxy, self.logic, self.emotion],
            messages=[],
            max_round=12,
        )
        self.manager = autogen.GroupChatManager(
            groupchat=self.groupchat,
            llm_config={"config_list": config_list},
        )

    def decide_move(self, context):
        initial_message = f"{self.name}, it's your turn. Here's the game state: {context}. How will you play your hand?"
        self.user_proxy.initiate_chat(self.manager, message=initial_message)

    # Implement the method to process and integrate decisions from logic and emotion agents
    def process_decision(self):
        # Placeholder for decision processing logic
        pass
