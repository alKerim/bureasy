// pages/checklist.js

import { useState, useRef } from "react";

export default function CheckListPage() {
  const [jsonFiles, setJsonFiles] = useState([]);
  const [uploadStatus, setUploadStatus] = useState("");
  const [query, setQuery] = useState("");
  const [rawChecklist, setRawChecklist] = useState("");
  const [parsedChecklist, setParsedChecklist] = useState(null);
  const [humanPhoneRaw, setHumanPhoneRaw] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef(null);

  // State to track checked items
  const [checkedSteps, setCheckedSteps] = useState([]);

  // Handle multiple JSON files
  const handleFilesSelected = (files) => {
    const selectedFiles = Array.from(files).filter(
      (file) => file.type === "application/json"
    );
    if (selectedFiles.length !== files.length) {
      setError("Only JSON files are allowed.");
      return;
    }
    setJsonFiles(selectedFiles);
    setUploadStatus("");
    setError("");
    if (selectedFiles.length > 0) {
      handleUploadJSON(selectedFiles);
    }
  };

  // Handle file input change
  const onFileChange = (e) => {
    handleFilesSelected(e.target.files);
  };

  // Handle drag events
  const onDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const onDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const onDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesSelected(e.dataTransfer.files);
      e.dataTransfer.clearData();
    }
  };

  // Upload JSON data and ingest
  const handleUploadJSON = async (files) => {
    if (!files.length) {
      setError("Please select at least one JSON file.");
      return;
    }

    setLoading(true);
    setError("");
    setUploadStatus("");

    try {
      const formData = new FormData();
      files.forEach((file) => {
        formData.append("files", file);
      });

      const response = await fetch("http://localhost:8000/assistant/ingest-data", {
        method: "POST",
        body: formData, // FormData automatically sets the correct Content-Type
      });

      if (!response.ok) {
        const errorResponse = await response.json();
        throw new Error(errorResponse.detail || "Data ingestion failed.");
      }

      const result = await response.json();
      setUploadStatus(result.message || "Data ingestion successful.");
      setJsonFiles([]); // Clear selected files after successful upload
    } catch (err) {
      setError(err.message || "An error occurred while uploading data.");
    } finally {
      setLoading(false);
    }
  };

  // Generate checklist after ingestion
  const handleGenerateChecklist = async () => {
    if (!query.trim()) {
      setError("Please enter a query to generate the checklist.");
      return;
    }

    setLoading(true);
    setError("");
    setRawChecklist("");
    setParsedChecklist(null);
    setHumanPhoneRaw("");
    setCheckedSteps([]); // Reset checked steps

    try {
      const response = await fetch("http://localhost:8000/assistant/generate-checklist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

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

  // Contact a Human for contact number
  const handleContactHuman = async () => {
    if (!query.trim()) {
      setError("Please enter a query to find a human contact.");
      return;
    }
  
    setLoading(true);
    setError("");
    setHumanPhoneRaw("");
  
    try {
      const response = await fetch("http://localhost:8000/assistant/ask-human", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
  
      if (!response.ok) {
        const errorResponse = await response.json();
        throw new Error(errorResponse.detail || "Failed to get human contact.");
      }
  
      const data = await response.json();
  
      // Ensure data is properly parsed if it contains a JSON string
      const phoneNumber = typeof data === "string" ? JSON.parse(data) : data;
  
      if (phoneNumber && phoneNumber.phone) {
        setHumanPhoneRaw(phoneNumber.phone);
      } else {
        throw new Error("Phone number not found in the response.");
      }
    } catch (err) {
      console.error("Error in handleContactHuman:", err.message);
      setError(err.message || "An error occurred while fetching the phone number.");
    } finally {
      setLoading(false);
    }
  };
  
    
  // Toggle checkbox state
  const toggleCheckbox = (index) => {
    setCheckedSteps((prev) => {
      const updated = [...prev];
      updated[index] = !updated[index];
      return updated;
    });
  };

  // Render parsed checklist with interactive checkboxes
  const renderChecklist = () => {
    if (!parsedChecklist || !Array.isArray(parsedChecklist.steps)) return null;

    return (
      <ul className="space-y-3">
        {parsedChecklist.steps.map((step, index) => (
          <li key={index} className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={checkedSteps[index]}
              onChange={() => toggleCheckbox(index)}
              className="h-6 w-6 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <span
              className={`text-gray-800 ${
                checkedSteps[index] ? "line-through text-gray-400" : ""
              } text-lg`}
            >
              {step}
            </span>
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8 flex flex-col items-center">
      <h1 className="text-4xl font-extrabold text-gray-800 mb-8">Checklist Generator</h1>

      {/* Step 1: Ingest JSON Data */}
      <div className="w-full max-w-2xl bg-white p-8 rounded-2xl shadow-lg mb-8">
        <h2 className="text-2xl font-semibold text-gray-700 mb-6">1. Ingest JSON Data</h2>
        <div
          className={`flex flex-col items-center justify-center border-2 ${
            isDragging ? "border-indigo-500 bg-indigo-50" : "border-dashed border-indigo-500"
          } rounded-lg p-6 cursor-pointer hover:bg-indigo-50 transition`}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={() => fileInputRef.current.click()}
        >
          <svg
            className="w-12 h-12 text-indigo-500"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"
            />
          </svg>
          <span className="mt-2 text-base leading-normal text-gray-600">
            {isDragging
              ? "Release to upload"
              : "Drag & Drop JSON Files or Click to Select"}
          </span>
          <input
            type="file"
            accept=".json"
            multiple
            onChange={onFileChange}
            className="hidden"
            ref={fileInputRef}
          />
        </div>
        {jsonFiles.length > 0 && (
          <div className="mt-4">
            <h3 className="text-lg font-medium text-gray-700">Selected Files:</h3>
            <ul className="list-disc list-inside text-gray-600">
              {jsonFiles.map((file, index) => (
                <li key={index}>{file.name}</li>
              ))}
            </ul>
          </div>
        )}
        {uploadStatus && (
          <p className="mt-4 text-green-600">{uploadStatus}</p>
        )}
      </div>

      {/* Step 2: Generate Checklist */}
      <div className="w-full max-w-2xl bg-white p-8 rounded-2xl shadow-lg mb-8">
        <h2 className="text-2xl font-semibold text-gray-700 mb-6">2. Generate Checklist</h2>
        <textarea
          rows="4"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter your query here..."
          className="w-full p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none text-gray-800 text-lg"
        />
        <button
          onClick={handleGenerateChecklist}
          disabled={loading || !query.trim()}
          className="mt-6 w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {loading ? (
            <>
              <svg
                className="animate-spin h-5 w-5 mr-3 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v8H4z"
                ></path>
              </svg>
              Generating...
            </>
          ) : (
            "Generate Checklist"
          )}
        </button>
      </div>

      {/* Step 3: Contact a Human */}
      <div className="w-full max-w-2xl bg-white p-8 rounded-2xl shadow-lg mb-8">
        <h2 className="text-2xl font-semibold text-gray-700 mb-6">3. Contact a Human</h2>
        <p className="mb-4 text-gray-600">
          If you’d prefer to speak directly with a human official, click below to find
          the best phone number from our data.
        </p>
        <button
          onClick={handleContactHuman}
          disabled={loading || !query.trim()}
          className="bg-purple-600 text-white py-3 px-6 rounded-lg hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {loading ? "Finding a Contact..." : "Contact a Human"}
        </button>

        {/* Contact Information Display */}
        {humanPhoneRaw && humanPhoneRaw !== "No Phone Available" && (
          <div className="mt-6 bg-blue-50 p-6 rounded-lg shadow">
            <div className="flex items-center flex-wrap">
              <p className="text-gray-700 mb-2 mr-4">
                <strong>Phone Number:</strong> {humanPhoneRaw}
              </p>
              <a href={`tel:${humanPhoneRaw}`}>
                <button
                  className="bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition flex items-center"
                >
                  <svg
                    className="w-5 h-5 mr-2"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 5a2 2 0 012-2h3.28a2 2 0 011.664.89l1.82 3.63a2 2 0 01-.105 2.286l-1.27 1.27a16.036 16.036 0 006.16 6.16l1.27-1.27a2 2 0 012.286-.105l3.63 1.82A2 2 0 0121 16.72V20a2 2 0 01-2 2h-4.28a2 2 0 01-1.664-.89l-1.82-3.63a2 2 0 01.105-2.286l1.27-1.27a12.034 12.034 0 00-6.16-6.16l-1.27 1.27a2 2 0 01-2.286.105l-3.63-1.82A2 2 0 013 16.72V5z"
                    />
                  </svg>
                  Call Now
                </button>
              </a>
            </div>
          </div>
        )}

        {/* No Phone Available Message */}
        {humanPhoneRaw === "No Phone Available" && (
          <div className="mt-6 bg-yellow-100 text-yellow-700 p-6 rounded-lg shadow">
            <h3 className="text-2xl font-bold text-gray-700 mb-4">No Contact Available</h3>
            <p className="text-gray-700">
              Currently, there is no available phone contact for your query. Please try again later or reach out through alternative methods.
            </p>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="w-full max-w-2xl bg-red-100 text-red-600 p-4 rounded-lg shadow mb-8">
          {error}
        </div>
      )}

      {/* Checklist Display */}
      {parsedChecklist && (
        <div className="w-full max-w-2xl bg-white p-8 rounded-2xl shadow-lg mb-8">
          <h3 className="text-2xl font-bold text-gray-700 mb-6">Generated Checklist</h3>
          {renderChecklist()}
          {parsedChecklist.closing && (
            <p className="mt-6 italic text-gray-600">{parsedChecklist.closing}</p>
          )}
        </div>
      )}

      {/* Raw Checklist JSON Fallback */}
      {!parsedChecklist && rawChecklist && (
        <div className="w-full max-w-2xl bg-gray-100 p-6 rounded-lg shadow mb-8">
          <h3 className="text-2xl font-bold text-gray-700 mb-4">Raw Checklist JSON</h3>
          <pre className="whitespace-pre-wrap bg-gray-200 p-4 rounded-lg overflow-auto text-gray-800">
            {rawChecklist}
          </pre>
        </div>
      )}
    </div>
  );
}
