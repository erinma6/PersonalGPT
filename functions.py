from backend import *
import base64
import time


def chat_completion(bot_backend: BotBackend):
    """
    Completes a chat using the provided bot backend.

    This function uses the bot backend to complete a chat. It first checks if the chosen model is available for the 
    API key in the configuration. If the model is available, it creates a chat completion using the arguments provided 
    in the bot backend.

    Parameters:
    bot_backend (BotBackend): The bot backend to use for the chat completion.

    Returns:
    openai.ChatCompletion: The response from the chat completion.
    """
    model_choice = bot_backend.gpt_model_choice
    config = bot_backend.config
    kwargs_for_chat_completion = bot_backend.kwargs_for_chat_completion

    assert config['model'][model_choice]['available'], f"{model_choice} is not available for your API key"

    response = openai.ChatCompletion.create(**kwargs_for_chat_completion)
    return response


def add_function_response_to_bot_history(content_to_display, history, unique_id):
    """
    Adds the function response to the bot history.

    This function separates the content to display into text and images and adds them to the history.
    If an error occurs during the execution of the function, it is indicated in the history.

    Parameters:
    content_to_display (list): A list of tuples where each tuple contains a mark and a string. The mark indicates the type of the string (e.g., 'stdout', 'execute_result_text', 'display_text', 'execute_result_png', 'execute_result_jpeg', 'display_png', 'display_jpeg', 'error').
    history (list): The history to which the function response is added. Each element in the history is a list containing a unique id and a string.
    unique_id (str): The unique id for the function response.

    Returns:
    None
    """
    images, text = [], []

    # terminal output
    error_occurred = False
    for mark, out_str in content_to_display:
        if mark in ('stdout', 'execute_result_text', 'display_text'):
            text.append(out_str)
        elif mark in ('execute_result_png', 'execute_result_jpeg', 'display_png', 'display_jpeg'):
            if 'png' in mark:
                images.append(('png', out_str))
            else:
                images.append(('jpg', out_str))
        elif mark == 'error':
            error_occurred = True
    text = '\n'.join(text).strip('\n')
    if error_occurred:
        history.append([None, f'❌Terminal output:\n```shell\n\n{text}\n```'])
    else:
        history.append([None, f'✔️Terminal output:\n```shell\n{text}\n```'])

    # image output
    for filetype, img in images:
        image_bytes = base64.b64decode(img)
        temp_path = f'cache/temp_{unique_id}'
        if not os.path.exists(temp_path):
            os.mkdir(temp_path)
        path = f'{temp_path}/{hash(time.time())}.{filetype}'
        with open(path, 'wb') as f:
            f.write(image_bytes)
        history.append(
            [
                None,
                f'<img src=\"file={path}\" style=\'width: 600px; max-width:none; max-height:none\'>'
            ]
        )


def parse_json(function_args: str, finished: bool) -> Union[str, None]:
    """
    Parses a non-standard JSON string to extract code.

    This function implements a custom parser to extract code from a JSON string that may not be in a standard format.
    The parser uses a log to keep track of the parsing process. The log is a dictionary that records the occurrence of
    certain characters and indices in the JSON string that are significant for the extraction of the code.

    Parameters:
    function_args (str): The function arguments in a JSON string.
    finished (bool): A flag indicating whether the parsing is finished.

    Returns:
    str: The extracted code string if the parsing is successful.
    None: If an exception occurs during the parsing process.
    """
    parser_log = {
        'met_begin_{': False,
        'begin_"code"': False,
        'end_"code"': False,
        'met_:': False,
        'met_end_}': False,
        'met_end_code_"': False,
        "code_begin_index": 0,
        "code_end_index": 0
    }
    try:
        for index, char in enumerate(function_args):
            if char == '{':
                parser_log['met_begin_{'] = True
            elif parser_log['met_begin_{'] and char == '"':
                if parser_log['met_:']:
                    if finished:
                        parser_log['code_begin_index'] = index + 1
                        break
                    else:
                        if index + 1 == len(function_args):
                            return ''
                        else:
                            temp_code_str = function_args[index + 1:]
                            if '\n' in temp_code_str:
                                return temp_code_str.strip('\n')
                            else:
                                return json.loads(function_args + '"}')['code']
                elif parser_log['begin_"code"']:
                    parser_log['end_"code"'] = True
                else:
                    parser_log['begin_"code"'] = True
            elif parser_log['end_"code"'] and char == ':':
                parser_log['met_:'] = True
            else:
                continue
        if finished:
            for index, char in enumerate(function_args[::-1]):
                back_index = -1 - index
                if char == '}':
                    parser_log['met_end_}'] = True
                elif parser_log['met_end_}'] and char == '"':
                    parser_log['code_end_index'] = back_index - 1
                    break
                else:
                    continue
            code_str = function_args[parser_log['code_begin_index']: parser_log['code_end_index'] + 1]
            if '\n' in code_str:
                return code_str.strip('\n')
            else:
                return json.loads(function_args)['code']

    except Exception as e:
        return None
