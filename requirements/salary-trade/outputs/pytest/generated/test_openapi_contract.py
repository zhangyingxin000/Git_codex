import os
import re

import httpx
import pytest

PACKAGE_ID = "salary-trade"
OPERATIONS = [
    {
        "id": "get__salary_trade_quota",
        "title": "查询工资交易额度",
        "method": "GET",
        "path": "/salary/trade/quota",
        "parameters": [
            {
                "name": "uid",
                "in": "query",
                "required": true,
                "example": "{{anchorUid}}",
            },
            {
                "name": "ticket",
                "in": "query",
                "required": true,
                "example": "{{anchorTicket}}",
            },
            {
                "name": "unionId",
                "in": "query",
                "required": true,
                "example": "{{unionId}}",
            },
            {
                "name": "deviceId",
                "in": "query",
                "required": true,
                "example": "apipost-anchor-device",
            },
            {"name": "language", "in": "query", "required": true, "example": "zh"},
            {
                "name": "systemLanguage",
                "in": "query",
                "required": true,
                "example": "zh-CN",
            },
            {"name": "appVersion", "in": "query", "required": true, "example": "1.0.0"},
            {"name": "os", "in": "query", "required": true, "example": "ios"},
            {"name": "osVersion", "in": "query", "required": true, "example": "18.0"},
            {"name": "channel", "in": "query", "required": true, "example": "apipost"},
            {"name": "appid", "in": "query", "required": true, "example": "sparty"},
            {"name": "appCode", "in": "query", "required": true, "example": "sparty"},
            {
                "name": "deviceType",
                "in": "query",
                "required": true,
                "example": "mobile",
            },
            {
                "name": "model",
                "in": "query",
                "required": true,
                "example": "iPhone15%2C2",
            },
            {"name": "netType", "in": "query", "required": true, "example": "wifi"},
        ],
        "request_body_example": null,
        "request_body_required": false,
        "required_variables": [],
        "expected_statuses": [200],
        "response_schema_type": "object",
        "tags": ["user/trade/主播侧"],
        "mapped_case_ids": [],
    },
    {
        "id": "get__userserv_salary_trade_agents",
        "title": "查询可交易代理",
        "method": "GET",
        "path": "/userserv/salary/trade/agents",
        "parameters": [
            {"name": "uid", "in": "query", "required": true, "example": "{{uid}}"},
            {
                "name": "ticket",
                "in": "query",
                "required": true,
                "example": "{{access_token}}",
            },
            {"name": "countryCode", "in": "query", "required": true, "example": "EG"},
            {"name": "currency", "in": "query", "required": true, "example": "USD"},
            {"name": "pageNum", "in": "query", "required": true, "example": "1"},
            {"name": "pageSize", "in": "query", "required": true, "example": "20"},
            {
                "name": "deviceId",
                "in": "query",
                "required": true,
                "example": "apipost-anchor-device",
            },
            {"name": "language", "in": "query", "required": true, "example": "zh"},
            {"name": "appVersion", "in": "query", "required": true, "example": "1.0.0"},
            {"name": "os", "in": "query", "required": true, "example": "ios"},
            {"name": "channel", "in": "query", "required": true, "example": "apipost"},
        ],
        "request_body_example": null,
        "request_body_required": false,
        "required_variables": [],
        "expected_statuses": [200],
        "response_schema_type": "object",
        "tags": ["user/trade/主播侧"],
        "mapped_case_ids": [
            "tc_cb0f14e257",
            "tc_6ff142e9f5",
            "tc_520d95529f",
            "tc_09f5709402",
            "tc_b96f244486",
            "tc_5c6a8b6e6b",
        ],
    },
    {
        "id": "post__userserv_salary_trade_order_create",
        "title": "创建工资交易订单",
        "method": "POST",
        "path": "/userserv/salary/trade/order/create",
        "parameters": [
            {
                "name": "Content-Type",
                "in": "header",
                "required": true,
                "example": "application/x-www-form-urlencoded",
            }
        ],
        "request_body_example": {
            "uid": "{{uid}}",
            "ticket": "{{access_token}}",
            "agentUid": "{{agentUid}}",
            "salaryAmount": "50",
            "receiveCurrency": "EGP",
            "receiveAccountType": "bank",
            "receiveAccount": "SA0380000000608010167519",
            "countryCode": "EG",
            "userRemark": "ApiPost mock salary trade order",
            "deviceId": "apipost-anchor-device",
            "language": "zh",
            "appVersion": "1.0.0",
            "os": "ios",
            "channel": "apipost",
            "bankReceiverName": "newbee",
            "swiftCode": "555555",
            "bankName": "newbee",
            "bankAccount": "12313132132131313123213",
            "bankReceiverAddress": "EG",
        },
        "request_body_required": false,
        "required_variables": [],
        "expected_statuses": [200],
        "response_schema_type": "object",
        "tags": ["user/trade/主播侧"],
        "mapped_case_ids": [
            "tc_ddc2782339",
            "tc_6f8644c487",
            "tc_9e9ab12cdd",
            "tc_e2826cb5f1",
            "tc_7b37235a8c",
            "tc_29ae76a3e3",
            "tc_ae27bbd8fb",
            "tc_8aac818fe6",
        ],
    },
    {
        "id": "get__userserv_salary_trade_order_page",
        "title": "主播订单分页",
        "method": "GET",
        "path": "/userserv/salary/trade/order/page",
        "parameters": [
            {"name": "uid", "in": "query", "required": true, "example": "{{uid}}"},
            {
                "name": "ticket",
                "in": "query",
                "required": true,
                "example": "{{access_token}}",
            },
        ],
        "request_body_example": null,
        "request_body_required": false,
        "required_variables": [],
        "expected_statuses": [200],
        "response_schema_type": "object",
        "tags": ["user/trade/主播侧"],
        "mapped_case_ids": [
            "tc_2c8302c8bf",
            "tc_1cb94e5edc",
            "tc_cec2930031",
            "tc_09a3bd659e",
            "tc_bcaafeea5a",
            "tc_bce7f0b1de",
        ],
    },
    {
        "id": "get__salary_trade_order_detail",
        "title": "主播订单详情",
        "method": "GET",
        "path": "/salary/trade/order/detail",
        "parameters": [
            {
                "name": "uid",
                "in": "query",
                "required": true,
                "example": "{{anchorUid}}",
            },
            {
                "name": "ticket",
                "in": "query",
                "required": true,
                "example": "{{anchorTicket}}",
            },
            {
                "name": "orderNo",
                "in": "query",
                "required": true,
                "example": "{{orderNo}}",
            },
            {
                "name": "deviceId",
                "in": "query",
                "required": true,
                "example": "apipost-anchor-device",
            },
            {"name": "language", "in": "query", "required": true, "example": "zh"},
            {"name": "appVersion", "in": "query", "required": true, "example": "1.0.0"},
            {"name": "os", "in": "query", "required": true, "example": "ios"},
            {"name": "channel", "in": "query", "required": true, "example": "apipost"},
        ],
        "request_body_example": null,
        "request_body_required": false,
        "required_variables": [],
        "expected_statuses": [200],
        "response_schema_type": "object",
        "tags": ["user/trade/主播侧"],
        "mapped_case_ids": [],
    },
    {
        "id": "post__userserv_salary_trade_order_cancel",
        "title": "主播取消订单",
        "method": "POST",
        "path": "/userserv/salary/trade/order/cancel",
        "parameters": [
            {
                "name": "Content-Type",
                "in": "header",
                "required": true,
                "example": "application/x-www-form-urlencoded",
            }
        ],
        "request_body_example": {
            "uid": "{{uid}}",
            "ticket": "{{access_token}}",
            "orderNo": "1455141260826164551792387",
        },
        "request_body_required": false,
        "required_variables": [],
        "expected_statuses": [200],
        "response_schema_type": "object",
        "tags": ["user/trade/主播侧"],
        "mapped_case_ids": [
            "tc_4a361f2e73",
            "tc_9cce4f325a",
            "tc_fd3c65bfca",
            "tc_ea40bd1230",
            "tc_5e834a4d16",
            "tc_9f5be4623d",
            "tc_0517361e1a",
            "tc_432f1720e0",
        ],
    },
    {
        "id": "post__salary_trade_order_confirm",
        "title": "主播确认到账",
        "method": "POST",
        "path": "/salary/trade/order/confirm",
        "parameters": [
            {
                "name": "Content-Type",
                "in": "header",
                "required": true,
                "example": "application/x-www-form-urlencoded",
            }
        ],
        "request_body_example": {
            "uid": "{{anchorUid}}",
            "ticket": "{{anchorTicket}}",
            "orderNo": "{{orderNo}}",
            "reason": "ApiPost mock payment received",
            "deviceId": "apipost-anchor-device",
            "language": "zh",
            "appVersion": "1.0.0",
            "os": "ios",
            "channel": "apipost",
        },
        "request_body_required": false,
        "required_variables": [],
        "expected_statuses": [200],
        "response_schema_type": "object",
        "tags": ["user/trade/主播侧"],
        "mapped_case_ids": [],
    },
    {
        "id": "post__salary_trade_order_appeal",
        "title": "主播申诉订单",
        "method": "POST",
        "path": "/salary/trade/order/appeal",
        "parameters": [
            {
                "name": "Content-Type",
                "in": "header",
                "required": true,
                "example": "application/x-www-form-urlencoded",
            }
        ],
        "request_body_example": {
            "uid": "{{anchorUid}}",
            "ticket": "{{anchorTicket}}",
            "orderNo": "{{orderNo}}",
            "reason": "ApiPost mock payment not received",
            "evidenceUrls": "{{evidenceUrl}},https://s3.gzxchate.com/Spartysys/evidence/mock-chat-record.jpg",
            "deviceId": "apipost-anchor-device",
            "language": "zh",
            "appVersion": "1.0.0",
            "os": "ios",
            "channel": "apipost",
        },
        "request_body_required": false,
        "required_variables": [],
        "expected_statuses": [200],
        "response_schema_type": "object",
        "tags": ["user/trade/主播侧"],
        "mapped_case_ids": [],
    },
    {
        "id": "post__salary_trade_evidence_upload",
        "title": "主播补充凭证",
        "method": "POST",
        "path": "/salary/trade/evidence/upload",
        "parameters": [
            {
                "name": "Content-Type",
                "in": "header",
                "required": true,
                "example": "application/x-www-form-urlencoded",
            }
        ],
        "request_body_example": {
            "uid": "{{anchorUid}}",
            "ticket": "{{anchorTicket}}",
            "orderNo": "{{orderNo}}",
            "evidenceType": "1",
            "url": "{{evidenceUrl}}",
            "remark": "ApiPost mock anchor evidence",
            "deviceId": "apipost-anchor-device",
            "language": "zh",
            "appVersion": "1.0.0",
            "os": "ios",
            "channel": "apipost",
        },
        "request_body_required": false,
        "required_variables": [],
        "expected_statuses": [200],
        "response_schema_type": "object",
        "tags": ["user/trade/主播侧"],
        "mapped_case_ids": [],
    },
    {
        "id": "get__salary_trade_evidence_list",
        "title": "主播查询凭证",
        "method": "GET",
        "path": "/salary/trade/evidence/list",
        "parameters": [
            {
                "name": "uid",
                "in": "query",
                "required": true,
                "example": "{{anchorUid}}",
            },
            {
                "name": "ticket",
                "in": "query",
                "required": true,
                "example": "{{anchorTicket}}",
            },
            {
                "name": "orderNo",
                "in": "query",
                "required": true,
                "example": "{{orderNo}}",
            },
            {
                "name": "deviceId",
                "in": "query",
                "required": true,
                "example": "apipost-anchor-device",
            },
            {"name": "language", "in": "query", "required": true, "example": "zh"},
            {"name": "appVersion", "in": "query", "required": true, "example": "1.0.0"},
            {"name": "os", "in": "query", "required": true, "example": "ios"},
            {"name": "channel", "in": "query", "required": true, "example": "apipost"},
        ],
        "request_body_example": null,
        "request_body_required": false,
        "required_variables": [],
        "expected_statuses": [200],
        "response_schema_type": "object",
        "tags": ["user/trade/主播侧"],
        "mapped_case_ids": [],
    },
    {
        "id": "get__salary_trade_logs",
        "title": "主播查询流转日志",
        "method": "GET",
        "path": "/salary/trade/logs",
        "parameters": [
            {
                "name": "uid",
                "in": "query",
                "required": true,
                "example": "{{anchorUid}}",
            },
            {
                "name": "ticket",
                "in": "query",
                "required": true,
                "example": "{{anchorTicket}}",
            },
            {
                "name": "orderNo",
                "in": "query",
                "required": true,
                "example": "{{orderNo}}",
            },
            {
                "name": "deviceId",
                "in": "query",
                "required": true,
                "example": "apipost-anchor-device",
            },
            {"name": "language", "in": "query", "required": true, "example": "zh"},
            {"name": "appVersion", "in": "query", "required": true, "example": "1.0.0"},
            {"name": "os", "in": "query", "required": true, "example": "ios"},
            {"name": "channel", "in": "query", "required": true, "example": "apipost"},
        ],
        "request_body_example": null,
        "request_body_required": false,
        "required_variables": [],
        "expected_statuses": [200],
        "response_schema_type": "object",
        "tags": ["user/trade/主播侧"],
        "mapped_case_ids": [],
    },
    {
        "id": "get__salary_trade_agent_order_page",
        "title": "代理订单分页",
        "method": "GET",
        "path": "/salary/trade/agent/order/page",
        "parameters": [
            {"name": "uid", "in": "query", "required": true, "example": "{{agentUid}}"},
            {
                "name": "ticket",
                "in": "query",
                "required": true,
                "example": "{{agentTicket}}",
            },
            {
                "name": "unionId",
                "in": "query",
                "required": true,
                "example": "{{unionId}}",
            },
            {"name": "orderNo", "in": "query", "required": true, "example": ""},
            {"name": "status", "in": "query", "required": true, "example": "10"},
            {
                "name": "receiveCurrency",
                "in": "query",
                "required": true,
                "example": "SAR",
            },
            {"name": "countryCode", "in": "query", "required": true, "example": "SA"},
            {"name": "hasAppeal", "in": "query", "required": true, "example": "false"},
            {
                "name": "startTime",
                "in": "query",
                "required": true,
                "example": "1785513600000",
            },
            {
                "name": "endTime",
                "in": "query",
                "required": true,
                "example": "1788192000000",
            },
            {"name": "pageNum", "in": "query", "required": true, "example": "1"},
            {"name": "pageSize", "in": "query", "required": true, "example": "20"},
            {
                "name": "deviceId",
                "in": "query",
                "required": true,
                "example": "apipost-agent-device",
            },
            {"name": "language", "in": "query", "required": true, "example": "zh"},
            {"name": "appVersion", "in": "query", "required": true, "example": "1.0.0"},
            {"name": "os", "in": "query", "required": true, "example": "android"},
            {"name": "osVersion", "in": "query", "required": true, "example": "15"},
            {"name": "channel", "in": "query", "required": true, "example": "apipost"},
            {
                "name": "deviceType",
                "in": "query",
                "required": true,
                "example": "mobile",
            },
            {"name": "model", "in": "query", "required": true, "example": "Pixel%209"},
            {"name": "netType", "in": "query", "required": true, "example": "wifi"},
        ],
        "request_body_example": null,
        "request_body_required": false,
        "required_variables": ["orderNo"],
        "expected_statuses": [200],
        "response_schema_type": "object",
        "tags": ["user/trade/代理侧"],
        "mapped_case_ids": [],
    },
    {
        "id": "get__salary_trade_agent_order_detail",
        "title": "代理订单详情",
        "method": "GET",
        "path": "/salary/trade/agent/order/detail",
        "parameters": [
            {"name": "uid", "in": "query", "required": true, "example": "{{agentUid}}"},
            {
                "name": "ticket",
                "in": "query",
                "required": true,
                "example": "{{agentTicket}}",
            },
            {
                "name": "orderNo",
                "in": "query",
                "required": true,
                "example": "{{orderNo}}",
            },
            {
                "name": "deviceId",
                "in": "query",
                "required": true,
                "example": "apipost-agent-device",
            },
            {"name": "language", "in": "query", "required": true, "example": "zh"},
            {"name": "appVersion", "in": "query", "required": true, "example": "1.0.0"},
            {"name": "os", "in": "query", "required": true, "example": "android"},
            {"name": "channel", "in": "query", "required": true, "example": "apipost"},
        ],
        "request_body_example": null,
        "request_body_required": false,
        "required_variables": [],
        "expected_statuses": [200],
        "response_schema_type": "object",
        "tags": ["user/trade/代理侧"],
        "mapped_case_ids": [],
    },
    {
        "id": "post__salary_trade_agent_order_accept",
        "title": "代理接单",
        "method": "POST",
        "path": "/salary/trade/agent/order/accept",
        "parameters": [
            {
                "name": "Content-Type",
                "in": "header",
                "required": true,
                "example": "application/x-www-form-urlencoded",
            }
        ],
        "request_body_example": {
            "uid": "{{agentUid}}",
            "ticket": "{{agentTicket}}",
            "orderNo": "{{orderNo}}",
            "reason": "ApiPost mock accept order",
            "deviceId": "apipost-agent-device",
            "language": "zh",
            "appVersion": "1.0.0",
            "os": "android",
            "channel": "apipost",
        },
        "request_body_required": false,
        "required_variables": [],
        "expected_statuses": [200],
        "response_schema_type": "object",
        "tags": ["user/trade/代理侧"],
        "mapped_case_ids": [],
    },
    {
        "id": "post__salary_trade_agent_order_reject",
        "title": "代理拒绝订单",
        "method": "POST",
        "path": "/salary/trade/agent/order/reject",
        "parameters": [
            {
                "name": "Content-Type",
                "in": "header",
                "required": true,
                "example": "application/x-www-form-urlencoded",
            }
        ],
        "request_body_example": {
            "uid": "{{agentUid}}",
            "ticket": "{{agentTicket}}",
            "orderNo": "{{orderNo}}",
            "reason": "ApiPost mock unsupported payment account",
            "deviceId": "apipost-agent-device",
            "language": "zh",
            "appVersion": "1.0.0",
            "os": "android",
            "channel": "apipost",
        },
        "request_body_required": false,
        "required_variables": [],
        "expected_statuses": [200],
        "response_schema_type": "object",
        "tags": ["user/trade/代理侧"],
        "mapped_case_ids": [],
    },
    {
        "id": "post__salary_trade_agent_order_paid",
        "title": "代理标记已付款",
        "method": "POST",
        "path": "/salary/trade/agent/order/paid",
        "parameters": [
            {
                "name": "Content-Type",
                "in": "header",
                "required": true,
                "example": "application/x-www-form-urlencoded",
            }
        ],
        "request_body_example": {
            "uid": "{{agentUid}}",
            "ticket": "{{agentTicket}}",
            "orderNo": "{{orderNo}}",
            "payProofUrls": "{{evidenceUrl}},https://s3.gzxchate.com/Spartysys/evidence/mock-bank-transfer.jpg",
            "agentRemark": "ApiPost mock bank transfer completed",
            "deviceId": "apipost-agent-device",
            "language": "zh",
            "appVersion": "1.0.0",
            "os": "android",
            "channel": "apipost",
        },
        "request_body_required": false,
        "required_variables": [],
        "expected_statuses": [200],
        "response_schema_type": "object",
        "tags": ["user/trade/代理侧"],
        "mapped_case_ids": [],
    },
    {
        "id": "post__salary_trade_agent_order_appeal",
        "title": "代理申诉订单",
        "method": "POST",
        "path": "/salary/trade/agent/order/appeal",
        "parameters": [
            {
                "name": "Content-Type",
                "in": "header",
                "required": true,
                "example": "application/x-www-form-urlencoded",
            }
        ],
        "request_body_example": {
            "uid": "{{agentUid}}",
            "ticket": "{{agentTicket}}",
            "orderNo": "{{orderNo}}",
            "reason": "ApiPost mock agent payment dispute",
            "evidenceUrls": "{{evidenceUrl}},https://s3.gzxchate.com/Spartysys/evidence/mock-agent-chat.jpg",
            "deviceId": "apipost-agent-device",
            "language": "zh",
            "appVersion": "1.0.0",
            "os": "android",
            "channel": "apipost",
        },
        "request_body_required": false,
        "required_variables": [],
        "expected_statuses": [200],
        "response_schema_type": "object",
        "tags": ["user/trade/代理侧"],
        "mapped_case_ids": [],
    },
    {
        "id": "post__salary_trade_agent_evidence_upload",
        "title": "代理补充付款凭证",
        "method": "POST",
        "path": "/salary/trade/agent/evidence/upload",
        "parameters": [
            {
                "name": "Content-Type",
                "in": "header",
                "required": true,
                "example": "application/x-www-form-urlencoded",
            }
        ],
        "request_body_example": {
            "uid": "{{agentUid}}",
            "ticket": "{{agentTicket}}",
            "orderNo": "{{orderNo}}",
            "evidenceType": "2",
            "url": "{{evidenceUrl}}",
            "remark": "ApiPost mock agent payment evidence",
            "deviceId": "apipost-agent-device",
            "language": "zh",
            "appVersion": "1.0.0",
            "os": "android",
            "channel": "apipost",
        },
        "request_body_required": false,
        "required_variables": [],
        "expected_statuses": [200],
        "response_schema_type": "object",
        "tags": ["user/trade/代理侧"],
        "mapped_case_ids": [],
    },
]


def _env_name(name):
    return "AUTOTEST_" + re.sub(r"[^A-Za-z0-9]+", "_", str(name)).strip("_").upper()


def _runtime_value(name, example=None):
    value = os.getenv(_env_name(name))
    return value if value not in (None, "") else example


def _request_parts(operation):
    path = operation["path"]
    query = {}
    headers = {}
    missing = []
    for parameter in operation.get("parameters", []):
        value = _runtime_value(parameter["name"], parameter.get("example"))
        if parameter.get("required") and value in (None, ""):
            missing.append(parameter["name"])
            continue
        if value in (None, ""):
            continue
        if parameter["in"] == "path":
            path = path.replace("{" + parameter["name"] + "}", str(value))
        elif parameter["in"] == "header":
            headers[parameter["name"]] = str(value)
        elif parameter["in"] == "query":
            query[parameter["name"]] = value
    return path, query, headers, missing


@pytest.mark.parametrize(
    "operation", OPERATIONS, ids=[item["id"] for item in OPERATIONS]
)
def test_openapi_contract(operation):
    if os.getenv("AUTOTEST_RUN_HTTP", "0").lower() not in {"1", "true", "yes"}:
        pytest.skip("设置 AUTOTEST_RUN_HTTP=1 后发送真实请求")
    base_url = os.getenv("AUTOTEST_BASE_URL", "").rstrip("/")
    if not base_url:
        pytest.skip("缺少 AUTOTEST_BASE_URL")
    path, query, headers, missing = _request_parts(operation)
    if missing:
        pytest.skip("缺少必填运行变量: " + ", ".join(missing))
    body = operation.get("request_body_example")
    if operation.get("request_body_required") and body in (None, {}):
        pytest.skip("OpenAPI未提供必填请求体示例，请在business目录补充")
    response = httpx.request(
        operation["method"],
        base_url + "/" + path.lstrip("/"),
        params=query,
        headers=headers,
        json=body if body is not None else None,
        timeout=float(os.getenv("AUTOTEST_HTTP_TIMEOUT", "30")),
    )
    assert response.status_code in operation["expected_statuses"], response.text[:1000]
    expected_type = operation.get("response_schema_type")
    if expected_type in {"object", "array"}:
        payload = response.json()
        assert isinstance(payload, dict if expected_type == "object" else list)
