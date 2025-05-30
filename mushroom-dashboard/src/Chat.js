import React, { useState } from "react";
import "./Chat.css";

const Chat = ({ currentZone }) => {
  const [threadId, setThreadId] = useState(null);
  const [userMessage, setUserMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isFullScreen, setIsFullScreen] = useState(false);

  const sendChat = async () => {
    if (!userMessage.trim()) return;

    if (!currentZone) {
      console.error("Zone not selected for chat. Message not sent.");
      setChatHistory((prev) => [...prev, { sender: "system", message: "Error: No zone selected. Cannot send message." }]);
      return;
    }

    const messageToSend = userMessage; // Preserve the message before clearing
    // Add user message to the history
    setChatHistory((prev) => [...prev, { sender: "user", message: messageToSend }]);
    setUserMessage(""); // Clear the input immediately

    setIsTyping(true);
    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thread_id: threadId, message: messageToSend, zone_name: currentZone })
      });
      const data = await response.json();
      if (!threadId && data.thread_id) {
        setThreadId(data.thread_id);
      }
      // Simulate typing effect for the AI response:
      const fullResponse = data.reply;
      let currentResponse = "";
      let index = 0;
      // If there's no previous AI entry, add one.
      setChatHistory((prev) => {
        if (prev.length === 0 || prev[prev.length - 1].sender !== "ai") {
          return [...prev, { sender: "ai", message: "" }];
        }
        return prev;
      });
      const typingInterval = 10; // milliseconds per character
      const intervalId = setInterval(() => {
        currentResponse += fullResponse[index];
        index++;
        // Update the last message (the AI message) in the chat history.
        setChatHistory((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = { sender: "ai", message: currentResponse };
          return updated;
        });
        if (index === fullResponse.length) {
          clearInterval(intervalId);
          setIsTyping(false);
        }
      }, typingInterval);
    } catch (err) {
      console.error("Error sending chat message:", err);
      setIsTyping(false);
    }
  };

  const toggleFullScreen = () => {
    setIsFullScreen(!isFullScreen);
  };

  return (
    <div className={`chat-container ${isFullScreen ? "fullscreen" : ""}`}>
      <div className="chat-header">
        <h2>Talk to Your Mushrooms</h2>
        <button className="fullscreen-toggle" onClick={toggleFullScreen}>
          {isFullScreen ? "Minimize" : "Expand"}
        </button>
      </div>
      <div className="chat-history">
        {chatHistory.map((entry, index) => (
          <div key={index} className={`chat-bubble ${entry.sender}`}>
            {entry.message}
          </div>
        ))}
        {isTyping && (
          <div className="chat-bubble ai typing">
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
          </div>
        )}
      </div>
      <div className="chat-input">
        <textarea
          rows="3"
          value={userMessage}
          onChange={(e) => setUserMessage(e.target.value)}
          placeholder="Type your message..."
        />
        <button className="chat-button" onClick={sendChat}>
          Send
        </button>
      </div>
    </div>
  );
};

export default Chat;