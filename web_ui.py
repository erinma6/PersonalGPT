from response_parser import *
import gradio as gr

# Initialize the state dictionary
def initialization(state_dict: Dict) -> None:
    """
    This function initializes the state dictionary and the bot backend.
    It also creates a cache directory if it doesn't exist and removes the OPENAI_API_KEY from the environment variables.

    Parameters:
    state_dict (Dict): The state dictionary to be initialized.

    Returns:
    None
    """
    # Create a cache directory if it doesn't exist
    if not os.path.exists('cache'):
        os.mkdir('cache')
    # Initialize the bot backend if it's not already initialized
    if state_dict["bot_backend"] is None:
        state_dict["bot_backend"] = BotBackend()
        # Remove the OPENAI_API_KEY from the environment variables
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']

# Get the bot backend from the state dictionary
def get_bot_backend(state_dict: Dict) -> BotBackend:
    """
    This function retrieves the bot backend from the state dictionary.
    If the bot backend is not already initialized, it initializes it and removes the OPENAI_API_KEY from the environment variables.

    Parameters:
    state_dict (Dict): The state dictionary from which the bot backend is retrieved.

    Returns:
    BotBackend: The bot backend retrieved from the state dictionary.
    """
    # Initialize the bot backend if it's not already initialized
    if state_dict["bot_backend"] is None:
        state_dict["bot_backend"] = BotBackend()
        # Remove the OPENAI_API_KEY from the environment variables
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']    
    return state_dict["bot_backend"]

# Add text to the bot backend
def add_text(state_dict: Dict, history: List, text: str) -> Tuple[List, Dict]:
    """
    This function adds a text message to the bot backend and updates the history.

    Parameters:
    state_dict (Dict): The state dictionary from which the bot backend is retrieved.
    history (List): The history of the conversation.
    text (str): The text message to be added.

    Returns:
    Tuple[List, Dict]: The updated history and a Gradio interface update.
    """
    bot_backend = get_bot_backend(state_dict)
    bot_backend.add_text_message(user_text=text)

    # Add the text to the history
    history = history + [(text, None)]

    return history, gr.update(value="", interactive=False)

# Restart the UI
def restart_ui(history: List) -> Tuple[List, Dict, Dict, Dict, Dict]:
    """
    This function restarts the user interface by clearing the history and resetting the interactive elements.

    Parameters:
    history (List): The history of the conversation.

    Returns:
    Tuple[List, Dict, Dict, Dict, Dict]: The cleared history and updates for the Gradio interface elements.
    """
    # Clear the history
    history.clear()
    return (
        history,
        gr.Textbox.update(value="", interactive=False),
        gr.Button.update(interactive=False),
        gr.Button.update(interactive=False),
        gr.Button.update(interactive=False)
    )

# Restart the bot backend
def restart_bot_backend(state_dict: Dict) -> None:
    """
    This function restarts the bot backend by calling the restart method of the bot backend.

    Parameters:
    state_dict (Dict): The state dictionary from which the bot backend is retrieved.

    Returns:
    None
    """
    bot_backend = get_bot_backend(state_dict)
    bot_backend.restart()

# Main bot function
def bot(state_dict: Dict, history: List) -> List:
    """
    This function runs the bot backend while the finish reason is 'new_input'. It gets the response from the chat completion,
    parses the response, updates the history, and yields the updated history. If the parsed response indicates to exit, the function
    will terminate with an exit code of -1.

    Parameters:
    state_dict (Dict): The state dictionary from which the bot backend is retrieved.
    history (List): The history of the conversation.

    Returns:
    List: The updated history of the conversation.
    """
    bot_backend = get_bot_backend(state_dict)

    # Keep running the bot while the finish reason is 'new_input'
    while bot_backend.finish_reason in ('new_input'):
        if history[-1][0] is None:
            history.append(
                [None, ""]
            )
        else:
            history[-1][1] = ""

        # Get the response from the chat completion
        response = chat_completion(bot_backend=bot_backend)
        # Parse the response and update the history
        for chunk in response:
            history, whether_exit = parse_response(
                chunk=chunk,
                history=history,
                bot_backend=bot_backend
            )
            yield history
            # Exit if the parsed response indicates to exit
            if whether_exit:
                exit(-1)

    yield history


# Main function
if __name__ == '__main__':
    """
    This is the main function that gets executed when the script is run directly.
    It gets the configuration, creates a Gradio interface, and starts the interface.
    """
    # Get the configuration
    config = get_config()
    # Create a Gradio interface
    with gr.Blocks(theme=gr.themes.Base()) as block:
        """
        Reference: https://www.gradio.app/guides/creating-a-chatbot-fast
        """
        # UI components
        state = gr.State(value={"bot_backend": None})
        with gr.Tab("WizTalk"):
            chatbot = gr.Chatbot([], elem_id="chatbot", label="Professor Synapse", show_label=False,height=550)
            with gr.Row():
                with gr.Column(scale=0.95):
                    text_box = gr.Textbox(
                        show_label=False,
                        placeholder="Enter text and press enter",
                        container=False
                    )
                
 
        # Components function binding
        txt_msg = text_box.submit(add_text, [state, chatbot, text_box], [chatbot, text_box], queue=False).then(
            bot, [state, chatbot], chatbot
        )
        
        txt_msg.then(lambda: gr.update(interactive=True), None, [text_box], queue=False)
        

        # Load the initialization function
        block.load(fn=initialization, inputs=[state])

    # Start the Gradio interface
    block.queue()
    block.launch(inbrowser=True)
