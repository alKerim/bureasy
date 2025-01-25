// pages/ingest.js

import { useState, useRef } from "react";

export default function IngestPage() {
  const [jsonFiles, setJsonFiles] = useState([]);
  const [uploadStatus, setUploadStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef(null);

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

  return (
    <div className="min-h-screen bg-gray-50 p-8 flex flex-col items-center">
      <h1 className="text-4xl font-extrabold text-gray-800 mb-8">JSON Data Ingest</h1>

      <div className="w-full max-w-2xl bg-white p-8 rounded-2xl shadow-lg">
        <h2 className="text-2xl font-semibold text-gray-700 mb-6">Ingest JSON Data</h2>
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
        {error && (
          <p className="mt-4 text-red-600">{error}</p>
        )}
      </div>
    </div>
  );
}
