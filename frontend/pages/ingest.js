// pages/ingest.js
import { useState, useRef } from "react";
import DarkModeToggle from "../components/DarkModeToggle";
import { ArrowUpTrayIcon, CheckCircleIcon, ExclamationCircleIcon } from "@heroicons/react/24/solid";

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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="bg-primary dark:bg-primary-dark text-white py-4 px-6 flex items-center justify-between">
        <div className="flex items-center">
          <ArrowUpTrayIcon className="h-6 w-6 mr-2" />
          <h1 className="text-2xl font-semibold">JSON Data Ingest</h1>
        </div>
        <DarkModeToggle />
      </div>

      {/* Content */}
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-2xl bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold mb-4 text-gray-800 dark:text-gray-100 text-center">
            Upload and Ingest JSON Data
          </h2>

          {/* Error Message */}
          {error && (
            <div className="flex items-center text-red-600 dark:text-red-400 mb-4">
              <ExclamationCircleIcon className="h-5 w-5 mr-2" />
              {error}
            </div>
          )}

          {/* Drag and Drop Area */}
          <div
            className={`flex flex-col items-center justify-center border-2 ${
              isDragging ? "border-indigo-500 bg-indigo-50" : "border-dashed border-indigo-500"
            } rounded-lg p-6 cursor-pointer hover:bg-indigo-50 transition`}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            onClick={() => fileInputRef.current.click()}
          >
            <ArrowUpTrayIcon className="h-12 w-12 text-indigo-500" />
            <span className="mt-2 text-base leading-normal text-gray-600 dark:text-gray-300">
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

          {/* Selected Files List */}
          {jsonFiles.length > 0 && (
            <div className="mt-4">
              <h3 className="text-lg font-medium text-gray-700 dark:text-gray-300">Selected Files:</h3>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-400">
                {jsonFiles.map((file, index) => (
                  <li key={index}>{file.name}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Upload Status */}
          {uploadStatus && (
            <p className="mt-4 text-green-600 dark:text-green-400 flex items-center">
              <CheckCircleIcon className="h-5 w-5 mr-2" /> {uploadStatus}
            </p>
          )}

          {/* Submit Button */}
          <button
            onClick={() => handleUploadJSON(jsonFiles)}
            disabled={loading || jsonFiles.length === 0}
            className="w-full mt-4 bg-primary hover:bg-primary-dark text-white py-2 rounded-md disabled:opacity-50 flex items-center justify-center transition-transform transform hover:scale-105"
          >
            {loading ? "Uploading..." : "Ingest JSON Files"}
          </button>
        </div>
      </div>
    </div>
  );
}
