// pages/assistant-response.js

import { useState, useRef, useEffect } from "react";
import {
  PaperAirplaneIcon,
  ChatBubbleLeftRightIcon,
  UserCircleIcon,
} from "@heroicons/react/24/solid"; // Corrected import paths
import DarkModeToggle from "../components/DarkModeToggle"; // Ensure this component exists

export default function AssistantResponsePage() {
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]); // [{ role: "user"/"assistant", content: "...", timestamp: Date }]
  const [userInput, setUserInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isTyping, setIsTyping] = useState(false); // Typing indicator
  const chatContainerRef = useRef(null);

  // Start a new conversation on mount
  useEffect(() => {
    const startConversation = async () => {
      try {
        const res = await fetch("http://localhost:8000/assistant/start-conversation", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ flow_type: "visa_extension" }), // or a user-selected flow
        });
        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || "Failed to start conversation.");
        }
        const data = await res.json();
        setConversationId(data.conversation_id);

        // Add assistant message with the first question
        setMessages([{ role: "assistant", content: data.first_question, timestamp: new Date() }]);
      } catch (err) {
        console.error(err);
        setError(err.message || "Could not start conversation");
      }
    };

    startConversation();
  }, []);

  // Always scroll to bottom when messages change
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!userInput.trim() || !conversationId) return;

    setLoading(true);
    setError("");
    setIsTyping(true); // Start typing indicator

    // Append user's message to chat
    const newUserMessage = { role: "user", content: userInput, timestamp: new Date() };
    setMessages((prev) => [...prev, newUserMessage]);

    const currentInput = userInput; // capture before resetting
    setUserInput("");

    try {
      // Send user message to the server
      const response = await fetch("http://localhost:8000/assistant/next-message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: conversationId,
          user_input: currentInput,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to get the next message.");
      }

      const data = await response.json();

      // Append assistant response to chat
      const newAssistantMessage = {
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, newAssistantMessage]);

      // If finished = true, we can show a message or just remain as is
      if (data.finished) {
        console.log("Conversation is finished. Final summary received.");
      }
    } catch (err) {
      console.error("Error:", err);
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
      setIsTyping(false); // End typing indicator
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col items-center p-4">
      <div className="w-full max-w-3xl flex flex-col bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden h-[80vh] transition-colors duration-500">
        {/* Header */}
        <div className="bg-primary dark:bg-primary-dark text-white py-4 px-6 flex items-center justify-between">
          <div className="flex items-center">
            <ChatBubbleLeftRightIcon className="h-6 w-6 mr-2 animate-bounce" />
            <div>
              <h1 className="text-2xl font-semibold animate-fadeIn">Chat with BUREASY</h1>
              <p className="text-sm text-blue-100 animate-fadeIn">
                We’ll guide you through the visa extension flow step by step.
              </p>
            </div>
          </div>
          <DarkModeToggle /> {/* Dark mode toggle button */}
        </div>

        {/* Chat Messages */}
        <div
          ref={chatContainerRef}
          className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-100 dark:bg-gray-700 animate-fadeIn"
        >
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${
                msg.role === "assistant" ? "justify-start" : "justify-end"
              } items-start`}
            >
              {msg.role === "assistant" && (
                <UserCircleIcon className="h-8 w-8 text-secondary mr-2 animate-pulseSlow" />
              )}
              <div
                className={`relative rounded-lg p-3 max-w-sm ${
                  msg.role === "assistant"
                    ? "bg-white dark:bg-gray-600 text-gray-800 dark:text-gray-100 border border-gray-200 dark:border-gray-600 animate-slideInLeft"
                    : "bg-primary text-white animate-fadeIn"
                }`}
              >
                <p>{msg.content}</p>
                <span
                  className={`block text-xs mt-1 ${
                    msg.role === "assistant"
                      ? "text-gray-600 dark:text-gray-400"
                      : "text-gray-200 dark:text-gray-400"
                  }`}
                >
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              {msg.role === "user" && (
                <UserCircleIcon className="h-8 w-8 text-primary ml-2 animate-pulseSlow" />
              )}
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex justify-start items-center animate-fadeIn">
              <UserCircleIcon className="h-8 w-8 text-secondary mr-2 animate-pulseSlow" />
              <div className="bg-white dark:bg-gray-600 text-gray-800 dark:text-gray-100 p-3 rounded-lg">
                <div className="flex space-x-1">
                  <span className="w-2 h-2 bg-gray-500 dark:bg-gray-400 rounded-full animate-bounce"></span>
                  <span className="w-2 h-2 bg-gray-500 dark:bg-gray-400 rounded-full animate-bounce delay-200"></span>
                  <span className="w-2 h-2 bg-gray-500 dark:bg-gray-400 rounded-full animate-bounce delay-400"></span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="px-6 py-2 bg-red-100 text-red-600 text-sm animate-fadeIn">
            {error}
          </div>
        )}

        {/* Input Area */}
        <div className="bg-white dark:bg-gray-800 p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <textarea
              className="flex-1 text-gray-800 dark:text-gray-100 rounded-md border border-gray-300 dark:border-gray-600 p-2 focus:outline-none focus:ring-2 focus:ring-primary dark:bg-gray-700 resize-none transition-colors duration-300"
              rows={1}
              placeholder="Type your response..."
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyDown={handleKeyPress}
            />
            <button
              onClick={handleSendMessage}
              disabled={loading || !conversationId}
              className="flex items-center justify-center bg-primary text-white p-3 rounded-md hover:bg-primary-dark disabled:opacity-50 transition transform hover:scale-105"
              aria-label="Send Message"
            >
              <PaperAirplaneIcon className="h-5 w-5 animate-pulseSlow" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
