//takes a question, displays it, fetches the answer, displays that too
function askQuestion(question) {
    const userMessage = document.createElement("div");
    userMessage.textContent = question;
    userMessage.className = "user-message";
    document.getElementById("messages").appendChild(userMessage);

    fetch("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question })
    })
    .then(response => response.json())
    .then(data => {
        const aiMessage = document.createElement("div");
        aiMessage.textContent = data.answer;
        aiMessage.className = "ai-message";
        document.getElementById("messages").appendChild(aiMessage);
    });
}

// grabs the input value, calls askQuestion with it
document.getElementById("send-button").addEventListener("click", function() {
    const questionInput = document.getElementById("question-input");
    const question = questionInput.value;
    askQuestion(question);
});

const suggestionButtons = document.querySelectorAll(".suggestion");
suggestionButtons.forEach(function(button) {
    button.addEventListener("click", function() {
        const question = button.textContent;
        askQuestion(question);
    });
    })
