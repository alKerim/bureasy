import { useState } from "react";

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
      // data = { filename, document_type, tags: [] }
      setResult({
        document_type: data.document_type,
        tags: data.tags
      });
    } catch (err) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-tr from-blue-200 to-blue-100 p-4">
      <div className="w-full max-w-md bg-white rounded-lg shadow-2xl p-6 text-gray-800">
        <h1 className="text-2xl font-bold mb-4 text-center text-blue-700">Upload PDF to Extract Metadata</h1>

        {error && (
          <div className="text-red-600 mb-4">
            {error}
          </div>
        )}

        <div className="mb-4">
          <label className="block mb-2 font-medium text-gray-700">
            Select PDF:
          </label>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="block w-full p-2 border border-gray-300 rounded"
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Processing..." : "Process PDF"}
        </button>

        {/* Display Results */}
        {(!loading && result.document_type) && (
          <div className="mt-6 p-4 bg-blue-50 border-l-4 border-blue-400 rounded">
            <h2 className="font-semibold text-lg mb-2 text-blue-900">Metadata Extracted</h2>
            <p className="mb-2">
              <strong>Document Type:</strong> {result.document_type}
            </p>
            <p>
              <strong>Tags:</strong>{" "}
              {result.tags.length > 0 ? result.tags.join(", ") : "No tags identified"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
