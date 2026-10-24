# Jenovate LMS Synthetic Dataset

This is wholly fictional, reproducible data for evaluating CyberShield XDR with a learning-management-system context. It contains no real Jenovate records, credentials, IP addresses, devices, or geolocation. Generator seed: `20261023`.

## Files

- `users.csv`: fictional administrators, mentors, and students.
- `courses.csv`, `batches.csv`, `course_modules.csv`: course structure and ownership.
- `enrollments.csv`, `student_progress.csv`: learner enrollment and progress.
- `quizzes.csv`, `quiz_attempts.csv`, `task_submissions.csv`, `announcements.csv`: academic activity.
- `security_events.jsonl`: benign and suspicious LMS audit events. `ground_truth` is evaluation-only and must never be supplied to a detector or stored by the adapter.
- `generate_dataset.py`, `validate_dataset.py`, `evaluate_detection.py`: generation, validation, and evaluation tools.

## Commands

```powershell
python datasets/jenovate_lms/generate_dataset.py --students 80 --seed 20261023
python datasets/jenovate_lms/validate_dataset.py
./backend/.venv/Scripts/python.exe datasets/jenovate_lms/evaluate_detection.py
```

The adapter in `backend/app/services/jenovate_lms.py` normalizes JSONL events to the existing `SecurityLog` schema. It validates fields and severity, converts timestamps to timezone-aware ISO-8601, retains source provenance, omits `ground_truth`, and avoids duplicate `event_id` values during a single import.
