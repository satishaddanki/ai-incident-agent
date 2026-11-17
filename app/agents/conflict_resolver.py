# app/agents/conflict_resolver.py
import json
import re
from typing import Any

from app.core.ollama_client import OllamaLLMClient


class ConflictResolver:
    """
    Consolidates findings from parallel specialist agents.

    Responsibilities:
    1. Validate specialist reports.
    2. Deduplicate historical evidence.
    3. Detect disagreements.
    4. Generate consolidated RCA using an LLM.
    5. Enforce confidence and human-review policies.
    """

    VALID_CONFIDENCES = {"Low", "Medium", "High"}

    def __init__(self):
        self.llm = OllamaLLMClient()

    @staticmethod
    def _collect_evidence_ids(value):
        """
        Recursively collect historical incident IDs.
        """

        evidence_ids = set()

        if isinstance(value, dict):

            for key, item in value.items():

                if key == "incident_id" and isinstance(item, str):
                    evidence_ids.add(item)

                evidence_ids.update(
                    ConflictResolver._collect_evidence_ids(item)
                )

        elif isinstance(value, list):

            for item in value:
                evidence_ids.update(
                    ConflictResolver._collect_evidence_ids(item)
                )

        return evidence_ids

    @staticmethod
    def _normalize_root_cause(value):
        """
        Normalize text for basic deterministic comparison.
        """

        if not isinstance(value, str):
            return ""

        value = value.lower()
        value = re.sub(r"[^a-z0-9\s]", " ", value)
        value = re.sub(r"\s+", " ", value)

        return value.strip()

    @staticmethod
    def _validate_list(value):
        """
        Ensure LLM list fields have the expected structure.
        """

        return value if isinstance(value, list) else []

    def _prepare_reports(self, investigation_results):

        reports = {}

        for domain, result in investigation_results.items():

            if not isinstance(result, dict):
                raise ValueError(
                    f"Invalid investigation result for {domain}"
                )

            if result.get("domain") != domain.upper():
                raise ValueError(
                    f"Domain identity mismatch for {domain}"
                )

            evidence = result.get("retrieved_evidence", [])

            if not isinstance(evidence, list):
                evidence = []

            reports[domain] = {
                "agent_name": result.get("agent_name"),
                "domain": result.get("domain"),
                "probable_root_cause": result.get(
                    "probable_root_cause",
                    "Not determined"
                ),
                "confidence": result.get("confidence", "Low"),
                "findings": result.get("findings", ""),
                "retrieved_evidence": evidence,
                "alternative_causes": self._validate_list(
                    result.get("alternative_causes", [])
                ),
                "recommended_actions": self._validate_list(
                    result.get("recommended_actions", [])
                ),
                "current_verification": self._validate_list(
                    result.get("current_verification", [])
                )
            }

        return reports

    def _deduplicate_evidence(self, reports):
        """
        Deduplicate historical incidents across all agents.

        Keep the record with the highest retrieval score.
        Preserve the agents that retrieved each incident.
        """

        unique_evidence = {}
        source_agents = {}

        for domain, report in reports.items():

            agent_name = report.get("agent_name")

            for item in report["retrieved_evidence"]:

                if not isinstance(item, dict):
                    continue

                incident_id = item.get("incident_id")

                if not incident_id:
                    continue

                source_agents.setdefault(
                    incident_id, set()
                ).add(agent_name)

                existing = unique_evidence.get(incident_id)

                if existing is None:

                    unique_evidence[incident_id] = item.copy()

                else:

                    current_score = item.get("score", 0) or 0
                    existing_score = existing.get("score", 0) or 0

                    if current_score > existing_score:
                        unique_evidence[incident_id] = item.copy()

        sorted_evidence = sorted(
            unique_evidence.values(),
            key=lambda item: item.get("score", 0) or 0,
            reverse=True
        )

        return sorted_evidence, source_agents

    def _check_current_verification(self, reports):
        """
        Historical retrieval is not current-system verification.

        High confidence requires explicit verified current evidence
        from at least one specialist.
        """

        verified_records = []

        for report in reports.values():

            for item in report["current_verification"]:

                if (
                    isinstance(item, dict)
                    and item.get("verified") is True
                    and item.get("evidence")
                    and item.get("source")
                ):
                    verified_records.append(item)

        return verified_records

    def resolve(self, incident, investigation_results):

        if not isinstance(incident, dict):
            raise ValueError("Invalid incident input.")

        if not investigation_results:
            raise ValueError(
                "No specialist investigation results provided."
            )

        print("\n========== CONFLICT RESOLVER ==========\n")

        print("[Conflict Resolver] Validating specialist reports...")

        # 1. Validate and prepare reports
        reports = self._prepare_reports(investigation_results)

        # 2. Deduplicate historical evidence
        unique_evidence, source_agents = (
            self._deduplicate_evidence(reports)
        )

        available_evidence_ids = {
            item["incident_id"]
            for item in unique_evidence
        }

        # 3. Check for explicitly verified current evidence
        current_verification = (
            self._check_current_verification(reports)
        )

        # 4. Build LLM prompt
        prompt = f"""
        You are an enterprise Incident Conflict Resolution Agent.

        Analyze the specialist investigation reports and produce
        a consolidated Root Cause Analysis.

        CURRENT INCIDENT:
        {json.dumps(incident, indent=2, default=str)}

        SPECIALIST REPORTS:
        {json.dumps(reports, indent=2, default=str)}

        DEDUPLICATED HISTORICAL EVIDENCE:
        {json.dumps(unique_evidence, indent=2, default=str)}

        VERIFIED CURRENT EVIDENCE:
        {json.dumps(current_verification, indent=2, default=str)}

        TASKS:

        1. Compare root-cause hypotheses from all specialists.
        2. Identify common findings.
        3. Identify disagreements and contradictory hypotheses.
        4. Evaluate supporting historical evidence.
        5. Distinguish current incident observations from historical incidents.
        6. Never treat historical incidents as proof of the current root cause.
        7. Never invent evidence, metrics, logs or incident IDs.
        8. Identify unsupported conclusions.
        9. Recommend additional diagnostic investigation.
        10. Recommend whether human review is required.

        EVIDENCE RULES:

        - Historical incident IDs must come from the supplied evidence.
        - Cite only evidence relevant to the finding.
        - Historical evidence is supporting context, not current verification.
        - High confidence is not justified by historical similarity alone.
        - If current verification is missing, explicitly state that.

        Return ONLY valid JSON:

        {{
            "consolidated_root_cause": "string",
            "confidence": "Low | Medium | High",
            "supporting_agents": [],
            "supporting_evidence": [
                {{
                    "incident_id": "historical incident ID",
                    "finding": "relevant evidence",
                    "source_agent": "agent name"
                }}
            ],
            "common_findings": [],
            "disagreements": [],
            "additional_investigation_required": [],
            "requires_human_review": true,
            "resolution_summary": "string"
        }}
        """

        print("[Conflict Resolver] Generating consolidated analysis...")

        # 5. Invoke LLM
        result = self.llm.generate_json(prompt)

        # Diagnostic: inspect the actual LLM response
        print("\n========== RAW QWEN RESPONSE ==========\n")

        print(
            json.dumps(
                result,
                indent=4,
                default=str
            )
        )
        if not isinstance(result, dict):
            raise ValueError(
                "Conflict Resolver returned invalid JSON."
            )

        # 6. Validate confidence
        confidence = result.get("confidence", "Low")

        if confidence not in self.VALID_CONFIDENCES:
            confidence = "Low"

        # 7. Validate and deduplicate supporting evidence

        supporting_evidence = self._validate_list(
            result.get("supporting_evidence", [])
        )

        # One final record per historical incident.
        validated_evidence_by_id = {}

        for item in supporting_evidence:

            if not isinstance(item, dict):
                continue

            incident_id = item.get("incident_id")

            # Reject evidence not found in retrieval results.
            if incident_id not in available_evidence_ids:
                continue

            valid_sources = source_agents.get(incident_id, set())

            source_agent = item.get("source_agent")

            if not isinstance(source_agent, str):
                continue

            if source_agent not in valid_sources:
                continue

            if incident_id not in validated_evidence_by_id:

                # Use authoritative retrieval data rather than
                # trusting an LLM-generated historical finding.
                retrieved_record = next(
                    evidence
                    for evidence in unique_evidence
                    if evidence["incident_id"] == incident_id
                )

                validated_evidence_by_id[incident_id] = {
                    "incident_id": incident_id,
                    "title": retrieved_record.get("title"),
                    "historical_root_cause": retrieved_record.get(
                        "root_cause"
                    ),
                    "source_agents": sorted(valid_sources)
                }

        # 8. Validate supporting agents

        valid_agent_names = {
            report["agent_name"]
            for report in reports.values()
            if isinstance(report.get("agent_name"), str)
            and report.get("agent_name").strip()
        }

        supporting_agents = self._validate_list(
            result.get("supporting_agents", [])
        )

        # Accept only strings matching known specialist agent names.
        # Ignore dictionaries, lists, numbers and unknown agent names.
        supporting_agents = [
            agent.strip()
            for agent in supporting_agents
            if isinstance(agent, str)
            and agent.strip() in valid_agent_names
        ]

        # Remove duplicate agent names while preserving order.
        supporting_agents = list(dict.fromkeys(supporting_agents))

        # 9. Validate LLM output fields
        disagreements = self._validate_list(
            result.get("disagreements", [])
        )

        common_findings = self._validate_list(
            result.get("common_findings", [])
        )

        additional_investigation = self._validate_list(
            result.get("additional_investigation_required", [])
        )

        # 10. Enforce application-controlled confidence
        #
        # Current specialist agents do not yet produce
        # independently verified current-system evidence.
        #
        # Therefore High confidence is not permitted.

        if not current_verification:
            if confidence == "High":
                confidence = "Medium"

        if not validated_evidence_by_id:
            confidence = "Low"

        # 11. Enforce human review
        requires_human_review = (
            result.get("requires_human_review") is True
            or confidence == "Low"
            or bool(disagreements)
            or not current_verification
        )

        # 12. Build consolidated result
        consolidated_result = {

            "incident_id": incident.get("incident_id"),

            "consolidated_root_cause": result.get(
                "consolidated_root_cause",
                "Unable to determine root cause."
            ),

            "confidence": confidence,

            "supporting_agents": supporting_agents,

            "supporting_evidence": list(validated_evidence_by_id.values()),

            "common_findings": common_findings,

            "disagreements": disagreements,

            "conflict_detected": bool(disagreements),

            "additional_investigation_required": (
                additional_investigation
            ),

            "current_verification": current_verification,

            "historical_evidence_used": bool(unique_evidence),

            "current_incident_signals_available": bool(
                incident.get("logs") or incident.get("description")
            ),

            "current_root_cause_verified": bool(
                current_verification
            ),

            "root_cause_status": (
                "VERIFIED"
                if current_verification
                else "UNVERIFIED_HYPOTHESIS"
            ),
            "requires_human_review": requires_human_review,

            "resolution_summary": result.get(
                "resolution_summary",
                ""
            ),

            "available_evidence_ids": sorted(
                available_evidence_ids
            ),

            "unique_historical_evidence_count": len(
                unique_evidence
            ),

            "original_specialist_reports": investigation_results
        }

        # 13. Print resolver summary
        print("\n========== CONFLICT RESOLUTION SUMMARY ==========\n")

        print(
            "[Conflict Resolver] Unique historical incidents:",
            len(unique_evidence)
        )

        print(
            "[Conflict Resolver] Validated evidence:",
            len(validated_evidence_by_id)
        )

        print(
            "[Conflict Resolver] Current verification records:",
            len(current_verification)
        )

        print(
            "[Conflict Resolver] Confidence:",
            confidence
        )

        print(
            "[Conflict Resolver] Conflict detected:",
            bool(disagreements)
        )

        print(
            "[Conflict Resolver] Human review required:",
            requires_human_review
        )

        print("\n[Conflict Resolver] Consolidated RCA completed.")

        return consolidated_result
