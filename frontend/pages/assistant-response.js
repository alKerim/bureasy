// pages/assistant-response.js
import { useState } from "react";

export default function AssistantResponsePage() {
  const [userInput, setUserInput] = useState("");
  const [assistantResponse, setAssistantResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGenerateResponse = async () => {
    setLoading(true);
    setError("");
    setAssistantResponse("");

    try {
      const response = await fetch("http://localhost:8000/assistant/generate-text-response", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_input: userInput }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to generate response.");
      }

      const data = await response.json();
      if (data.success) {
        setAssistantResponse(data.response);
      } else {
        throw new Error("Response generation unsuccessful.");
      }
    } catch (err) {
      console.error("Error:", err);
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-10 px-4">
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-8 text-gray-800">
        <h1 className="text-3xl font-bold mb-6 text-center text-blue-600">Ask BUREASY</h1>
        <p className="mb-8 text-center text-gray-600">
          Need help with a visa, driver’s license, or other administrative tasks? 
          Ask away and BUREASY will guide you step by step.
        </p>

        <label className="block mb-2 font-semibold">Enter your question/request:</label>
        <textarea
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          rows={4}
          className="w-full p-3 mb-4 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="e.g., 'How do I renew my student visa in Munich?'"
        />

        <button
          onClick={handleGenerateResponse}
          disabled={loading || !userInput.trim()}
          className="w-full px-4 py-2 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 transition disabled:opacity-50"
        >
          {loading ? "Generating..." : "Get Guidance"}
        </button>

        {error && (
          <div className="mt-4 text-red-600 font-semibold text-center">
            {error}
          </div>
        )}

        {assistantResponse && (
          <div className="mt-6 bg-gray-50 p-4 rounded-md border border-gray-200">
            <h2 className="text-xl font-semibold mb-2">BUREASY&apos;s Response:</h2>
            <p>{assistantResponse}</p>
          </div>
        )}
      </div>
    </div>
  );
}
