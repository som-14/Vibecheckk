// Plain-English description: Analysis result page that polls the backend every 3 seconds until status is completed, then displays virality score and critiques.

import { useState, useEffect } from "react";
import { useRouter } from "next/router";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ResultPage() {
  const router = useRouter();
  const { id } = router.query;

  const [analysis, setAnalysis] = useState(null);
  const [status, setStatus] = useState("PROCESSING");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;

    const token = typeof window !== "undefined" ? sessionStorage.getItem("vibecheck_token") : null;
    if (!token) {
      router.replace("/login");
      return;
    }

    let isSubscribed = true;

    const fetchAnalysis = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/analysis/${id}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.status === 403) {
          setError("Forbidden: You do not have permission to view this video analysis.");
          return;
        }

        if (response.status === 404) {
          setError("Video not found.");
          return;
        }

        const data = await response.json();

        if (isSubscribed) {
          if (data.status === "COMPLETED") {
            setAnalysis(data);
            setStatus("COMPLETED");
          } else {
            setStatus("PROCESSING");
          }
        }
      } catch (err) {
        if (isSubscribed) {
          setError(err.message || "Failed to fetch analysis.");
        }
      }
    };

    // Initial fetch immediately
    fetchAnalysis();

    // Poll every 3 seconds until completed
    const intervalId = setInterval(() => {
      if (status !== "COMPLETED") {
        fetchAnalysis();
      }
    }, 3000);

    return () => {
      isSubscribed = false;
      clearInterval(intervalId);
    };
  }, [id, status, router]);

  return (
    <div>
      <h3>Virality Analysis Result</h3>
      <p>Video ID: {id}</p>

      {error && (
        <div style={{ color: "red", padding: "10px", border: "1px solid red", marginBottom: "16px" }}>
          {error}
        </div>
      )}

      {status === "PROCESSING" && !error && (
        <div style={{ padding: "20px", background: "#f0f0f0", textAlign: "center" }}>
          <h4>Analyzing video...</h4>
          <p>Multi-agent evaluation in progress. Polling status every 3 seconds.</p>
        </div>
      )}

      {status === "COMPLETED" && analysis && (
        <div>
          <div style={{ background: "#e8f4fd", padding: "16px", borderRadius: "4px", marginBottom: "20px" }}>
            <p><strong>Virality Score:</strong> {analysis.virality_score} / 100</p>
            <p><strong>Classification:</strong> {analysis.classification}</p>
            <p><strong>Audience Fit Score:</strong> {analysis.audience_fit_score}</p>
          </div>

          <h4>Agent Critiques</h4>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {analysis.critiques && analysis.critiques.map((critique) => (
              <div
                key={critique.critique_id}
                style={{ border: "1px solid #ddd", padding: "12px", borderRadius: "4px" }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                  <strong>{critique.agent_role}</strong>
                  <span>Priority: {critique.priority}</span>
                </div>
                {critique.timestamp_marker !== null && (
                  <p style={{ margin: "4px 0", color: "#666", fontSize: "0.9em" }}>
                    Timestamp: {critique.timestamp_marker}s
                  </p>
                )}
                <p style={{ margin: "6px 0 0 0" }}>{critique.feedback_text}</p>
              </div>
            ))}
          </div>

          <div style={{ marginTop: "24px" }}>
            <button
              onClick={() => router.push("/upload")}
              style={{ padding: "8px 16px", cursor: "pointer" }}
            >
              Upload Another Video
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

