from quality_hub_backend.services.jmeter_skill_gate import (
    external_jmeter_skill_registry,
    validate_and_correct_jmx,
)


def _jmx(*, header_value="${ticket}", extractor_tag="JSONPostProcessor", match_numbers=True, filename=""):
    match_prop = '<stringProp name="JSONPostProcessor.match_numbers">1</stringProp>' if match_numbers else ""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Skill gate" enabled="true">
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments">
        <collectionProp name="Arguments.arguments">
          <elementProp name="ticket" elementType="Argument"><stringProp name="Argument.name">ticket</stringProp><stringProp name="Argument.value">${{__P(ticket,)}}</stringProp></elementProp>
        </collectionProp>
      </elementProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Flow" enabled="true">
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController"><boolProp name="LoopController.continue_forever">false</boolProp><stringProp name="LoopController.loops">1</stringProp></elementProp>
        <stringProp name="ThreadGroup.num_threads">1</stringProp>
        <stringProp name="ThreadGroup.ramp_time">1</stringProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Create" enabled="true">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments"><collectionProp name="Arguments.arguments"/></elementProp>
          <stringProp name="HTTPSampler.domain">example.test</stringProp>
          <stringProp name="HTTPSampler.protocol">https</stringProp>
          <stringProp name="HTTPSampler.path">/orders</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
        </HTTPSamplerProxy>
        <hashTree>
          <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="Headers" enabled="true">
            <collectionProp name="HeaderManager.headers"><elementProp name="ticket" elementType="Header"><stringProp name="Header.name">ticket</stringProp><stringProp name="Header.value">{header_value}</stringProp></elementProp></collectionProp>
          </HeaderManager>
          <hashTree/>
          <{extractor_tag} guiclass="JSONPostProcessorGui" testclass="JSONPostProcessor" testname="Extract order" enabled="true">
            <stringProp name="JSONPostProcessor.referenceNames">order_no</stringProp>
            <stringProp name="JSONPostProcessor.jsonPathExprs">$.data.orderNo</stringProp>
            {match_prop}
          </{extractor_tag}>
          <hashTree/>
          <JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" testname="Sync" enabled="true"><stringProp name="filename">{filename}</stringProp><stringProp name="script">vars.put('saved', vars.get('order_no'))</stringProp></JSR223PostProcessor>
          <hashTree/>
          <ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="HTTP 200" enabled="true"><collectionProp name="Asserion.test_strings"><stringProp name="200">200</stringProp></collectionProp><stringProp name="Assertion.test_field">Assertion.response_code</stringProp><intProp name="Assertion.test_type">8</intProp></ResponseAssertion>
          <hashTree/>
        </hashTree>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>'''


def test_skill_gate_passes_portable_jmx_with_runtime_credentials() -> None:
    result = validate_and_correct_jmx(_jmx(), allowed_runtime_variables={"ticket"})

    assert result["status"] == "PASS"
    assert result["summary"]["http_samplers"] == 1
    assert result["checks"]["credentials_runtime_only"] is True


def test_skill_gate_blocks_raw_credentials_before_mcp() -> None:
    result = validate_and_correct_jmx(_jmx(header_value="raw-secret-ticket"))

    assert result["status"] == "BLOCKED"
    assert any(item["code"] == "raw_credentials" for item in result["blockers"])


def test_skill_gate_applies_one_deterministic_correction_pass() -> None:
    result = validate_and_correct_jmx(
        _jmx(extractor_tag="JSONExtractor", match_numbers=False, filename="   \n"),
        allowed_runtime_variables={"ticket"},
    )

    assert result["status"] == "PASS"
    assert "<JSONExtractor" not in result["corrected_text"]
    assert "JSONPostProcessor.match_numbers" in result["corrected_text"]
    assert '<stringProp name="filename"></stringProp>' in result["corrected_text"]
    assert {item["code"] for item in result["corrections"]} == {
        "json_extractor_element",
        "blank_script_filename",
        "json_match_numbers",
    }
    assert result["audit"]["correction_passes"] == 1
    assert result["audit"]["semantic_change"] is False
    assert result["audit"]["original_sha256"] != result["audit"]["corrected_sha256"]


def test_skill_gate_blocks_heavy_gui_listener_for_load_profiles() -> None:
    jmx = _jmx().replace(
        "</hashTree>\n    </hashTree>\n  </hashTree>",
        '<ResultCollector guiclass="ViewResultsFullVisualizer" testclass="ResultCollector" testname="View Results" enabled="true"/><hashTree/>\n'
        "</hashTree>\n    </hashTree>\n  </hashTree>",
        1,
    )

    result = validate_and_correct_jmx(
        jmx,
        allowed_runtime_variables={"ticket"},
        performance_profile="load",
    )

    assert result["status"] == "BLOCKED"
    assert any(item["code"] == "heavy_gui_listener" for item in result["blockers"])


def test_skill_gate_allows_request_only_profile_without_claiming_business_tps() -> None:
    result = validate_and_correct_jmx(
        _jmx(),
        allowed_runtime_variables={"ticket"},
        performance_profile="baseline",
        transaction_mode="request_only",
    )

    assert result["status"] == "PASS_WITH_WARNINGS"
    assert result["checks"]["transaction_mode"] == "request_only"
    assert any(item["code"] == "request_only_no_tps" for item in result["warnings"])


def test_external_registry_does_not_mislabel_plugin_as_installable_skill() -> None:
    registry = external_jmeter_skill_registry()

    assert registry["generation"]["alias"] == "jmeter-generator"
    assert registry["correlation_and_correction"]["name"] == "Smart-GenAI-Powered-JMeter"
    assert registry["correlation_and_correction"]["agent_skill_installable"] is False
    assert registry["execution"]["responsibility"].startswith("Import an approved JMX")
