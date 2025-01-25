// pages/doc-parser.js
import { useState } from "react";
import DarkModeToggle from "../components/DarkModeToggle";
import {
  PaperAirplaneIcon,
  DocumentIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
} from "@heroicons/react/24/solid";

export default function UploadPdfPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [result, setResult] = useState({ document_type: "", tags: [] });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      setError("Please select a PDF file first.");
      return;
    }

    setError("");
    setLoading(true);
    setResult({ document_type: "", tags: [] });

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await fetch("http://localhost:8000/documents/process-pdf", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Error uploading PDF");
      }

      const data = await res.json();
      setResult({
        document_type: data.document_type,
        tags: data.tags,
      });
    } catch (err) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="bg-primary dark:bg-primary-dark text-white py-4 px-6 flex items-center justify-between">
        <div className="flex items-center">
          <DocumentIcon className="h-6 w-6 mr-2" />
          <h1 className="text-2xl font-semibold">Upload and Parse PDF</h1>
        </div>
        <DarkModeToggle />
      </div>

      {/* Content */}
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-md bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold mb-4 text-gray-800 dark:text-gray-100 text-center">
            Extract Metadata from PDF
          </h2>

          {/* Error Message */}
          {error && (
            <div className="flex items-center text-red-600 dark:text-red-400 mb-4">
              <ExclamationCircleIcon className="h-5 w-5 mr-2" />
              {error}
            </div>
          )}

          {/* File Upload */}
          <div className="mb-4">
            <label className="block text-gray-700 dark:text-gray-300 font-medium mb-2">
              Select PDF File:
            </label>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="block w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-gray-50 dark:bg-gray-700 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-primary hover:bg-primary-dark text-white py-2 rounded-md disabled:opacity-50 flex items-center justify-center transition-transform transform hover:scale-105"
          >
            {loading ? "Processing..." : (
              <>
                <PaperAirplaneIcon className="h-5 w-5 mr-2" /> Process PDF
              </>
            )}
          </button>

          {/* Results Display */}
          {(!loading && result.document_type) && (
            <div className="mt-6 bg-blue-50 dark:bg-blue-700 p-4 rounded-lg shadow">
              <div className="flex items-center mb-2">
                <CheckCircleIcon className="h-6 w-6 text-blue-500 mr-2" />
                <h3 className="text-lg font-bold text-gray-800 dark:text-gray-100">
                  Metadata Extracted
                </h3>
              </div>
              <p className="text-gray-800 dark:text-gray-300 mb-1">
                <strong>Document Type:</strong> {result.document_type}
              </p>
              <p className="text-gray-800 dark:text-gray-300">
                <strong>Tags:</strong> {result.tags.length > 0 ? result.tags.join(", ") : "No tags identified"}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}