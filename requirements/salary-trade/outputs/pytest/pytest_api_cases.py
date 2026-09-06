import csv
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_URL = os.getenv("AUTOTEST_BASE_URL", "https://test2westarlive.gzxchate.com/")
PACKAGE_ID = "salary-trade"
PACKAGE_ROOT_HINT = "C:\\Users\\DELL\\Documents\\Codex\\2026-08-19\\new-chat\\outputs\\AutoTest-AI\\requirements\\salary-trade"
CASES = [
  {
    "id": "tc_3c2aa3f293",
    "title": "返回工资快速结算创建入口开关：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "GET",
    "path": "/union/getAnchorApplyRecord?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_c4f56bbedb",
    "title": "返回工资快速结算创建入口开关：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "POST",
    "path": "/union/getAnchorApplyRecord?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_586b91c352",
    "title": "进入入口时查询可结算额度：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/quota?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_cb0f14e257",
    "title": "按国家和币种选择代理用户：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/agents?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_ddc2782339",
    "title": "提交收款信息并创建待代理处理订单：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/order/create?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_2c8302c8bf",
    "title": "查看本人快速结算订单列表：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/order/page?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_ed495e60ee",
    "title": "查看本人订单详情：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/order/detail?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_4a361f2e73",
    "title": "取消待代理处理订单：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/order/cancel?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_da1f72545f",
    "title": "确认已收到代理转账：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/order/confirm?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_be228a1cd1",
    "title": "待确认收款时提交投诉：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/order/appeal?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_8ea08e4145",
    "title": "补充上传本人订单凭证：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/evidence/upload?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_3b931425b2",
    "title": "查看本人订单凭证：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/evidence/list?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_634b8077e8",
    "title": "查看本人订单流转记录：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/logs?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_8038c2a2f7",
    "title": "查看自己的交易公告编辑页信息：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/notice?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_92bfaeecaf",
    "title": "保存自己的交易公告：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/notice/save?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_6e4c0c21e9",
    "title": "查看可处理或已承接的订单列表：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/order/page?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_b05f2ae271",
    "title": "查看代理侧订单详情：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/order/detail?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_e07f18ed5f",
    "title": "接受待代理处理订单：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/accept?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_d1023be903",
    "title": "拒绝待代理处理订单：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/reject?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_3fea7697b2",
    "title": "标记已完成线下转账：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/paid?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_343e941fe3",
    "title": "待确认收款时提交投诉：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/appeal?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_aaf3603a09",
    "title": "补充上传付款或投诉凭证：正常请求",
    "scenario_type": "正常请求",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/evidence/upload?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_a29da10d78",
    "title": "返回工资快速结算创建入口开关：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/union/getAnchorApplyRecord?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_931a51df47",
    "title": "返回工资快速结算创建入口开关：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/union/getAnchorApplyRecord?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_4186d63f07",
    "title": "返回工资快速结算创建入口开关：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/union/getAnchorApplyRecord?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_25bb4b4110",
    "title": "返回工资快速结算创建入口开关：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/union/getAnchorApplyRecord?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_ffe359e00e",
    "title": "返回工资快速结算创建入口开关：重复提交与幂等性",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/union/getAnchorApplyRecord?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_71d4c8f02c",
    "title": "进入入口时查询可结算额度：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/quota?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_43c6c779d8",
    "title": "进入入口时查询可结算额度：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/quota?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_520d95529f",
    "title": "按国家和币种选择代理用户：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/agents?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_09f5709402",
    "title": "按国家和币种选择代理用户：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/agents?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_9e9ab12cdd",
    "title": "提交收款信息并创建待代理处理订单：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/order/create?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_e2826cb5f1",
    "title": "提交收款信息并创建待代理处理订单：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/order/create?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_7b37235a8c",
    "title": "提交收款信息并创建待代理处理订单：重复提交与幂等性",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/order/create?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_cec2930031",
    "title": "查看本人快速结算订单列表：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/order/page?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_09a3bd659e",
    "title": "查看本人快速结算订单列表：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/order/page?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_040bef7520",
    "title": "查看本人订单详情：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/order/detail?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_1c37a1d263",
    "title": "查看本人订单详情：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/order/detail?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_fd3c65bfca",
    "title": "取消待代理处理订单：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/order/cancel?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_ea40bd1230",
    "title": "取消待代理处理订单：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/order/cancel?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_5e834a4d16",
    "title": "取消待代理处理订单：重复提交与幂等性",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/order/cancel?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_82c425f44c",
    "title": "确认已收到代理转账：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/order/confirm?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_d280272aef",
    "title": "确认已收到代理转账：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/order/confirm?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_d5cae5cd7e",
    "title": "确认已收到代理转账：重复提交与幂等性",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/order/confirm?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_60ad3df5c9",
    "title": "待确认收款时提交投诉：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/order/appeal?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_78189ffc40",
    "title": "待确认收款时提交投诉：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/order/appeal?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_ac39a4c15e",
    "title": "待确认收款时提交投诉：重复提交与幂等性",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/order/appeal?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_6501f71533",
    "title": "补充上传本人订单凭证：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/evidence/upload?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_2e9af91fa2",
    "title": "补充上传本人订单凭证：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/evidence/upload?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=invalid-token&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_92a0e95d19",
    "title": "补充上传本人订单凭证：重复提交与幂等性",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/evidence/upload?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_894bfa0bef",
    "title": "查看本人订单凭证：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/evidence/list?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_44f440f8ec",
    "title": "查看本人订单凭证：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/evidence/list?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=invalid-token&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_204821a151",
    "title": "查看本人订单流转记录：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/logs?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_3995b1037b",
    "title": "查看本人订单流转记录：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/logs?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_148e1062ae",
    "title": "查看自己的交易公告编辑页信息：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/notice?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_970acf530c",
    "title": "查看自己的交易公告编辑页信息：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/notice?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_aa5fd1ad97",
    "title": "保存自己的交易公告：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/notice/save?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_456ee46651",
    "title": "保存自己的交易公告：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/notice/save?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_5754cedeaa",
    "title": "保存自己的交易公告：重复提交与幂等性",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/notice/save?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_92de8ee503",
    "title": "查看可处理或已承接的订单列表：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/order/page?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_f96f0a6e7c",
    "title": "查看可处理或已承接的订单列表：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/order/page?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_67d008fb3c",
    "title": "查看代理侧订单详情：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/order/detail?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_13d2898449",
    "title": "查看代理侧订单详情：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/order/detail?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_d5b812d9bc",
    "title": "接受待代理处理订单：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/accept?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_2cbdc73c2a",
    "title": "接受待代理处理订单：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/accept?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_6d0fa5869e",
    "title": "接受待代理处理订单：重复提交与幂等性",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/accept?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_ae8f94bb13",
    "title": "拒绝待代理处理订单：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/reject?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_e7f828e13a",
    "title": "拒绝待代理处理订单：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/reject?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_e3fe32d890",
    "title": "拒绝待代理处理订单：重复提交与幂等性",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/reject?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_7b351242d9",
    "title": "标记已完成线下转账：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/paid?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_81ca4518aa",
    "title": "标记已完成线下转账：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/paid?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_cecc2e452e",
    "title": "标记已完成线下转账：重复提交与幂等性",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/paid?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_63b49481af",
    "title": "待确认收款时提交投诉：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/appeal?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_9703f0d4b0",
    "title": "待确认收款时提交投诉：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/appeal?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=not-a-number&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_6d43b840fc",
    "title": "待确认收款时提交投诉：重复提交与幂等性",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/appeal?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  },
  {
    "id": "tc_a252cf3ccf",
    "title": "补充上传付款或投诉凭证：缺失必填参数",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/evidence/upload?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_4754618c13",
    "title": "补充上传付款或投诉凭证：字段边界与类型错误",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/evidence/upload?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=invalid-token&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 400,
    "expected_business_code": ""
  },
  {
    "id": "tc_8f0fbfb1e9",
    "title": "补充上传付款或投诉凭证：重复提交与幂等性",
    "scenario_type": "接口契约",
    "coverage_tool": "",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/evidence/upload?os=android&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&packageName=com.soulfree.happiness&ispType=4&language=en&channel=google&model=SM-A546B&netType=2&organic=Organic&uid=1454694&osVersion=16&appCode=100154&version=100.1.5.4&deviceType=0&ticket=***REDACTED***&appid=soulfree&systemLanguage=zh&appsflyerId=1787628595990-5267637366511328587&isVpnConnected=0&appVersion=100.1.5.4",
    "headers": {
      "t": "1788529375534"
    },
    "payload": "",
    "expected_status": 200,
    "expected_business_code": ""
  }
]
RUNTIME_STATE = {}


def package_root():
    hinted = Path(PACKAGE_ROOT_HINT) if PACKAGE_ROOT_HINT else None
    if hinted and hinted.exists():
        return hinted
    here = Path(__file__).resolve()
    return here.parents[2] if len(here.parents) > 2 else here.parent


def project_root():
    root = package_root()
    return root.parents[1] if len(root.parents) > 1 and root.parent.name == "requirements" else root


def load_json(path, default):
    try:
        p = Path(path)
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else default
    except Exception:
        return default


def load_yaml(path, default):
    p = Path(path)
    if not p.is_file():
        return default
    try:
        import yaml
        return yaml.safe_load(p.read_text(encoding="utf-8")) or default
    except Exception as exc:
        return {"_load_error": str(exc), "rules": []}


def load_env_file(path):
    p = Path(path)
    if not p.is_file():
        return
    for raw in p.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def bootstrap_env():
    root = project_root()
    load_env_file(root / "database.env")
    load_env_file(root / "config" / "runtime.env")
    load_env_file(package_root() / "data" / "database.env")


def runtime_variables():
    runtime = {}
    for env_key in ("AUTOTEST_RUNTIME_PARAMS_JSON", "AUTOTEST_EVIDENCE_RUNTIME_JSON"):
        try:
            payload = json.loads(os.getenv(env_key, "{}"))
            if isinstance(payload, dict):
                runtime.update(payload)
        except Exception:
            pass
    aliases = {
        "AUTOTEST_ORDER_NO": "order_no",
        "AUTOTEST_SALARY_ORDER_NO": "order_no",
        "AUTOTEST_APPLICANT_UID": "applicant_uid",
        "AUTOTEST_PROXY_UID": "proxy_uid",
        "AUTOTEST_AGENT_UID": "proxy_uid",
        "AUTOTEST_COUNTRY_CODE": "country_code",
        "AUTOTEST_CURRENCY": "currency",
        "AUTOTEST_EXPECTED_LOG_STATUSES": "expected_log_statuses",
        "AUTOTEST_RUNTIME_TICKET": "ticket",
        "AUTOTEST_RUNTIME_UID": "uid",
    }
    for env_key, name in aliases.items():
        value = os.getenv(env_key, "")
        if value:
            runtime[name] = value
    runtime.update({key: value for key, value in RUNTIME_STATE.items() if value not in (None, "")})
    if "orderNo" in runtime and "order_no" not in runtime:
        runtime["order_no"] = runtime["orderNo"]
    if "salary_order_no" in runtime and "order_no" not in runtime:
        runtime["order_no"] = runtime["salary_order_no"]
    if "countryCode" in runtime and "country_code" not in runtime:
        runtime["country_code"] = runtime["countryCode"]
    if "agent_uid" in runtime and "proxy_uid" not in runtime:
        runtime["proxy_uid"] = runtime["agent_uid"]
    return runtime


def snake_case(name):
    text = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", str(name or ""))
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    return re.sub(r"[^a-zA-Z0-9_]+", "_", text).strip("_").lower()


def camel_case(name):
    parts = [x for x in re.split(r"[_\-\s]+", str(name or "")) if x]
    if not parts:
        return ""
    return parts[0] + "".join(x[:1].upper() + x[1:] for x in parts[1:])


def load_runtime_aliases():
    root = package_root()
    payload = load_yaml(root / "runtime_aliases.yaml", {})
    aliases = payload.get("aliases") if isinstance(payload, dict) else None
    if not isinstance(aliases, dict):
        aliases = {}
    defaults = {
        "orderNo": ["order_no", "orderNo"],
        "orderId": ["order_id", "orderId"],
        "uid": ["uid"],
        "agentUid": ["agent_uid", "proxy_uid", "agentUid", "proxyUid"],
        "proxyUid": ["proxy_uid", "agent_uid", "proxyUid", "agentUid"],
        "countryCode": ["country_code", "countryCode"],
        "currency": ["currency"],
    }
    for key, values in defaults.items():
        aliases.setdefault(key, values)
    return aliases


def remember_runtime_value(name, value, aliases=None, overwrite=False):
    if value in (None, ""):
        return
    aliases = aliases or load_runtime_aliases()
    names = set(aliases.get(name) or [])
    names.add(name)
    names.add(snake_case(name))
    camel = camel_case(name)
    if camel:
        names.add(camel)
    for key in names:
        if not key:
            continue
        if key in ("ticket", "token", "access_token", "password"):
            continue
        if overwrite or RUNTIME_STATE.get(key) in (None, ""):
            RUNTIME_STATE[key] = value


def walk_json_scalars(value, parent_key=""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from walk_json_scalars(item, str(key))
    elif isinstance(value, list):
        for item in value[:3]:
            yield from walk_json_scalars(item, parent_key)
    else:
        yield parent_key, value


def fill_runtime(value):
    if isinstance(value, dict):
        return {k: fill_runtime(v) for k, v in value.items()}
    if isinstance(value, list):
        return [fill_runtime(v) for v in value]
    text = str(value or "")
    runtime = runtime_variables()
    for key, raw in runtime.items():
        text = text.replace("{{" + key + "}}", str(raw))
    return text


def ensure_common_query_params(path):
    runtime = runtime_variables()
    parsed = urllib.parse.urlsplit(path)
    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    current = {key: value for key, value in query_pairs}
    additions = []
    aliases = load_runtime_aliases()
    mapping = {
        "ticket": runtime.get("ticket"),
        "uid": runtime.get("uid") or runtime.get("applicant_uid"),
        "countryCode": runtime.get("countryCode") or runtime.get("country_code"),
        "currency": runtime.get("currency"),
        "agentUid": runtime.get("agentUid") or runtime.get("proxy_uid"),
        "proxyUid": runtime.get("proxyUid") or runtime.get("proxy_uid"),
        "orderNo": runtime.get("orderNo") or runtime.get("order_no"),
        "orderId": runtime.get("orderId") or runtime.get("order_id"),
    }
    for key in ("deviceType", "systemLanguage", "appVersion", "os", "netType", "channel", "appsflyerId", "language", "appCode", "deviceId", "version", "osVersion", "isVpnConnected", "appid", "model", "packageName", "ispType", "organic"):
        if runtime.get(key):
            mapping[key] = runtime.get(key)
    for query_key in re.findall(r"[?&]([A-Za-z_][A-Za-z0-9_]*)=", "?" + parsed.query):
        alias_names = [query_key, snake_case(query_key), camel_case(query_key)] + list(aliases.get(query_key) or [])
        for name in alias_names:
            if runtime.get(name) not in (None, ""):
                mapping[query_key] = runtime.get(name)
                break
    for key, value in mapping.items():
        existing = current.get(key)
        if value not in (None, "") and (existing in (None, "", "***REDACTED***")):
            additions.append((key, str(value)))
    if not additions:
        return path
    query = urllib.parse.urlencode(query_pairs + additions, safe="{}")
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))


def apply_case_query_variant(case, path):
    title = str(case.get("title") or "").lower()
    parsed = urllib.parse.urlsplit(path)
    pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    target_aliases = {
        "uid": ("uid", "用户id", "用户 id"),
        "ticket": ("ticket", "token", "令牌", "登录态", "凭证"),
        "orderNo": ("orderno", "order no", "订单号"),
        "orderId": ("orderid", "order id", "订单id"),
        "pageNo": ("pageno", "page no", "页码"),
        "pageSize": ("pagesize", "page size", "分页大小"),
    }
    missing = any(word in title for word in ("缺失", "为空", "空值", "missing", "empty", "omit"))
    invalid = any(word in title for word in ("非法", "无效", "错误类型", "类型错误", "invalid", "wrong type"))
    target = next((key for key, aliases in target_aliases.items() if any(alias in title for alias in aliases)), "")
    if not target and (missing or invalid):
        target = "uid"
    if not target:
        return path
    if missing:
        pairs = [(key, value) for key, value in pairs if key.lower() != target.lower()]
    elif invalid:
        invalid_value = "not-a-number" if target.lower() in {"uid", "orderid", "pageno", "pagesize"} else "invalid-token"
        pairs = [(key, invalid_value if key.lower() == target.lower() else value) for key, value in pairs]
        if not any(key.lower() == target.lower() for key, _ in pairs):
            pairs.append((target, invalid_value))
    query = urllib.parse.urlencode(pairs, safe="{}")
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))


def update_runtime_from_response(case, body):
    try:
        payload = json.loads(body[body.find("{"):]) if "{" in body else json.loads(body)
    except Exception:
        return
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, (dict, list)):
        return
    path = str(case.get("path") or "")
    aliases = load_runtime_aliases()
    for key, value in walk_json_scalars(data):
        remember_runtime_value(key, value, aliases)
    if isinstance(data, dict):
        if data.get("countryCode") not in (None, ""):
            RUNTIME_STATE["country_code"] = data.get("countryCode")
            RUNTIME_STATE["countryCode"] = data.get("countryCode")
        if isinstance(data.get("supportCurrencies"), list) and data.get("supportCurrencies") and not RUNTIME_STATE.get("currency"):
            RUNTIME_STATE["currency"] = data["supportCurrencies"][0]
        for key, target in (("orderNo", "order_no"), ("order_no", "order_no"), ("orderId", "order_id"), ("id", "order_id")):
            if data.get(key) not in (None, "") and ("order" in path or "salary/trade" in path):
                RUNTIME_STATE[target] = data.get(key)
                if target == "order_no":
                    RUNTIME_STATE["orderNo"] = data.get(key)
        if isinstance(data.get("list"), list) and data.get("list"):
            first = data["list"][0]
            if isinstance(first, dict):
                if "agents" in path and first.get("uid") not in (None, ""):
                    RUNTIME_STATE["proxy_uid"] = first.get("uid")
                    RUNTIME_STATE["agentUid"] = first.get("uid")
                if first.get("countryCode") not in (None, "") and not RUNTIME_STATE.get("country_code"):
                    RUNTIME_STATE["country_code"] = first.get("countryCode")
                    RUNTIME_STATE["countryCode"] = first.get("countryCode")
                if isinstance(first.get("supportCurrencies"), list) and first.get("supportCurrencies") and not RUNTIME_STATE.get("currency"):
                    RUNTIME_STATE["currency"] = first["supportCurrencies"][0]
                if first.get("orderNo") not in (None, ""):
                    RUNTIME_STATE["order_no"] = first.get("orderNo")
                    RUNTIME_STATE["orderNo"] = first.get("orderNo")
                if first.get("id") not in (None, ""):
                    RUNTIME_STATE["order_id"] = first.get("id")
    elif isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict) and first.get("orderNo") not in (None, ""):
            RUNTIME_STATE["order_no"] = first.get("orderNo")
            RUNTIME_STATE["orderNo"] = first.get("orderNo")


def run_case(case):
    case = dict(case)
    case["path"] = apply_case_query_variant(case, ensure_common_query_params(fill_runtime(case.get("path", ""))))
    case["headers"] = fill_runtime(case.get("headers") or {})
    case["payload"] = fill_runtime(case.get("payload"))
    url = case["path"] if case["path"].startswith("http") else BASE_URL.rstrip("/") + "/" + case["path"].lstrip("/")
    body = case.get("payload")
    data = None if body in ("", None) else (body.encode("utf-8") if isinstance(body, str) else json.dumps(body, ensure_ascii=False).encode("utf-8"))
    headers = dict(case.get("headers") or {})
    runtime = runtime_variables()
    if runtime.get("t"):
        headers["t"] = str(runtime.get("t"))
    if runtime.get("sn") and "sn" not in headers:
        headers["sn"] = str(runtime.get("sn"))
    if data and "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=case["method"])
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.read(200000).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(200000).decode("utf-8", "replace")
    except urllib.error.URLError as exc:
        return 0, str(exc)
    except Exception as exc:
        return 0, str(exc)


def parse_jtl(path):
    p = Path(path or "")
    if not p.is_file():
        return {"path": str(p) if path else "", "exists": False, "samples": 0, "failures": 0, "failed_labels": []}
    if p.suffix.lower() == ".xml":
        root = ET.parse(p).getroot()
        samples = [x for x in root.iter() if x.attrib.get("lb")]
        failed = [x.attrib.get("lb", "") for x in samples if x.attrib.get("s") == "false"]
        return {"path": str(p), "exists": True, "samples": len(samples), "failures": len(failed), "failed_labels": failed[:30]}
    with p.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        rows = list(csv.DictReader(f))
    failed = [r.get("label", "") for r in rows if str(r.get("success", "")).lower() == "false" or str(r.get("responseCode", "")).startswith(("4", "5"))]
    return {"path": str(p), "exists": True, "samples": len(rows), "failures": len(failed), "failed_labels": failed[:30]}


def load_newman(path):
    payload = load_json(path, {})
    run = payload.get("run", {}) if isinstance(payload, dict) else {}
    failures = run.get("failures", []) if isinstance(run, dict) else []
    stats = run.get("stats", {}) if isinstance(run, dict) else {}
    return {"path": path or "", "exists": bool(payload), "failures": len(failures), "stats": stats}


def sql_value(value):
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    text = str(value if value is not None else "")
    return "'" + text.replace("\\", "\\\\").replace("'", "''") + "'"


def render_template(template, variables, missing):
    def repl(match):
        name = match.group(1)
        if name not in variables or variables.get(name) in (None, ""):
            missing.add(name)
            return "NULL"
        return sql_value(variables.get(name))
    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", repl, str(template or ""))


def mysql_query(sql):
    if not re.match(r"^\s*(select|show|describe|explain)\b", sql, re.I):
        raise RuntimeError("pytest evidence only allows read-only SQL")
    try:
        import pymysql
    except Exception as exc:
        raise RuntimeError("PyMySQL is not installed: " + str(exc))
    conn = pymysql.connect(
        host=os.getenv("AUTOTEST_DB_HOST", ""),
        port=int(os.getenv("AUTOTEST_DB_PORT", "3306") or "3306"),
        user=os.getenv("AUTOTEST_DB_USER", ""),
        password=os.getenv("AUTOTEST_DB_PASSWORD", ""),
        database=os.getenv("AUTOTEST_DB_NAME", ""),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=8,
        read_timeout=15,
        write_timeout=15,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return list(cur.fetchall())
    finally:
        conn.close()


def redis_read(rule, variables):
    try:
        import redis
    except Exception as exc:
        raise RuntimeError("redis package is not installed: " + str(exc))
    query = rule.get("query") if isinstance(rule.get("query"), dict) else {}
    key_template = query.get("key") or query.get("pattern") or rule.get("redis_key") or ""
    key = key_template
    missing = set()
    for name in re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", key_template):
        if not variables.get(name):
            missing.add(name)
        key = key.replace("${" + name + "}", str(variables.get(name, "")))
    if missing:
        raise RuntimeError("missing runtime variables: " + ",".join(sorted(missing)))
    client = redis.Redis(
        host=os.getenv("AUTOTEST_REDIS_HOST", os.getenv("REDIS_HOST", "")),
        port=int(os.getenv("AUTOTEST_REDIS_PORT", os.getenv("REDIS_PORT", "6379")) or "6379"),
        db=int(os.getenv("AUTOTEST_REDIS_DB", os.getenv("REDIS_DB", "0")) or "0"),
        ssl=str(os.getenv("AUTOTEST_REDIS_SSL", "false")).lower() in ("1", "true", "yes"),
        socket_timeout=8,
        decode_responses=True,
    )
    key_type = client.type(key)
    if key_type == "hash":
        return {"key": key, "type": key_type, "records": [client.hgetall(key)]}
    if key_type == "string":
        return {"key": key, "type": key_type, "records": [{"value": client.get(key)}]}
    return {"key": key, "type": key_type, "records": []}


def values_for_field(records, field):
    return [item.get(field) for item in records if isinstance(item, dict) and field in item]


def resolve_expected(value, variables):
    if isinstance(value, str):
        m = re.fullmatch(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", value.strip())
        if m:
            return variables.get(m.group(1))
    return value


def run_assertion(assertion, records, variables):
    field = str(assertion.get("field") or "")
    operator = str(assertion.get("operator") or "equals")
    expected = resolve_expected(assertion.get("expected"), variables)
    values = values_for_field(records, field)
    first = values[0] if values else None
    if operator == "exists":
        passed = bool(records)
    elif operator == "equals":
        passed = str(first) == str(expected)
    elif operator == "contains":
        passed = any(str(expected) in str(v or "") for v in values)
    elif operator == "contains_any":
        items = expected if isinstance(expected, list) else re.split(r"[,，\s]+", str(expected or ""))
        items = [str(x).strip() for x in items if str(x).strip()]
        passed = bool(items) and any(str(v) in items for v in values)
    elif operator == "not_empty":
        passed = any(v not in (None, "") for v in values)
    elif operator == "greater_than":
        try:
            passed = float(first) > float(expected)
        except Exception:
            passed = False
    else:
        passed = False
    return {"field": field, "operator": operator, "expected": expected, "actual": first if len(values) <= 1 else values[:20], "passed": bool(passed), "reason": "" if passed else "assertion not satisfied"}


def rule_identifier(rule):
    return str(rule.get("id") or rule.get("name") or "").strip()


def run_evidence_rules(rule_ids=None):
    bootstrap_env()
    root = package_root()
    variables = runtime_variables()
    rules_payload = load_yaml(root / "evidence_rules.yaml", {"rules": []})
    rules = rules_payload.get("rules") if isinstance(rules_payload, dict) else []
    selected = set(str(item) for item in (rule_ids or []) if str(item).strip())
    results = []
    for rule in rules or []:
        if selected and rule_identifier(rule) not in selected:
            continue
        query = rule.get("query") if isinstance(rule.get("query"), dict) else {}
        source = str(query.get("source") or rule.get("source") or "mysql").lower()
        blockers = []
        records = []
        sql = ""
        try:
            if source == "mysql":
                missing = set()
                table = str(query.get("table") or rule.get("table") or "")
                where = render_template(query.get("where") or rule.get("where") or "1=1", variables, missing)
                if missing:
                    blockers.append("缺少运行变量：" + ",".join(sorted(missing)))
                elif not table:
                    blockers.append("缺少表名")
                else:
                    sql = f"SELECT * FROM {table} WHERE {where} LIMIT 100"
                    records = mysql_query(sql)
            elif source == "redis":
                records = redis_read(rule, variables).get("records") or []
            else:
                blockers.append("不支持的数据源：" + source)
        except Exception as exc:
            blockers.append(str(exc))
        assertions = []
        if not blockers:
            assertions.append({"field": "__rows__", "operator": "exists", "expected": "至少1行", "actual": len(records), "passed": len(records) > 0, "reason": "" if records else "query returned no rows"})
            for assertion in rule.get("assertions") or []:
                assertions.append(run_assertion(assertion, records, variables))
        status = "BLOCKED" if blockers else "PASSED" if assertions and all(x.get("passed") for x in assertions) else "FAILED"
        results.append({"id": rule.get("id"), "name": rule.get("name"), "source": source, "sql": sql, "status": status, "rows": len(records), "assertions": assertions, "blockers": blockers, "sample": records[:3]})
    return results


def redact_text(text):
    text = str(text or "")
    text = re.sub(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+", "***jwt***", text)
    text = re.sub(r'("?(?:access_token|ticket|token)"?\s*[:=]\s*")([^"]+)(")', r'\1***\3', text, flags=re.I)
    return text


def redact_obj(value):
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if any(word in str(key).lower() for word in ("ticket", "token", "password")):
                out[key] = "***"
            else:
                out[key] = redact_obj(item)
        return out
    if isinstance(value, list):
        return [redact_obj(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def load_package_manifest():
    root = package_root()
    return load_json(root / "manifest.json", {})


def resolve_package_asset_path(*relative_candidates):
    root = package_root()
    manifest = load_package_manifest()
    orchestration = manifest.get("orchestration") if isinstance(manifest, dict) else None
    paths = []
    if isinstance(orchestration, dict):
        for key in ("primary_plan", "execution_plan", "scenario_plan", "path"):
            if orchestration.get(key):
                paths.append(orchestration.get(key))
    for candidate in relative_candidates:
        if candidate:
            paths.append(candidate)
    for item in paths:
        path = Path(str(item))
        if not path.is_absolute():
            path = root / path
        if path.is_file():
            return path
    return root / (relative_candidates[0] if relative_candidates else "")


def load_execution_plan():
    root = package_root()
    path = resolve_package_asset_path("outputs/execution-plan.json")
    payload = load_json(path, {})
    scenarios = payload.get("scenarios") if isinstance(payload, dict) else None
    return scenarios if isinstance(scenarios, list) else []


def case_scenario_index():
    mapping = {}
    order = []
    for scenario in load_execution_plan():
        scenario_id = scenario.get("scenario_id") or scenario.get("id") or scenario.get("name") or "unassigned"
        scenario_name = scenario.get("name") or scenario_id
        for case in scenario.get("cases") or []:
            case_id = case.get("id") if isinstance(case, dict) else case
            if case_id:
                mapping[str(case_id)] = {"scenario_id": scenario_id, "scenario_name": scenario_name, "scenario_status": scenario.get("status")}
                order.append(str(case_id))
        for task in scenario.get("tool_tasks") or []:
            for case_id in task.get("cases") or []:
                if case_id:
                    mapping[str(case_id)] = {"scenario_id": scenario_id, "scenario_name": scenario_name, "scenario_status": scenario.get("status")}
                    order.append(str(case_id))
    return {"mapping": mapping, "order": order}


def scenario_for_case(case, index=None):
    index = index or case_scenario_index()
    mapping = index.get("mapping") if isinstance(index, dict) else index
    item = (mapping or {}).get(str(case.get("id") or ""))
    if item:
        return item
    scenario_name = case.get("scenario_type") or "未分组场景"
    scenario_id = snake_case(scenario_name) or "unassigned"
    return {"scenario_id": scenario_id, "scenario_name": scenario_name, "scenario_status": ""}


def ordered_cases(cases, index=None):
    index = index or case_scenario_index()
    order = index.get("order") if isinstance(index, dict) else []
    case_by_id = {str(case.get("id") or ""): case for case in cases}
    seen = set()
    result = []
    for case_id in order or []:
        if case_id in case_by_id and case_id not in seen:
            result.append(case_by_id[case_id])
            seen.add(case_id)
    for case in cases:
        case_id = str(case.get("id") or "")
        if case_id not in seen:
            result.append(case)
            seen.add(case_id)
    return result


def planned_scenario_batches(cases, index=None):
    index = index or case_scenario_index()
    case_by_id = {str(case.get("id") or ""): case for case in cases}
    seen = set()
    batches = []
    for scenario in load_execution_plan():
        scenario_id = scenario.get("scenario_id") or scenario.get("id") or scenario.get("name") or "unassigned"
        scenario_name = scenario.get("name") or scenario_id
        case_ids = []
        evidence_rule_ids = []
        for rule_id in scenario.get("evidence_rules") or []:
            if rule_id:
                evidence_rule_ids.append(str(rule_id))
        for case in scenario.get("cases") or []:
            case_id = case.get("id") if isinstance(case, dict) else case
            if case_id:
                case_ids.append(str(case_id))
        for task in scenario.get("tool_tasks") or []:
            for rule_id in task.get("evidence_rules") or []:
                if rule_id:
                    evidence_rule_ids.append(str(rule_id))
            for case_id in task.get("cases") or []:
                if case_id:
                    case_ids.append(str(case_id))
        batch_cases = []
        for case_id in case_ids:
            if case_id in case_by_id and case_id not in seen:
                batch_cases.append(case_by_id[case_id])
                seen.add(case_id)
        if batch_cases:
            batches.append({
                "scenario_id": scenario_id,
                "scenario_name": scenario_name,
                "scenario_status": scenario.get("status"),
                "cases": batch_cases,
                "evidence_rule_ids": sorted(set(evidence_rule_ids)),
                "uses_explicit_evidence_rules": bool(evidence_rule_ids),
                "source": "orchestration",
                "raw": scenario,
            })
    fallback = {}
    for case in cases:
        case_id = str(case.get("id") or "")
        if case_id in seen:
            continue
        scenario = scenario_for_case(case, index)
        key = scenario.get("scenario_id") or "unassigned"
        item = fallback.setdefault(key, {"scenario_id": key, "scenario_name": scenario.get("scenario_name") or key, "scenario_status": scenario.get("scenario_status") or "", "cases": [], "evidence_rule_ids": [], "uses_explicit_evidence_rules": False, "source": "scenario_type", "raw": {}})
        item["cases"].append(case)
        seen.add(case_id)
    batches.extend(fallback.values())
    if not batches:
        batches.append({"scenario_id": "package_review", "scenario_name": "需求包证据复核", "scenario_status": "", "cases": [], "evidence_rule_ids": [], "uses_explicit_evidence_rules": False, "source": "empty", "raw": {}})
    return batches


def apply_scenario_runtime(scenario):
    raw = scenario.get("raw") if isinstance(scenario.get("raw"), dict) else {}
    values = {}
    for key in ("runtime", "runtime_variables", "variables", "params", "parameters"):
        item = raw.get(key)
        if isinstance(item, dict):
            values.update(item)
    for key in ("scenario_id", "account_slot", "order_variable", "order_no", "orderNo", "order_id", "orderId", "applicant_uid", "proxy_uid", "agent_uid", "country_code", "countryCode", "currency"):
        value = raw.get(key, scenario.get(key))
        if value not in (None, ""):
            values[key] = value
    for key, value in values.items():
        if isinstance(value, (dict, list)):
            continue
        remember_runtime_value(key, value, overwrite=True)


def run_single_case(case, scenario):
    status, body = run_case(case)
    update_runtime_from_response(case, body)
    business_code = ""
    business_message = ""
    try:
        parsed_body = json.loads(body[body.find("{"):]) if "{" in body else json.loads(body)
        if isinstance(parsed_body, dict):
            business_code = parsed_body.get("code", "")
            business_message = parsed_body.get("message", "")
    except Exception:
        pass
    return {"id": case.get("id"), "title": case["title"], "scenario_id": scenario.get("scenario_id"), "scenario_name": scenario.get("scenario_name"), "method": case["method"], "path": redact_text(ensure_common_query_params(fill_runtime(case.get("path", "")))), "status": status, "expected_status": case["expected_status"], "expected_business_code": case.get("expected_business_code"), "business_code": business_code, "business_message": business_message, "response_preview": redact_text(body[:800])}


def http_case_passed(result):
    if result.get("status") != result.get("expected_status"):
        return False
    expected_business_code = result.get("expected_business_code")
    if expected_business_code not in (None, ""):
        return str(result.get("business_code")) == str(expected_business_code)
    try:
        expected_status = int(result.get("expected_status"))
    except (TypeError, ValueError):
        expected_status = 0
    if 200 <= expected_status < 300:
        return str(result.get("business_code") or "200") == "200"
    return True


def run_scenario_batch(scenario, base_runtime_state=None):
    RUNTIME_STATE.clear()
    RUNTIME_STATE.update(base_runtime_state or {})
    apply_scenario_runtime(scenario)
    http_results = []
    for case in scenario.get("cases") or []:
        http_results.append(run_single_case(case, scenario))
    rule_ids = scenario.get("evidence_rule_ids") or []
    evidence = run_evidence_rules(rule_ids if rule_ids else None)
    for item in evidence:
        item["scenario_id"] = scenario.get("scenario_id")
        item["scenario_name"] = scenario.get("scenario_name")
    http_failed = sum(1 for x in http_results if not http_case_passed(x))
    failed = sum(1 for x in evidence if x.get("status") == "FAILED")
    blocked = sum(1 for x in evidence if x.get("status") == "BLOCKED")
    status = "BLOCKED" if blocked else "FAILED" if failed or http_failed else "PASSED"
    return {
        "scenario_id": scenario.get("scenario_id"),
        "name": scenario.get("scenario_name"),
        "planned_status": scenario.get("scenario_status"),
        "source": scenario.get("source"),
        "status": status,
        "http_cases": len(http_results),
        "http_failed": http_failed,
        "evidence_rule_ids": rule_ids,
        "evidence_rules": [{"id": x.get("id"), "name": x.get("name"), "status": x.get("status"), "source": x.get("source")} for x in evidence],
        "runtime_variables": {k: ("***" if "ticket" in k.lower() or "token" in k.lower() else v) for k, v in runtime_variables().items()},
        "http_results": http_results,
        "evidence_results": evidence,
    }


def build_evidence_report(scenario_runs):
    root = package_root()
    plan_path = resolve_package_asset_path("outputs/execution-plan.json")
    jtl = parse_jtl(os.getenv("AUTOTEST_JTL_PATH", ""))
    newman = load_newman(os.getenv("AUTOTEST_NEWMAN_JSON", ""))
    http_results = [item for scenario in scenario_runs for item in scenario.get("http_results") or []]
    evidence = [item for scenario in scenario_runs for item in scenario.get("evidence_results") or []]
    http_failed = sum(1 for x in http_results if not http_case_passed(x))
    failed = sum(1 for x in evidence if x["status"] == "FAILED")
    blocked = sum(1 for x in evidence if x["status"] == "BLOCKED")
    for scenario in scenario_runs:
        if jtl.get("failures"):
            scenario["jmeter_failed_labels"] = jtl.get("failed_labels") or []
        if newman.get("failures"):
            scenario["newman_failures"] = newman.get("failures", 0)
    report = {
        "report_type": "PYTEST_DEEP_EVIDENCE_REVIEW",
        "package_id": PACKAGE_ID or root.name,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "status": "BLOCKED" if blocked else "FAILED" if failed or http_failed or jtl.get("failures") or newman.get("failures") else "PASSED",
        "orchestration": {"path": str(plan_path), "exists": plan_path.is_file(), "fallback": "scenario_type" if not plan_path.is_file() else ""},
        "summary": {
            "http_cases": len(http_results),
            "http_failed": http_failed,
            "rules_total": len(evidence),
            "rules_failed": failed,
            "rules_blocked": blocked,
            "jtl_samples": jtl.get("samples", 0),
            "jtl_failures": jtl.get("failures", 0),
            "newman_failures": newman.get("failures", 0),
        },
        "runtime_variables": {k: ("***" if "ticket" in k.lower() or "token" in k.lower() else v) for k, v in runtime_variables().items()},
        "scenarios": scenario_runs,
        "http_results": http_results,
        "jmeter": jtl,
        "newman": newman,
        "evidence_rules": evidence,
    }
    out_dir = root / "reports" / ("pytest-evidence-" + time.strftime("%Y%m%d-%H%M%S"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out = Path(os.getenv("AUTOTEST_PYTEST_EVIDENCE_OUT", str(out_dir / "summary.json")))
    out.parent.mkdir(parents=True, exist_ok=True)
    safe_report = redact_obj(report)
    out.write_text(json.dumps(safe_report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    safe_report["summary_path"] = str(out)
    return safe_report


def test_api_cases():
    assert BASE_URL, "缺少 AUTOTEST_BASE_URL"
    bootstrap_env()
    scenario_index = case_scenario_index()
    base_runtime_state = dict(RUNTIME_STATE)
    scenario_runs = [run_scenario_batch(scenario, base_runtime_state) for scenario in planned_scenario_batches(CASES, scenario_index)]
    report = build_evidence_report(scenario_runs)
    strict = os.getenv("AUTOTEST_STRICT_EVIDENCE", "true").lower() not in ("0", "false", "no")
    if strict:
        assert report["status"] == "PASSED", "pytest evidence review failed: " + report.get("summary_path", "")
