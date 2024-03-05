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
def working_dir():
    dir = ".data"

    os.makedirs(dir, exist_ok=True)
    for filename in os.listdir(dir):
        file_path = os.path.join(dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

    yield dir


@pytest.fixture()
def code_execution_config(working_dir):
    yield {
        "work_dir": working_dir,
        "use_docker": False,  # running code in a devcontainer
    }


@pytest.fixture()
def create_assistant(config_list, cache_seed):
    def _create_assistant(temperature=0, timeout=300):
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
You are not done until the user has confirmed that their needs have been met.  You do not reply TERMINATE until you have confirmation.
Reply "TERMINATE" once the user has confirmed that their needs have been met.
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


def test_adder_function(create_user_proxy, create_assistant, code_execution_config):
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


def test_adder_test_function(
    create_user_proxy, create_assistant, code_execution_config
):
    user_proxy = create_user_proxy()
    assistant = create_assistant()

    file_name = "adder.py"

    chat_res = user_proxy.initiate_chat(
        assistant,
        message=f"""create a test suite for a python function that adds two numbers.  Tests should be written in pytest.  These tests should have comprehensive coverage.  Write this function to a file called test_{file_name}""",
        summary_method="reflection_with_llm",
    )

    assert chat_res
    assert os.path.isfile(f"{code_execution_config['work_dir']}/test_{file_name}")
