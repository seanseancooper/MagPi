from app.server import start_flask
from pyngrok import ngrok

# Flag to control whether ngrok is used or not
USE_NGROK = False   # Set to True to enable ngrok
USE_OPENAI = False  # Set to True to enable openai

if __name__ == "__main__":
    if USE_NGROK:
        # Set up ngrok to expose Flask server
        public_url = ngrok.connect('8000')
        print(f" * ngrok tunnel \"{public_url}\" -> \"http://127.0.0.1:8000\"")
    else:
        print(" * Running Flask locally without ngrok.")

    # Pass the flag to Flask configuration
    from app.server import app

    # Configure Flask app to reflect ngrok status
    app.config['USE_NGROK'] = USE_NGROK
    app.config['USE_OPENAI'] = USE_OPENAI

    # Run the Flask app
    start_flask()
