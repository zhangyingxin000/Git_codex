import json
import os
import urllib.error
import urllib.request

BASE_URL = os.getenv("AUTOTEST_BASE_URL", "https://test2westarlive.gzxchate.com/")
CASES = [
  {
    "title": "返回工资快速结算创建入口开关：正常请求",
    "method": "GET",
    "path": "/union/getAnchorApplyRecord?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "返回工资快速结算创建入口开关：正常请求",
    "method": "POST",
    "path": "/union/getAnchorApplyRecord?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "进入入口时查询可结算额度：正常请求",
    "method": "GET",
    "path": "/userserv/salary/trade/quota?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "按国家和币种选择代理用户：正常请求",
    "method": "GET",
    "path": "/userserv/salary/trade/agents?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "提交收款信息并创建待代理处理订单：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/order/create?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看本人快速结算订单列表：正常请求",
    "method": "GET",
    "path": "/userserv/salary/trade/order/page?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看本人订单详情：正常请求",
    "method": "GET",
    "path": "/userserv/salary/trade/order/detail?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "取消待代理处理订单：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/order/cancel?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "确认已收到代理转账：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/order/confirm?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "待确认收款时提交投诉：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/order/appeal?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "补充上传本人订单凭证：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/evidence/upload?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看本人订单凭证：正常请求",
    "method": "GET",
    "path": "/userserv/salary/trade/evidence/list?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看本人订单流转记录：正常请求",
    "method": "GET",
    "path": "/userserv/salary/trade/logs?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看自己的交易公告编辑页信息：正常请求",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/notice?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "保存自己的交易公告：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/notice/save?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看可处理或已承接的订单列表：正常请求",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/order/page?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看代理侧订单详情：正常请求",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/order/detail?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "接受待代理处理订单：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/accept?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "拒绝待代理处理订单：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/reject?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "标记已完成线下转账：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/paid?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "待确认收款时提交投诉：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/appeal?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "补充上传付款或投诉凭证：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/evidence/upload?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "返回工资快速结算创建入口开关：正常请求",
    "method": "GET",
    "path": "/union/getAnchorApplyRecord?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "返回工资快速结算创建入口开关：正常请求",
    "method": "POST",
    "path": "/union/getAnchorApplyRecord?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "进入入口时查询可结算额度：正常请求",
    "method": "GET",
    "path": "/userserv/salary/trade/quota?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "按国家和币种选择代理用户：正常请求",
    "method": "GET",
    "path": "/userserv/salary/trade/agents?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "提交收款信息并创建待代理处理订单：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/order/create?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看本人快速结算订单列表：正常请求",
    "method": "GET",
    "path": "/userserv/salary/trade/order/page?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看本人订单详情：正常请求",
    "method": "GET",
    "path": "/userserv/salary/trade/order/detail?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "取消待代理处理订单：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/order/cancel?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "确认已收到代理转账：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/order/confirm?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "待确认收款时提交投诉：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/order/appeal?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "补充上传本人订单凭证：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/evidence/upload?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看本人订单凭证：正常请求",
    "method": "GET",
    "path": "/userserv/salary/trade/evidence/list?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看本人订单流转记录：正常请求",
    "method": "GET",
    "path": "/userserv/salary/trade/logs?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看自己的交易公告编辑页信息：正常请求",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/notice?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "保存自己的交易公告：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/notice/save?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看可处理或已承接的订单列表：正常请求",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/order/page?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看代理侧订单详情：正常请求",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/order/detail?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "接受待代理处理订单：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/accept?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "拒绝待代理处理订单：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/reject?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "标记已完成线下转账：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/paid?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "待确认收款时提交投诉：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/appeal?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "补充上传付款或投诉凭证：正常请求",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/evidence/upload?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "返回工资快速结算创建入口开关：缺失必填参数",
    "method": "GET",
    "path": "/union/getAnchorApplyRecord",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "返回工资快速结算创建入口开关：字段边界与类型错误",
    "method": "GET",
    "path": "/union/getAnchorApplyRecord",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "返回工资快速结算创建入口开关：缺失必填参数",
    "method": "POST",
    "path": "/union/getAnchorApplyRecord",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "返回工资快速结算创建入口开关：字段边界与类型错误",
    "method": "POST",
    "path": "/union/getAnchorApplyRecord",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "返回工资快速结算创建入口开关：重复提交与幂等性",
    "method": "POST",
    "path": "/union/getAnchorApplyRecord?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "进入入口时查询可结算额度：缺失必填参数",
    "method": "GET",
    "path": "/userserv/salary/trade/quota",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "进入入口时查询可结算额度：字段边界与类型错误",
    "method": "GET",
    "path": "/userserv/salary/trade/quota",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "按国家和币种选择代理用户：缺失必填参数",
    "method": "GET",
    "path": "/userserv/salary/trade/agents",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "按国家和币种选择代理用户：字段边界与类型错误",
    "method": "GET",
    "path": "/userserv/salary/trade/agents",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "提交收款信息并创建待代理处理订单：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/order/create",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "提交收款信息并创建待代理处理订单：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/order/create",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "提交收款信息并创建待代理处理订单：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/order/create?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看本人快速结算订单列表：缺失必填参数",
    "method": "GET",
    "path": "/userserv/salary/trade/order/page",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看本人快速结算订单列表：字段边界与类型错误",
    "method": "GET",
    "path": "/userserv/salary/trade/order/page",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看本人订单详情：缺失必填参数",
    "method": "GET",
    "path": "/userserv/salary/trade/order/detail",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看本人订单详情：字段边界与类型错误",
    "method": "GET",
    "path": "/userserv/salary/trade/order/detail",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "取消待代理处理订单：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/order/cancel",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "取消待代理处理订单：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/order/cancel",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "取消待代理处理订单：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/order/cancel?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "确认已收到代理转账：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/order/confirm",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "确认已收到代理转账：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/order/confirm",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "确认已收到代理转账：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/order/confirm?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "待确认收款时提交投诉：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/order/appeal",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "待确认收款时提交投诉：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/order/appeal",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "待确认收款时提交投诉：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/order/appeal?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "补充上传本人订单凭证：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/evidence/upload",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "补充上传本人订单凭证：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/evidence/upload",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "补充上传本人订单凭证：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/evidence/upload?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看本人订单凭证：缺失必填参数",
    "method": "GET",
    "path": "/userserv/salary/trade/evidence/list",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看本人订单凭证：字段边界与类型错误",
    "method": "GET",
    "path": "/userserv/salary/trade/evidence/list",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看本人订单流转记录：缺失必填参数",
    "method": "GET",
    "path": "/userserv/salary/trade/logs",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看本人订单流转记录：字段边界与类型错误",
    "method": "GET",
    "path": "/userserv/salary/trade/logs",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看自己的交易公告编辑页信息：缺失必填参数",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/notice",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看自己的交易公告编辑页信息：字段边界与类型错误",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/notice",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "保存自己的交易公告：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/notice/save",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "保存自己的交易公告：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/notice/save",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "保存自己的交易公告：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/notice/save?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看可处理或已承接的订单列表：缺失必填参数",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/order/page",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看可处理或已承接的订单列表：字段边界与类型错误",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/order/page",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看代理侧订单详情：缺失必填参数",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/order/detail",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看代理侧订单详情：字段边界与类型错误",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/order/detail",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "接受待代理处理订单：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/accept",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "接受待代理处理订单：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/accept",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "接受待代理处理订单：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/accept?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "拒绝待代理处理订单：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/reject",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "拒绝待代理处理订单：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/reject",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "拒绝待代理处理订单：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/reject?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "标记已完成线下转账：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/paid",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "标记已完成线下转账：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/paid",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "标记已完成线下转账：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/paid?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "待确认收款时提交投诉：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/appeal",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "待确认收款时提交投诉：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/appeal",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "待确认收款时提交投诉：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/appeal?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "补充上传付款或投诉凭证：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/evidence/upload",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "补充上传付款或投诉凭证：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/evidence/upload",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "补充上传付款或投诉凭证：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/evidence/upload?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "返回工资快速结算创建入口开关：缺失必填参数",
    "method": "GET",
    "path": "/union/getAnchorApplyRecord",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "返回工资快速结算创建入口开关：字段边界与类型错误",
    "method": "GET",
    "path": "/union/getAnchorApplyRecord",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "返回工资快速结算创建入口开关：缺失必填参数",
    "method": "POST",
    "path": "/union/getAnchorApplyRecord",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "返回工资快速结算创建入口开关：字段边界与类型错误",
    "method": "POST",
    "path": "/union/getAnchorApplyRecord",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "返回工资快速结算创建入口开关：重复提交与幂等性",
    "method": "POST",
    "path": "/union/getAnchorApplyRecord?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "进入入口时查询可结算额度：缺失必填参数",
    "method": "GET",
    "path": "/userserv/salary/trade/quota",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "进入入口时查询可结算额度：字段边界与类型错误",
    "method": "GET",
    "path": "/userserv/salary/trade/quota",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "按国家和币种选择代理用户：缺失必填参数",
    "method": "GET",
    "path": "/userserv/salary/trade/agents",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "按国家和币种选择代理用户：字段边界与类型错误",
    "method": "GET",
    "path": "/userserv/salary/trade/agents",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "提交收款信息并创建待代理处理订单：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/order/create",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "提交收款信息并创建待代理处理订单：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/order/create",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "提交收款信息并创建待代理处理订单：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/order/create?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看本人快速结算订单列表：缺失必填参数",
    "method": "GET",
    "path": "/userserv/salary/trade/order/page",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看本人快速结算订单列表：字段边界与类型错误",
    "method": "GET",
    "path": "/userserv/salary/trade/order/page",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看本人订单详情：缺失必填参数",
    "method": "GET",
    "path": "/userserv/salary/trade/order/detail",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看本人订单详情：字段边界与类型错误",
    "method": "GET",
    "path": "/userserv/salary/trade/order/detail",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "取消待代理处理订单：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/order/cancel",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "取消待代理处理订单：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/order/cancel",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "取消待代理处理订单：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/order/cancel?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "确认已收到代理转账：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/order/confirm",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "确认已收到代理转账：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/order/confirm",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "确认已收到代理转账：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/order/confirm?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "待确认收款时提交投诉：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/order/appeal",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "待确认收款时提交投诉：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/order/appeal",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "待确认收款时提交投诉：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/order/appeal?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "补充上传本人订单凭证：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/evidence/upload",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "补充上传本人订单凭证：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/evidence/upload",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "补充上传本人订单凭证：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/evidence/upload?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看本人订单凭证：缺失必填参数",
    "method": "GET",
    "path": "/userserv/salary/trade/evidence/list",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看本人订单凭证：字段边界与类型错误",
    "method": "GET",
    "path": "/userserv/salary/trade/evidence/list",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看本人订单流转记录：缺失必填参数",
    "method": "GET",
    "path": "/userserv/salary/trade/logs",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看本人订单流转记录：字段边界与类型错误",
    "method": "GET",
    "path": "/userserv/salary/trade/logs",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看自己的交易公告编辑页信息：缺失必填参数",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/notice",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看自己的交易公告编辑页信息：字段边界与类型错误",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/notice",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "保存自己的交易公告：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/notice/save",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "保存自己的交易公告：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/notice/save",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "保存自己的交易公告：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/notice/save?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "查看可处理或已承接的订单列表：缺失必填参数",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/order/page",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看可处理或已承接的订单列表：字段边界与类型错误",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/order/page",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看代理侧订单详情：缺失必填参数",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/order/detail",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "查看代理侧订单详情：字段边界与类型错误",
    "method": "GET",
    "path": "/userserv/salary/trade/agent/order/detail",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "接受待代理处理订单：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/accept",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "接受待代理处理订单：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/accept",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "接受待代理处理订单：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/accept?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "拒绝待代理处理订单：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/reject",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "拒绝待代理处理订单：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/reject",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "拒绝待代理处理订单：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/reject?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "标记已完成线下转账：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/paid",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "标记已完成线下转账：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/paid",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "标记已完成线下转账：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/paid?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "待确认收款时提交投诉：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/appeal",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "待确认收款时提交投诉：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/appeal",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "待确认收款时提交投诉：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/order/appeal?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  },
  {
    "title": "补充上传付款或投诉凭证：缺失必填参数",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/evidence/upload",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "补充上传付款或投诉凭证：字段边界与类型错误",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/evidence/upload",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "补充上传付款或投诉凭证：重复提交与幂等性",
    "method": "POST",
    "path": "/userserv/salary/trade/agent/evidence/upload?osVersion=16&language=ar&appsflyerId=1787803900487-1623248308013165548&appCode=100156&channel=google&isVpnConnected=0&systemLanguage=zh&model=SM-A546B&packageName=com.soulfree.happiness&appid=soulfree&appVersion=100.1.5.6&ispType=4&version=100.1.5.6&deviceType=0&deviceId=8fcce1f1-5153-3207-9786-0240140a524a&organic=Organic&netType=2&os=android",
    "headers": {
      "t": "1788177850680"
    },
    "payload": "",
    "expected_status": 200
  }
]


def fill_runtime(value):
    if isinstance(value, dict):
        return {k: fill_runtime(v) for k, v in value.items()}
    if isinstance(value, list):
        return [fill_runtime(v) for v in value]
    text = str(value or "")
    runtime = {}
    try:
        runtime = json.loads(os.getenv("AUTOTEST_RUNTIME_PARAMS_JSON", "{}"))
    except Exception:
        runtime = {}
    runtime.setdefault("ticket", os.getenv("AUTOTEST_RUNTIME_TICKET", ""))
    runtime.setdefault("uid", os.getenv("AUTOTEST_RUNTIME_UID", ""))
    for key, raw in runtime.items():
        text = text.replace("{{" + key + "}}", str(raw))
    return text


def run_case(case):
    case = dict(case)
    case["path"] = fill_runtime(case.get("path", ""))
    case["headers"] = fill_runtime(case.get("headers") or {})
    case["payload"] = fill_runtime(case.get("payload"))
    url = case["path"] if case["path"].startswith("http") else BASE_URL.rstrip("/") + "/" + case["path"].lstrip("/")
    body = case.get("payload")
    data = None if body in ("", None) else (body.encode("utf-8") if isinstance(body, str) else json.dumps(body, ensure_ascii=False).encode("utf-8"))
    headers = dict(case.get("headers") or {})
    if data and "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=case["method"])
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.read(200000).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(200000).decode("utf-8", "replace")


def test_api_cases():
    assert BASE_URL, "缺少 AUTOTEST_BASE_URL"
    for case in CASES:
        status, _ = run_case(case)
        assert status == case["expected_status"], f'{case["title"]} expected {case["expected_status"]}, got {status}'
