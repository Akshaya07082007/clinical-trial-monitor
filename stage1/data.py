"""Synthetic Clinical Trial Study Data (Study 042 - Oncology/Immunology Protocol 042-ONC)

Contains CDISC SDTM-aligned domains:
- DM: Demographics
- AE: Adverse Events
- LB: Laboratory Measurements
- EX: Exposure / Study Drug Administrations
- CM: Concomitant Medications
- SV: Subject Visits
- MH: Medical History
- DS: Disposition
Organized across study data cuts: Cut 1, Cut 2, Cut 3.
"""

from typing import Dict, List, Any

# Cut 1: Initial Study Data Cut (Enrollment and early cycles)
CUT_1_DATA: Dict[str, List[Dict[str, Any]]] = {
    "DM": [
        {"USUBJID": "042-S01-001", "SITEID": "S01", "AGE": 58, "SEX": "M", "ARM": "Arm A (Active 100mg)", "ENRLDTC": "2026-01-10"},
        {"USUBJID": "042-S01-002", "SITEID": "S01", "AGE": 62, "SEX": "F", "ARM": "Arm A (Active 100mg)", "ENRLDTC": "2026-01-15"},
        {"USUBJID": "042-S01-003", "SITEID": "S01", "AGE": 47, "SEX": "F", "ARM": "Arm B (Active 200mg)", "ENRLDTC": "2026-01-20"},
        {"USUBJID": "042-S02-001", "SITEID": "S02", "AGE": 54, "SEX": "M", "ARM": "Arm A (Active 100mg)", "ENRLDTC": "2026-01-12"},
        {"USUBJID": "042-S02-002", "SITEID": "S02", "AGE": 69, "SEX": "M", "ARM": "Arm B (Active 200mg)", "ENRLDTC": "2026-01-18"},
        {"USUBJID": "042-S02-003", "SITEID": "S02", "AGE": 51, "SEX": "F", "ARM": "Arm A (Active 100mg)", "ENRLDTC": "2026-01-25"},
        {"USUBJID": "042-S02-004", "SITEID": "S02", "AGE": 66, "SEX": "M", "ARM": "Arm B (Active 200mg)", "ENRLDTC": "2026-02-01"},
        {"USUBJID": "042-S03-005", "SITEID": "S03", "AGE": 43, "SEX": "F", "ARM": "Arm A (Active 100mg)", "ENRLDTC": "2026-02-05"},
        {"USUBJID": "042-S03-006", "SITEID": "S03", "AGE": 60, "SEX": "M", "ARM": "Arm B (Active 200mg)", "ENRLDTC": "2026-02-08"},
    ],
    "AE": [
        {
            # Official Worked Example: AESHOSP=Y, AESER=N -> Critical SAE rule violation
            "USUBJID": "042-S02-004", "SITEID": "S02", "AESEQ": 1,
            "AETERM": "Syncope with severe head trauma requiring inpatient hospitalization",
            "AESTDTC": "2026-03-12", "AEENDTC": "2026-03-15",
            "AESER": "N", "AESHOSP": "Y", "AEREL": "POSSIBLE",
            "AESEV": "SEVERE", "AEOUT": "RECOVERED",
            "SOURCE_DOC": "CRF-AE-042-S02-004-Seq1",
            "COMMENT": "Patient collapsed at home, admitted to emergency ward for 72h observation."
        },
        {
            "USUBJID": "042-S01-001", "SITEID": "S01", "AESEQ": 1,
            "AETERM": "Mild transient nausea",
            "AESTDTC": "2026-01-22", "AEENDTC": "2026-01-24",
            "AESER": "N", "AESHOSP": "N", "AEREL": "PROBABLE",
            "AESEV": "MILD", "AEOUT": "RECOVERED",
            "SOURCE_DOC": "CRF-AE-042-S01-001-Seq1"
        },
        {
            # Data issue: AE before first dose (First dose was 2026-02-15)
            "USUBJID": "042-S03-005", "SITEID": "S03", "AESEQ": 1,
            "AETERM": "Severe throbbing tension headache",
            "AESTDTC": "2026-02-10", "AEENDTC": "2026-02-11",
            "AESER": "N", "AESHOSP": "N", "AEREL": "UNLIKELY",
            "AESEV": "MODERATE", "AEOUT": "RECOVERED",
            "SOURCE_DOC": "CRF-AE-042-S03-005-Seq1"
        },
        {
            # Data issue: AE chronology impossible (End date before Start date)
            "USUBJID": "042-S03-006", "SITEID": "S03", "AESEQ": 1,
            "AETERM": "Skin erythema and pruritus",
            "AESTDTC": "2026-02-12", "AEENDTC": "2026-02-05",
            "AESER": "N", "AESHOSP": "N", "AEREL": "POSSIBLE",
            "AESEV": "MILD", "AEOUT": "RECOVERED",
            "SOURCE_DOC": "CRF-AE-042-S03-006-Seq1"
        }
    ],
    "LB": [
        # Subject 042-S01-002: Screening ALT elevated (82 U/L), Visit 2 ALT elevated (94 U/L)
        {
            "USUBJID": "042-S01-002", "SITEID": "S01", "LBSEQ": 1,
            "VISIT": "Screening (Day -7)", "LBDTC": "2026-02-01",
            "LBTESTCD": "ALT", "LBTEST": "Alanine Aminotransferase",
            "LBORRES": 82.0, "LBORRESU": "U/L", "LBORNRLO": 10.0, "LBORNRHI": 45.0,
            "LBNRIND": "HIGH", "IS_SCREENING": True,
            "SOURCE_DOC": "LAB-042-S01-002-SCR-ALT"
        },
        {
            "USUBJID": "042-S01-002", "SITEID": "S01", "LBSEQ": 2,
            "VISIT": "Screening (Day -7)", "LBDTC": "2026-02-01",
            "LBTESTCD": "AST", "LBTEST": "Aspartate Aminotransferase",
            "LBORRES": 54.0, "LBORRESU": "U/L", "LBORNRLO": 10.0, "LBORNRHI": 40.0,
            "LBNRIND": "HIGH", "IS_SCREENING": True,
            "SOURCE_DOC": "LAB-042-S01-002-SCR-AST"
        },
        {
            "USUBJID": "042-S01-002", "SITEID": "S01", "LBSEQ": 3,
            "VISIT": "Visit 2 (Day 14)", "LBDTC": "2026-02-22",
            "LBTESTCD": "ALT", "LBTEST": "Alanine Aminotransferase",
            "LBORRES": 94.0, "LBORRESU": "U/L", "LBORNRLO": 10.0, "LBORNRHI": 45.0,
            "LBNRIND": "HIGH", "IS_SCREENING": False,
            "SOURCE_DOC": "LAB-042-S01-002-V2-ALT"
        },
        # Subject 042-S02-003: Unit discrepancy (110 mg/dL for Creatinine)
        {
            "USUBJID": "042-S02-003", "SITEID": "S02", "LBSEQ": 1,
            "VISIT": "Visit 1 (Baseline)", "LBDTC": "2026-02-02",
            "LBTESTCD": "CREAT", "LBTEST": "Serum Creatinine",
            "LBORRES": 110.0, "LBORRESU": "mg/dL", "LBORNRLO": 0.6, "LBORNRHI": 1.2,
            "LBNRIND": "HIGH", "IS_SCREENING": False,
            "SOURCE_DOC": "LAB-042-S02-003-V1-CREAT"
        },
        # Subject 042-S01-003: eGFR 52 (Compliant under v1 threshold <45, non-compliant under v2 <60)
        {
            "USUBJID": "042-S01-003", "SITEID": "S01", "LBSEQ": 1,
            "VISIT": "Screening (Day -5)", "LBDTC": "2026-01-15",
            "LBTESTCD": "EGFR", "LBTEST": "Estimated GFR (CKD-EPI)",
            "LBORRES": 52.0, "LBORRESU": "mL/min/1.73m2", "LBORNRLO": 60.0, "LBORNRHI": 120.0,
            "LBNRIND": "LOW", "IS_SCREENING": True,
            "SOURCE_DOC": "LAB-042-S01-003-SCR-EGFR"
        }
    ],
    "EX": [
        {"USUBJID": "042-S01-001", "SITEID": "S01", "EXSEQ": 1, "VISIT": "Visit 1", "EXTRT": "Study Drug ONC-42", "EXDOSE": 100, "EXDOSU": "mg", "EXSTDTC": "2026-01-15", "EXENDTC": "2026-01-15", "SOURCE_DOC": "CRF-EX-042-S01-001-V1"},
        {"USUBJID": "042-S01-001", "SITEID": "S01", "EXSEQ": 2, "VISIT": "Visit 2", "EXTRT": "Study Drug ONC-42", "EXDOSE": 100, "EXDOSU": "mg", "EXSTDTC": "2026-02-01", "EXENDTC": "2026-02-01", "SOURCE_DOC": "CRF-EX-042-S01-001-V2"},
        # Visit 3 is attended per SV, but EX entry for Visit 3 is MISSING!
        {"USUBJID": "042-S01-002", "SITEID": "S01", "EXSEQ": 1, "VISIT": "Visit 1", "EXTRT": "Study Drug ONC-42", "EXDOSE": 100, "EXDOSU": "mg", "EXSTDTC": "2026-01-20", "EXENDTC": "2026-01-20", "SOURCE_DOC": "CRF-EX-042-S01-002-V1"},
        {"USUBJID": "042-S02-004", "SITEID": "S02", "EXSEQ": 1, "VISIT": "Visit 1", "EXTRT": "Study Drug ONC-42", "EXDOSE": 200, "EXDOSU": "mg", "EXSTDTC": "2026-02-05", "EXENDTC": "2026-02-05", "SOURCE_DOC": "CRF-EX-042-S02-004-V1"},
        {"USUBJID": "042-S03-005", "SITEID": "S03", "EXSEQ": 1, "VISIT": "Visit 1", "EXTRT": "Study Drug ONC-42", "EXDOSE": 100, "EXDOSU": "mg", "EXSTDTC": "2026-02-15", "EXENDTC": "2026-02-15", "SOURCE_DOC": "CRF-EX-042-S03-005-V1"},
    ],
    "CM": [
        # Subject 042-S01-002 takes Paracetamol/Acetaminophen (relevant for liver clarify query)
        {"USUBJID": "042-S01-002", "SITEID": "S01", "CMSEQ": 1, "CMTRT": "Acetaminophen", "CMDOSE": 500, "CMDOSU": "mg", "CMSTDTC": "2026-01-10", "CMENDTC": "2026-03-01", "CMIND": "Chronic osteoarthritis pain", "SOURCE_DOC": "CRF-CM-042-S01-002-Seq1"},
        # Subject 042-S02-001 takes Naproxen (Allowed under v1, Prohibited under v2 Amendment)
        {"USUBJID": "042-S02-001", "SITEID": "S02", "CMSEQ": 1, "CMTRT": "Naproxen", "CMDOSE": 500, "CMDOSU": "mg", "CMSTDTC": "2026-01-20", "CMENDTC": "2026-03-10", "CMIND": "Lower back pain", "SOURCE_DOC": "CRF-CM-042-S02-001-Seq1"},
    ],
    "SV": [
        # Visit window deviation: 042-S02-002 Visit 2 scheduled 2026-02-20, attended 2026-02-27 (+7 days vs window +/-3)
        {"USUBJID": "042-S02-002", "SITEID": "S02", "SVSEQ": 1, "VISIT": "Visit 1", "VISITNUM": 1, "SVSTDTC": "2026-01-22", "TARGETDTC": "2026-01-22", "WINDOW_DAYS": 3, "SOURCE_DOC": "SV-042-S02-002-V1"},
        {"USUBJID": "042-S02-002", "SITEID": "S02", "SVSEQ": 2, "VISIT": "Visit 2", "VISITNUM": 2, "SVSTDTC": "2026-02-27", "TARGETDTC": "2026-02-20", "WINDOW_DAYS": 3, "SOURCE_DOC": "SV-042-S02-002-V2"},
        # Subject 042-S01-001 attended Visit 3 on 2026-03-01 (corresponds to missing dose finding)
        {"USUBJID": "042-S01-001", "SITEID": "S01", "SVSEQ": 3, "VISIT": "Visit 3", "VISITNUM": 3, "SVSTDTC": "2026-03-01", "TARGETDTC": "2026-03-01", "WINDOW_DAYS": 3, "SOURCE_DOC": "SV-042-S01-001-V3"}
    ],
    "MH": [
        {"USUBJID": "042-S01-002", "SITEID": "S01", "MHSEQ": 1, "MHTERM": "Non-alcoholic fatty liver disease (NAFLD)", "MHSTDTC": "2021-05-10", "SOURCE_DOC": "MH-042-S01-002-1"},
        {"USUBJID": "042-S02-004", "SITEID": "S02", "MHSEQ": 1, "MHTERM": "Hypertension", "MHSTDTC": "2018-03-15", "SOURCE_DOC": "MH-042-S02-004-1"}
    ],
    "DS": [
        {"USUBJID": "042-S01-001", "SITEID": "S01", "DSSEQ": 1, "DSDECOD": "ONGOING", "DSSTDTC": "2026-03-01", "SOURCE_DOC": "DS-042-S01-001"},
        {"USUBJID": "042-S02-004", "SITEID": "S02", "DSSEQ": 1, "DSDECOD": "ONGOING", "DSSTDTC": "2026-03-15", "SOURCE_DOC": "DS-042-S02-004"}
    ]
}

# Cut 2: Interim Study Data Cut (Cumulative data, recurrence, site-level patterns)
CUT_2_DATA: Dict[str, List[Dict[str, Any]]] = {
    "DM": list(CUT_1_DATA["DM"]) + [
        {"USUBJID": "042-S03-007", "SITEID": "S03", "AGE": 55, "SEX": "F", "ARM": "Arm B (Active 200mg)", "ENRLDTC": "2026-02-15"}
    ],
    "AE": list(CUT_1_DATA["AE"]) + [
        # Recurrent issue for Site S03: chronological dosing/AE discrepancy
        {
            "USUBJID": "042-S03-007", "SITEID": "S03", "AESEQ": 1,
            "AETERM": "Fatigue and Asthenia",
            "AESTDTC": "2026-02-12", "AEENDTC": "2026-02-14",
            "AESER": "N", "AESHOSP": "N", "AEREL": "UNLIKELY",
            "AESEV": "MILD", "AEOUT": "RECOVERED",
            "SOURCE_DOC": "CRF-AE-042-S03-007-Seq1"
        }
    ],
    "LB": list(CUT_1_DATA["LB"]) + [
        # Follow-up lab for 042-S01-002
        {
            "USUBJID": "042-S01-002", "SITEID": "S01", "LBSEQ": 4,
            "VISIT": "Visit 3 (Day 28)", "LBDTC": "2026-03-10",
            "LBTESTCD": "ALT", "LBTEST": "Alanine Aminotransferase",
            "LBORRES": 88.0, "LBORRESU": "U/L", "LBORNRLO": 10.0, "LBORNRHI": 45.0,
            "LBNRIND": "HIGH", "IS_SCREENING": False,
            "SOURCE_DOC": "LAB-042-S01-002-V3-ALT"
        }
    ],
    "EX": list(CUT_1_DATA["EX"]) + [
        # Recurrent subject issue: 042-S03-005 in Cut 2 has missing dose log for Visit 2
        {"USUBJID": "042-S03-005", "SITEID": "S03", "EXSEQ": 2, "VISIT": "Visit 2", "EXTRT": "Study Drug ONC-42", "EXDOSE": 0, "EXDOSU": "mg", "EXSTDTC": "", "EXENDTC": "", "SOURCE_DOC": "CRF-EX-042-S03-005-V2-BLANK"},
        {"USUBJID": "042-S03-007", "SITEID": "S03", "EXSEQ": 1, "VISIT": "Visit 1", "EXTRT": "Study Drug ONC-42", "EXDOSE": 200, "EXDOSU": "mg", "EXSTDTC": "2026-02-18", "EXENDTC": "2026-02-18", "SOURCE_DOC": "CRF-EX-042-S03-007-V1"}
    ],
    "CM": list(CUT_1_DATA["CM"]),
    "SV": list(CUT_1_DATA["SV"]) + [
        {"USUBJID": "042-S03-005", "SITEID": "S03", "SVSEQ": 2, "VISIT": "Visit 2", "VISITNUM": 2, "SVSTDTC": "2026-03-01", "TARGETDTC": "2026-03-01", "WINDOW_DAYS": 3, "SOURCE_DOC": "SV-042-S03-005-V2"},
        {"USUBJID": "042-S03-007", "SITEID": "S03", "SVSEQ": 1, "VISIT": "Visit 1", "VISITNUM": 1, "SVSTDTC": "2026-02-18", "TARGETDTC": "2026-02-18", "WINDOW_DAYS": 3, "SOURCE_DOC": "SV-042-S03-007-V1"}
    ],
    "MH": list(CUT_1_DATA["MH"]),
    "DS": list(CUT_1_DATA["DS"])
}

CUT_3_DATA = CUT_2_DATA

CUTS = {
    1: CUT_1_DATA,
    2: CUT_2_DATA,
    3: CUT_3_DATA
}
