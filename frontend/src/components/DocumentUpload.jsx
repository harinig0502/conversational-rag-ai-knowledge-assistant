
import { useState } from "react";
import api from "../services/api";

function DocumentUpload() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);

  function handleFileChange(event) {
    const file = event.target.files[0];

    setMessage("");
    setIsError(false);

    if (!file) {
      setSelectedFile(null);
      return;
    }

    const allowedExtensions = [".pdf", ".docx", ".txt"];
    const extension = file.name
      .substring(file.name.lastIndexOf("."))
      .toLowerCase();

    if (!allowedExtensions.includes(extension)) {
      setSelectedFile(null);
      setIsError(true);
      setMessage("Only PDF, DOCX and TXT files are supported.");
      event.target.value = "";
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setSelectedFile(null);
      setIsError(true);
      setMessage("File size must not exceed 10 MB.");
      event.target.value = "";
      return;
    }

    setSelectedFile(file);
  }

  async function handleUpload(event) {
    event.preventDefault();

    if (!selectedFile || isUploading) {
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    setIsUploading(true);
    setMessage("");
    setIsError(false);

    try {
      const response = await api.post(
        "/documents/upload",
        formData
      );

      setMessage(
        `${response.data.filename} uploaded successfully. ${response.data.chunks_indexed} chunks indexed.`
      );
      setSelectedFile(null);
      event.target.reset();
    } catch (error) {
      setIsError(true);

      setMessage(
        error.response?.data?.message ||
        error.response?.data?.detail ||
        "Document upload failed. Please check your backend services."
      );
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-bold text-slate-800">
        Upload Documents
      </h2>

      <p className="mt-1 text-sm text-slate-500">
        Upload PDF, DOCX or TXT files to your knowledge base.
      </p>

      <form onSubmit={handleUpload} className="mt-4">
        <input
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={handleFileChange}
          disabled={isUploading}
          className="block w-full text-sm text-slate-600 file:mr-4 file:rounded-lg file:border-0 file:bg-blue-50 file:px-4 file:py-2 file:font-semibold file:text-blue-700 hover:file:bg-blue-100"
        />

        {selectedFile && (
          <p className="mt-3 text-sm text-slate-600">
            Selected: {selectedFile.name}
          </p>
        )}

        <button
          type="submit"
          disabled={!selectedFile || isUploading}
          className="mt-4 rounded-lg bg-blue-600 px-5 py-2 font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isUploading ? "Uploading..." : "Upload Document"}
        </button>
      </form>

      {message && (
        <p
          className={`mt-4 rounded-lg p-3 text-sm ${
            isError
              ? "bg-red-50 text-red-700"
              : "bg-green-50 text-green-700"
          }`}
        >
          {message}
        </p>
      )}

      <p className="mt-3 text-xs text-slate-400">
        Maximum file size: 10 MB
      </p>
    </div>
  );
}

export default DocumentUpload;
