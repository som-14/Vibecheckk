# Plain-English description: Provides realistic mock AI evaluation functions for transcription, cut analysis, virality scoring, audience fit, and multi-agent critiques.

from typing import List, Dict, Any

def mock_transcribe(video_id: str) -> str:
    # MOCK - replace with real model (e.g. OpenAI Whisper / Whisper.cpp)
    return (
        "Stop scrolling! If you want to crack short-form virality in 2026, "
        "you need a visual pattern interrupt in the first 3 seconds, followed by high-density pacing."
    )

def mock_count_cuts_first_3_seconds(video_id: str) -> int:
    # MOCK - replace with real model (e.g. OpenCV scene cut detection)
    return 3

def mock_compute_virality_score(cut_count: int = 3, transcript_len: int = 120) -> float:
    # MOCK - replace with real model (e.g. Multimodal virality prediction network)
    # Returns score between 0 and 100
    base_score = 75.0
    if cut_count >= 2:
        base_score += 10.0
    return min(100.0, max(0.0, base_score))

def mock_audience_fit(persona_id: int = 1) -> float:
    # MOCK - replace with real model (e.g. CLIP / Audience interest embedding alignment)
    # Returns score between 0 and 1 (e.g. 0.88)
    return 0.88

def mock_generate_critiques(virality_score: float = 85.0, cut_count: int = 3) -> List[Dict[str, Any]]:
    # MOCK - replace with real model (e.g. Multi-agent LLM critique system)
    return [
        {
            "agent_role": "Hook Doctor",
            "feedback_text": f"Excellent visual hook with {cut_count} quick cuts in the first 3 seconds, minimizing early drop-off.",
            "timestamp_marker": 1.5,
            "priority": "INFO"
        },
        {
            "agent_role": "Persona Agent",
            "feedback_text": "Strong language alignment with Gen Z demographic, but add highlighted animated captions to improve sound-off retention.",
            "timestamp_marker": 4.0,
            "priority": "MEDIUM"
        },
        {
            "agent_role": "Audio Engineer",
            "feedback_text": "Voice track is clear; consider adding subtle background trending music to increase emotional resonance.",
            "timestamp_marker": 0.5,
            "priority": "INFO"
        }
    ]

