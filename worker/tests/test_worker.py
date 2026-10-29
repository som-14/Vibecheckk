# Plain-English description: Tests for the Celery worker logic, including score classification, critique generation, and task retry configuration.

import pytest
from worker.tasks import classify_virality_score, process_video
from worker.mock_models import mock_generate_critiques, mock_compute_virality_score

# 1. Test virality score classification
def test_score_classification_boundaries():
    # VIRAL: score >= 70
    assert classify_virality_score(100.0) == "VIRAL"
    assert classify_virality_score(70.0) == "VIRAL"
    assert classify_virality_score(70.1) == "VIRAL"

    # AVERAGE: 40 to 69.9
    assert classify_virality_score(69.9) == "AVERAGE"
    assert classify_virality_score(55.0) == "AVERAGE"
    assert classify_virality_score(40.0) == "AVERAGE"

    # LOW: score < 40
    assert classify_virality_score(39.9) == "LOW"
    assert classify_virality_score(15.0) == "LOW"
    assert classify_virality_score(0.0) == "LOW"

# 2. Test critique generation structure and content
def test_critique_generation():
    critiques = mock_generate_critiques(virality_score=85.0, cut_count=3)

    # Must generate 2 to 3 critiques
    assert 2 <= len(critiques) <= 3

    roles = [c["agent_role"] for c in critiques]
    assert "Hook Doctor" in roles
    assert "Persona Agent" in roles

    valid_priorities = {"CRITICAL", "MEDIUM", "INFO"}
    for critique in critiques:
        assert "agent_role" in critique and len(critique["agent_role"]) > 0
        assert "feedback_text" in critique and len(critique["feedback_text"]) > 0
        assert "priority" in critique and critique["priority"] in valid_priorities
        assert "timestamp_marker" in critique

# 3. Test Celery task configuration (retries and name)
def test_task_configuration():
    assert process_video.name == "process_video"
    assert process_video.max_retries == 3
    assert process_video.default_retry_delay == 5

