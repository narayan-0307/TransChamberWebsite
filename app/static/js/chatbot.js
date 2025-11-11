let responses = null;
// Removed hasAutoOpened and auto-open logic

// Load responses when the page loads
document.addEventListener("DOMContentLoaded", async () => {
  try {
    const response = await fetch("/static/data/chatbot_responses.json");
    responses = await response.json();
    // Removed setTimeout for auto-opening chat
  } catch (error) {
    console.error("Error loading chatbot responses:", error);
  }
});

function toggleChat() {
  const chatWindow = document.getElementById("chatWindow");
  const isOpening = !chatWindow.classList.contains("active");
  chatWindow.classList.toggle("active");

  if (isOpening) {
    showWelcomeMessage();
  }
}

function showWelcomeMessage() {
  const chatbox = document.getElementById("chatbox");
  chatbox.innerHTML = "";
  addBotMessage("Welcome to Trans Asian Chamber! How can I assist you today?");
}

function getCurrentTime() {
  const now = new Date();
  return now.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function createMessageElement(message, isUser = false) {
  const messageDiv = document.createElement("div");
  messageDiv.className = `flex ${isUser ? "justify-end" : "justify-start"}`;

  const bubble = document.createElement("div");
  bubble.className = `message-bubble ${isUser ? "user" : "bot"}`;

  const content = document.createElement("div");
  // Render message as HTML but make sure plain URLs become clickable links
  // If message is already HTML (contains '<a' or '<br'), assume it's safe to set as-is
  if (typeof message === "string") {
    let safeMessage = message;

    // If the message does not already contain anchor tags, convert plain URLs to links
    if (!/\<a\s/i.test(safeMessage)) {
      // Simple URL regex (matches http(s)://...)
      const urlRegex = /(https?:\/\/[^\s"'<>]+)/g;
      safeMessage = safeMessage.replace(urlRegex, function (url) {
        return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
      });
    }

    content.innerHTML = safeMessage;
  } else {
    // fallback
    content.textContent = String(message);
  }

  const time = document.createElement("div");
  time.className = `message-time ${isUser ? "user" : "bot"}`;
  time.textContent = getCurrentTime();

  bubble.appendChild(content);
  bubble.appendChild(time);
  messageDiv.appendChild(bubble);

  return messageDiv;
}

function showTypingIndicator() {
  const indicator = document.createElement("div");
  indicator.className = "flex justify-start";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble bot";

  const dots = document.createElement("div");
  dots.className = "typing-indicator";
  dots.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;

  bubble.appendChild(dots);
  indicator.appendChild(bubble);
  return indicator;
}

function findBestMatch(input, section) {
  const words = input.toLowerCase().split(/\s+/);
  let bestMatch = null;
  let highestScore = 0;

  for (const [key, value] of Object.entries(section)) {
    const keyWords = key.toLowerCase().split(/\s+/);
    let score = 0;

    // Check for exact matches
    if (input.includes(key)) {
      score += 100;
    }

    // Check for word matches
    for (const word of words) {
      if (
        keyWords.some(
          (keyWord) => keyWord.includes(word) || word.includes(keyWord)
        )
      ) {
        score += 10;
      }
    }

    // Check for partial matches
    for (const word of words) {
      for (const keyWord of keyWords) {
        if (keyWord.includes(word) || word.includes(keyWord)) {
          score += 5;
        }
      }
    }

    if (score > highestScore) {
      highestScore = score;
      bestMatch = value;
    }
  }

  return highestScore > 0 ? bestMatch : null;
}

function getBotResponse(userInput) {
  if (!responses)
    return "I'm having trouble connecting. Please try again later.";

  const input = userInput.toLowerCase().trim();

  // Check greetings first
  if (responses.greetings[input]) {
    return responses.greetings[input];
  }

  // Check each section for matches
  const sections = [
    {
      name: "about",
      keywords: [
        "about",
        "trans",
        "chamber",
        "what",
        "who",
        "do",
        "organization",
      ],
    },
    {
      name: "membership",
      keywords: ["member", "join", "benefit", "fee", "cost", "type"],
    },
    {
      name: "events",
      keywords: [
        "event",
        "conference",
        "seminar",
        "register",
        "calendar",
        "schedule",
      ],
    },
    {
      name: "services",
      keywords: [
        "service",
        "offer",
        "matchmaking",
        "research",
        "consulting",
        "trade",
      ],
    },
    {
      name: "contact",
      keywords: [
        "contact",
        "reach",
        "location",
        "address",
        "email",
        "phone",
        "call",
      ],
    },
    {
      name: "general",
      keywords: ["thank", "bye", "help", "not sure", "confused"],
    },
  ];

  // First, check if any section keywords are in the input
  for (const section of sections) {
    if (section.keywords.some((keyword) => input.includes(keyword))) {
      const match = findBestMatch(input, responses[section.name]);
      if (match) {
        // If this is a contact/address response, and a map link exists, append it
        if (section.name === "contact" && typeof match === "string") {
          // Try to find a map link in responses.contact
          const contactSection = responses.contact || {};
          const mapLink =
            contactSection["map link"] ||
            contactSection["map_link"] ||
            contactSection.maplink;
          if (mapLink) {
            // Return address with map link on a new line; add a class for styling
            return `${match} <br><a class="chatbot-map-link" href="${mapLink}" target="_blank" rel="noopener noreferrer">View on map</a>`;
          }
        }
        return match;
      }
    }
  }

  // If no section match, try direct matching in all sections
  for (const section of sections) {
    const match = findBestMatch(input, responses[section.name]);
    if (match) {
      return match;
    }
  }

  return responses.general.default;
}

function addBotMessage(message) {
  const chatbox = document.getElementById("chatbox");
  chatbox.appendChild(createMessageElement(message));
  chatbox.scrollTop = chatbox.scrollHeight;
}

function sendMessage() {
  const input = document.getElementById("userInput");
  const msg = input.value.trim();
  if (!msg) return;

  const chatbox = document.getElementById("chatbox");

  // Add user message
  chatbox.appendChild(createMessageElement(msg, true));

  // Add typing indicator
  const typingIndicator = showTypingIndicator();
  chatbox.appendChild(typingIndicator);

  // Scroll to bottom
  chatbox.scrollTop = chatbox.scrollHeight;

  // Clear input
  input.value = "";

  // Simulate response delay
  setTimeout(() => {
    // Remove typing indicator
    typingIndicator.remove();

    // Get and add bot response
    const botResponse = getBotResponse(msg);
    addBotMessage(botResponse);
  }, 1000);
}
