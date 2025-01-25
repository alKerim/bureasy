import { useState, useRef } from "react";

export default function CheckListPage() {
  const [jsonFiles, setJsonFiles] = useState([]);
  const [uploadStatus, setUploadStatus] = useState("");
  const [query, setQuery] = useState("");
  const [rawChecklist, setRawChecklist] = useState("");
  const [parsedChecklist, setParsedChecklist] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  
  const fileInputRef = useRef(null);

  // Handle multiple JSON files
  const handleFilesSelected = (files) => {
    const selectedFiles = Array.from(files).filter(file => file.type === "application/json");
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
        const parsed = JSON.parse(data.checklist);
        setParsedChecklist(parsed);
      } catch (err) {
        setParsedChecklist(null); // Fallback to raw output
        console.warn("The checklist response is not valid JSON.");
      }
    } catch (err) {
      setError(err.message || "An error occurred while generating the checklist.");
    } finally {
      setLoading(false);
    }
  };

  // Render parsed checklist
  const renderChecklist = () => {
    if (!parsedChecklist || !Array.isArray(parsedChecklist.steps)) return null;

    return (
      <ul className="space-y-3">
        {parsedChecklist.steps.map((step, index) => (
          <li key={index} className="flex items-start space-x-3">
            <input
              type="checkbox"
              className="mt-1 h-5 w-5 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <span className="text-gray-800">{step}</span>
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
            {isDragging ? "Release to upload" : "Drag & Drop JSON Files or Click to Select"}
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
        {uploadStatus && <p className="mt-4 text-green-600">{uploadStatus}</p>}
      </div>

      {/* Step 2: Generate Checklist */}
      <div className="w-full max-w-2xl bg-white p-8 rounded-2xl shadow-lg mb-8">
        <h2 className="text-2xl font-semibold text-gray-700 mb-6">2. Generate Checklist</h2>
        <textarea
          rows="4"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter your query here..."
          className="w-full p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none text-gray-800"
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

      {/* Error Display */}
      {error && (
        <div className="w-full max-w-2xl bg-red-100 text-red-600 p-4 rounded-lg shadow mb-8">
          {error}
        </div>
      )}

      {/* Checklist Display */}
      {parsedChecklist && (
        <div className="w-full max-w-2xl bg-white p-8 rounded-2xl shadow-lg">
          <h3 className="text-2xl font-bold text-gray-700 mb-6">Generated Checklist</h3>
          {renderChecklist()}
        </div>
      )}

      {/* Raw JSON Fallback */}
      {!parsedChecklist && rawChecklist && (
        <div className="w-full max-w-2xl bg-gray-100 p-6 rounded-lg shadow">
          <h3 className="text-2xl font-bold text-gray-700 mb-4">Raw Checklist JSON</h3>
          <pre className="whitespace-pre-wrap bg-gray-200 p-4 rounded-lg overflow-auto text-gray-800">
            {rawChecklist}
          </pre>
        </div>
      )}
    </div>
  );
}
