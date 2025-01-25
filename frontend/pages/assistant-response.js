// pages/assistant-response.js

import { useState, useRef, useEffect } from "react";
import {
  PaperAirplaneIcon,
  ChatBubbleLeftRightIcon,
  UserCircleIcon,
} from "@heroicons/react/24/solid";
import DarkModeToggle from "../components/DarkModeToggle";

export default function AssistantResponsePage() {
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [requestText, setRequestText] = useState(""); // For the generated user request

  const chatContainerRef = useRef(null);

  // Auto-scroll chat
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!userInput.trim()) return;

    setLoading(true);
    setError("");
    setIsTyping(true);

    const userMsg = {
      role: "user",
      content: userInput,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    const localInput = userInput;
    setUserInput("");

    try {
      const res = await fetch("http://localhost:8000/assistant/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_input: localInput,
          conversation_id: conversationId,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to process request.");
      }

      const data = await res.json(); // { conversation_id, response, finished }
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
      }

      const assistantMsg = {
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

    } catch (err) {
      console.error(err);
      setError(err.message || "Unexpected error occurred.");
    } finally {
      setLoading(false);
      setIsTyping(false);
    }
  };

  // "Skip" => generate user request from partial data
  const handleSkip = async () => {
    if (!conversationId) {
      setError("No conversation to skip. Please start by sending a message.");
      return;
    }
    setLoading(true);
    setError("");
    setIsTyping(true);

    try {
      const res = await fetch(`http://localhost:8000/assistant/${conversationId}/generate-request`);
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to generate request.");
      }

      const data = await res.json(); // { conversation_id, user_request }
      setRequestText(data.user_request); // Display in the side panel
    } catch (err) {
      console.error(err);
      setError(err.message || "Error generating user request.");
    } finally {
      setLoading(false);
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const closeRequest = () => setRequestText("");

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col items-center p-4">
      <div className="w-full max-w-5xl flex flex-row bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden transition-colors duration-500 h-[80vh]">
        
        {/* LEFT: Chat Panel */}
        <div className="flex flex-col w-2/3 border-r border-gray-200 dark:border-gray-700">
          <div className="bg-primary dark:bg-primary-dark text-white py-4 px-6 flex items-center justify-between">
            <div className="flex items-center">
              <ChatBubbleLeftRightIcon className="h-6 w-6 mr-2 animate-bounce" />
              <div>
                <h1 className="text-2xl font-semibold">Chat with BUREASY</h1>
                <p className="text-sm text-blue-100">
                  Ask about renewing your visa, or skip anytime to generate a request.
                </p>
              </div>
            </div>
            <DarkModeToggle />
          </div>

          <div
            ref={chatContainerRef}
            className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-100 dark:bg-gray-700"
          >
            {messages.map((msg, idx) => (
              <div
                key={idx}
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
                      ? "bg-white dark:bg-gray-600 text-gray-800 dark:text-gray-100 border border-gray-200 dark:border-gray-600"
                      : "bg-primary text-white"
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
                    {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
                {msg.role === "user" && (
                  <UserCircleIcon className="h-8 w-8 text-primary ml-2 animate-pulseSlow" />
                )}
              </div>
            ))}

            {/* Typing Indicator */}
            {isTyping && (
              <div className="flex justify-start items-center">
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

          {error && (
            <div className="px-6 py-2 bg-red-100 text-red-600 text-sm">
              {error}
            </div>
          )}

          {/* Input Area */}
          <div className="bg-white dark:bg-gray-800 p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-2">
              <textarea
                className="flex-1 text-gray-800 dark:text-gray-100 rounded-md border border-gray-300 dark:border-gray-600 p-2 focus:outline-none focus:ring-2 focus:ring-primary dark:bg-gray-700 resize-none transition-colors duration-300"
                rows={1}
                placeholder="Type your request or question..."
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                onKeyDown={handleKeyDown}
              />
              <button
                onClick={handleSendMessage}
                disabled={loading}
                className="flex items-center justify-center bg-primary text-white p-3 rounded-md hover:bg-primary-dark disabled:opacity-50 transition transform hover:scale-105"
              >
                <PaperAirplaneIcon className="h-5 w-5 animate-pulseSlow" />
              </button>
              {/* Skip Button */}
              <button
                onClick={handleSkip}
                disabled={loading}
                className="ml-2 bg-orange-500 text-white p-3 rounded-md hover:bg-orange-600 disabled:opacity-50 transition transform hover:scale-105"
              >
                Skip
              </button>
            </div>
          </div>
        </div>

        {/* RIGHT: Request Display */}
        <div className="w-1/3 bg-gray-50 dark:bg-gray-900 p-4 relative">
          <h2 className="text-lg font-bold mb-2 text-gray-800 dark:text-gray-100">
            Generated Request
          </h2>
          {requestText ? (
            <div className="bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 p-4 rounded shadow h-full">
              <p className="whitespace-pre-line">
                {requestText}
              </p>
              <button
                onClick={() => setRequestText("")}
                className="mt-2 px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 transition"
              >
                Close
              </button>
            </div>
          ) : (
            <p className="text-sm text-gray-600 dark:text-gray-300">
              No request generated yet. Click &quot;Skip&quot; to see a request.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
