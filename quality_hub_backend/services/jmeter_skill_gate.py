from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from typing import Any


GENERATOR_SKILL = {
    "name": "jmeter-ai-generator",
    "alias": "jmeter-generator",
    "source": "https://github.com/ShanNanBean/jmeter-ai-generator-skill",
    "revision": "a7b37bcb4e86ff432f31fbf8f8c73d50d2910082",
    "contract": "SKILL.md",
}

CORRECTION_REFERENCE = {
    "name": "Smart-GenAI-Powered-JMeter",
    "source": "https://github.com/aditiaa2578/Smart-GenAI-Powered-JMeter",
    "revision": "551cf99943988b3fa2b26c207280271b552ed60b",
    "license": "MIT",
    "packaging": "jmeter-plugin",
    "agent_skill_installable": False,
    "reason": "The upstream repository has no SKILL.md; its correlation and correction rules are used as provenance for the deterministic pre-execution gate.",
}

_JMETER_VARIABLE_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_.-]*)\}")
_RAW_CREDENTIAL_NAMES = {
    "authorization",
    "cookie",
    "password",
    "ticket",
    "token",
    "access_token",
    "refresh_token",
    "x-api-key",
}
_ASSERTION_TAGS = {
    "ResponseAssertion",
    "JSONPathAssertion",
    "JSONSchemaAssertion",
    "JSR223Assertion",
    "DurationAssertion",
    "SizeAssertion",
    "XPath2Assertion",
}
_EXTRACTOR_PROPERTIES = {
    "JSONPostProcessor.referenceNames",
    "RegexExtractor.refname",
    "BoundaryExtractor.refname",
    "XPathExtractor.refname",
    "XPath2Extractor.refname",
    "CounterConfig.varName",
    "variableNames",
}

_HEAVY_GUI_LISTENERS = {
    "ViewResultsFullVisualizer",
    "GraphVisualizer",
    "StatGraphVisualizer",
    "RespTimeGraphVisualizer",
}


def _content_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _semantic_snapshot(jmx_text: str) -> dict[str, Any] | None:
    try:
        root = ET.fromstring(jmx_text)
    except ET.ParseError:
        return None
    thread_groups = []
    samplers = []
    assertions = []
    for element in root.iter():
        if element.tag in {"ThreadGroup", "SetupThreadGroup", "PostThreadGroup"}:
            thread_groups.append({
                "tag": element.tag,
                "name": element.attrib.get("testname") or "",
                "threads": _property(element, "ThreadGroup.num_threads"),
                "ramp": _property(element, "ThreadGroup.ramp_time"),
                "duration": _property(element, "ThreadGroup.duration"),
                "scheduler": _property(element, "ThreadGroup.scheduler"),
            })
        elif element.tag == "HTTPSamplerProxy":
            arguments = []
            for argument in element.iter("elementProp"):
                if argument.attrib.get("elementType") not in {"HTTPArgument", "Argument"}:
                    continue
                arguments.append({
                    "name": _property(argument, "Argument.name"),
                    "value": _property(argument, "Argument.value"),
                })
            samplers.append({
                "name": element.attrib.get("testname") or "",
                "method": _property(element, "HTTPSampler.method"),
                "protocol": _property(element, "HTTPSampler.protocol"),
                "domain": _property(element, "HTTPSampler.domain"),
                "port": _property(element, "HTTPSampler.port"),
                "path": _property(element, "HTTPSampler.path"),
                "arguments": arguments,
            })
        elif element.tag in _ASSERTION_TAGS:
            assertions.append({
                "tag": element.tag,
                "name": element.attrib.get("testname") or "",
                "properties": sorted(
                    (child.attrib.get("name") or "", child.text or "")
                    for child in element.iter()
                    if child.tag.endswith("Prop")
                ),
            })
    return {
        "thread_groups": thread_groups,
        "samplers": samplers,
        "assertions": assertions,
    }


def external_jmeter_skill_registry() -> dict[str, Any]:
    return {
        "generation": dict(GENERATOR_SKILL),
        "correlation_and_correction": dict(CORRECTION_REFERENCE),
        "execution": {
            "name": "jmeter-mcp-server",
            "version": "0.3.1",
            "responsibility": "Import an approved JMX, execute it, and collect JTL/HTML/analysis artifacts only.",
        },
    }


def _property(element: ET.Element, name: str) -> str:
    for child in element.iter():
        if child.tag.endswith("Prop") and child.attrib.get("name") == name:
            return child.text or ""
    return ""


def _split_names(value: str) -> set[str]:
    return {part.strip() for part in re.split(r"[;,]", value or "") if part.strip()}


def _apply_single_correction_pass(jmx_text: str) -> tuple[str, list[dict[str, str]]]:
    corrected = jmx_text
    corrections: list[dict[str, str]] = []

    if "<JSONExtractor" in corrected or "</JSONExtractor>" in corrected:
        corrected = corrected.replace("<JSONExtractor", "<JSONPostProcessor")
        corrected = corrected.replace("</JSONExtractor>", "</JSONPostProcessor>")
        corrections.append({
            "code": "json_extractor_element",
            "message": "Replaced unsupported JSONExtractor tags with JMeter 5.6 JSONPostProcessor tags.",
        })

    empty_filename_pattern = re.compile(
        r'(<stringProp\s+name="filename">)[\t\r\n ]+(</stringProp>)',
        re.IGNORECASE,
    )
    corrected, filename_count = empty_filename_pattern.subn(r"\1\2", corrected)
    if filename_count:
        corrections.append({
            "code": "blank_script_filename",
            "message": f"Cleared {filename_count} whitespace-only JSR223 script filename value(s).",
        })

    block_pattern = re.compile(
        r"(<JSONPostProcessor\b[^>]*>)(.*?)(</JSONPostProcessor>)",
        re.IGNORECASE | re.DOTALL,
    )

    def ensure_match_numbers(match: re.Match[str]) -> str:
        head, body, tail = match.groups()
        reference_match = re.search(
            r'<stringProp\s+name="JSONPostProcessor\.referenceNames">(.*?)</stringProp>',
            body,
            re.IGNORECASE | re.DOTALL,
        )
        references = _split_names(reference_match.group(1) if reference_match else "")
        expected = max(1, len(references))
        numbers_match = re.search(
            r'<stringProp\s+name="JSONPostProcessor\.match_numbers">(.*?)</stringProp>',
            body,
            re.IGNORECASE | re.DOTALL,
        )
        values = _split_names(numbers_match.group(1) if numbers_match else "")
        if numbers_match and len(values) == expected:
            return match.group(0)
        replacement = ";".join("1" for _ in range(expected))
        prop = f'<stringProp name="JSONPostProcessor.match_numbers">{replacement}</stringProp>'
        if numbers_match:
            body = body[: numbers_match.start()] + prop + body[numbers_match.end() :]
        else:
            body = body.rstrip() + "\n            " + prop + "\n          "
        corrections.append({
            "code": "json_match_numbers",
            "message": "Normalized JSON extractor match_numbers to one value per reference name.",
        })
        return head + body + tail

    corrected = block_pattern.sub(ensure_match_numbers, corrected)
    return corrected, corrections


def _validate_hash_tree_pairs(tree: ET.Element, blockers: list[dict[str, str]], location: str) -> None:
    children = list(tree)
    if len(children) % 2:
        blockers.append({
            "code": "jmx_tree_pairing",
            "message": f"{location} contains an unmatched test element without a sibling hashTree.",
        })
        return
    for index in range(0, len(children), 2):
        element = children[index]
        child_tree = children[index + 1]
        if element.tag == "hashTree" or child_tree.tag != "hashTree":
            blockers.append({
                "code": "jmx_tree_pairing",
                "message": f"{location} must alternate test elements and sibling hashTree nodes.",
            })
            return
        _validate_hash_tree_pairs(child_tree, blockers, f"{location}/{element.attrib.get('testname') or element.tag}")


def _iter_test_pairs(tree: ET.Element):
    children = list(tree)
    for index in range(0, len(children) - 1, 2):
        element = children[index]
        child_tree = children[index + 1]
        if child_tree.tag != "hashTree":
            continue
        yield element, child_tree
        yield from _iter_test_pairs(child_tree)


def _defined_variables(root: ET.Element, allowed_runtime_variables: Iterable[str]) -> set[str]:
    defined = {str(name).strip() for name in allowed_runtime_variables if str(name).strip()}
    for element in root.iter():
        if element.tag == "elementProp" and element.attrib.get("elementType") == "Argument":
            name = _property(element, "Argument.name")
            if name:
                defined.add(name.strip())
        if element.tag.endswith("Prop") and element.attrib.get("name") in _EXTRACTOR_PROPERTIES:
            defined.update(_split_names(element.text or ""))
    return defined


def _raw_credentials(root: ET.Element) -> list[str]:
    findings: list[str] = []
    for element in root.iter("elementProp"):
        element_type = str(element.attrib.get("elementType") or "")
        if element_type == "Header":
            name = _property(element, "Header.name").strip().lower()
            value = _property(element, "Header.value").strip()
        elif element_type == "Argument":
            name = _property(element, "Argument.name").strip().lower()
            value = _property(element, "Argument.value").strip()
        else:
            continue
        if name in _RAW_CREDENTIAL_NAMES and value and "${" not in value:
            findings.append(name)
    return sorted(set(findings))


def validate_and_correct_jmx(
    jmx_text: str,
    *,
    allowed_runtime_variables: Iterable[str] = (),
    allowed_absolute_paths: Iterable[str] = (),
    performance_profile: str = "",
    transaction_mode: str = "business_transaction",
) -> dict[str, Any]:
    original_text = str(jmx_text or "")
    original_hash = _content_hash(original_text)
    original_semantics = _semantic_snapshot(original_text)
    corrected_text, corrections = _apply_single_correction_pass(original_text)
    corrected_hash = _content_hash(corrected_text)
    corrected_semantics = _semantic_snapshot(corrected_text)
    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, Any]] = []
    if original_semantics is not None and corrected_semantics != original_semantics:
        blockers.append({
            "code": "semantic_rewrite_detected",
            "message": "The correction pass changed threads, requests, or assertions; semantic rewrites are forbidden in the gate.",
        })
    try:
        root = ET.fromstring(corrected_text)
    except ET.ParseError as exc:
        return {
            "status": "BLOCKED",
            "corrected_text": corrected_text,
            "corrections": corrections,
            "blockers": [{"code": "invalid_xml", "message": str(exc)}],
            "warnings": warnings,
            "checks": {"xml": False},
            "summary": {"thread_groups": 0, "http_samplers": 0, "assertions": 0},
            "audit": {
                "correction_passes": 1,
                "original_sha256": original_hash,
                "corrected_sha256": corrected_hash,
                "semantic_change": original_semantics is not None and corrected_semantics != original_semantics,
            },
            "skills": external_jmeter_skill_registry(),
        }

    if root.tag != "jmeterTestPlan":
        blockers.append({"code": "invalid_root", "message": "JMX root must be jmeterTestPlan."})
    top_tree = next((child for child in root if child.tag == "hashTree"), None)
    if top_tree is None:
        blockers.append({"code": "missing_root_hash_tree", "message": "JMX has no root hashTree."})
    else:
        _validate_hash_tree_pairs(top_tree, blockers, "jmeterTestPlan")

    thread_groups = [
        element for element in root.iter()
        if element.tag in {"ThreadGroup", "SetupThreadGroup", "PostThreadGroup"}
    ]
    samplers = list(root.iter("HTTPSamplerProxy"))
    transactions = list(root.iter("TransactionController"))
    sync_timers = list(root.iter("SyncTimer"))
    assertions = [element for element in root.iter() if element.tag in _ASSERTION_TAGS]
    if not thread_groups:
        blockers.append({"code": "missing_thread_group", "message": "JMX has no executable thread group."})
    if not samplers:
        blockers.append({"code": "missing_http_sampler", "message": "JMX has no HTTP sampler."})
    if not assertions:
        blockers.append({"code": "missing_assertion", "message": "JMX must contain at least one executable assertion."})

    invalid_samplers = []
    sampler_without_assertion = []
    if top_tree is not None:
        for element, child_tree in _iter_test_pairs(top_tree):
            if element.tag != "HTTPSamplerProxy":
                continue
            name = element.attrib.get("testname") or "HTTPSamplerProxy"
            method = _property(element, "HTTPSampler.method").upper()
            path = _property(element, "HTTPSampler.path").strip()
            if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"} or not path:
                invalid_samplers.append(name)
            if not any(child.tag in _ASSERTION_TAGS for child in child_tree.iter()):
                sampler_without_assertion.append(name)
    if invalid_samplers:
        blockers.append({
            "code": "invalid_sampler",
            "message": "HTTP sampler method/path is incomplete: " + ", ".join(invalid_samplers[:10]),
        })
    if sampler_without_assertion:
        warnings.append({
            "code": "sampler_without_assertion",
            "count": len(sampler_without_assertion),
            "items": sampler_without_assertion[:20],
        })

    credentials = _raw_credentials(root)
    if credentials:
        blockers.append({
            "code": "raw_credentials",
            "message": "Raw credential values are forbidden in JMX: " + ", ".join(credentials),
        })

    defined = _defined_variables(root, allowed_runtime_variables)
    used = {name for name in _JMETER_VARIABLE_RE.findall(corrected_text) if not name.startswith("__")}
    unresolved = sorted(used - defined)
    if unresolved:
        warnings.append({
            "code": "unresolved_variables",
            "count": len(unresolved),
            "items": unresolved[:50],
            "message": "Variables may be created by JSR223 or runtime data; verify before execution.",
        })

    allowed_paths = {
        str(value).strip().replace("\\", "/").lower()
        for value in allowed_absolute_paths
        if str(value).strip()
    }
    absolute_paths = []
    approved_runtime_paths = []
    for element in root.iter():
        if element.tag.endswith("Prop") and element.attrib.get("name") in {"filename", "File.path"}:
            value = (element.text or "").strip()
            if re.match(r"^[A-Za-z]:[\\/]", value):
                normalized = value.replace("\\", "/").lower()
                if normalized in allowed_paths:
                    approved_runtime_paths.append(value)
                else:
                    absolute_paths.append(value)
    if absolute_paths:
        blockers.append({
            "code": "absolute_paths",
            "message": "JMX still contains machine-specific absolute paths.",
        })

    requested_profile = str(performance_profile or "").strip().lower()
    if requested_profile in {"load", "concurrency", "spike", "stress", "soak", "stability"}:
        heavy_listeners = sorted({
            str(element.attrib.get("guiclass") or "")
            for element in root.iter("ResultCollector")
            if str(element.attrib.get("guiclass") or "") in _HEAVY_GUI_LISTENERS
            and str(element.attrib.get("enabled") or "true").lower() != "false"
        })
        if heavy_listeners:
            blockers.append({
                "code": "heavy_gui_listener",
                "message": "Non-GUI performance plans must disable heavy GUI listeners: " + ", ".join(heavy_listeners),
            })
    requested_transaction_mode = str(transaction_mode or "request_only").strip().lower()
    if (
        requested_profile in {"baseline", "load", "concurrency", "spike", "stress", "soak", "stability"}
        and requested_transaction_mode == "business_transaction"
        and not transactions
    ):
        blockers.append({
            "code": "missing_business_transaction",
            "message": "Performance JMX must use a Transaction Controller so request RPS and business TPS remain distinguishable.",
        })
    if (
        requested_profile in {"baseline", "load", "concurrency", "spike", "stress", "soak", "stability"}
        and requested_transaction_mode != "business_transaction"
        and not transactions
    ):
        warnings.append({
            "code": "request_only_no_tps",
            "message": "This plan measures request throughput only; business TPS remains unavailable until a validated multi-step transaction is selected.",
        })
    if requested_profile in {"concurrency", "spike"} and not sync_timers:
        blockers.append({
            "code": "missing_synchronizing_timer",
            "message": "Concurrency and spike profiles require a Synchronizing Timer for simultaneous release.",
        })

    checks = {
        "xml": True,
        "tree_structure": not any(item["code"] == "jmx_tree_pairing" for item in blockers),
        "thread_groups": bool(thread_groups),
        "http_samplers": bool(samplers),
        "sampler_method_and_path": not invalid_samplers,
        "credentials_runtime_only": not credentials,
        "portable_paths": not absolute_paths,
        "assertions_present": bool(assertions),
        "business_transaction_present": bool(transactions),
        "transaction_mode": requested_transaction_mode,
        "synchronizing_timer_present": bool(sync_timers),
    }
    status = "BLOCKED" if blockers else "PASS_WITH_WARNINGS" if warnings else "PASS"
    return {
        "status": status,
        "corrected_text": corrected_text,
        "corrections": corrections,
        "blockers": blockers,
        "warnings": warnings,
        "checks": checks,
        "summary": {
            "thread_groups": len(thread_groups),
            "http_samplers": len(samplers),
            "assertions": len(assertions),
            "transactions": len(transactions),
            "synchronizing_timers": len(sync_timers),
            "defined_variables": len(defined),
            "used_variables": len(used),
            "approved_runtime_paths": len(approved_runtime_paths),
        },
        "audit": {
            "correction_passes": 1,
            "original_sha256": original_hash,
            "corrected_sha256": corrected_hash,
            "semantic_change": original_semantics is not None and corrected_semantics != original_semantics,
            "allowed_corrections": [
                "json_extractor_element",
                "blank_script_filename",
                "json_match_numbers",
            ],
        },
        "skills": external_jmeter_skill_registry(),
    }
