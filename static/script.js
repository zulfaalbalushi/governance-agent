function appendMessage(text, role) {
    const row = document.createElement("div");
    row.className = `message-row ${role}`;

    const message = document.createElement("div");
    message.className = `message ${role}-message`;

    const label = document.createElement("span");
    label.className = "message-meta";
    label.textContent = role === "user" ? "You" : "AI Governance Agent";

    const body = document.createElement("div");
    if (role === "ai") {
        // render Markdown from the model; fall back to plain text if marked isn't loaded
        if (typeof marked !== "undefined" && marked.parse) {
            body.innerHTML = marked.parse(text);
        } else {
            body.textContent = text;
        }
    } else {
        // user input stays as plain text to avoid any HTML-injection risk
        body.textContent = text;
    }

    message.appendChild(label);
    message.appendChild(body);
    row.appendChild(message);

    const messages = document.getElementById("messages");
    messages.appendChild(row);
    messages.scrollTop = messages.scrollHeight;
}

//shows a subtle "thinking..." indicator while we wait on /ask
function showThinking() {
    const row = document.createElement("div");
    row.className = "message-row ai";
    row.id = "thinking-indicator";

    const message = document.createElement("div");
    message.className = "message ai-message thinking";

    const label = document.createElement("span");
    label.className = "message-meta";
    label.textContent = "AI Governance Agent";

    const body = document.createElement("div");
    body.className = "thinking-dots";
    body.innerHTML = "<span></span><span></span><span></span>";

    message.appendChild(label);
    message.appendChild(body);
    row.appendChild(message);

    const messages = document.getElementById("messages");
    messages.appendChild(row);
    messages.scrollTop = messages.scrollHeight;
}

//removes the thinking indicator once the real answer arrives
function removeThinking() {
    const indicator = document.getElementById("thinking-indicator");
    if (indicator) {
        indicator.remove();
    }
}

//takes a question, displays it, fetches the answer, displays that too
function askQuestion(question) {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
        return;
    }

    appendMessage(trimmedQuestion, "user");
    showThinking();

    fetch("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmedQuestion })
    })
    .then(response => response.json())
    .then(data => {
        removeThinking();
        appendMessage(data.answer, "ai");
    })
    .catch(error => {
        removeThinking();
        appendMessage("Sorry, something went wrong while fetching the answer.", "ai");
        console.error(error);
    });
}

// grabs the input value, calls askQuestion with it
document.getElementById("input-area").addEventListener("submit", function(event) {
    event.preventDefault();

    const questionInput = document.getElementById("question-input");
    const question = questionInput.value;
    askQuestion(question);
    questionInput.value = "";
    questionInput.focus();
});

const suggestionButtons = document.querySelectorAll(".suggestion");
suggestionButtons.forEach(function(button) {
    button.addEventListener("click", function() {
        const question = button.textContent;
        askQuestion(question);
    });
});

document.getElementById("question-input").addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        document.getElementById("input-area").requestSubmit();
    }
});
