import gradio as gr
import requests

def ask_defgen(user_input):
    try:
        response = requests.post(
            "https://defgen-backend.onrender.com/chat",
            json={"message": user_input}
        )
        return response.json().get("response", "❌ No response returned.")
    except Exception as e:
        return f"❌ Error: {str(e)}"

gr.Interface(
    fn=ask_defgen,
    inputs="text",
    outputs="text",
    title="DEF-GEN: Indian Defence Chatbot",
    description="Ask anything about DRDO, SSB, Indian defence systems, missiles, or interviews.",
).launch(share=True)
