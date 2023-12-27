import gradio as gr

def chatbot_model(input_text):
    # This is where you would call your chatbot model and return the response
    # For the sake of this example, we'll just echo back the input text
    return f"Chatbot response: {input_text}"

iface = gr.Interface(fn=chatbot_model, 
                     inputs=gr.Textbox(lines=2, placeholder='Type something here...'), 
                     outputs="text",
                     title="Simple Chatbot")


iface.launch()