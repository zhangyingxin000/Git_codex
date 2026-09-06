from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Iterable


_MCP_RESULT_WRITER_CLASSES = {"StatVisualizer", "SummaryReport"}


def _property(tag: str, name: str, value: Any) -> ET.Element:
    element = ET.Element(tag, {"name": name})
    element.text = str(value)
    return element


def _test_plan_tree(root: ET.Element) -> ET.Element:
    top_tree = next((child for child in root if child.tag == "hashTree"), None)
    if top_tree is None:
        raise ValueError("JMX has no root hashTree")
    children = list(top_tree)
    if len(children) < 2 or children[0].tag != "TestPlan" or children[1].tag != "hashTree":
        raise ValueError("JMX TestPlan/hashTree structure is invalid")
    return children[1]


def _has_result_writer(root: ET.Element) -> bool:
    return any(
        element.attrib.get("guiclass") in _MCP_RESULT_WRITER_CLASSES
        and str(element.attrib.get("enabled", "true")).lower() != "false"
        for element in root.iter("ResultCollector")
    )


def _result_writer() -> ET.Element:
    writer = ET.Element("ResultCollector", {
        "guiclass": "StatVisualizer",
        "testclass": "ResultCollector",
        "testname": "Platform execution result writer",
        "enabled": "true",
    })
    writer.append(_property("boolProp", "ResultCollector.error_logging", "false"))
    writer.append(_property("stringProp", "filename", ""))
    return writer


def _csv_data_set(item: dict[str, Any]) -> ET.Element:
    data_set = ET.Element("CSVDataSet", {
        "guiclass": "TestBeanGUI",
        "testclass": "CSVDataSet",
        "testname": str(item.get("name") or "Platform runtime CSV"),
        "enabled": "true",
    })
    properties = (
        ("stringProp", "delimiter", item.get("delimiter") or ","),
        ("stringProp", "fileEncoding", item.get("file_encoding") or "UTF-8"),
        ("stringProp", "filename", item.get("filename") or ""),
        ("boolProp", "ignoreFirstLine", str(bool(item.get("ignore_first_line", False))).lower()),
        ("boolProp", "quotedData", str(bool(item.get("quoted_data", False))).lower()),
        ("boolProp", "recycle", str(bool(item.get("recycle", True))).lower()),
        ("stringProp", "shareMode", item.get("share_mode") or "shareMode.all"),
        ("boolProp", "stopThread", str(bool(item.get("stop_thread", False))).lower()),
        ("stringProp", "variableNames", item.get("variable_names") or ""),
    )
    for tag, name, value in properties:
        data_set.append(_property(tag, name, value))
    return data_set


def prepare_runtime_jmx(
    jmx_text: str,
    *,
    csv_data_sets: Iterable[dict[str, Any]] = (),
    ensure_result_writer: bool = True,
) -> str:
    root = ET.fromstring(jmx_text)
    plan_tree = _test_plan_tree(root)
    insertion_index = 0
    for item in csv_data_sets:
        data_set = _csv_data_set(dict(item))
        plan_tree.insert(insertion_index, data_set)
        plan_tree.insert(insertion_index + 1, ET.Element("hashTree"))
        insertion_index += 2
    if ensure_result_writer and not _has_result_writer(root):
        plan_tree.insert(insertion_index, _result_writer())
        plan_tree.insert(insertion_index + 1, ET.Element("hashTree"))
    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")
