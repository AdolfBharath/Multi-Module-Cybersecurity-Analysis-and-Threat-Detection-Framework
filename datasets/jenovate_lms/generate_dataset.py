"""Generate fictional Jenovate LMS data and security telemetry (seeded, no PII)."""
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SEED = 20261023
ROOT = Path(__file__).parent
NAMES = ["Avery", "Blake", "Casey", "Devon", "Emery", "Finley", "Gray", "Harper", "Indigo", "Jordan", "Kai", "Logan", "Morgan", "Nova", "Parker", "Quinn"]
COURSES = [("Python Foundations", "programming", "beginner"), ("Applied Cyber Defense", "cybersecurity", "intermediate"), ("Modern Web Development", "web development", "intermediate"), ("Practical Machine Learning", "AI/ML", "advanced"), ("Data Analytics Essentials", "data analytics", "beginner")]

def write_csv(name: str, rows: list[dict]) -> None:
    with (ROOT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [])
        writer.writeheader(); writer.writerows(rows)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--students", type=int, default=80)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args(); rng = random.Random(args.seed); ROOT.mkdir(parents=True, exist_ok=True)
    now = datetime(2026, 10, 1, 9, tzinfo=timezone.utc)
    users = []
    for i, role in enumerate(["admin", "admin", "mentor", "mentor", "mentor", "mentor", "mentor"]):
        users.append({"user_id":f"USR-{i+1:04d}","full_name":f"{NAMES[i]} {['Reed','Lane','Shaw','Cruz','Vale'][i%5]}","email":f"{role}.{i+1}@jenovate.example.test","role":role,"status":"active","created_at":(now-timedelta(days=300-i)).isoformat()})
    for i in range(args.students):
        users.append({"user_id":f"USR-{i+8:04d}","full_name":f"{NAMES[i%len(NAMES)]} Learner{i+1:03d}","email":f"student.{i+1:03d}@jenovate.example.test","role":"student","status":"active" if i%19 else "inactive","created_at":(now-timedelta(days=rng.randint(30,280))).isoformat()})
    mentors=[u for u in users if u["role"]=="mentor"]; students=[u for u in users if u["role"]=="student"]
    courses=[]; batches=[]; modules=[]; quizzes=[]
    for i,(name,cat,level) in enumerate(COURSES,1):
        cid=f"CRS-{i:03d}"; mentor=mentors[(i-1)%len(mentors)]
        courses.append({"course_id":cid,"course_name":name,"category":cat,"level":level,"mentor_id":mentor["user_id"],"status":"published"})
        batches.append({"batch_id":f"BAT-{i:03d}","batch_name":f"{name} Cohort 2026-{i}","course_id":cid,"mentor_id":mentor["user_id"],"start_date":"2026-01-15","end_date":"2026-11-30","status":"active"})
        for order in range(1,7): modules.append({"module_id":f"MOD-{i:03d}-{order:02d}","course_id":cid,"module_title":f"{name} Module {order}","module_order":order,"content_type":"video" if order%2 else "lab","duration_minutes":45+order*10,"status":"published"})
        quizzes.append({"quiz_id":f"QZ-{i:03d}","course_id":cid,"quiz_title":f"{name} Knowledge Check","total_marks":100,"passing_marks":50,"status":"published"})
    enrollments=[]; progress=[]; attempts=[]; submissions=[]; announcements=[]
    for course,batch,quiz in zip(courses,batches,quizzes):
        announcements.append({"announcement_id":f"ANN-{course['course_id'][-3:]}","batch_id":batch["batch_id"],"title":"Weekly learning update","message":"Complete this week's module and submit questions in the learning forum.","created_by_mentor_id":batch["mentor_id"],"created_date":"2026-09-20"})
    for i,student in enumerate(students,1):
        course=courses[i%len(courses)]; batch=batches[i%len(batches)]; quiz=quizzes[i%len(quizzes)]; completed=rng.randint(0,6); marks=rng.randint(35,100)
        enrollments.append({"enrollment_id":f"ENR-{i:05d}","student_id":student["user_id"],"course_id":course["course_id"],"batch_id":batch["batch_id"],"enrollment_date":"2026-02-01","enrollment_status":"active"})
        progress.append({"progress_id":f"PRG-{i:05d}","student_id":student["user_id"],"course_id":course["course_id"],"modules_completed":completed,"total_modules":6,"progress_percent":round(completed/6*100,2),"last_activity_date":f"2026-09-{(i%28)+1:02d}"})
        attempts.append({"attempt_id":f"ATT-{i:05d}","student_id":student["user_id"],"quiz_id":quiz["quiz_id"],"attempt_date":f"2026-09-{(i%28)+1:02d}","marks_obtained":marks,"total_marks":100,"result":"pass" if marks>=50 else "fail"})
        submissions.append({"submission_id":f"SUB-{i:05d}","student_id":student["user_id"],"course_id":course["course_id"],"batch_id":batch["batch_id"],"task_title":"Applied exercise","submitted_at":(now-timedelta(days=i%25)).isoformat(),"status":"graded","marks":rng.randint(45,100),"mentor_feedback":"Synthetic feedback: review the submitted approach."})
    for name,rows in [("users.csv",users),("courses.csv",courses),("batches.csv",batches),("enrollments.csv",enrollments),("course_modules.csv",modules),("student_progress.csv",progress),("quizzes.csv",quizzes),("quiz_attempts.csv",attempts),("task_submissions.csv",submissions),("announcements.csv",announcements)]: write_csv(name,rows)
    events=[]
    benign=[("login","login_success","successful login","info"),("course","course_view","course module viewed","info"),("submission","submit_assignment","assignment submitted","info")]
    suspicious=[("auth","failed_login","failed login attempt", "medium"),("access","forbidden_student_record","../student-record access denied", "high"),("admin","unauthorized_role_change","DROP TABLE roles request rejected", "critical"),("malware","assignment_upload_quarantined","malware signature detected in assignment upload", "high")]
    for i in range(args.students*4):
        actor=students[i%len(students)]; event=benign[i%len(benign)]; label="benign"
        if i%11==0: event=suspicious[(i//11)%len(suspicious)]; label="suspicious"
        metadata={"dataset":"jenovate_lms","generator_seed":args.seed}
        if label=="suspicious": metadata["network"]={"src_ip":f"198.51.100.{(i % 200)+1}","dst_ip":"10.20.0.15","protocol":"HTTPS","port":443,"bytes_in":1200+i*4,"bytes_out":640+i*3}
        payload={"event_id":f"EVT-{i+1:06d}","timestamp":(now+timedelta(minutes=i)).isoformat(),"source":"jenovate_lms","event_type":event[1],"actor_id":actor["user_id"],"actor_role":actor["role"],"target_type":"course","target_id":courses[i%len(courses)]["course_id"],"action":event[2],"outcome":"denied" if label=="suspicious" else "success","severity":event[3],"metadata":metadata,"ground_truth":label}
        events.append(payload)
    with (ROOT/"security_events.jsonl").open("w",encoding="utf-8") as handle:
        for event in events: handle.write(json.dumps(event,sort_keys=True)+"\n")
    print(json.dumps({"seed":args.seed,"users":len(users),"events":len(events)},indent=2))

if __name__ == "__main__": main()
