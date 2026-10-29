// Plain-English description: Video upload page allowing creators to upload MP4 videos with persona selection and caption.

import { useState, useEffect } from "react";
import { useRouter } from "next/router";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState(null);
  const [personaId, setPersonaId] = useState("1");
  const [caption, setCaption] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check if user is authenticated
    const token = typeof window !== "undefined" ? sessionStorage.getItem("vibecheck_token") : null;
    if (!token) {
      router.replace("/login");
    }
  }, [router]);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (!selectedFile.name.toLowerCase().endsWith(".mp4")) {
        setError("Please select an MP4 video file.");
        setFile(null);
        return;
      }
      setError("");
      setFile(selectedFile);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select an MP4 video file.");
      return;
    }

    const token = sessionStorage.getItem("vibecheck_token");
    if (!token) {
      router.replace("/login");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("persona_id", personaId);
      formData.append("caption", caption);

      const response = await fetch(`${API_BASE_URL}/api/v1/videos/upload`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Video upload failed.");
      }

      // Redirect to the result polling page
      router.push(`/result/${data.video_id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h3>Upload Short Video</h3>
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        <div>
          <label style={{ display: "block", marginBottom: "4px" }}>Select Video (MP4 only, max 50MB):</label>
          <input
            type="file"
            accept=".mp4,video/mp4"
            onChange={handleFileChange}
            required
            style={{ width: "100%" }}
          />
        </div>

        <div>
          <label style={{ display: "block", marginBottom: "4px" }}>Target Persona:</label>
          <select
            value={personaId}
            onChange={(e) => setPersonaId(e.target.value)}
            style={{ width: "100%", padding: "8px" }}
          >
            <option value="1">Gen Z Trendsetters (Ages 14-24)</option>
            <option value="2">Millennial Techies (Ages 25-40)</option>
            <option value="3">General Casual Viewers (Ages 18-65)</option>
          </select>
        </div>

        <div>
          <label style={{ display: "block", marginBottom: "4px" }}>Video Caption / Hook:</label>
          <textarea
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            rows={3}
            placeholder="Enter caption or hook..."
            style={{ width: "100%", padding: "8px" }}
          />
        </div>

        {error && (
          <div style={{ color: "red", padding: "8px", border: "1px solid red" }}>
            {error}
          </div>
        )}

        <button type="submit" disabled={loading} style={{ padding: "10px", cursor: "pointer" }}>
          {loading ? "Uploading..." : "Submit Video for Analysis"}
        </button>
      </form>
    </div>
  );
}

