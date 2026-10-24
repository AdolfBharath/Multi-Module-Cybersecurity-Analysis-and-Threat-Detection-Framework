"""Validate generated Jenovate LMS CSV relationships and event shapes."""
from __future__ import annotations
import csv, json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).parent
def rows(name):
    with (ROOT/name).open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def ids(records,key):
    values=[r[key] for r in records]; assert len(values)==len(set(values)),f"duplicate {key}"; return set(values)
def main():
    users=rows("users.csv"); courses=rows("courses.csv"); batches=rows("batches.csv"); enrollments=rows("enrollments.csv"); modules=rows("course_modules.csv"); progress=rows("student_progress.csv"); quizzes=rows("quizzes.csv"); attempts=rows("quiz_attempts.csv"); submissions=rows("task_submissions.csv"); announcements=rows("announcements.csv")
    user_ids=ids(users,"user_id"); course_ids=ids(courses,"course_id"); batch_ids=ids(batches,"batch_id"); mentor_ids={r["user_id"] for r in users if r["role"]=="mentor"}; student_ids={r["user_id"] for r in users if r["role"]=="student"}; quiz_ids=ids(quizzes,"quiz_id")
    assert all(r["mentor_id"] in mentor_ids for r in courses+batches)
    assert all(r["student_id"] in student_ids and r["course_id"] in course_ids and r["batch_id"] in batch_ids for r in enrollments+submissions)
    assert all(r["student_id"] in student_ids and r["course_id"] in course_ids and 0<=float(r["progress_percent"])<=100 and int(r["modules_completed"])<=int(r["total_modules"]) for r in progress)
    assert all(r["course_id"] in course_ids and int(r["module_order"])>=1 for r in modules)
    passing={r["quiz_id"]:int(r["passing_marks"]) for r in quizzes}; assert all(r["student_id"] in student_ids and r["quiz_id"] in quiz_ids and 0<=int(r["marks_obtained"])<=int(r["total_marks"]) and (r["result"]==("pass" if int(r["marks_obtained"])>=passing[r["quiz_id"]] else "fail")) for r in attempts)
    assert all(r["batch_id"] in batch_ids and r["created_by_mentor_id"] in mentor_ids for r in announcements)
    events=[json.loads(line) for line in (ROOT/"security_events.jsonl").read_text(encoding="utf-8").splitlines() if line]; ids(events,"event_id"); assert all(e["ground_truth"] in {"benign","suspicious"} and "password" not in e["metadata"] for e in events)
    report={"valid":True,"rows":{n:len(v) for n,v in {"users":users,"courses":courses,"batches":batches,"enrollments":enrollments,"course_modules":modules,"student_progress":progress,"quizzes":quizzes,"quiz_attempts":attempts,"task_submissions":submissions,"announcements":announcements,"security_events":events}.items()},"null_counts":{n:sum(not value for r in v for value in r.values()) for n,v in {"users":users,"courses":courses,"security_events":events}.items()},"labels":dict(Counter(e["ground_truth"] for e in events))}
    (ROOT/"validation_summary.json").write_text(json.dumps(report,indent=2),encoding="utf-8"); print(json.dumps(report,indent=2))
if __name__=="__main__":main()
