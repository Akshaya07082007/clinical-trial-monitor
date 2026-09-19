"""Stage 2: Protocol Versioning and Amendment Engine

Maintains immutable versioned protocol rules and evaluates subjects against the
protocol version in force for a given cut.
Provides real amendment mechanism and PROTOCOL DIFF generation.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


# Protocol Version 1 (Original Protocol)
PROTOCOL_V1_RULES = {
    "version": 1,
    "effective_cut": 1,
    "title": "Protocol 042-ONC Original (v1.0)",
    "rules": {
        "visit_window": {
            "name": "Scheduled Visit Window Tolerance",
            "section": "Section 4.2",
            "max_allowed_days": 3,
            "description": "All scheduled study visits must occur within ±3 calendar days of target study day."
        },
        "renal_exclusion": {
            "name": "Renal Function Exclusion Criterion",
            "section": "Section 5.3.1",
            "egfr_cutoff": 45.0,  # eGFR < 45 mL/min is excluded / deviation
            "unit": "mL/min/1.73m2",
            "description": "Subjects with screening or on-treatment eGFR < 45.0 mL/min/1.73m2 must be withheld or discontinued."
        },
        "prohibited_medications": {
            "name": "Prohibited Concomitant Medications",
            "section": "Section 6.4",
            "prohibited_list": ["Ketoconazole", "Clarithromycin", "Itraconazole"],
            "description": "Strong CYP3A4 inhibitors are strictly prohibited during active study drug administration."
        },
        "sae_reporting": {
            "name": "Expedited Serious Adverse Event Reporting",
            "section": "Section 7.3",
            "timeframe_hours": 24,
            "description": "Any adverse event resulting in inpatient hospitalization, disability, or death must be flagged as serious (AESER=Y) and reported within 24 hours."
        }
    },
    "amendment_summary": "Initial protocol baseline approved for trial initiation."
}

# Protocol Version 2 (Substantial Amendment 1)
PROTOCOL_V2_RULES = {
    "version": 2,
    "effective_cut": 2,
    "title": "Protocol 042-ONC Amendment 1 (v2.0)",
    "rules": {
        "visit_window": {
            "name": "Scheduled Visit Window Tolerance",
            "section": "Section 4.2",
            "max_allowed_days": 3,
            "description": "All scheduled study visits must occur within ±3 calendar days of target study day."
        },
        "renal_exclusion": {
            "name": "Renal Function Exclusion Criterion (Hardened)",
            "section": "Section 5.3.1 (Amended)",
            "egfr_cutoff": 60.0,  # Hardened from 45.0 to 60.0!
            "unit": "mL/min/1.73m2",
            "description": "Safety Amendment: Renal threshold heightened. Subjects with eGFR < 60.0 mL/min/1.73m2 meet exclusion criterion."
        },
        "prohibited_medications": {
            "name": "Prohibited Concomitant Medications (Expanded)",
            "section": "Section 6.4 (Amended)",
            "prohibited_list": ["Ketoconazole", "Clarithromycin", "Itraconazole", "Naproxen", "Ibuprofen"],
            "description": "NSAIDs (Naproxen, Ibuprofen) added to prohibited list due to observed drug-induced nephrotoxicity risk."
        },
        "sae_reporting": {
            "name": "Expedited Serious Adverse Event Reporting",
            "section": "Section 7.3",
            "timeframe_hours": 24,
            "description": "Any adverse event resulting in inpatient hospitalization, disability, or death must be flagged as serious (AESER=Y) and reported within 24 hours."
        }
    },
    "amendment_summary": "Amendment 1: Elevated renal safety cut-off to eGFR < 60 mL/min and added NSAIDs (Naproxen, Ibuprofen) to prohibited medications list."
}


class ProtocolEngine:
    def __init__(self, memory=None):
        self.memory = memory
        self._seed_default_protocols()

    def _seed_default_protocols(self):
        if self.memory:
            if not self.memory.get_protocol_version(1):
                self.memory.upsert_protocol_version(
                    1, PROTOCOL_V1_RULES["effective_cut"],
                    PROTOCOL_V1_RULES["title"],
                    PROTOCOL_V1_RULES["rules"],
                    PROTOCOL_V1_RULES["amendment_summary"]
                )
            if not self.memory.get_protocol_version(2):
                self.memory.upsert_protocol_version(
                    2, PROTOCOL_V2_RULES["effective_cut"],
                    PROTOCOL_V2_RULES["title"],
                    PROTOCOL_V2_RULES["rules"],
                    PROTOCOL_V2_RULES["amendment_summary"]
                )

    def get_protocol(self, version: int) -> Dict[str, Any]:
        if self.memory:
            stored = self.memory.get_protocol_version(version)
            if stored:
                return stored
        if version == 2:
            return PROTOCOL_V2_RULES
        return PROTOCOL_V1_RULES

    def evaluate_subject_compliance(
        self,
        raw_data: Dict[str, List[Dict[str, Any]]],
        protocol_version: int,
        cut: int
    ) -> List[Dict[str, Any]]:
        """Evaluates every subject against the specified protocol version rules."""
        proto = self.get_protocol(protocol_version)
        rules = proto["rules"]
        deviations: List[Dict[str, Any]] = []

        # 1. Visit Window Deviations
        max_days = rules["visit_window"]["max_allowed_days"]
        for sv in raw_data.get("SV", []):
            stdtc = sv.get("SVSTDTC", "")
            tgtdtc = sv.get("TARGETDTC", "")
            if stdtc and tgtdtc and stdtc != tgtdtc:
                try:
                    d1 = datetime.strptime(stdtc, "%Y-%m-%d")
                    d2 = datetime.strptime(tgtdtc, "%Y-%m-%d")
                    delta = abs((d1 - d2).days)
                    if delta > max_days:
                        deviations.append({
                            "deviation_id": f"DEV-VIS-{sv.get('USUBJID')}-{sv.get('VISIT', '')}-v{protocol_version}",
                            "subject": sv.get("USUBJID"),
                            "site": sv.get("SITEID"),
                            "deviation_type": "VISIT_WINDOW_DEVIATION",
                            "protocol_version": protocol_version,
                            "evidence": {
                                "visit": sv.get("VISIT"),
                                "actual_date": stdtc,
                                "target_date": tgtdtc,
                                "delta_days": delta,
                                "allowed_window": f"±{max_days} days",
                                "source_doc": sv.get("SOURCE_DOC")
                            },
                            "explanation": f"{sv.get('VISIT')} conducted {delta} days from target, exceeding protocol v{protocol_version} limit of ±{max_days} days.",
                            "status": "CONFIRMED",
                            "created_cycle": cut
                        })
                except Exception:
                    pass

        # 2. Renal Exclusion Criterion
        egfr_limit = rules["renal_exclusion"]["egfr_cutoff"]
        for lb in raw_data.get("LB", []):
            if lb.get("LBTESTCD") == "EGFR":
                val = lb.get("LBORRES", 0.0)
                if val < egfr_limit:
                    deviations.append({
                        "deviation_id": f"DEV-RENAL-{lb.get('USUBJID')}-v{protocol_version}",
                        "subject": lb.get("USUBJID"),
                        "site": lb.get("SITEID"),
                        "deviation_type": "RENAL_EXCLUSION_VIOLATION",
                        "protocol_version": protocol_version,
                        "evidence": {
                            "test": "EGFR",
                            "value": val,
                            "unit": lb.get("LBORRESU"),
                            "cutoff": egfr_limit,
                            "visit": lb.get("VISIT"),
                            "source_doc": lb.get("SOURCE_DOC")
                        },
                        "explanation": f"eGFR of {val} mL/min/1.73m2 violates protocol v{protocol_version} renal safety exclusion threshold (< {egfr_limit} mL/min/1.73m2).",
                        "status": "CONFIRMED",
                        "created_cycle": cut
                    })

        # 3. Prohibited Concomitant Medications
        prohibited_list = rules["prohibited_medications"]["prohibited_list"]
        for cm in raw_data.get("CM", []):
            med_name = cm.get("CMTRT", "")
            # Check case-insensitive match
            for p_med in prohibited_list:
                if p_med.lower() in med_name.lower():
                    deviations.append({
                        "deviation_id": f"DEV-MED-{cm.get('USUBJID')}-{p_med}-v{protocol_version}",
                        "subject": cm.get("USUBJID"),
                        "site": cm.get("SITEID"),
                        "deviation_type": "PROHIBITED_MEDICATION_VIOLATION",
                        "protocol_version": protocol_version,
                        "evidence": {
                            "concomitant_med": med_name,
                            "dose": f"{cm.get('CMDOSE')} {cm.get('CMDOSU')}",
                            "dates": f"{cm.get('CMSTDTC')} to {cm.get('CMENDTC')}",
                            "prohibited_drug": p_med,
                            "protocol_section": rules["prohibited_medications"]["section"],
                            "source_doc": cm.get("SOURCE_DOC")
                        },
                        "explanation": f"Subject received {med_name}, which is explicitly prohibited under Protocol v{protocol_version} {rules['prohibited_medications']['section']}.",
                        "status": "CONFIRMED",
                        "created_cycle": cut
                    })

        return deviations

    def compute_protocol_diff(
        self,
        v_old: int,
        v_new: int,
        raw_data: Dict[str, List[Dict[str, Any]]],
        cut: int
    ) -> Dict[str, Any]:
        """Calculates exact protocol difference, affected subjects, and newly generated deviations."""
        old_proto = self.get_protocol(v_old)
        new_proto = self.get_protocol(v_new)

        changed_rules = []
        old_rules = old_proto["rules"]
        new_rules = new_proto["rules"]

        for rule_key, new_rule in new_rules.items():
            if rule_key not in old_rules:
                changed_rules.append({
                    "rule_key": rule_key,
                    "change_type": "ADDED",
                    "description": new_rule.get("description")
                })
            elif old_rules[rule_key] != new_rule:
                changed_rules.append({
                    "rule_key": rule_key,
                    "change_type": "MODIFIED",
                    "old_spec": old_rules[rule_key],
                    "new_spec": new_rule,
                    "description": new_rule.get("description")
                })

        # Evaluate deviations under both
        old_devs = self.evaluate_subject_compliance(raw_data, v_old, cut)
        new_devs = self.evaluate_subject_compliance(raw_data, v_new, cut)

        old_keys = {f"{d['subject']}_{d['deviation_type']}" for d in old_devs}
        new_deviations_list = [
            d for d in new_devs if f"{d['subject']}_{d['deviation_type']}" not in old_keys
        ]
        affected_subjects = sorted(list({d["subject"] for d in new_deviations_list}))

        return {
            "old_version": v_old,
            "new_version": v_new,
            "old_title": old_proto["title"],
            "new_title": new_proto["title"],
            "changed_rules": changed_rules,
            "affected_subjects": affected_subjects,
            "new_deviations": new_deviations_list,
            "total_new_deviations": len(new_deviations_list),
            "historical_preserved": True
        }
