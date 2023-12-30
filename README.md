# WizTalk

This is a Python package that provides a chatbot interface using OpenAI's GPT model. The chatbot, named Professor Synapse, is designed to support users in accomplishing their goals by finding alignment with them and calling upon an expert agent perfectly suited to the task.

This package inspired by and builds upon the work of [ProfSynapse](https://github.com/ProfSynapse/Synapse_CoR/tree/main) on GitHub.

## Files in this package

- `functional.py`: Contains functions for completing a chat using the provided bot backend, adding the function response to the bot history, and parsing a non-standard JSON string to extract code.

- `bot_backend.py`: Contains the BotBackend class which is responsible for managing the conversation with the GPT model. It also includes the GPTResponseLog class for logging the responses from the GPT model.

- `web_ui.py`: Contains functions for initializing the state dictionary, getting the bot backend from the state dictionary, adding text to the bot backend, restarting the UI, restarting the bot backend, and running the bot backend while the finish reason is 'new_input'.

- `response_parser.py`: Contains the ChoiceStrategy abstract base class and its subclasses for handling different choice strategies. It also includes the ChoiceHandler class for handling different choice strategies.

## Usage

To use this package, you need to have Python installed on your machine. You can then clone this repository and run the `web_ui.py` script to start the chatbot interface.

You will need an OpenAI key setup in your OS environment variables titled 'OPENAI_API_KEY'.

All necessary packages are stored in 'requirements_full.txt'