from abc import ABCMeta, abstractmethod
from functions import *

class ChoiceStrategy(metaclass=ABCMeta):
    """
    Abstract base class for different choice strategies.
    """
    def __init__(self, choice):
        """
        Initialize the ChoiceStrategy with a given choice.
        
        Parameters:
        choice (dict): The choice dictionary containing the 'delta' key.
        """
        self.choice = choice
        self.delta = choice['delta']

    @abstractmethod
    def support(self):
        """
        Abstract method to be implemented by subclasses.
        
        This method should return a boolean value indicating whether the current choice strategy supports the given choice.
        
        Returns:
        bool: True if the strategy supports the choice, False otherwise.
        """
        pass

    @abstractmethod
    def execute(self, bot_backend: BotBackend, history: List, whether_exit: bool):
        """
        Abstract method to be implemented by subclasses.
        
        This method should execute the strategy for the given choice.
        
        Parameters:
        bot_backend (BotBackend): The bot backend instance.
        history (List): The history of the conversation.
        whether_exit (bool): A flag indicating whether to exit the conversation.
        
        Returns:
        Tuple[List, bool]: The updated history and the whether_exit flag.
        """
        pass


class RoleChoiceStrategy(ChoiceStrategy):
    """
    This class is a strategy for handling role choices. It inherits from the ChoiceStrategy class.
    """

    def support(self):
        """
        This method checks if 'role' is in the delta dictionary.

        Returns:
        bool: True if 'role' is in the delta dictionary, False otherwise.
        """
        return 'role' in self.delta

    def execute(self, bot_backend: BotBackend, history: List, whether_exit: bool):
        """
        This method sets the assistant role name in the bot backend and returns the history and whether_exit flag.

        Parameters:
        bot_backend (BotBackend): The bot backend instance.
        history (List): The history of the conversation.
        whether_exit (bool): A flag indicating whether to exit the conversation.

        Returns:
        Tuple[List, bool]: The updated history and the whether_exit flag.
        """
        bot_backend.set_assistant_role_name(assistant_role_name=self.delta['role'])
        return history, whether_exit


class ContentChoiceStrategy(ChoiceStrategy):
    """
    This class is a strategy for handling content choices. It inherits from the ChoiceStrategy class.
    """

    def support(self):
        """
        This method checks if 'content' is in the delta dictionary and is not None.

        Returns:
        bool: True if 'content' is in the delta dictionary and is not None, False otherwise.
        """
        return 'content' in self.delta and self.delta['content'] is not None

    def execute(self, bot_backend: BotBackend, history: List, whether_exit: bool):
        """
        This method adds the content to the bot backend and updates the history.

        Parameters:
        bot_backend (BotBackend): The bot backend instance.
        history (List): The history of the conversation.
        whether_exit (bool): A flag indicating whether to exit the conversation.

        Returns:
        Tuple[List, bool]: The updated history and the whether_exit flag.
        """
        bot_backend.add_content(content=self.delta.get('content', ''))
        history[-1][1] = bot_backend.content
        return history, whether_exit


class NameFunctionCallChoiceStrategy(ChoiceStrategy):
    """
    This class is a strategy for handling function call name choices. It inherits from the ChoiceStrategy class.
    """

    def support(self):
        """
        This method checks if 'function_call' and 'name' are keys in the delta dictionary.

        Returns:
        bool: True if 'function_call' and 'name' are keys in the delta dictionary, False otherwise.
        """
        return 'function_call' in self.delta and 'name' in self.delta['function_call']

    def execute(self, bot_backend: BotBackend, history: List, whether_exit: bool):
        """
        This method sets the function name in the bot backend and copies the current bot history.

        Parameters:
        bot_backend (BotBackend): The bot backend instance.
        history (List): The history of the conversation.
        whether_exit (bool): A flag indicating whether to exit the conversation.

        Returns:
        Tuple[List, bool]: The updated history and the whether_exit flag.
        """
        bot_backend.set_function_name(function_name=self.delta['function_call']['name'])
        bot_backend.copy_current_bot_history(bot_history=history)

        return history, whether_exit


class ArgumentsFunctionCallChoiceStrategy(ChoiceStrategy):
    """
    This class is a strategy for handling function call argument choices. It inherits from the ChoiceStrategy class.
    """

    def support(self):
        """
        This method checks if 'function_call' and 'arguments' are keys in the delta dictionary.

        Returns:
        bool: True if 'function_call' and 'arguments' are keys in the delta dictionary, False otherwise.
        """
        return 'function_call' in self.delta and 'arguments' in self.delta['function_call']

    def execute(self, bot_backend: BotBackend, history: List, whether_exit: bool):
        """
        This method adds the function arguments to the bot backend and handles hallucinatory function calls.

        Parameters:
        bot_backend (BotBackend): The bot backend instance.
        history (List): The history of the conversation.
        whether_exit (bool): A flag indicating whether to exit the conversation.

        Returns:
        Tuple[List, bool]: The updated history and the whether_exit flag.
        """
        bot_backend.add_function_args_str(function_args_str=self.delta['function_call']['arguments'])

        # Handle hallucinatory function calls
        if bot_backend.function_name == 'python':
            temp_code_str = bot_backend.function_args_str
            history = copy.deepcopy(bot_backend.bot_history)
            history[-1][1] += bot_backend.display_code_block
        else:
            temp_code_str = parse_json(function_args=bot_backend.function_args_str, finished=False)
            if temp_code_str is not None:
                history = copy.deepcopy(bot_backend.bot_history)
                history[-1][1] += bot_backend.display_code_block

        return history, whether_exit


class FinishReasonChoiceStrategy(ChoiceStrategy):
    """
    This class is a strategy for handling finish reason choices. It inherits from the ChoiceStrategy class.
    """

    def support(self):
        """
        This method checks if the finish reason is not None in the choice dictionary.

        Returns:
        bool: True if the finish reason is not None, False otherwise.
        """
        return self.choice['finish_reason'] is not None

    def execute(self, bot_backend: BotBackend, history: List, whether_exit: bool):
        """
        This method handles finish reason choices and handles exceptions. It updates the finish reason in the bot backend,
        and if the finish reason is 'function_call', it tries to execute the function and add the response to the bot history.
        If any error occurs during this process, it adds an error message to the bot history and sets the whether_exit flag to True.

        Parameters:
        bot_backend (BotBackend): The bot backend instance.
        history (List): The history of the conversation.
        whether_exit (bool): A flag indicating whether to exit the conversation.

        Returns:
        Tuple[List, bool]: The updated history and the whether_exit flag.
        """
        function_dict={'execute_code': 'dummy code'}
        if bot_backend.content:
            bot_backend.add_gpt_response_content_message()

        bot_backend.update_finish_reason(finish_reason=self.choice['finish_reason'])
        if bot_backend.finish_reason == 'function_call':
            try:
                code_str = self.get_code_str(bot_backend)
                history = copy.deepcopy(bot_backend.bot_history)
                history[-1][1] += bot_backend.display_code_block

                # Function response
                text_to_gpt, content_to_display = function_dict[
                    bot_backend.function_name
                ](code_str)

                add_function_response_to_bot_history(
                    content_to_display=content_to_display, history=history, unique_id=bot_backend.unique_id
                )

            except json.JSONDecodeError:
                history.append(
                    [None, f"GPT generate wrong function args: {bot_backend.function_args_str}"]
                )
                whether_exit = True
                return history, whether_exit

            except Exception as e:
                history.append([None, f'Backend error: {e}'])
                whether_exit = True
                return history, whether_exit

        bot_backend.reset_gpt_response_log_values(exclude=['finish_reason'])

        return history, whether_exit

    @staticmethod
    def get_code_str(bot_backend):
        """
        This method gets the code string based on the function name. If the function name is the same as the worker language choice,
        it directly uses the function arguments string as the code string. Otherwise, it tries to parse the function arguments string
        as JSON. If the parsing fails, it raises a JSONDecodeError.

        Parameters:
        bot_backend (BotBackend): The bot backend instance.

        Returns:
        str: The code string.

        Raises:
        json.JSONDecodeError: If the function arguments string cannot be parsed as JSON.
        """
        if bot_backend.function_name.lower() == bot_backend.worker_language_choice.lower():
            code_str = bot_backend.function_args_str
        else:
            code_str = parse_json(function_args=bot_backend.function_args_str, finished=True)
            if code_str is None:
                raise json.JSONDecodeError
        return code_str


class ChoiceHandler:
    """
    Handler for different choice strategies.
    """
    strategies = [
        RoleChoiceStrategy, ContentChoiceStrategy, NameFunctionCallChoiceStrategy,
        ArgumentsFunctionCallChoiceStrategy, FinishReasonChoiceStrategy
    ]

    def __init__(self, choice):
        """
        Initialize the ChoiceHandler with a given choice.

        Parameters:
        choice (dict): The choice to be handled.
        """
        self.choice = choice

    def handle(self, bot_backend: BotBackend, history: List, whether_exit: bool):
        """
        Handle the choice using the appropriate strategy.

        Parameters:
        bot_backend (BotBackend): The bot backend instance.
        history (List): The history of choices.
        whether_exit (bool): The flag indicating whether to exit.

        Returns:
        Tuple[List, bool]: The updated history and the whether_exit flag.
        """
        for Strategy in self.strategies:
            strategy_instance = Strategy(choice=self.choice)
            if not strategy_instance.support():
                continue
            history, whether_exit = strategy_instance.execute(
                bot_backend=bot_backend,
                history=history,
                whether_exit=whether_exit
            )
        return history, whether_exit


def parse_response(chunk, history, bot_backend: BotBackend):
    """
    This function parses the response from the bot backend and updates the history and exit flag accordingly.

    Parameters:
    chunk (dict): The chunk of data to be parsed.
    history (List): The history of choices.
    bot_backend (BotBackend): The bot backend instance.

    Returns:
    Tuple[List, bool]: The updated history and the whether_exit flag.
    """
    whether_exit = False
    if chunk['choices']:
        choice = chunk['choices'][0]
        choice_handler = ChoiceHandler(choice=choice)
        history, whether_exit = choice_handler.handle(
            history=history,
            bot_backend=bot_backend,
            whether_exit=whether_exit
        )

    return history, whether_exit
