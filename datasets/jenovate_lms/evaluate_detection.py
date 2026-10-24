"""Evaluate the existing text-signature detector against synthetic LMS events."""
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).parent; sys.path.insert(0,str(ROOT.parents[1]/"backend"))
from app.services.security_detection import analyze_text
def main():
    events=[json.loads(line) for line in (ROOT/"security_events.jsonl").read_text(encoding="utf-8").splitlines() if line]
    tp=fp=tn=fn=0
    for event in events:
        predicted=analyze_text(event["action"],event["source"])["matched"]; actual=event["ground_truth"]=="suspicious"
        if predicted and actual:tp+=1
        elif predicted:fp+=1
        elif actual:fn+=1
        else:tn+=1
    precision=tp/(tp+fp) if tp+fp else 0; recall=tp/(tp+fn) if tp+fn else 0; f1=2*precision*recall/(precision+recall) if precision+recall else 0
    report={"dataset":"jenovate_lms","events":len(events),"confusion_matrix":{"tp":tp,"fp":fp,"tn":tn,"fn":fn},"precision":round(precision,4),"recall":round(recall,4),"f1":round(f1,4),"note":"Synthetic labels are evaluation-only and are not supplied to the detector."}
    (ROOT/"detection_evaluation.json").write_text(json.dumps(report,indent=2),encoding="utf-8"); print(json.dumps(report,indent=2))
if __name__=="__main__":main()
