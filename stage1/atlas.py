"""Stage 1: ATLAS Detection Engine

ATLAS (Automated Trial Laboratory & Adverse-event Surveillance) performs automated
first-pass surveillance across synthetic clinical trial study data cuts.
Detects:
- Safety findings (e.g. miscoded serious adverse events, liver elevations)
- Data-quality findings (e.g. chronological errors, missing dosing, unit discrepancies)
- Compliance findings (e.g. visit window excursions)
- Monitoring findings
- Site-level patterns
"""

from typing import Dict, List, Any, Optional
from stage1.data import CUTS, CUT_1_DATA


class AtlasFinding:
    """Represents a standardized Stage 1 clinical finding."""
    def __init__(
        self,
        finding_code: str,
        subject_id: str,
        site: str,
        severity: str,
        rationale: str,
        domain: str,
        sequence: int,
        source_evidence: Dict[str, Any],
        cut: int
    ):
        self.finding_code = finding_code
        self.subject_id = subject_id
        self.site = site
        self.severity = severity
        self.rationale = rationale
        self.domain = domain
        self.sequence = sequence
        self.source_evidence = source_evidence
        self.cut = cut

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_code": self.finding_code,
            "subject_id": self.subject_id,
            "site": self.site,
            "severity": self.severity,
            "rationale": self.rationale,
            "domain": self.domain,
            "sequence": self.sequence,
            "source_evidence": self.source_evidence,
            "cut": self.cut
        }


class Atlas:
    """Stage 1 ATLAS Surveillance System."""

    def __init__(self, default_cut: int = 1):
        self.default_cut = default_cut

    def get_raw_data(self, cut: Optional[int] = None) -> Dict[str, List[Dict[str, Any]]]:
        cut_num = cut if cut is not None else self.default_cut
        return CUTS.get(cut_num, CUT_1_DATA)

    def detect_findings(self, cut: int) -> List[Dict[str, Any]]:
        """Run Stage 1 Atlas surveillance against the selected cut data.
        Returns a list of finding dictionaries referencing real synthetic data.
        """
        data = self.get_raw_data(cut)
        findings: List[AtlasFinding] = []

        # 1. AE Safety & Miscoding Detection (AESHOSP=Y and AESER=N rule)
        for ae in data.get("AE", []):
            usubjid = ae.get("USUBJID", "")
            site = ae.get("SITEID", "")
            seq = ae.get("AESEQ", 1)
            aeshosp = ae.get("AESHOSP", "N")
            aeser = ae.get("AESER", "N")

            # CRITICAL RULE: IF AESHOSP = Y AND AESER = N, MUST be recognized as serious
            if aeshosp == "Y" and aeser == "N":
                findings.append(
                    AtlasFinding(
                        finding_code="SAE_MISCODED",
                        subject_id=usubjid,
                        site=site,
                        severity="HIGH",
                        rationale="Inpatient hospitalization reported (AESHOSP=Y) but serious event flag marked 'N' (AESER=N). Miscoded potential SAE requiring immediate expedited regulatory escalation.",
                        domain="AE",
                        sequence=seq,
                        source_evidence={
                            "domain": "AE",
                            "USUBJID": usubjid,
                            "SITEID": site,
                            "AESEQ": seq,
                            "AETERM": ae.get("AETERM"),
                            "AESTDTC": ae.get("AESTDTC"),
                            "AEENDTC": ae.get("AEENDTC"),
                            "AESHOSP": aeshosp,
                            "AESER": aeser,
                            "AESEV": ae.get("AESEV"),
                            "AEREL": ae.get("AEREL"),
                            "SOURCE_DOC": ae.get("SOURCE_DOC"),
                            "COMMENT": ae.get("COMMENT", "")
                        },
                        cut=cut
                    )
                )

            # Chronology check: AE end date before start date
            aestdtc = ae.get("AESTDTC", "")
            aeendtc = ae.get("AEENDTC", "")
            if aestdtc and aeendtc and aeendtc < aestdtc:
                findings.append(
                    AtlasFinding(
                        finding_code="DATE_CHRONOLOGY_ERROR",
                        subject_id=usubjid,
                        site=site,
                        severity="LOW",
                        rationale=f"Adverse event resolution date ({aeendtc}) precedes onset date ({aestdtc}). Chronologically invalid.",
                        domain="AE",
                        sequence=seq,
                        source_evidence={
                            "domain": "AE",
                            "USUBJID": usubjid,
                            "SITEID": site,
                            "AESEQ": seq,
                            "AETERM": ae.get("AETERM"),
                            "AESTDTC": aestdtc,
                            "AEENDTC": aeendtc,
                            "SOURCE_DOC": ae.get("SOURCE_DOC")
                        },
                        cut=cut
                    )
                )

        # 2. Cross-domain Chronology: AE before first dose
        ex_first_doses: Dict[str, str] = {}
        for ex in data.get("EX", []):
            subj = ex.get("USUBJID", "")
            stdtc = ex.get("EXSTDTC", "")
            if subj and stdtc:
                if subj not in ex_first_doses or stdtc < ex_first_doses[subj]:
                    ex_first_doses[subj] = stdtc

        for ae in data.get("AE", []):
            subj = ae.get("USUBJID", "")
            aestdtc = ae.get("AESTDTC", "")
            first_dose = ex_first_doses.get(subj)
            if first_dose and aestdtc and aestdtc < first_dose:
                findings.append(
                    AtlasFinding(
                        finding_code="AE_BEFORE_FIRST_DOSE",
                        subject_id=subj,
                        site=ae.get("SITEID", ""),
                        severity="MEDIUM",
                        rationale=f"Adverse event onset ({aestdtc}) occurred prior to first study drug administration ({first_dose}). Requires clarification whether pre-treatment Medical History.",
                        domain="AE",
                        sequence=ae.get("AESEQ", 1),
                        source_evidence={
                            "domain": "AE",
                            "USUBJID": subj,
                            "AETERM": ae.get("AETERM"),
                            "AESTDTC": aestdtc,
                            "FIRST_DOSE_DATE": first_dose,
                            "SOURCE_DOC": ae.get("SOURCE_DOC")
                        },
                        cut=cut
                    )
                )

        # 3. Lab Findings: Liver signal candidate & Unit discrepancies
        for lb in data.get("LB", []):
            subj = lb.get("USUBJID", "")
            site = lb.get("SITEID", "")
            test = lb.get("LBTESTCD", "")
            val = lb.get("LBORRES", 0.0)
            u = lb.get("LBORRESU", "")
            hi = lb.get("LBORNRHI", 0.0)
            is_scr = lb.get("IS_SCREENING", False)

            # Post-baseline elevated ALT/AST -> Liver candidate
            if not is_scr and test in ["ALT", "AST"] and hi > 0 and val > (1.5 * hi):
                findings.append(
                    AtlasFinding(
                        finding_code="LIVER_SIGNAL_CANDIDATE",
                        subject_id=subj,
                        site=site,
                        severity="MEDIUM",
                        rationale=f"Post-baseline {test} value of {val} {u} exceeds 1.5x ULN (ULN: {hi} {u}). Liver signal candidate.",
                        domain="LB",
                        sequence=lb.get("LBSEQ", 1),
                        source_evidence={
                            "domain": "LB",
                            "USUBJID": subj,
                            "SITEID": site,
                            "LBTESTCD": test,
                            "LBTEST": lb.get("LBTEST"),
                            "LBORRES": val,
                            "LBORRESU": u,
                            "LBORNRHI": hi,
                            "VISIT": lb.get("VISIT"),
                            "LBDTC": lb.get("LBDTC"),
                            "SOURCE_DOC": lb.get("SOURCE_DOC")
                        },
                        cut=cut
                    )
                )

            # Plausibility check: Creatinine 110 mg/dL is physiologically implausible for mg/dL
            if test == "CREAT" and u == "mg/dL" and val > 20.0:
                findings.append(
                    AtlasFinding(
                        finding_code="LAB_UNIT_DISCREPANCY",
                        subject_id=subj,
                        site=site,
                        severity="MEDIUM",
                        rationale=f"Serum Creatinine reported as {val} {u}. Normal physiological upper limit is ~1.5 mg/dL. Likely unit error (e.g. reported umol/L as mg/dL).",
                        domain="LB",
                        sequence=lb.get("LBSEQ", 1),
                        source_evidence={
                            "domain": "LB",
                            "USUBJID": subj,
                            "SITEID": site,
                            "LBTESTCD": test,
                            "LBORRES": val,
                            "LBORRESU": u,
                            "SOURCE_DOC": lb.get("SOURCE_DOC")
                        },
                        cut=cut
                    )
                )

        # 4. Exposure & Visit Reconciliation: Missing dose record
        # If visit attended per SV but missing in EX
        ex_visits = set()
        for ex in data.get("EX", []):
            ex_visits.add((ex.get("USUBJID"), ex.get("VISIT")))

        for sv in data.get("SV", []):
            subj = sv.get("USUBJID", "")
            vis = sv.get("VISIT", "")
            # If dosing visit (e.g. Visit 1, Visit 2, Visit 3) attended
            if "Visit" in vis and (subj, vis) not in ex_visits:
                findings.append(
                    AtlasFinding(
                        finding_code="MISSING_DOSE_RECORD",
                        subject_id=subj,
                        site=sv.get("SITEID", ""),
                        severity="MEDIUM",
                        rationale=f"{vis} attendance recorded in Subject Visits domain on {sv.get('SVSTDTC')}, but no corresponding study drug administration logged in EX domain.",
                        domain="EX",
                        sequence=sv.get("SVSEQ", 1),
                        source_evidence={
                            "domain": "SV",
                            "USUBJID": subj,
                            "VISIT": vis,
                            "SVSTDTC": sv.get("SVSTDTC"),
                            "SOURCE_DOC": sv.get("SOURCE_DOC")
                        },
                        cut=cut
                    )
                )

        # 5. Visit Window Excursion in SV
        for sv in data.get("SV", []):
            stdtc = sv.get("SVSTDTC", "")
            tgtdtc = sv.get("TARGETDTC", "")
            window = sv.get("WINDOW_DAYS", 3)
            if stdtc and tgtdtc and stdtc != tgtdtc:
                # simple date diff check
                from datetime import datetime
                try:
                    d_act = datetime.strptime(stdtc, "%Y-%m-%d")
                    d_tgt = datetime.strptime(tgtdtc, "%Y-%m-%d")
                    diff = abs((d_act - d_tgt).days)
                    if diff > window:
                        findings.append(
                            AtlasFinding(
                                finding_code="VISIT_WINDOW_EXCEEDED",
                                subject_id=sv.get("USUBJID", ""),
                                site=sv.get("SITEID", ""),
                                severity="LOW",
                                rationale=f"{sv.get('VISIT')} conducted {diff} days from target date ({tgtdtc}), exceeding the protocol allowable window of ±{window} days.",
                                domain="SV",
                                sequence=sv.get("SVSEQ", 1),
                                source_evidence={
                                    "domain": "SV",
                                    "USUBJID": sv.get("USUBJID"),
                                    "VISIT": sv.get("VISIT"),
                                    "SVSTDTC": stdtc,
                                    "TARGETDTC": tgtdtc,
                                    "DEVIATION_DAYS": diff,
                                    "ALLOWED_WINDOW": window,
                                    "SOURCE_DOC": sv.get("SOURCE_DOC")
                                },
                                cut=cut
                            )
                        )
                except Exception:
                    pass

        # 6. Blank / Incomplete Dose Record in Cut 2 (042-S03-005)
        for ex in data.get("EX", []):
            if ex.get("EXDOSE") == 0 and not ex.get("EXSTDTC"):
                findings.append(
                    AtlasFinding(
                        finding_code="INCOMPLETE_DOSE_RECORD",
                        subject_id=ex.get("USUBJID", ""),
                        site=ex.get("SITEID", ""),
                        severity="MEDIUM",
                        rationale=f"Exposure record for {ex.get('VISIT')} logged with 0 mg dose and blank administration dates.",
                        domain="EX",
                        sequence=ex.get("EXSEQ", 1),
                        source_evidence={
                            "domain": "EX",
                            "USUBJID": ex.get("USUBJID"),
                            "VISIT": ex.get("VISIT"),
                            "SOURCE_DOC": ex.get("SOURCE_DOC")
                        },
                        cut=cut
                    )
                )

        return [f.to_dict() for f in findings]
