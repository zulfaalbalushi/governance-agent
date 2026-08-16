from flask import Flask, render_template, request, jsonify
from query import get_answer 


# Creates the app
app = Flask(__name__)

# Defines the route using a decorator: a function that wraps another function to add behaviour, this tells Flask what URL should trigger our function
@app.route('/')
def home():
    # Landing page
    return render_template('home.html')

@app.route('/chat')
def chat():
    # Existing chat interface
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    question = request.json.get("question")
    # RAG logic goes here
    answer = get_answer(question)
    return jsonify({"answer": answer})

if __name__ == '__main__':
    # Starts the server, auto-reloads when you save changes and shows helpflu error pages.
    app.run(debug=True)


