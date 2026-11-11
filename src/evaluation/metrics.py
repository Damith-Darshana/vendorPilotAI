from typing import List,Dict,Optional
from dataclasses import dataclass

@dataclass
class FieldResult:
  field_name:str
  expected: Optional[str]
  actual : Optional[str]
  correct:bool
  page_expected:Optional[int]
  page_actual:Optional[int]
  evidence_correct:Optional[bool]


@dataclass
class FindingResult:
  expected_rule:Optional[str] #none if no finding expected
  actual_rule: Optional[str] #None if no finding Reported
  match:bool


def compute_evidence_correctness(field_results:List[FieldResult])-> Optional[float]:
  """Of fields extracted correctly, what fraction had the right page number?"""
  correct_with_evidence = [r for r in field_results if r.correct and r.evidence_correct is not None]
  if not correct_with_evidence:
    return None
  return sum(1 for r in correct_with_evidence if r.evidence_correct) / len(correct_with_evidence)

def compute_finding_metrics(finding_results:List[FindingResult])-> Dict[str,float]:
  """Precission, recall, F1 for finding Detection"""
  tp = sum(1 for r in finding_results if r.match and r.expected_rule is not None)
  fp = sum(1 for r in finding_results if not r.match and r.actual_rule is not None)
  fn = sum(1 for r in finding_results if not r.match and r.expected_rule is not None)

  precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
  recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
  f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

  return {
    "precision":precision,
    "recall": recall,
    "f1":f1,
    "tp":tp, "fp": fp, "fn":fn,
  }

def compute_outcome_accuracy(expected: List[str], actual: List[str]) -> float:
    """Fraction of cases where routing outcome matched expected."""
    if not expected:
        return 1.0
    matches = sum(1 for e, a in zip(expected, actual) if e == a)
    return matches / len(expected)








