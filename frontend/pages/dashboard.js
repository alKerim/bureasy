// pages/assistant-response.js

import { useState, useRef, useEffect } from "react";
import {
  PaperAirplaneIcon,
  ChatBubbleLeftRightIcon,
  UserCircleIcon,
  CheckIcon,
} from "@heroicons/react/24/solid";
import DarkModeToggle from "../components/DarkModeToggle";

export default function AssistantResponsePage() {
  // Chat States
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [requestText, setRequestText] = useState(""); // For the generated user request

  // Checklist States
  const [rawChecklist, setRawChecklist] = useState("");
  const [parsedChecklist, setParsedChecklist] = useState(null);
  const [humanPhoneRaw, setHumanPhoneRaw] = useState("");
  const [checkedSteps, setCheckedSteps] = useState([]);

  const chatContainerRef = useRef(null);
  const checklistContainerRef = useRef(null);

  // Auto-scroll chat to the bottom when messages update
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  // Function to generate checklist based on a given query
  const generateChecklist = async (query) => {
    if (!query.trim()) {
      setError("Invalid query for generating the checklist.");
      return;
    }

    setLoading(true);
    setError("");
    setRawChecklist("");
    setParsedChecklist(null);
    setHumanPhoneRaw("");
    setCheckedSteps([]); // Reset checked steps

    try {
      const response = await fetch(
        "http://localhost:8000/assistant/generate-checklist",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query }),
        }
      );

      if (!response.ok) {
        const errorResponse = await response.json();
        throw new Error(errorResponse.detail || "Failed to generate checklist.");
      }

      const data = await response.json();
      setRawChecklist(data.checklist);

      try {
        // Parse the checklist JSON
        const parsed = JSON.parse(data.checklist);
        if (Array.isArray(parsed.steps) && typeof parsed.closing === "string") {
          setParsedChecklist(parsed);
          setCheckedSteps(new Array(parsed.steps.length).fill(false)); // All steps start unchecked
        } else {
          throw new Error("Invalid checklist format.");
        }
      } catch (err) {
        // If parsing fails, fall back to raw JSON
        setParsedChecklist(null);
        console.warn("Failed to parse checklist JSON:", err.message);
      }
    } catch (err) {
      setError(err.message || "An error occurred while generating the checklist.");
    } finally {
      setLoading(false);
    }
  };

  // Handle sending a message
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

      const data = await res.json(); // Expected: { conversation_id, response, finished }
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
      }

      const assistantMsg = {
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // If the conversation is finished, generate the checklist
      if (data.finished) {
        setRequestText(data.response);
        await generateChecklist(data.response);
      }
    } catch (err) {
      console.error(err);
      setError(err.message || "Unexpected error occurred.");
    } finally {
      setLoading(false);
      setIsTyping(false);
    }
  };

  // Handle skipping to generate user request
  const handleSkip = async () => {
    if (!conversationId) {
      setError("No conversation to skip. Please start by sending a message.");
      return;
    }
    setLoading(true);
    setError("");
    setIsTyping(true);

    try {
      const res = await fetch(
        `http://localhost:8000/assistant/${conversationId}/generate-request`
      );
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to generate request.");
      }

      const data = await res.json(); // Expected: { conversation_id, user_request }
      setRequestText(data.user_request); // Display in the side panel
      await generateChecklist(data.user_request); // Automatically generate checklist
    } catch (err) {
      console.error(err);
      setError(err.message || "Error generating user request.");
    } finally {
      setLoading(false);
      setIsTyping(false);
    }
  };

  // Handle pressing Enter to send message
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Close the generated request display
  const closeRequest = () => setRequestText("");

  // Handle contacting a human
  const handleContactHuman = async () => {
    if (!requestText.trim()) {
      setError("No request available to find a human contact.");
      return;
    }

    setLoading(true);
    setError("");
    setHumanPhoneRaw("");

    try {
      const response = await fetch("http://localhost:8000/assistant/ask-human", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: requestText }),
      });

      if (!response.ok) {
        const errorResponse = await response.json();
        throw new Error(errorResponse.detail || "Failed to get human contact.");
      }

      const data = await response.json();

      // Ensure data is properly parsed if it contains a JSON string
      const phoneNumber =
        typeof data === "string" ? JSON.parse(data) : data;

      if (phoneNumber && phoneNumber.phone) {
        setHumanPhoneRaw(phoneNumber.phone);
      } else {
        setHumanPhoneRaw("No Phone Available");
      }
    } catch (err) {
      console.error("Error in handleContactHuman:", err.message);
      setError(err.message || "An error occurred while fetching the phone number.");
    } finally {
      setLoading(false);
    }
  };

  // Toggle checkbox state for checklist
  const toggleCheckbox = (index) => {
    setCheckedSteps((prev) => {
      const updated = [...prev];
      updated[index] = !updated[index];
      return updated;
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
      <div className="flex-1 flex flex-col lg:flex-row max-w-7xl mx-auto bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden transition-colors duration-500">
        
        {/* LEFT: Chat Panel */}
        <div className="flex flex-col w-full lg:w-2/3 border-b lg:border-b-0 lg:border-r border-gray-200 dark:border-gray-700">
          {/* Header */}
          <div className="bg-primary dark:bg-primary-dark text-white py-4 px-6 flex items-center justify-between">
            <div className="flex items-center">
              <ChatBubbleLeftRightIcon className="h-6 w-6 mr-2 animate-bounce" />
              <div>
                <h1 className="text-2xl font-semibold">Chat with BUREASY</h1>
                <p className="text-sm text-gray-200">
                  Ask about renewing your visa, or skip anytime to generate a request.
                </p>
              </div>
            </div>
            <DarkModeToggle />
          </div>

          {/* Messages Container */}
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
                  <UserCircleIcon className="h-8 w-8 text-secondary mr-2" />
                )}
                <div
                  className={`relative rounded-lg p-3 max-w-sm ${
                    msg.role === "assistant"
                      ? "bg-white dark:bg-gray-600 text-gray-800 dark:text-gray-100 border border-gray-200 dark:border-gray-600"
                      : "bg-primary text-white"
                  } shadow-sm`}
                >
                  <p>{msg.content}</p>
                  <span
                    className={`block text-xs mt-1 ${
                      msg.role === "assistant"
                        ? "text-gray-700 dark:text-gray-400"
                        : "text-gray-200 dark:text-gray-400"
                    }`}
                  >
                    {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
                {msg.role === "user" && (
                  <UserCircleIcon className="h-8 w-8 text-primary ml-2" />
                )}
              </div>
            ))}

            {/* Typing Indicator */}
            {isTyping && (
              <div className="flex justify-start items-center">
                <UserCircleIcon className="h-8 w-8 text-secondary mr-2" />
                <div className="bg-white dark:bg-gray-600 text-gray-800 dark:text-gray-100 p-3 rounded-lg flex space-x-1">
                  <span className="w-2 h-2 bg-gray-700 dark:bg-gray-400 rounded-full animate-bounce"></span>
                  <span className="w-2 h-2 bg-gray-700 dark:bg-gray-400 rounded-full animate-bounce delay-200"></span>
                  <span className="w-2 h-2 bg-gray-700 dark:bg-gray-400 rounded-full animate-bounce delay-400"></span>
                </div>
              </div>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="px-6 py-2 bg-red-100 text-red-700 text-sm flex items-center space-x-2">
              <ChatBubbleLeftRightIcon className="h-5 w-5" />
              <span>{error}</span>
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
                className="flex items-center justify-center bg-primary hover:bg-primary-dark text-white p-3 rounded-md disabled:opacity-50 transition transform hover:scale-105"
              >
                <PaperAirplaneIcon className="h-5 w-5" />
              </button>
              {/* Skip Button */}
              <button
                onClick={handleSkip}
                disabled={loading}
                className="ml-2 bg-orange-500 hover:bg-orange-600 text-white p-3 rounded-md disabled:opacity-50 transition transform hover:scale-105"
              >
                Skip
              </button>
            </div>
          </div>
        </div>

        {/* RIGHT: Checklist and Contact Panel */}
        <div className="flex flex-col w-full lg:w-1/3 bg-gray-50 dark:bg-gray-900 p-6 space-y-6">
          
          {/* Generated Request Display */}
          {requestText && (
            <div className="bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 p-4 rounded-lg shadow">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-bold">Generated Request</h2>
                <button onClick={closeRequest} className="text-red-500 hover:text-red-700">
                  ✕
                </button>
              </div>
              <p className="mt-2 whitespace-pre-line">{requestText}</p>
            </div>
          )}

          {/* Checklist Display */}
          <div className="bg-white dark:bg-gray-700 p-6 rounded-lg shadow flex flex-col">
            <h2 className="text-xl font-semibold mb-4 flex items-center space-x-2">
              <CheckIcon className="h-6 w-6 text-green-500" />
              <span>Generated Checklist</span>
            </h2>
            {parsedChecklist ? (
              <div className="flex-1 max-h-80 overflow-y-auto" ref={checklistContainerRef}>
                <ul className="space-y-3">
                  {parsedChecklist.steps.map((step, index) => (
                    <li key={index} className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={checkedSteps[index]}
                        onChange={() => toggleCheckbox(index)}
                        className="h-6 w-6 text-indigo-600 focus:ring-indigo-500 border-gray-300 dark:border-gray-600 rounded"
                      />
                      <span
                        className={`text-gray-800 dark:text-gray-100 ${
                          checkedSteps[index] ? "line-through text-gray-700 dark:text-gray-500" : ""
                        } text-lg`}
                      >
                        {step}
                      </span>
                    </li>
                  ))}
                </ul>
                {parsedChecklist.closing && (
                  <p className="mt-4 italic text-gray-700 dark:text-gray-400">{parsedChecklist.closing}</p>
                )}
              </div>
            ) : rawChecklist ? (
              <div className="mt-4 bg-gray-100 dark:bg-gray-600 p-4 rounded-lg shadow overflow-y-auto max-h-80">
                <h3 className="text-lg font-bold mb-2">Raw Checklist JSON</h3>
                <pre className="whitespace-pre-wrap bg-gray-200 dark:bg-gray-500 p-2 rounded-lg overflow-auto text-gray-800 dark:text-gray-100">
                  {rawChecklist}
                </pre>
              </div>
            ) : (
              <p className="text-gray-700 dark:text-gray-300">No checklist generated yet.</p>
            )}
          </div>

          {/* Contact a Human */}
          <div className="bg-white dark:bg-gray-700 p-6 rounded-lg shadow flex flex-col">
            <h2 className="text-xl font-semibold mb-4 flex items-center space-x-2">
              <ChatBubbleLeftRightIcon className="h-6 w-6 text-purple-500" />
              <span>Contact a Human</span>
            </h2>
            <p className="mb-4 text-gray-700 dark:text-gray-300">
              If you’d prefer to speak directly with a human official, click below to find
              the best phone number based on your request.
            </p>
            <button
              onClick={handleContactHuman}
              disabled={loading || !requestText.trim()}
              className="w-full bg-purple-600 hover:bg-purple-700 dark:bg-purple-500 dark:hover:bg-purple-600 text-white py-2 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {loading ? "Finding a Contact..." : "Contact a Human"}
            </button>

            {/* Contact Information Display */}
            {humanPhoneRaw && humanPhoneRaw !== "No Phone Available" && (
              <div className="mt-6 bg-blue-50 dark:bg-blue-700 p-4 rounded-lg shadow flex flex-col">
                <div className="flex items-center flex-wrap">
                  <p className="text-gray-700 dark:text-gray-200 mb-2 mr-4">
                    <strong>Phone Number:</strong> {humanPhoneRaw}
                  </p>
                  <a href={`tel:${humanPhoneRaw}`}>
                    <button
                      className="bg-blue-600 dark:bg-blue-500 hover:bg-blue-700 dark:hover:bg-blue-600 text-white py-2 px-4 rounded-lg transition flex items-center"
                    >
                      {/* Using ChatBubbleLeftRightIcon as a substitute for PhoneIcon */}
                      <ChatBubbleLeftRightIcon className="w-5 h-5 mr-2" />
                      Call Now
                    </button>
                  </a>
                </div>
              </div>
            )}

            {/* No Phone Available Message */}
            {humanPhoneRaw === "No Phone Available" && (
              <div className="mt-6 bg-yellow-100 dark:bg-yellow-700 text-yellow-700 dark:text-yellow-200 p-4 rounded-lg shadow">
                <h3 className="text-lg font-bold mb-2">No Contact Available</h3>
                <p>
                  Currently, there is no available phone contact for your request. Please try again later or reach out through alternative methods.
                </p>
              </div>
            )}
          </div>

          {/* Error Display */}
          {error && (
            <div className="w-full bg-red-100 dark:bg-red-700 text-red-700 dark:text-red-200 p-4 rounded-lg shadow flex items-center space-x-2">
              <ChatBubbleLeftRightIcon className="h-5 w-5" />
              <span>{error}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
