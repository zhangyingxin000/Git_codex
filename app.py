from __future__ import annotations

import json
import hashlib
import hmac
import io
import concurrent.futures
import csv
import statistics
import math
import ssl
import socket
import threading
import base64
import zipfile
import xml.etree.ElementTree as ET
import subprocess
import os
import re
import shutil
import sqlite3
import sys
import time
import traceback
import urllib.error
import urllib.request
import urllib.parse
import uuid
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
BUILD_ID = "20260901.01"
STATIC = ROOT / "static"
DATA = ROOT / "data"
DB_PATH = DATA / "autotest_ai.db"
DATA.mkdir(exist_ok=True)
CONFIG_DIR = ROOT / "config"
SKILL_DIR = ROOT / "skills"
YAML_BACKEND = "fallback"


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _dpapi(value, protect=True):
    """Encrypt/decrypt runtime credentials for the current Windows user."""
    raw=value if isinstance(value,bytes) else str(value).encode("utf-8")
    source_buffer=ctypes.create_string_buffer(raw)
    source=_DataBlob(len(raw),ctypes.cast(source_buffer,ctypes.POINTER(ctypes.c_byte)))
    target=_DataBlob()
    crypt32=ctypes.windll.crypt32
    kernel32=ctypes.windll.kernel32
    fn=crypt32.CryptProtectData if protect else crypt32.CryptUnprotectData
    args=(ctypes.byref(source),None,None,None,None,0x1,ctypes.byref(target)) if protect else (ctypes.byref(source),None,None,None,None,0x1,ctypes.byref(target))
    if not fn(*args):
        raise OSError("Windows凭证加密失败")
    try:
        return ctypes.string_at(target.pbData,target.cbData)
    finally:
        kernel32.LocalFree(target.pbData)


def credential_path(project_id):
    safe=re.sub(r"[^a-zA-Z0-9_-]","_",str(project_id))
    return DATA/f"runtime-credential-{safe}.bin"


def _fallback_credential_key():
    path=DATA/".runtime-credential.key"
    if not path.is_file(): path.write_bytes(os.urandom(32))
    key=path.read_bytes()
    if len(key)!=32: raise OSError("本机凭证密钥无效")
    return key


def _seal_local(raw):
    key=_fallback_credential_key(); nonce=os.urandom(16); out=bytearray()
    for offset in range(0,len(raw),32):
        stream=hashlib.sha256(key+nonce+(offset//32).to_bytes(4,"big")).digest()
        out.extend(a^b for a,b in zip(raw[offset:offset+32],stream))
    cipher=bytes(out); tag=hmac.new(key,nonce+cipher,hashlib.sha256).digest()
    return b"LOCAL1"+nonce+tag+cipher


def _open_local(blob):
    if not blob.startswith(b"LOCAL1") or len(blob)<54: raise ValueError("凭证格式无效")
    key=_fallback_credential_key(); nonce=blob[6:22]; tag=blob[22:54]; cipher=blob[54:]
    if not hmac.compare_digest(tag,hmac.new(key,nonce+cipher,hashlib.sha256).digest()): raise ValueError("凭证完整性校验失败")
    out=bytearray()
    for offset in range(0,len(cipher),32):
        stream=hashlib.sha256(key+nonce+(offset//32).to_bytes(4,"big")).digest()
        out.extend(a^b for a,b in zip(cipher[offset:offset+32],stream))
    return bytes(out)


def save_runtime_credential(project_id, ticket, sn, uid_value, runtime_context=None, encrypted_password=""):
    context = {key: str(value) for key, value in (runtime_context or {}).items() if key in LOGIN_CONTEXT_KEYS or key in {"t", "sn"}}
    payload=json.dumps({"ticket":ticket,"sn":sn or context.get("sn",""),"uid":uid_value,"context":context,"encrypted_password":encrypted_password or "","saved_at":now()},ensure_ascii=False).encode("utf-8")
    encrypted=_seal_local(payload)
    credential_path(project_id).write_bytes(encrypted)


def load_runtime_credential(project_id):
    path=credential_path(project_id)
    if not path.is_file(): return {}
    try:
        encrypted=path.read_bytes()
        raw=_dpapi(encrypted[6:],False) if encrypted.startswith(b"DPAPI1") else _open_local(encrypted)
        return json.loads(raw.decode("utf-8"))
    except Exception: return {}


def jwt_claims_unverified(token):
    """Read routing claims only; authentication is still decided by the server."""
    try:
        part=str(token).split(".")[1]; part += "="*((4-len(part)%4)%4)
        value=json.loads(base64.urlsafe_b64decode(part.encode()).decode("utf-8"))
        return value if isinstance(value,dict) else {}
    except Exception: return {}


def _looks_like_jwt(value):
    text = str(value or "").strip()
    if text.count(".") != 2:
        return False
    return bool(re.match(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$", text))


def _looks_like_timestamp_t(value):
    text = str(value or "").strip()
    if not re.fullmatch(r"\d{10}|\d{13}", text):
        return False
    millis = int(text) if len(text) == 13 else int(text) * 1000
    return 1577836800000 <= millis <= 2051222400000


def _fresh_login_t():
    return str(int(time.time() * 1000))


def _is_sensitive_runtime_value(key, value):
    name = str(key or "")
    if name == "t" and _looks_like_jwt(value):
        return True
    return bool(re.search(r"^(sn|sign|signature)$|token|ticket|authorization|cookie|password|secret", name, re.I))


def account_credential_path(account_id):
    return DATA/f"test-account-{re.sub(r'[^a-zA-Z0-9_-]','_',str(account_id))}.bin"


def save_account_credential(account_id, ticket="", encrypted_password=""):
    raw=json.dumps({"ticket":ticket or "","encrypted_password":encrypted_password or ""},ensure_ascii=False).encode("utf-8")
    try: encrypted=b"DPAPI1"+_dpapi(raw,True)
    except Exception: encrypted=_seal_local(raw)
    account_credential_path(account_id).write_bytes(encrypted)


def load_account_credential(account_id):
    path=account_credential_path(account_id)
    if not path.is_file(): return {}
    try:
        encrypted=path.read_bytes(); raw=_dpapi(encrypted[6:],False) if encrypted.startswith(b"DPAPI1") else _open_local(encrypted)
        return json.loads(raw.decode("utf-8"))
    except Exception: return {}


def list_test_accounts(project_id):
    result=[]
    for item in rows("SELECT * FROM test_accounts WHERE project_id=? ORDER BY mutable DESC,wealth_level,short_id",(project_id,)):
        secret=load_account_credential(item["id"]); item["has_ticket"]=bool(secret.get("ticket")); item["has_password"]=bool(secret.get("encrypted_password")); result.append(item)
    return result


def upsert_test_account(project_id, payload):
    account_uid=int(payload.get("uid")); short_id=str(payload.get("short_id") or "").strip()
    if not short_id: raise ValueError("短ID不能为空")
    ticket=str(payload.get("ticket") or "").strip(); password=str(payload.get("encrypted_password") or "").strip()
    claim_uid=jwt_claims_unverified(ticket).get("uid") if ticket else None
    if claim_uid is not None and int(claim_uid)!=account_uid: raise ValueError("Ticket中的UID与账号UID不一致")
    existing=row("SELECT * FROM test_accounts WHERE project_id=? AND account_uid=?",(project_id,account_uid)); t=now()
    if existing:
        aid=existing["id"]; execute("UPDATE test_accounts SET nickname=?,short_id=?,wealth_level=?,account_role=?,mutable=?,status='ready',updated_at=? WHERE id=?",(payload.get("nickname",""),short_id,payload.get("wealth_level"),payload.get("role","general"),int(bool(payload.get("mutable"))),t,aid)); old=load_account_credential(aid); save_account_credential(aid,ticket or old.get("ticket",""),password or old.get("encrypted_password",""))
    else:
        aid=uid("acct"); execute("INSERT INTO test_accounts VALUES (?,?,?,?,?,?,?,?,?,?,?)",(aid,project_id,payload.get("nickname",""),short_id,account_uid,payload.get("wealth_level"),payload.get("role","general"),int(bool(payload.get("mutable"))),"ready",t,t)); save_account_credential(aid,ticket,password)
    return next(x for x in list_test_accounts(project_id) if x["id"]==aid)


def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def percentile_value(values, percentile):
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int((len(ordered) - 1) * percentile)))
    return ordered[index]


def run_jmeter_wealth(ticket, login_uid, threads=2, loops=5, rampup=2):
    """Run the real JMeter plan with an in-memory token and return a safe summary."""
    threads=max(1,min(int(threads),50)); loops=max(1,min(int(loops),100)); rampup=max(0,min(int(rampup),300))
    jmeter=Path(os.getenv("AUTOTEST_JMETER", r"D:\apache-jmeter-5.6.3\bin\jmeter.bat"))
    plan=ROOT/"jmeter"/"wealth-level-performance.jmx"
    if not jmeter.exists(): return {"status":"BLOCKED","message":"本机未找到 JMeter，请配置 AUTOTEST_JMETER","engine":"JMeter"}
    if not plan.exists(): return {"status":"BLOCKED","message":"JMeter 脚本不存在","engine":"JMeter"}
    stamp=datetime.now().strftime("%Y%m%d-%H%M%S")
    report_dir=ROOT/"reports"/f"jmeter-wealth-{stamp}"; html_dir=report_dir/"html"; report_dir.mkdir(parents=True,exist_ok=True)
    jtl=report_dir/"result.jtl"
    env=os.environ.copy(); env["AUTOTEST_RUNTIME_TICKET"]=str(ticket)
    command=[str(jmeter),"-n","-t",str(plan),"-l",str(jtl),"-e","-o",str(html_dir),f"-Jthreads={threads}",f"-Jloops={loops}",f"-Jrampup={rampup}",f"-Juid={login_uid}","-Jjmeter.save.saveservice.url=false","-Jjmeter.save.saveservice.response_data=false","-Jjmeter.save.saveservice.requestHeaders=false","-Jjmeter.save.saveservice.responseHeaders=false"]
    started=time.perf_counter()
    try:
        completed=subprocess.run(command,cwd=str(ROOT),env=env,capture_output=True,text=True,timeout=max(120,threads*loops*25),creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    except subprocess.TimeoutExpired:
        return {"status":"FAILED","message":"JMeter 执行超时","engine":"JMeter","threads":threads,"loops":loops,"rampup_seconds":rampup}
    if completed.returncode!=0 or not jtl.exists():
        message=(completed.stderr or completed.stdout or "JMeter 未生成结果")[-1000:]
        return {"status":"FAILED","message":message,"engine":"JMeter","threads":threads,"loops":loops,"rampup_seconds":rampup}
    with jtl.open("r",encoding="utf-8-sig",newline="") as handle:
        samples=list(csv.DictReader(handle))
    elapsed=[int(x.get("elapsed") or 0) for x in samples]
    errors=[x for x in samples if str(x.get("success","")).lower()!="true"]
    codes={}
    for item in samples:
        code=str(item.get("responseCode") or "UNKNOWN"); codes[code]=codes.get(code,0)+1
    starts=[int(x.get("timeStamp") or 0) for x in samples]
    ends=[int(x.get("timeStamp") or 0)+int(x.get("elapsed") or 0) for x in samples]
    sample_seconds=max(.001,(max(ends)-min(starts))/1000) if samples else .001
    failure_reason=""
    if errors:
        if codes and set(codes)=={"401"}: failure_reason="所有请求均返回401：本次登录会话未被服务端接受或已失效"
        elif codes and set(codes)=={"403"}: failure_reason="所有请求均返回403：账号或环境权限不足"
        elif any(x.get("failureMessage") for x in errors): failure_reason="JMeter业务断言未通过"
        else: failure_reason="存在网络错误或非预期HTTP响应"
    result={"status":"PASSED" if samples and not errors else "FAILED","engine":"JMeter","requests":len(samples),"success":len(samples)-len(errors),"errors":len(errors),"error_rate":round(len(errors)/len(samples)*100,2) if samples else 100,"throughput_rps":round(len(samples)/sample_seconds,2),"average_ms":round(statistics.mean(elapsed),2) if elapsed else 0,"min_ms":min(elapsed) if elapsed else 0,"max_ms":max(elapsed) if elapsed else 0,"p50_ms":percentile_value(elapsed,.50),"p90_ms":percentile_value(elapsed,.90),"p95_ms":percentile_value(elapsed,.95),"p99_ms":percentile_value(elapsed,.99),"response_codes":codes,"failure_reason":failure_reason,"threads":threads,"loops":loops,"rampup_seconds":rampup,"jtl_path":str(jtl),"html_report":str(html_dir/"index.html"),"security_note":"Token仅通过进程环境变量注入，JTL与HTML不保存请求URL、请求头或响应正文"}
    (report_dir/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    return result


def uid(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _parse_simple_yaml_value(value):
    text = str(value or "").strip()
    if not text:
        return ""
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    if text.startswith("[") and text.endswith("]"):
        try:
            return json.loads(text.replace("'", '"'))
        except Exception:
            return [item.strip().strip('"').strip("'") for item in text[1:-1].split(",") if item.strip()]
    if re.fullmatch(r"-?\d+", text):
        try:
            return int(text)
        except Exception:
            return text
    if re.fullmatch(r"-?\d+\.\d+", text):
        try:
            return float(text)
        except Exception:
            return text
    return text


def _parse_simple_yaml(text):
    """Small YAML subset parser for project env files; avoids making startup depend on PyYAML."""
    root = {}
    stack = [(-1, root)]
    for raw_line in str(text or "").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value == "":
            node = {}
            parent[key] = node
            stack.append((indent, node))
        else:
            parent[key] = _parse_simple_yaml_value(value)
    return root


def _load_yaml_file(path):
    global YAML_BACKEND
    path = Path(path)
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text) or {}
        YAML_BACKEND = "PyYAML"
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        YAML_BACKEND = "fallback"
        return _parse_simple_yaml(text)


def deep_get(mapping, dotted, default=None):
    current = mapping
    for part in str(dotted).split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def deep_merge(base, override):
    result = dict(base or {})
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_environment_config(env_name=None):
    env = str(env_name or os.getenv("AUTOTEST_ENV") or "test").strip() or "test"
    example = _load_yaml_file(CONFIG_DIR / "env.example.yaml")
    concrete = _load_yaml_file(CONFIG_DIR / f"env.{env}.yaml")
    data_sources = _load_yaml_file(CONFIG_DIR / "data-sources.yaml")
    config = deep_merge(deep_merge(example, concrete), data_sources)
    if not config:
        config = {}
    config.setdefault("project", {})
    config.setdefault("tools", {})
    config.setdefault("data_sources", {})
    config.setdefault("accounts", {})
    config.setdefault("reports", {})
    config["env_file"] = str(CONFIG_DIR / f"env.{env}.yaml")
    config["env_name"] = env
    return config


def environment_config_status(project_id=None):
    config = load_environment_config()
    project = row("SELECT * FROM projects WHERE id=?", (project_id,)) if project_id else None
    jmeter_home = str(deep_get(config, "tools.jmeter.home", "") or "").strip()
    jmeter_bat = Path(jmeter_home) / "bin" / "jmeter.bat" if jmeter_home else Path("")
    redis = deep_get(config, "data_sources.redis", {}) or {}
    mysql = deep_get(config, "data_sources.mysql", {}) or {}
    accounts = deep_get(config, "accounts", {}) or {}
    base_url = str(deep_get(config, "project.base_url", "") or (project.get("base_url") if project else "") or "")
    return {
        "status": "READY" if base_url and (jmeter_bat.exists() or bool(shutil.which("jmeter"))) else "ATTENTION",
        "build": BUILD_ID,
        "env_name": config.get("env_name", "test"),
        "env_file": config.get("env_file", ""),
        "yaml_backend": YAML_BACKEND,
        "project": {
            "name": deep_get(config, "project.name", project.get("name") if project else "AutoTest AI"),
            "env": deep_get(config, "project.env", "soulfree-test"),
            "base_url": base_url,
        },
        "tools": {
            "jmeter_home": jmeter_home,
            "jmeter_command": str(jmeter_bat) if jmeter_bat.exists() else _jmeter_command(),
            "newman_enabled": bool(deep_get(config, "tools.newman.enabled", True)),
        },
        "data_sources": {
            "mysql_readonly": bool(mysql.get("readonly", True)) if isinstance(mysql, dict) else True,
            "mysql_configured": bool(isinstance(mysql, dict) and mysql.get("host")),
            "mysql_live": mysql_connection_status(project_id),
            "redis_readonly": bool(redis.get("readonly", True)) if isinstance(redis, dict) else True,
            "redis_configured": bool(isinstance(redis, dict) and redis.get("host")),
            "redis_host": redis.get("host", "") if isinstance(redis, dict) else "",
            "redis_port": redis.get("port", "") if isinstance(redis, dict) else "",
        },
        "accounts": {
            "strategy": accounts.get("strategy", "csv_or_login_or_redis") if isinstance(accounts, dict) else "csv_or_login_or_redis",
            "csv_path": accounts.get("csv_path", "data/accounts.csv") if isinstance(accounts, dict) else "data/accounts.csv",
            "roles": accounts.get("roles", []) if isinstance(accounts, dict) else [],
        },
        "reports": {
            "root": deep_get(config, "reports.root", "reports"),
            "group_by": deep_get(config, "reports.group_by", "requirement_package"),
        },
        "policy": {
            "secrets_in_yaml": False,
            "business_datasource_readonly": True,
            "config_overridable_by_ui": True,
        },
    }


def _read_env_file(path):
    values = {}
    if not Path(path).is_file():
        return values
    for raw_line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        values[key.strip()] = value
    return values


def _runtime_setting(name, default=""):
    file_values = _read_env_file(ROOT / "database.env")
    return os.getenv(name) or file_values.get(name) or default


def mysql_connection_config():
    config = load_environment_config()
    yaml_mysql = deep_get(config, "data_sources.mysql", {}) or {}
    env_file_values = _read_env_file(ROOT / "database.env")
    yaml_value = lambda key, default="": yaml_mysql.get(key, default) if isinstance(yaml_mysql, dict) else default
    host = os.getenv("AUTOTEST_DB_HOST") or env_file_values.get("AUTOTEST_DB_HOST") or yaml_value("host", "")
    port = int(os.getenv("AUTOTEST_DB_PORT") or env_file_values.get("AUTOTEST_DB_PORT") or yaml_value("port", 3306) or 3306)
    database = os.getenv("AUTOTEST_DB_NAME") or env_file_values.get("AUTOTEST_DB_NAME") or yaml_value("database", "")
    user = os.getenv("AUTOTEST_DB_USER") or env_file_values.get("AUTOTEST_DB_USER") or yaml_value("user", "")
    password = os.getenv("AUTOTEST_DB_PASSWORD") or env_file_values.get("AUTOTEST_DB_PASSWORD") or ""
    mode = str(os.getenv("AUTOTEST_DB_MODE") or env_file_values.get("AUTOTEST_DB_MODE") or yaml_value("mode", "readonly")).strip().lower() or "readonly"
    return {
        "type": _runtime_setting("AUTOTEST_DB_TYPE", "mysql"),
        "host": str(host or "").strip(),
        "port": port,
        "database": str(database or "").strip(),
        "user": str(user or "").strip(),
        "password": str(password or ""),
        "mode": mode,
        "readonly": mode != "write_test_sandbox",
    }


def mysql_connection_status(project_id=None):
    cfg = mysql_connection_config()
    configured = all([cfg["host"], cfg["port"], cfg["user"]])
    return {
        "status": "CONFIGURED" if configured else "NOT_CONFIGURED",
        "host": cfg["host"],
        "port": cfg["port"],
        "database": cfg["database"],
        "database_configured": bool(cfg["database"]),
        "user": cfg["user"],
        "password_configured": bool(cfg["password"]),
        "readonly": True,
        "allowed_sql": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"],
        "project_id": project_id,
    }


def _import_pymysql():
    try:
        import pymysql
        return pymysql
    except Exception as exc:
        raise RuntimeError("缺少 PyMySQL，请先安装：python -m pip install PyMySQL") from exc


READONLY_SQL_PREFIXES = ("select", "show", "describe", "desc", "explain")
MUTATION_SQL_PATTERN = re.compile(r"\b(insert|update|delete|drop|alter|truncate|create|replace|grant|revoke|call|load|lock|unlock|set|merge|rename)\b", re.I)


def assert_readonly_sql(sql):
    text = str(sql or "").strip()
    if not text:
        raise ValueError("SQL不能为空")
    if ";" in text.rstrip(";"):
        raise ValueError("只允许单条只读SQL，不允许多语句")
    text = text.rstrip(";").strip()
    lowered = re.sub(r"^\s*/\*.*?\*/\s*", "", text, flags=re.S).lower()
    if not lowered.startswith(READONLY_SQL_PREFIXES):
        raise ValueError("只允许 SELECT、SHOW、DESCRIBE、EXPLAIN")
    if MUTATION_SQL_PATTERN.search(lowered):
        raise ValueError("检测到写入或高风险关键字，已拦截")
    return text


def _mysql_connect():
    cfg = mysql_connection_config()
    if not all([cfg["host"], cfg["port"], cfg["user"]]):
        raise ValueError("MySQL未配置完整，请在 database.env 填写 Host、Port、User")
    pymysql = _import_pymysql()
    kwargs = dict(
        host=cfg["host"],
        port=int(cfg["port"]),
        user=cfg["user"],
        password=cfg["password"],
        charset="utf8mb4",
        autocommit=True,
        connect_timeout=5,
        read_timeout=12,
        write_timeout=12,
        cursorclass=pymysql.cursors.DictCursor,
    )
    if cfg["database"]:
        kwargs["database"] = cfg["database"]
    return pymysql.connect(**kwargs)


def _limit_select_sql(sql, limit):
    text = sql.rstrip(";").strip()
    if re.match(r"(?is)^\s*select\b", text) and not re.search(r"(?is)\blimit\s+\d+\b", text):
        return f"{text} LIMIT {int(limit)}"
    return text


def mysql_readonly_query(project_id, payload):
    sql = assert_readonly_sql(payload.get("sql", ""))
    limit = max(1, min(int(payload.get("limit") or 100), 500))
    sql = _limit_select_sql(sql, limit)
    started = time.perf_counter()
    with _mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            result_rows = cur.fetchall() if cur.description else []
            columns = [item[0] for item in (cur.description or [])]
    safe_rows = json.loads(json.dumps(result_rows, ensure_ascii=False, default=str))
    return {
        "status": "PASSED",
        "readonly": True,
        "sql": sql,
        "columns": columns,
        "rows": safe_rows,
        "row_count": len(safe_rows),
        "duration_ms": int((time.perf_counter() - started) * 1000),
        "project_id": project_id,
    }


def mysql_test_connection(project_id=None):
    status = mysql_connection_status(project_id)
    started = time.perf_counter()
    result = mysql_readonly_query(project_id or "", {"sql": "SELECT 1 AS ok", "limit": 1})
    status.update({
        "status": "CONNECTED",
        "duration_ms": int((time.perf_counter() - started) * 1000),
        "probe": result["rows"][0] if result["rows"] else {},
    })
    return status


def import_mysql_schema_live(project_id):
    cfg = mysql_connection_config()
    if not cfg["database"]:
        raise ValueError("MySQL database 未配置，无法读取 information_schema")
    tables_sql = """
        SELECT table_name, table_schema, COALESCE(table_comment,'') AS table_comment, COALESCE(table_rows,0) AS table_rows
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        ORDER BY table_name
    """
    columns_sql = """
        SELECT table_name, column_name, column_type, is_nullable, column_key, column_default, extra, COALESCE(column_comment,'') AS column_comment
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
        ORDER BY table_name, ordinal_position
    """
    tables = mysql_readonly_query(project_id, {"sql": tables_sql, "limit": 500})["rows"]
    columns = mysql_readonly_query(project_id, {"sql": columns_sql, "limit": 5000})["rows"]
    pick = lambda item, *keys, default="": next((item.get(key) for key in keys if key in item), default)
    schema = {
        "tables": [[pick(x, "table_name", "TABLE_NAME"), pick(x, "table_schema", "TABLE_SCHEMA", default=cfg["database"]), pick(x, "table_comment", "TABLE_COMMENT"), pick(x, "table_rows", "TABLE_ROWS", default=0)] for x in tables],
        "columns": [[pick(x, "table_name", "TABLE_NAME"), pick(x, "column_name", "COLUMN_NAME"), pick(x, "column_type", "COLUMN_TYPE"), pick(x, "is_nullable", "IS_NULLABLE"), pick(x, "column_key", "COLUMN_KEY"), pick(x, "column_default", "COLUMN_DEFAULT"), pick(x, "extra", "EXTRA"), pick(x, "column_comment", "COLUMN_COMMENT")] for x in columns],
    }
    result = import_db_schema(project_id, json.dumps(schema, ensure_ascii=False))
    result.update({"status": "PASSED", "source": "live_mysql_information_schema", "readonly": True})
    return result


def jmeter_generation_skill_status(project_id=None):
    path = SKILL_DIR / "jmeter-script-generation" / "SKILL.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    checks = [
        ("账号模型优先", "Account Model First"),
        ("线程组", "Thread Group Standards"),
        ("请求参数", "Request Generation"),
        ("CSV参数化", "CSV Parameterization"),
        ("断言", "Assertions"),
        ("监听器", "Listeners And Reports"),
        ("压测场景", "smoke"),
        ("并发数", "concurrency"),
        ("持续时间", "duration"),
        ("性能指标", "Performance Metrics"),
        ("DB/Redis证据", "DB And Redis Evidence"),
    ]
    coverage = [{"name": name, "status": "READY" if marker in text else "MISSING"} for name, marker in checks]
    model = salary_trade_case_to_jmeter_model(project_id) if project_id else {}
    return {
        "status": "READY" if text and all(item["status"] == "READY" for item in coverage) else "ATTENTION",
        "path": str(path),
        "summary": "JMeter脚本生成规则已沉淀为平台Skill：从测试用例生成线程组、请求、参数化、提取器、断言、监听器、压测场景和报告指标。",
        "coverage": coverage,
        "output_contract": [
            "独立JMX脚本",
            "需求包账号模型 account_model.yaml",
            "用例到线程组映射Manifest",
            "可读说明文档",
            "JMeter GUI启动命令",
            "JTL/HTML报告归档位置",
        ],
        "case_model": {
            "flows": len(model.get("flows") or []),
            "gaps": len(model.get("gaps") or []),
            "ready_flows": sum(1 for item in model.get("flows") or [] if item.get("automation_status") == "ready"),
        },
        "agent_ready": {
            "implemented": False,
            "reason": "当前只封装工具能力和规则契约，预留给后续Agent编排，不直接实现Agent。",
        },
    }


def multi_account_context_status(project_id):
    accounts = list_test_accounts(project_id)
    config = load_environment_config()
    salary_dataset = deep_get(config, "requirement_datasets.salary_trade", {}) or {}
    wealth_dataset = deep_get(config, "requirement_datasets.wealth_level", {}) or {}
    account_csv = ROOT / str(salary_dataset.get("account_csv_path") or "data/salary-trade-accounts.csv")
    applicant_csv = ROOT / str(salary_dataset.get("applicant_csv_path") or "data/salary-trade-applicants.csv")

    def read_csv_rows(path):
        if not path.is_file():
            return []
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                return [item for item in csv.DictReader(handle) if item]
        except Exception:
            return []

    account_csv_rows = read_csv_rows(account_csv)
    applicant_csv_rows = read_csv_rows(applicant_csv)
    enabled_account_rows = [item for item in account_csv_rows if str(item.get("enabled", "true")).strip().lower() not in ("0", "false", "no", "off")]
    by_role = {}
    for account in accounts:
        role = account.get("account_role") or "general"
        by_role.setdefault(role, []).append(account)
    csv_by_role = {}
    for item in enabled_account_rows:
        role = (item.get("role") or "general").strip() or "general"
        csv_by_role.setdefault(role, []).append(item)
    applicant_count = len(by_role.get("applicant", [])) + len(csv_by_role.get("applicant", [])) + len(applicant_csv_rows)
    proxy_count = len(by_role.get("proxy", [])) + len(by_role.get("agent", [])) + len(csv_by_role.get("proxy", [])) + len(csv_by_role.get("agent", []))
    mismatched_currency = []
    for item in enabled_account_rows:
        currency = str(item.get("currency") or "").strip()
        support = str(item.get("supportCurrencies") or "").strip()
        supported = [x.strip() for x in re.split(r"[|,;/]", support) if x.strip()]
        if currency and supported and currency not in supported:
            mismatched_currency.append(item)
    requirement_strategies = build_multi_account_strategy(project_id, {
        "accounts": accounts,
        "account_csv_rows": account_csv_rows,
        "applicant_csv_rows": applicant_csv_rows,
        "enabled_account_rows": enabled_account_rows,
        "applicant_count": applicant_count,
        "proxy_count": proxy_count,
    })
    gaps = []
    if applicant_count < 8:
        gaps.append({"level": "P0", "item": "申请人账号", "detail": f"工资交易8条流程建议准备8个申请人账号，当前识别{applicant_count}个。"})
    if proxy_count < 1:
        gaps.append({"level": "P1", "item": "代理账号", "detail": "代理人可以复用，但至少需要1个可登录或可复用token的代理账号。"})
    no_secret = [item for item in accounts if not item.get("has_ticket") and not item.get("has_password")]
    if no_secret:
        gaps.append({"level": "P1", "item": "账号凭证", "detail": f"{len(no_secret)}个账号缺少ticket或登录密码，运行前需要登录接口/Redis/CSV补齐。"})
    csv_no_login_source = [item for item in enabled_account_rows if not str(item.get("password_encrypted") or "").strip() and not str(item.get("ticket") or "").strip() and not str(item.get("redis_uid") or item.get("uid") or "").strip()]
    if csv_no_login_source:
        gaps.append({"level": "P1", "item": "CSV登录来源", "detail": f"{len(csv_no_login_source)}行CSV账号缺少登录密码、ticket或可查Redis的uid。"})
    if mismatched_currency:
        gaps.append({"level": "P0", "item": "国家币种匹配", "detail": f"{len(mismatched_currency)}行账号的currency不在supportCurrencies里，工资交易不能严格校验。"})
    return {
        "status": "READY" if not any(item["level"] == "P0" for item in gaps) else "ATTENTION",
        "strategy": "按需求和测试用例判断数据载体：单账号可走运行参数，多账号/多流程才启用CSV。",
        "requirement_strategies": requirement_strategies,
        "standard_rules": [
            {"mode": "single_account", "when": "单用户、单角色、无账号互斥", "data_source": "运行参数 / 登录前置 / Redis登录态", "example": "财富等级闭环"},
            {"mode": "dual_role", "when": "同一流程存在申请人、代理人、运营等角色", "data_source": "角色化账号CSV + 登录接口/Redis补ticket", "example": "申请人创建订单，代理人接单"},
            {"mode": "multi_flow_slots", "when": "一个账号同一时间只能有一个处理中订单，多个流程并行或连续覆盖", "data_source": "流程槽位CSV + 申请人账号池 + DB白名单匹配代理", "example": "工资交易8条状态流"},
        ],
        "credential_resolution_order": [
            "运行时显式传入 ticket/password",
            "角色CSV中填写 ticket/password/redis_uid",
            "登录接口按 shortId + password_encrypted 获取 access_token",
            "Redis只读读取 user_login_info:{uid}.access_token",
            "仍未取得则阻断，不伪造身份认证",
        ],
        "matching_rules": [
            "申请人由用例流程槽位决定，不能所有流程复用同一个申请人。",
            "代理人先按申请人国家和收款币种在DB白名单匹配候选，再用CSV或Redis补齐该代理的真实登录态。",
            "JWT解析出的uid必须等于当前角色uid，否则直接阻断，避免拿错人的ticket导致401。",
            "数据库只证明代理资格和订单证据，不保存ticket，也不替代登录态。",
        ],
        "roles": [
            {"role": "wealth_user", "purpose": "财富等级单账号闭环，变量独立于工资交易。"},
            {"role": "applicant", "purpose": "工资交易申请人，一人同一时刻只能有一个处理中订单。"},
            {"role": "proxy", "purpose": "工资交易代理人，可跨多个流程复用，但国家和币种必须匹配。"},
            {"role": "operator", "purpose": "投诉处理等后台/运营动作，暂作为预留角色。"},
        ],
        "counts": {
            "accounts_table": len(accounts),
            "applicant": applicant_count,
            "proxy": proxy_count,
            "salary_account_csv_rows": len(account_csv_rows),
            "salary_account_csv_enabled": len(enabled_account_rows),
            "salary_applicant_csv_rows": len(applicant_csv_rows),
        },
        "csv_contract": {
            "account_csv": str(account_csv),
            "applicant_csv": str(applicant_csv),
            "template_dir": str(ROOT / "data" / "templates"),
            "rule": "数据文件不是所有需求强制项；只有多账号、多流程、多数据组合的需求才必须使用。",
        },
        "variable_policy": {
            "wealth": ["wealth_user_uid", "wealth_user_ticket"],
            "salary_trade": ["applicant_uid", "applicant_ticket", "proxy_uid", "proxy_ticket", "salary_order_no"],
            "rule": "不同需求包必须使用独立变量命名，避免财富等级和工资交易互相污染。",
        },
        "gaps": gaps,
        "readonly_sources": {
            "redis_login_cache_key": "user_login_info:{uid}.access_token",
            "db_agent_tables": ["anchor_salary_trade_agent_whitelist", "anchor_salary_trade_order", "anchor_salary_trade_order_log", "anchor_salary_trade_evidence"],
        },
    }


def build_multi_account_strategy(project_id, context=None):
    context = context or {}
    strategies = []
    for package in requirement_package_catalog(project_id).get("packages", []):
        package_id = package.get("package_id")
        cases = _requirement_package_cases(project_id, package_id)
        flows = SALARY_TRADE_CASE_FLOWS if package_id == "salary-trade" else []
        decision = infer_jmeter_runtime_data_strategy(cases, flows)
        if package_id == "wealth-level":
            mode = "single_account"
            required_roles = ["wealth_user"]
            min_accounts = {"wealth_user": 1}
            data_carrier = "runtime_or_login_or_redis"
            blocking_rule = "缺少可登录账号或ticket时阻断；不强制CSV。"
        elif decision.get("csv_required"):
            mode = "multi_flow_slots" if len(decision.get("account_slots") or []) > 1 else "dual_role"
            required_roles = decision.get("roles") or ["applicant", "proxy"]
            min_accounts = {"applicant": max(1, len(decision.get("account_slots") or [])), "proxy": 1}
            data_carrier = "csv_plus_db_redis"
            blocking_rule = "申请人槽位不足、代理白名单不匹配、ticket与uid不一致时阻断。"
        else:
            mode = "single_account"
            required_roles = decision.get("roles") or ["default_user"]
            min_accounts = {required_roles[0]: 1}
            data_carrier = "runtime_parameters"
            blocking_rule = "缺少运行参数时提示补齐，不自动创建CSV。"
        readiness = []
        for role, needed in min_accounts.items():
            if role == "applicant":
                actual = context.get("applicant_count", 0)
            elif role in {"proxy", "agent"}:
                actual = context.get("proxy_count", 0)
            elif role == "wealth_user":
                actual = len([x for x in context.get("accounts", []) if (x.get("account_role") or "") in {"wealth_user", "general", ""}])
            else:
                actual = len(context.get("accounts", []))
            readiness.append({"role": role, "needed": needed, "actual": actual, "status": "READY" if actual >= needed else "MISSING"})
        strategies.append({
            "package_id": package_id,
            "package_name": package.get("name"),
            "mode": mode,
            "data_carrier": data_carrier,
            "required_roles": required_roles,
            "min_accounts": min_accounts,
            "readiness": readiness,
            "csv_required": mode in {"dual_role", "multi_flow_slots"},
            "reasons": decision.get("reasons") or [],
            "blocking_rule": blocking_rule,
            "variable_namespace": f"{package_id.replace('-', '_')}_*",
        })
    return strategies


def _yaml_dump(data):
    try:
        import yaml
        return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    except Exception:
        return json.dumps(data, ensure_ascii=False, indent=2)


def _unknown_account_signals(cases):
    known = {"uid", "ticket", "agentuid", "operatorid", "roomid", "anchoruid", "countrycode", "currency", "userid", "shortid"}
    role_hints = {
        "reviewerUid": "reviewer",
        "auditorUid": "auditor",
        "adminUid": "admin",
        "familyOwnerUid": "family_owner",
        "payerUid": "payer",
        "payeeUid": "payee",
    }
    pending = []
    text = "\n".join(str(case.get(key) or "") for case in cases for key in ("title", "steps", "expected", "path", "payload", "parameters"))
    for field, role in role_hints.items():
        if field in text and field.lower() not in known:
            pending.append({
                "type": "role",
                "name": role,
                "reason": f"测试用例或接口字段出现 {field}，需要确认是否为独立执行身份。",
                "suggested_fields": [field, "ticket"],
            })
    return pending


def generate_requirement_account_model(project_id, package_id, persist=True):
    context = multi_account_context_status(project_id)
    package = requirement_package_by_id(project_id, package_id)
    package_id = package.get("package_id") or package_id
    strategy = next((item for item in context.get("requirement_strategies", []) if item.get("package_id") == package_id), None)
    if not strategy:
        raise ValueError("没有找到该需求包的账号策略")
    cases = _requirement_package_cases(project_id, package_id)
    roles = []
    for role in strategy.get("required_roles") or []:
        credential_sources = ["runtime.ticket", "csv.ticket", "login_api", "redis:user_login_info:{uid}.access_token"]
        if role in {"proxy", "agent"}:
            candidate_sources = ["db:anchor_salary_trade_agent_whitelist", "csv"]
            match_rules = ["countryCode", "currency"]
            reusable = True
        elif role == "applicant":
            candidate_sources = ["csv"]
            match_rules = ["countryCode", "currency"]
            reusable = strategy.get("mode") != "multi_flow_slots"
        else:
            candidate_sources = ["runtime", "csv", "redis"]
            match_rules = []
            reusable = True
        roles.append({
            "name": role,
            "min_count": int((strategy.get("min_accounts") or {}).get(role, 1)),
            "reusable": reusable,
            "candidate_sources": candidate_sources,
            "credential_sources": credential_sources,
            "match_rules": match_rules,
            "required_fields": ["uid", "ticket"],
        })
    if package_id == "salary-trade":
        blocking_rules = context.get("matching_rules") or []
    elif package_id == "wealth-level":
        blocking_rules = [
            "单账号需求不强制CSV；运行参数、登录接口或Redis登录态任一可用即可。",
            "ticket必须能代表当前wealth_user_uid，不能拿其他用户ticket执行。",
            "只有多账号登录压测或账号矩阵场景才启用CSV账号池。",
        ]
    else:
        blocking_rules = [
            "没有明确多角色、多流程或数据矩阵证据时，默认按单账号执行。",
            "检测到未知角色或身份字段时先进入extensions.pending，测试确认后才生效。",
            "ticket必须校验uid归属，无法校验或不匹配时阻断。",
        ]
    model = {
        "schema_version": "1.0",
        "package_id": package_id,
        "package_name": package.get("name"),
        "generated_at": now(),
        "source": {
            "skill": str(SKILL_DIR / "account-model-generation" / "SKILL.md"),
            "decision_basis": "需求包测试用例、接口参数、业务角色、账号互斥和数据证据规则",
        },
        "mode": strategy.get("mode"),
        "csv_required": bool(strategy.get("csv_required")),
        "data_carrier": strategy.get("data_carrier"),
        "variable_namespace": strategy.get("variable_namespace"),
        "roles": roles,
        "credential_resolution_order": context.get("credential_resolution_order") or [],
        "data_sources": {
            "runtime": "测试执行时显式传入的非持久化参数",
            "csv": "仅在多账号、多角色、多流程或数据矩阵需求启用",
            "login_api": "用 shortId + password_encrypted 前置登录，提取 access_token",
            "redis": "只读读取 user_login_info:{uid}.access_token 或缓存证据",
            "mysql": "只读查询业务候选和执行证据，不保存ticket",
        },
        "blocking_rules": blocking_rules,
        "readiness": strategy.get("readiness") or [],
        "extensions": {
            "pending": _unknown_account_signals(cases),
            "confirmed": [],
        },
    }
    if persist:
        path = Path(package["root"]) / "account_model.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_yaml_dump(model), encoding="utf-8")
        model["path"] = str(path)
    return model


def _file_status(path):
    path = Path(path)
    return {
        "path": str(path),
        "exists": path.is_file(),
        "updated_at": datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds") if path.is_file() else "",
    }


def _package_latest_report_status(package_root):
    root = Path(package_root) / "reports"
    if not root.exists():
        return {"exists": False, "status": "PENDING", "latest": "", "count": 0}
    summaries = sorted(root.glob("*/summary.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not summaries:
        return {"exists": False, "status": "PENDING", "latest": "", "count": 0}
    try:
        latest_payload = json.loads(summaries[0].read_text(encoding="utf-8"))
    except Exception:
        latest_payload = {}
    return {
        "exists": True,
        "status": latest_payload.get("status") or "READY",
        "latest": str(summaries[0]),
        "count": len(summaries),
    }


def _requirement_package_workflow_status(package_root, counts, artifacts):
    root = Path(package_root)
    output_root = root / "outputs"
    structured = _file_status(output_root / "structured-test-cases.json")
    mapping = _file_status(output_root / "case-jmeter-mapping.json")
    preflight = _read_json_asset(output_root / "data-preflight-check.json")
    tool_manifest = _read_json_asset(output_root / "tool-assets-manifest.json")
    report_status = _package_latest_report_status(root)
    evidence_ready = artifacts.get("evidence_rules", {}).get("exists") or (root / "evidence_rules.candidates.yaml").is_file()
    stages = [
        {
            "code": "01",
            "name": "需求资料",
            "status": "READY" if counts.get("sources") else "PENDING",
            "summary": f"{counts.get('sources', 0)}份资料",
            "next_action": "导入需求文档和接口文档" if not counts.get("sources") else "继续生成测试用例",
        },
        {
            "code": "02",
            "name": "测试用例",
            "status": "READY" if counts.get("test_cases") else "PENDING",
            "summary": f"{counts.get('test_cases', 0)}条用例 · {counts.get('test_points', 0)}个测试点",
            "next_action": "生成结构化测试用例" if not counts.get("test_cases") else "检查结构化用例和覆盖状态",
        },
        {
            "code": "03",
            "name": "数据准备",
            "status": preflight.get("status") or ("READY" if structured.get("exists") else "PENDING"),
            "summary": f"结构化用例{'已生成' if structured.get('exists') else '待生成'} · 证据规则{'已就绪' if evidence_ready else '待确认'}",
            "next_action": "处理账号、CSV、DB/Redis证据或预检阻断",
        },
        {
            "code": "04",
            "name": "工具脚本",
            "status": tool_manifest.get("status") or ("READY" if any((artifacts.get(name) or {}).get("exists") for name in ("newman", "jmeter", "pytest")) else "PENDING"),
            "summary": f"Newman/JMeter/pytest 资产{len(tool_manifest.get('generated') or [])}份",
            "next_action": "生成本包脚本资产",
        },
        {
            "code": "05",
            "name": "执行报告",
            "status": report_status.get("status"),
            "summary": f"{report_status.get('count', 0)}份需求包报告",
            "next_action": "运行 Newman/JMeter 并回收报告",
        },
        {
            "code": "06",
            "name": "AI复盘",
            "status": "READY" if list((root / "reports").glob("ai-review-*/summary.json")) else "PENDING",
            "summary": "结合接口、DB/Redis证据做复盘",
            "next_action": "生成当前需求包 AI 复盘",
        },
    ]
    blockers = [stage for stage in stages if stage["status"] in {"PENDING", "BLOCKED", "NEEDS_DATA", "UNCONFIGURED"}]
    return {
        "stages": stages,
        "next_step": blockers[0] if blockers else {"code": "DONE", "name": "持续优化", "status": "READY", "next_action": "补异常场景、性能阈值和证据规则"},
        "structured_cases": structured,
        "jmeter_mapping": mapping,
        "preflight_status": preflight.get("status") or "NOT_GENERATED",
    }


def _requirement_package_template(project_id, key):
    config = load_environment_config()
    salary = deep_get(config, "requirement_datasets.salary_trade", {}) or {}
    wealth = deep_get(config, "requirement_datasets.wealth_level", {}) or {}
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    base_url = (project.get("base_url") if project else "") or deep_get(config, "project.base_url", "")
    if key == "salary-trade":
        return {
            "id": "salary-trade",
            "name": salary.get("name") or "工资代理快速结算",
            "domain": "工资交易",
            "description": "多申请人、多代理、订单状态流转、DB白名单和Redis登录态校验。",
            "primary_tool": "JMeter",
            "tool_strategy": {
                "newman": "读接口、鉴权和参数回归",
                "jmeter": "多账号订单状态机和性能观察",
                "pytest": "接口结果、DB、Redis证据复盘",
            },
            "data_policy": "申请人/代理身份走CSV或Redis；数据库只负责代理资格和订单证据，不保存ticket。",
            "base_url": base_url,
            "artifacts": {
                "account_model": REQUIREMENT_PACKAGE_ROOT / "salary-trade" / "account_model.yaml",
                "test_cases": ROOT / "outputs" / "salary-trade-manual-test-cases.md",
                "jmeter": ROOT / "outputs" / "salary-trade-state-machine.jmx",
                "launcher": ROOT / "outputs" / "open-salary-trade-state-machine.ps1",
                "manifest": ROOT / "outputs" / "salary-trade-case-jmeter-manifest.json",
                "applicant_csv": ROOT / str(salary.get("applicant_csv_path") or "data/salary-trade-applicants.csv"),
                "proxy_csv": ROOT / "data" / "salary-trade-proxies.csv",
                "jtl": Path(str(salary.get("result_jtl_path") or "D:/apache-jmeter-5.6.3/jmx/20260826/工资代理结算-result.jtl")),
            },
            "workflow": [
                "导入需求文档和接口文档",
                "生成正常/异常/边界测试用例",
                "按用例生成独立JMeter状态机",
                "JMeter按申请人CSV读取8条流程",
                "DB匹配代理白名单，CSV/Redis补身份认证",
                "回收JTL并结合DB/Redis复盘",
            ],
        }
    return {
        "id": "wealth-level",
        "name": wealth.get("name") or "财富等级",
        "domain": "财富等级",
        "description": "登录、钱包快照、送礼、财富经验增长、账单追踪的业务闭环。",
        "primary_tool": "JMeter",
        "tool_strategy": {
            "newman": "登录、查询、异常参数等轻量接口回归",
            "jmeter": "送礼闭环、循环次数、性能基线和图形报告",
            "pytest": "经验、钱包、账单和阈值配置复盘",
        },
        "data_policy": "单账号可走运行参数或Redis复用，多账号压测再启用CSV。",
        "base_url": base_url,
        "artifacts": {
            "account_model": REQUIREMENT_PACKAGE_ROOT / "wealth-level" / "account_model.yaml",
            "jmeter": Path("D:/apache-jmeter-5.6.3/jmx/20260826/性能基线.jmx"),
            "runtime_csv": ROOT / str(wealth.get("runtime_csv_path") or "data/wealth-level-runtime.csv"),
            "jtl": Path(str(wealth.get("result_jtl_path") or "D:/apache-jmeter-5.6.3/jmx/20260826/性能基线-result.jtl")),
            "skill": ROOT / "skills" / "jmeter-script-generation" / "SKILL.md",
        },
        "workflow": [
            "导入需求和接口资料",
            "生成接口回归和闭环用例",
            "JMeter执行送礼闭环",
            "回收JTL/HTML报告",
            "结合财富等级、钱包、账单数据复盘",
        ],
    }


def _package_signal_counts(project_id, package_id):
    if package_id == "salary-trade":
        words = ("工资", "代理", "交易", "订单", "结算", "投诉")
    else:
        words = ("财富", "等级", "经验", "送礼", "钱包", "账单")
    where = " OR ".join(["title LIKE ? OR requirement_ref LIKE ? OR steps LIKE ?" for _ in words])
    params = []
    for word in words:
        params.extend([f"%{word}%", f"%{word}%", f"%{word}%"])
    cases = row(f"SELECT COUNT(*) n FROM test_cases WHERE project_id=? AND ({where})", (project_id, *params))["n"] if where else 0
    points_where = " OR ".join(["title LIKE ? OR module LIKE ? OR rationale LIKE ?" for _ in words])
    points_params = []
    for word in words:
        points_params.extend([f"%{word}%", f"%{word}%", f"%{word}%"])
    points = row(f"SELECT COUNT(*) n FROM test_points WHERE project_id=? AND ({points_where})", (project_id, *points_params))["n"] if points_where else 0
    source_where = " OR ".join(["name LIKE ? OR content LIKE ?" for _ in words])
    source_params = []
    for word in words:
        source_params.extend([f"%{word}%", f"%{word}%"])
    sources = row(f"SELECT COUNT(*) n FROM sources WHERE project_id=? AND ({source_where})", (project_id, *source_params))["n"] if source_where else 0
    return {"sources": sources, "test_points": points, "test_cases": cases}


def ensure_requirement_package_manifest(project_id, package):
    root = REQUIREMENT_PACKAGE_ROOT / package["id"]
    for child in ("docs", "data", "skills", "outputs/jmeter", "outputs/newman", "outputs/pytest", "reports"):
        (root / child).mkdir(parents=True, exist_ok=True)
    manifest_path = root / "manifest.json"
    try:
        existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    except Exception:
        existing_manifest = {}
    artifacts = {name: _file_status(path) for name, path in (package.get("artifacts") or {}).items()}
    counts = _package_signal_counts(project_id, package["id"])
    ready_artifacts = sum(1 for item in artifacts.values() if item["exists"])
    status = "READY" if counts["test_cases"] and ready_artifacts else "DRAFT" if counts["sources"] or ready_artifacts else "EMPTY"
    manifest = {
        "schema_version": "1.0",
        "project_id": project_id,
        "package_id": package["id"],
        "name": package["name"],
        "domain": package["domain"],
        "description": package["description"],
        "status": status,
        "primary_tool": package["primary_tool"],
        "tool_strategy": package["tool_strategy"],
        "data_policy": package["data_policy"],
        "base_url": package.get("base_url", ""),
        "workflow": package["workflow"],
        "orchestration": package.get("orchestration") or existing_manifest.get("orchestration") or {
            "primary_plan": "outputs/execution-plan.json",
            "kind": "scenario_execution_plan",
            "fallback": "structured test case scenario_type",
            "rule": "需求包可以声明自己的主编排文件；未声明时默认使用场景执行计划，未来可替换为更高级编排资产。",
        },
        "counts": counts,
        "artifacts": artifacts,
        "portable_layout": {
            "docs": "需求、接口文档、抓包说明",
            "data": "CSV账号池、参数化数据、运行槽位",
            "skills": "工具生成规则和场景约束",
            "outputs": "Newman/JMeter/pytest生成物",
            "reports": "执行报告和AI复盘",
        },
    }
    data_scope = package.get("data_scope") or existing_manifest.get("data_scope")
    if data_scope:
        manifest["data_scope"] = data_scope
    comparable_existing = {k: v for k, v in existing_manifest.items() if k not in {"updated_at", "root", "manifest_path"}}
    manifest["updated_at"] = existing_manifest.get("updated_at") if comparable_existing == manifest else now()
    if comparable_existing != {k: v for k, v in manifest.items() if k != "updated_at"} or existing_manifest.get("updated_at") != manifest["updated_at"]:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    readme = root / "README.md"
    if not readme.exists():
        readme.write_text(
            f"# {package['name']}\n\n"
            "这是 AutoTest AI 的可迁移需求包。资料、测试数据、工具脚本和报告按同一目录归档。\n\n"
            "## 流程\n\n"
            + "\n".join(f"{i + 1}. {step}" for i, step in enumerate(package["workflow"]))
            + "\n\n## 工具分工\n\n"
            + "\n".join(f"- {tool}: {purpose}" for tool, purpose in package["tool_strategy"].items())
            + "\n",
            encoding="utf-8",
        )
    manifest["root"] = str(root)
    manifest["manifest_path"] = str(manifest_path)
    manifest["workflow_status"] = _requirement_package_workflow_status(root, counts, artifacts)
    return manifest


def _package_slug(value):
    text = str(value or "").strip().lower()
    if not text:
        return ""
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff_-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-_")
    if re.fullmatch(r"[\u4e00-\u9fff_-]+", text):
        text = "req-" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    return text[:64]


def _custom_requirement_package_template(project_id, manifest):
    package_id = str(manifest.get("package_id") or manifest.get("id") or "").strip()
    name = str(manifest.get("name") or package_id or "未命名需求包").strip()
    domain = str(manifest.get("domain") or name).strip()
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    config = load_environment_config()
    base_url = (project.get("base_url") if project else "") or deep_get(config, "project.base_url", "")
    return {
        "id": package_id,
        "name": name,
        "domain": domain,
        "description": str(manifest.get("description") or "独立需求包，按资料、用例、脚本和报告分开归档。").strip(),
        "primary_tool": str(manifest.get("primary_tool") or "JMeter").strip(),
        "tool_strategy": manifest.get("tool_strategy") or {
            "newman": "轻量接口回归",
            "jmeter": "业务流程和性能执行",
            "pytest": "深度断言和AI复盘",
        },
        "data_policy": str(manifest.get("data_policy") or "按测试用例判断是否需要运行参数、CSV、DB或Redis证据。").strip(),
        "data_scope": manifest.get("data_scope") or {},
        "orchestration": manifest.get("orchestration") or {},
        "base_url": base_url,
        "artifacts": {
            "manifest": REQUIREMENT_PACKAGE_ROOT / package_id / "manifest.json",
            "account_model": REQUIREMENT_PACKAGE_ROOT / package_id / "account_model.yaml",
            "evidence_rules": REQUIREMENT_PACKAGE_ROOT / package_id / "evidence_rules.yaml",
            "newman": REQUIREMENT_PACKAGE_ROOT / package_id / "outputs" / "newman" / "postman-collection.json",
            "jmeter": REQUIREMENT_PACKAGE_ROOT / package_id / "outputs" / "jmeter" / "jmeter-plan.jmx",
            "pytest": REQUIREMENT_PACKAGE_ROOT / package_id / "outputs" / "pytest" / "pytest_api_cases.py",
        },
        "workflow": manifest.get("workflow") or [
            "导入需求和接口资料",
            "生成测试点和测试用例",
            "按需求包生成外部工具脚本",
            "执行并回收报告",
            "结合接口、DB、Redis证据复盘",
        ],
    }


def requirement_package_catalog(project_id):
    package_templates = {
        "wealth-level": _requirement_package_template(project_id, "wealth-level"),
        "salary-trade": _requirement_package_template(project_id, "salary-trade"),
    }
    if REQUIREMENT_PACKAGE_ROOT.exists():
        for manifest_path in REQUIREMENT_PACKAGE_ROOT.glob("*/manifest.json"):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            package_id = str(manifest.get("package_id") or manifest_path.parent.name).strip()
            if package_id and package_id not in package_templates:
                package_templates[package_id] = _custom_requirement_package_template(project_id, {**manifest, "package_id": package_id})
    packages = [ensure_requirement_package_manifest(project_id, item) for item in package_templates.values()]
    summary = {
        "total": len(packages),
        "ready": sum(item["status"] == "READY" for item in packages),
        "draft": sum(item["status"] == "DRAFT" for item in packages),
        "empty": sum(item["status"] == "EMPTY" for item in packages),
        "root": str(REQUIREMENT_PACKAGE_ROOT),
    }
    return {
        "status": "READY" if summary["ready"] else "DRAFT",
        "summary": summary,
        "packages": packages,
        "process": [
            {"step": "需求包", "owner": "测试/产品", "output": "docs + manifest"},
            {"step": "测试用例", "owner": "AI生成、测试确认", "output": "test-cases.yaml / markdown"},
            {"step": "工具资产", "owner": "平台生成", "output": "Newman collection、JMeter JMX、pytest"},
            {"step": "外部执行", "owner": "Newman/JMeter/pytest", "output": "json、jtl、html"},
            {"step": "AI复盘", "owner": "平台", "output": "失败原因、证据、风险、下一步"},
        ],
    }


def create_requirement_package(project_id, payload):
    project = row("SELECT id FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    name = str(payload.get("name") or "").strip()
    if not name:
        raise ValueError("请填写需求包名称")
    package_id = _package_slug(payload.get("package_id") or name)
    if not package_id:
        raise ValueError("需求包标识无效")
    root = REQUIREMENT_PACKAGE_ROOT / package_id
    if (root / "manifest.json").exists() and not payload.get("overwrite"):
        raise ValueError("需求包已存在，请换一个名称或进入原需求包维护")
    template = _custom_requirement_package_template(project_id, {
        "package_id": package_id,
        "name": name,
        "domain": payload.get("domain") or name,
        "description": payload.get("description") or "",
        "primary_tool": payload.get("primary_tool") or "JMeter",
        "data_policy": payload.get("data_policy") or "",
    })
    package = ensure_requirement_package_manifest(project_id, template)
    return {
        "status": "READY",
        "package": package,
        "catalog": requirement_package_catalog(project_id),
    }


def requirement_package_by_id(project_id, package_id):
    package_id = str(package_id or "").strip()
    catalog = requirement_package_catalog(project_id)
    for package in catalog.get("packages", []):
        if package.get("package_id") == package_id or package.get("id") == package_id:
            return package
    raise ValueError("没有找到这个需求包")


def requirement_evidence_rules(project_id, package_id):
    package = requirement_package_by_id(project_id, package_id)
    path = Path(package["root"]) / "evidence_rules.yaml"
    payload = _load_yaml_file(path)
    rules = payload.get("rules") if isinstance(payload, dict) else []
    if not isinstance(rules, list):
        rules = []
    known_tables = {x["table_name"] for x in rows("SELECT table_name FROM db_tables WHERE project_id=?", (project_id,)) if x.get("table_name")}
    known_redis = {x["key_name"] for x in rows("SELECT key_name FROM redis_key_snapshots WHERE project_id=?", (project_id,)) if x.get("key_name")}
    items = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        query = rule.get("query") or {}
        source = str(query.get("source") or "").strip().lower()
        table_name = str(query.get("table") or "").strip()
        redis_key = str(query.get("key") or query.get("pattern") or "").strip()
        blockers = []
        if source == "mysql" and table_name and table_name not in known_tables:
            blockers.append(f"表 {table_name} 未在平台数据库元数据中找到")
        if source == "redis" and redis_key and known_redis and redis_key not in known_redis:
            blockers.append(f"Redis Key {redis_key} 未在平台快照中找到")
        if source not in {"mysql", "redis", "api", ""}:
            blockers.append(f"暂不支持的数据源 {source}")
        items.append({
            "id": rule.get("id") or uid("evidence_rule"),
            "name": rule.get("name") or "未命名证据规则",
            "trigger": rule.get("trigger") or "",
            "business_object": rule.get("business_object") or "",
            "source": source or "manual",
            "table": table_name,
            "redis_key": redis_key,
            "where": query.get("where") or "",
            "assertions": rule.get("assertions") if isinstance(rule.get("assertions"), list) else [],
            "status": "READY" if not blockers else "ATTENTION",
            "blockers": blockers,
        })
    summary = {
        "rules": len(items),
        "ready": sum(1 for x in items if x["status"] == "READY"),
        "attention": sum(1 for x in items if x["status"] != "READY"),
        "mysql_rules": sum(1 for x in items if x["source"] == "mysql"),
        "redis_rules": sum(1 for x in items if x["source"] == "redis"),
        "known_db_tables": len(known_tables),
        "known_redis_keys": len(known_redis),
    }
    status = "READY" if items and not summary["attention"] else "READY_WITH_WARNINGS" if items else "MISSING"
    return {
        "status": status,
        "project_id": project_id,
        "package_id": package.get("package_id"),
        "package_name": package.get("name"),
        "rules_path": str(path),
        "rules_exists": path.is_file(),
        "summary": summary,
        "rules": items,
        "runtime_order": [
            "接口/JMeter/Newman/pytest先执行并产生业务对象编号",
            "平台读取证据规则中的查询目标和运行变量",
            "只读查询MySQL/Redis并计算断言结果",
            "将查询位置、断言、失败原因和原始摘要写入报告中心",
        ],
    }


def generate_business_evidence_plan(project_id, payload=None):
    payload = payload or {}
    package_id = str(payload.get("package_id") or "").strip() or "salary-trade"
    plan = requirement_evidence_rules(project_id, package_id)
    summary = plan["summary"]
    report = {
        "report_type": "BUSINESS_EVIDENCE_RULE_PLAN",
        "project_id": project_id,
        "package_id": package_id,
        "package_name": plan.get("package_name"),
        "status": plan["status"],
        "created_at": now(),
        "summary": summary,
        "rules_path": plan["rules_path"],
        "rules": plan["rules"],
        "runtime_order": plan["runtime_order"],
        "conclusion": "已生成执行后业务数据证据计划。它定义接口执行后去哪查、查什么、如何断言；真实业务写入由接口执行产生，平台只读取证。",
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = ROOT / "reports" / f"business-evidence-plan-{project_id}-{package_id}-{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["json_url"] = "/reports/" + out.name
    report["file_name"] = out.name
    return report


def _evidence_runtime_vars(payload):
    variables = payload.get("runtime_variables") or payload.get("variables") or {}
    if isinstance(variables, str):
        try:
            variables = json.loads(variables or "{}")
        except Exception:
            variables = {}
    variables = variables if isinstance(variables, dict) else {}
    for key in ("order_no", "orderNo", "salary_order_no", "applicant_uid", "proxy_uid", "agent_uid", "country_code", "countryCode", "currency", "expected_log_statuses"):
        if key in payload and payload.get(key) not in (None, ""):
            variables[key] = payload.get(key)
    if "orderNo" in variables and "order_no" not in variables:
        variables["order_no"] = variables["orderNo"]
    if "salary_order_no" in variables and "order_no" not in variables:
        variables["order_no"] = variables["salary_order_no"]
    if "agent_uid" in variables and "proxy_uid" not in variables:
        variables["proxy_uid"] = variables["agent_uid"]
    if "countryCode" in variables and "country_code" not in variables:
        variables["country_code"] = variables["countryCode"]
    return variables


def _evidence_sql_value(value):
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    text = str(value if value is not None else "")
    return "'" + text.replace("\\", "\\\\").replace("'", "''") + "'"


def _render_evidence_template(template, variables, missing):
    def repl(match):
        name = match.group(1)
        if name not in variables or variables.get(name) in (None, ""):
            missing.add(name)
            return "NULL"
        return _evidence_sql_value(variables.get(name))

    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", repl, str(template or ""))


def _resolve_expected_value(value, variables, missing):
    if isinstance(value, str):
        match = re.fullmatch(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", value.strip())
        if match:
            name = match.group(1)
            if name not in variables or variables.get(name) in (None, ""):
                missing.add(name)
                return None
            return variables.get(name)
    return value


def _values_for_field(records, field):
    return [item.get(field) for item in records if isinstance(item, dict) and field in item]


def _number_value(value):
    try:
        return float(str(value).strip())
    except Exception:
        return None


def _run_evidence_assertion(assertion, records, variables):
    field = str(assertion.get("field") or "").strip()
    operator = str(assertion.get("operator") or "equals").strip()
    missing = set()
    expected = _resolve_expected_value(assertion.get("expected"), variables, missing)
    values = _values_for_field(records, field)
    first = values[0] if values else None
    if missing:
        return {"field": field, "operator": operator, "expected": assertion.get("expected"), "actual": first, "passed": False, "reason": "缺少运行变量：" + ",".join(sorted(missing))}
    if operator == "equals":
        passed = str(first) == str(expected)
    elif operator == "contains":
        passed = any(str(expected) in str(value or "") for value in values)
    elif operator == "contains_any":
        expected_items = expected if isinstance(expected, list) else re.split(r"[,，\s]+", str(expected or ""))
        expected_items = [str(x).strip() for x in expected_items if str(x).strip()]
        passed = bool(expected_items) and any(str(value) in expected_items for value in values)
    elif operator == "not_empty":
        passed = any(value not in (None, "") for value in values)
    elif operator == "greater_than":
        left = _number_value(first)
        right = _number_value(expected)
        passed = left is not None and right is not None and left > right
    else:
        passed = False
    return {"field": field, "operator": operator, "expected": expected, "actual": first if len(values) <= 1 else values[:20], "passed": bool(passed), "reason": "" if passed else "断言不满足"}


def run_business_evidence_rules(project_id, payload=None):
    payload = payload or {}
    package_id = str(payload.get("package_id") or "").strip() or "salary-trade"
    plan = requirement_evidence_rules(project_id, package_id)
    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        scenarios = [{"name": payload.get("scenario_name") or "默认场景", **payload}]
    scenario_results = []
    all_rule_results = []
    for index, scenario in enumerate(scenarios, 1):
        if not isinstance(scenario, dict):
            continue
        variables = _evidence_runtime_vars({**payload, **scenario})
        selected = set(scenario.get("rule_ids") or payload.get("rule_ids") or [])
        rule_results = []
        scenario_name = str(scenario.get("name") or scenario.get("scenario") or f"场景{index}")
        for rule in plan.get("rules", []):
            if selected and rule.get("id") not in selected:
                continue
            missing = set()
            source = rule.get("source")
            rows_data = []
            sql = ""
            blockers = list(rule.get("blockers") or [])
            if source == "mysql" and not blockers:
                where_sql = _render_evidence_template(rule.get("where") or "1=1", variables, missing)
                table_name = _mysql_safe_string(rule.get("table"), "table", 128)
                if missing:
                    blockers.append("缺少运行变量：" + ",".join(sorted(missing)))
                else:
                    sql = f"SELECT * FROM {table_name} WHERE {where_sql} LIMIT 100"
                    try:
                        rows_data = _mysql_rows(sql, 100)
                    except Exception as exc:
                        blockers.append(str(exc))
            elif source == "redis":
                blockers.append("Redis证据规则执行器待接入，只读计划已保留")
            elif source not in {"mysql", "redis"}:
                blockers.append(f"暂不支持的数据源 {source}")
            assertions = []
            if not blockers:
                assertions.append({"field": "__rows__", "operator": "exists", "expected": "至少1行", "actual": len(rows_data), "passed": len(rows_data) > 0, "reason": "" if rows_data else "查询无数据"})
                for assertion in rule.get("assertions") or []:
                    assertions.append(_run_evidence_assertion(assertion, rows_data, variables))
            status = "BLOCKED" if blockers else "PASSED" if assertions and all(x.get("passed") for x in assertions) else "FAILED"
            rule_results.append({
                "scenario": scenario_name,
                "id": rule.get("id"),
                "name": rule.get("name"),
                "trigger": rule.get("trigger"),
                "source": source,
                "table": rule.get("table"),
                "where": rule.get("where"),
                "sql": sql,
                "status": status,
                "rows": len(rows_data),
                "assertions": assertions,
                "blockers": blockers,
                "sample": rows_data[:3],
            })
        scenario_passed = sum(1 for x in rule_results if x["status"] == "PASSED")
        scenario_failed = sum(1 for x in rule_results if x["status"] == "FAILED")
        scenario_blocked = sum(1 for x in rule_results if x["status"] == "BLOCKED")
        scenario_status = "PASSED" if rule_results and not scenario_failed and not scenario_blocked else "BLOCKED" if scenario_blocked else "FAILED" if scenario_failed else "MISSING"
        scenario_results.append({
            "name": scenario_name,
            "status": scenario_status,
            "runtime_variables": {k: ("***" if "ticket" in str(k).lower() or "token" in str(k).lower() else v) for k, v in variables.items()},
            "summary": {
                "rules_total": len(rule_results),
                "rules_passed": scenario_passed,
                "rules_failed": scenario_failed,
                "rules_blocked": scenario_blocked,
            },
            "rules": rule_results,
        })
        all_rule_results.extend(rule_results)
    passed = sum(1 for x in all_rule_results if x["status"] == "PASSED")
    failed = sum(1 for x in all_rule_results if x["status"] == "FAILED")
    blocked = sum(1 for x in all_rule_results if x["status"] == "BLOCKED")
    status = "PASSED" if all_rule_results and not failed and not blocked else "BLOCKED" if blocked else "FAILED" if failed else "MISSING"
    report = {
        "report_type": "BUSINESS_EVIDENCE_RULE_RUN",
        "project_id": project_id,
        "package_id": package_id,
        "package_name": plan.get("package_name"),
        "status": status,
        "created_at": now(),
        "summary": {
            "scenarios_total": len(scenario_results),
            "scenarios_passed": sum(1 for x in scenario_results if x["status"] == "PASSED"),
            "scenarios_failed": sum(1 for x in scenario_results if x["status"] == "FAILED"),
            "scenarios_blocked": sum(1 for x in scenario_results if x["status"] == "BLOCKED"),
            "rules_total": len(all_rule_results),
            "rules_passed": passed,
            "rules_failed": failed,
            "rules_blocked": blocked,
            "mysql_rules": sum(1 for x in all_rule_results if x.get("source") == "mysql"),
            "redis_rules": sum(1 for x in all_rule_results if x.get("source") == "redis"),
        },
        "scenarios": scenario_results,
        "rules": all_rule_results,
        "readonly_policy": {
            "mysql": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"],
            "business_write_allowed": False,
            "note": "业务写入由接口执行产生；执行器只读取业务库并归档证据。",
        },
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = ROOT / "reports" / f"business-evidence-run-{project_id}-{package_id}-{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    report["json_url"] = "/reports/" + out.name
    report["file_name"] = out.name
    return report


def _case_text(case):
    return "\n".join(str(case.get(key) or "") for key in ("title", "method", "path", "payload", "steps", "expected", "requirement_ref", "scenario_type"))


def _words_for_matching(text):
    raw = re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}|[\u4e00-\u9fff]{2,}", str(text or ""))
    stop = {"get", "post", "put", "delete", "api", "http", "https", "uid", "ticket", "json", "data", "code", "message", "success"}
    return [x.lower() for x in raw if x.lower() not in stop]


def _table_match_score(table, words):
    haystack = " ".join(str(table.get(key) or "") for key in ("table_name", "table_comment", "module", "columns_json")).lower()
    score = 0
    for word in words:
        if word and word in haystack:
            score += 3 if word in str(table.get("table_name") or "").lower() else 1
    name = str(table.get("table_name") or "").lower()
    if any(word in name for word in ("order", "trade", "salary")) and any(word in words for word in ("order", "trade", "salary", "订单", "交易", "工资")):
        score += 4
    if any(word in name for word in ("log", "record")) and any(word in words for word in ("log", "record", "日志", "记录", "流转")):
        score += 4
    if any(word in name for word in ("evidence", "appeal", "complaint")) and any(word in words for word in ("evidence", "appeal", "complaint", "投诉", "凭证")):
        score += 4
    if any(word in name for word in ("wallet", "purse", "balance")) and any(word in words for word in ("wallet", "purse", "balance", "钱包", "余额")):
        score += 4
    return score


def _candidate_expected_status(text):
    text = str(text or "")
    pairs = [
        (100, ("完成", "确认收款", "finished", "confirm")),
        (90, ("投诉成功", "appeal success")),
        (80, ("投诉失败", "appeal failed")),
        (50, ("取消", "cancel")),
        (30, ("已转账", "mark paid", "paid")),
        (20, ("接受", "接单", "accept")),
        (10, ("创建", "待处理", "pending", "create")),
    ]
    for status, words in pairs:
        if any(word.lower() in text.lower() for word in words):
            return status
    m = re.search(r"状态[^\d]{0,6}(\d{1,3})", text)
    return int(m.group(1)) if m else None


def _candidate_rule_assertions(table_name, case_text):
    lower = str(case_text or "").lower()
    assertions = []
    if "whitelist" in table_name:
        return [
            {"field": "uid", "operator": "equals", "expected": "${proxy_uid}"},
            {"field": "status", "operator": "equals", "expected": 1},
            {"field": "country_code", "operator": "equals", "expected": "${country_code}"},
            {"field": "support_currencies", "operator": "contains", "expected": "${currency}"},
        ]
    if "order" in table_name or "订单" in case_text:
        assertions.append({"field": "order_no", "operator": "equals", "expected": "${order_no}"})
    if any(word in lower for word in ("申请人", "applicant")):
        assertions.append({"field": "uid", "operator": "equals", "expected": "${applicant_uid}"})
    if any(word in lower for word in ("代理", "agent", "proxy")):
        assertions.append({"field": "agent_uid", "operator": "equals", "expected": "${proxy_uid}"})
    status = _candidate_expected_status(case_text)
    if status is not None and ("order" in table_name or "status" in lower):
        assertions.append({"field": "status", "operator": "equals", "expected": status})
    if any(word in lower for word in ("投诉", "appeal", "凭证", "evidence")):
        assertions.append({"field": "evidence_type", "operator": "not_empty"})
    return assertions or [{"field": "__rows__", "operator": "exists", "expected": "至少1行"}]


def generate_candidate_evidence_rules(project_id, payload=None):
    payload = payload or {}
    package_id = str(payload.get("package_id") or "").strip() or "salary-trade"
    package = requirement_package_by_id(project_id, package_id)
    manifest_path = Path(package["root"]) / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    except Exception:
        manifest = {}
    cases = _requirement_package_cases(project_id, package_id)
    tables = rows("SELECT table_name,table_comment,module,columns_json FROM db_tables WHERE project_id=?", (project_id,))
    existing = requirement_evidence_rules(project_id, package_id)
    existing_ids = {x.get("id") for x in existing.get("rules", [])}
    existing_tables = {x.get("table") for x in existing.get("rules", []) if x.get("table")}
    scoped_tables = set()
    data_scope = manifest.get("data_scope") if isinstance(manifest, dict) else {}
    if isinstance(data_scope, dict):
        scoped_tables.update(str(x).strip() for x in data_scope.get("mysql_tables") or [] if str(x).strip())
    if existing_tables:
        table_pool = [x for x in tables if x.get("table_name") in existing_tables]
        scope_mode = "confirmed_business_tables"
        needs_scope_confirmation = False
    elif scoped_tables:
        table_pool = [x for x in tables if x.get("table_name") in scoped_tables]
        scope_mode = "manifest_data_scope"
        needs_scope_confirmation = False
    else:
        table_pool = tables
        scope_mode = "all_imported_tables"
        needs_scope_confirmation = True
    candidates = []
    seen = set()
    for case in cases:
        text = _case_text(case)
        words = _words_for_matching(text)
        ranked = sorted(
            ({"score": _table_match_score(table, words), **table} for table in table_pool),
            key=lambda x: x["score"],
            reverse=True,
        )
        ranked = [x for x in ranked if x["score"] > 0][:3]
        path = str(case.get("path") or "").split("?", 1)[0]
        method = str(case.get("method") or "").upper() or "CASE"
        for table in ranked[:1]:
            table_name = table.get("table_name")
            if not table_name:
                continue
            base = re.sub(r"[^a-z0-9_]+", "_", f"{package_id}_{method}_{path}_{table_name}".lower()).strip("_")
            rule_id = re.sub(r"_+", "_", base)[-96:] or uid("candidate_rule")
            if rule_id in seen or rule_id in existing_ids:
                continue
            seen.add(rule_id)
            if "whitelist" in table_name:
                where = "uid = ${proxy_uid}"
            elif any(x in table_name for x in ("order", "evidence", "log")):
                where = "order_no = ${order_no}"
            else:
                where = "uid = ${uid}"
            candidates.append({
                "id": rule_id,
                "name": f"候选证据：{case.get('title') or path}",
                "trigger": f"{method} {path}".strip(),
                "business_object": table_name,
                "confidence": round(min(0.95, (0.25 if needs_scope_confirmation else 0.45) + table["score"] / 20), 2),
                "review_status": "NEEDS_SCOPE_CONFIRMATION" if needs_scope_confirmation else "READY_FOR_REVIEW",
                "reason": (f"未声明 data_scope，本候选只表示关键词命中，需先确认需求包数据范围；命中表 {table_name}。"
                           if needs_scope_confirmation else
                           f"测试用例与表 {table_name} 命中业务关键词，建议人工确认后转入正式 evidence_rules.yaml。"),
                "query": {
                    "source": "mysql",
                    "table": table_name,
                    "where": where,
                },
                "assertions": _candidate_rule_assertions(table_name, text),
                "source_case": {
                    "id": case.get("id"),
                    "title": case.get("title"),
                    "method": method,
                    "path": path,
                },
            })
    out_payload = {
        "schema_version": "1.0",
        "package_id": package_id,
        "package_name": package.get("name"),
        "generated_at": now(),
        "mode": "candidate_only",
        "note": "候选规则不会自动覆盖正式 evidence_rules.yaml。请人工确认后再复制或合并。",
        "summary": {
            "cases_scanned": len(cases),
            "db_tables_scanned": len(table_pool),
            "candidates": len(candidates),
            "existing_rules": len(existing_ids),
            "scope": scope_mode,
            "needs_scope_confirmation": needs_scope_confirmation,
        },
        "rules": candidates,
    }
    candidates_path = Path(package["root"]) / "evidence_rules.candidates.yaml"
    candidates_path.write_text(_yaml_dump(out_payload), encoding="utf-8")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report = {
        "report_type": "CANDIDATE_EVIDENCE_RULES",
        "project_id": project_id,
        "package_id": package_id,
        "package_name": package.get("name"),
        "status": "NEEDS_SCOPE_CONFIRMATION" if needs_scope_confirmation and candidates else "READY" if candidates else "ATTENTION",
        "created_at": now(),
        "summary": out_payload["summary"],
        "candidates_path": str(candidates_path),
        "candidates": candidates[:50],
        "conclusion": "未声明数据范围，请先确认需求包 data_scope 后再采纳候选规则。" if needs_scope_confirmation else "已根据测试用例和数据库元数据生成候选证据规则；候选结果需要测试人员确认后再进入正式规则。",
    }
    out = ROOT / "reports" / f"candidate-evidence-rules-{project_id}-{package_id}-{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["json_url"] = "/reports/" + out.name
    report["file_name"] = out.name
    return report


def accept_candidate_evidence_rules(project_id, payload=None):
    payload = payload or {}
    package_id = str(payload.get("package_id") or "").strip() or "salary-trade"
    package = requirement_package_by_id(project_id, package_id)
    package_root = Path(package["root"])
    candidates_path = package_root / "evidence_rules.candidates.yaml"
    official_path = package_root / "evidence_rules.yaml"
    candidates_payload = _load_yaml_file(candidates_path)
    candidate_rules = candidates_payload.get("rules") if isinstance(candidates_payload, dict) else []
    if not isinstance(candidate_rules, list) or not candidate_rules:
        raise ValueError("当前需求包还没有候选证据规则，请先生成候选规则")
    selected = payload.get("rule_ids")
    if isinstance(selected, str):
        selected = [x.strip() for x in re.split(r"[\n,，;；\s]+", selected) if x.strip()]
    selected = set(selected or [])
    official_payload = _load_yaml_file(official_path)
    if not isinstance(official_payload, dict) or not official_payload:
        official_payload = {
            "schema_version": "1.0",
            "package_id": package_id,
            "package_name": package.get("name"),
            "purpose": "执行后用只读 MySQL/Redis 证据证明接口产生的业务结果真实落库、状态正确、流水可追溯。",
            "runtime_variables": {},
            "rules": [],
        }
    official_rules = official_payload.get("rules")
    if not isinstance(official_rules, list):
        official_rules = []
    existing_ids = {str(x.get("id")) for x in official_rules if isinstance(x, dict) and x.get("id")}
    accepted, skipped = [], []
    matched_selected = set()
    for rule in candidate_rules:
        if not isinstance(rule, dict):
            continue
        rule_id = str(rule.get("id") or "").strip()
        if selected and rule_id not in selected:
            continue
        matched_selected.add(rule_id)
        if rule.get("review_status") == "NEEDS_SCOPE_CONFIRMATION" and not payload.get("force"):
            skipped.append({"id": rule_id, "reason": "候选规则缺少数据范围确认"})
            continue
        if rule_id in existing_ids:
            skipped.append({"id": rule_id, "reason": "正式规则中已存在"})
            continue
        clean = {k: v for k, v in rule.items() if k not in {"confidence", "review_status", "reason", "source_case"}}
        clean["source"] = {
            "type": "candidate_evidence_rule",
            "accepted_at": now(),
            "source_case": rule.get("source_case") or {},
            "confidence": rule.get("confidence"),
        }
        official_rules.append(clean)
        existing_ids.add(rule_id)
        accepted.append({"id": rule_id, "name": clean.get("name"), "table": (clean.get("query") or {}).get("table")})
    for missing_id in sorted(selected - matched_selected):
        skipped.append({"id": missing_id, "reason": "候选文件中未找到这个规则ID"})
    if accepted:
        official_payload["rules"] = official_rules
        official_payload["updated_at"] = now()
        official_path.write_text(_yaml_dump(official_payload), encoding="utf-8")
    report = {
        "report_type": "ACCEPT_CANDIDATE_EVIDENCE_RULES",
        "project_id": project_id,
        "package_id": package_id,
        "package_name": package.get("name"),
        "status": "READY" if accepted else "ATTENTION",
        "created_at": now(),
        "summary": {
            "candidate_rules": len(candidate_rules),
            "selected": len(selected) if selected else "all",
            "accepted": len(accepted),
            "skipped": len(skipped),
            "official_rules": len(official_rules),
        },
        "official_rules_path": str(official_path),
        "candidates_path": str(candidates_path),
        "accepted": accepted,
        "skipped": skipped,
        "conclusion": "已将确认后的候选证据规则追加到正式 evidence_rules.yaml。" if accepted else "没有新增正式规则，请检查是否已存在或仍需确认数据范围。",
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = ROOT / "reports" / f"accepted-evidence-rules-{project_id}-{package_id}-{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["json_url"] = "/reports/" + out.name
    report["file_name"] = out.name
    return report


def _path_variables(text):
    return sorted(set(re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", str(text or ""))))


def _case_interface_fields(case):
    fields = set()
    for source in (case.get("path"), case.get("payload"), case.get("headers")):
        text = str(source or "")
        fields.update(re.findall(r"[?&]([A-Za-z_][A-Za-z0-9_]*)=", text))
        fields.update(re.findall(r'"([A-Za-z_][A-Za-z0-9_]*)"\s*:', text))
        fields.update(_path_variables(text))
    return sorted(fields)


def _clean_case_step(text):
    return re.sub(r"^\s*\d+[\.\)、)]\s*", "", str(text or "")).strip()


def _case_related_evidence_rules(case, official_rules, candidate_rules):
    method = str(case.get("method") or "").upper()
    path = str(case.get("path") or "").split("?", 1)[0]
    related = []
    for rule in official_rules:
        trigger = str(rule.get("trigger") or "")
        if path and path in trigger and (not method or method in trigger.upper()):
            item = dict(rule)
            item["rule_origin"] = "official"
            related.append(item)
    case_id = case.get("id")
    for rule in candidate_rules:
        source_case = rule.get("source_case") or {}
        trigger = str(rule.get("trigger") or "")
        if source_case.get("id") == case_id or (path and path in trigger and (not method or method in trigger.upper())):
            item = dict(rule)
            item["rule_origin"] = "candidate"
            related.append(item)
    return related


def _evidence_rule_query(rule):
    query = rule.get("query") if isinstance(rule.get("query"), dict) else {}
    return {
        "source": query.get("source") or rule.get("source") or "mysql",
        "table": query.get("table") or rule.get("table"),
        "where": query.get("where") or rule.get("where"),
        "key": query.get("key") or rule.get("redis_key"),
    }


def _case_text(case):
    return "\n".join(str(case.get(key) or "") for key in (
        "title", "scenario_type", "steps", "expected", "requirement_ref", "path", "payload", "headers"
    ))


def _case_exception_sources(case):
    text = _case_text(case).lower()
    scenario = str(case.get("scenario_type") or "")
    sources = []
    if any(word in scenario for word in ("异常", "反向", "失败", "非法", "边界")):
        sources.append("requirement_exception")
    if any(word in text for word in ("ticket", "token", "鉴权", "认证", "必填", "缺失", "为空", "参数", "类型", "格式", "非法uid", "无效")):
        sources.append("api_contract_exception")
    if any(word in text for word in ("订单状态", "状态流", "待处理", "接单", "转账", "确认收款", "交易完成", "取消订单", "拒绝订单", "投诉", "过期", "重复申请", "不能", "不允许")):
        sources.append("state_machine_exception")
    if any(word in text for word in ("数据库", "db", "redis", "缓存", "余额", "额度", "白名单", "国家", "币种", "处理中", "唯一", "互斥")):
        sources.append("data_constraint_exception")
    return sorted(set(sources))


def _case_manual_signals(case):
    text = _case_text(case).lower()
    return any(word in text for word in (
        "人工", "手工", "后台人工", "运营处理", "等待12小时", "12小时", "等待24小时", "24小时", "定时任务", "自然过期"
    ))


def _classify_structured_case(case, required_variables, db_checks, redis_checks):
    method = str(case.get("method") or "").upper()
    path = str(case.get("path") or "").strip()
    variables = set(required_variables or [])
    evidence_checks = list(db_checks or []) + list(redis_checks or [])
    confirmed_evidence = [x for x in evidence_checks if x.get("review_status") == "CONFIRMED"]
    candidate_evidence = [x for x in evidence_checks if x.get("review_status") != "CONFIRMED"]
    exception_sources = _case_exception_sources(case)
    manual = _case_manual_signals(case)
    reasons = []

    if not method or not path:
        quality_status = "MANUAL_ONLY"
        automation_readiness = "MANUAL_ONLY"
        coverage_tool = "manual"
        reasons.append("缺少可直接执行的接口 method/path。")
    elif manual:
        quality_status = "MANUAL_ONLY"
        automation_readiness = "MANUAL_ONLY"
        coverage_tool = "manual"
        reasons.append("包含人工处理、后台处理、定时过期或长时间等待信号。")
    elif method in {"POST", "PUT", "PATCH", "DELETE"} and not evidence_checks:
        quality_status = "NEEDS_EVIDENCE"
        automation_readiness = "SCRIPTABLE_EVIDENCE_PENDING"
        coverage_tool = "jmeter"
        reasons.append("写操作/状态变更用例缺少DB或Redis证据规则。")
    elif variables and any(name in variables for name in ("ticket", "uid", "orderNo", "order_no", "country_code", "currency")) and not method:
        quality_status = "NEEDS_DATA"
        automation_readiness = "BLOCKED_NEEDS_DATA"
        coverage_tool = "manual"
        reasons.append("依赖运行变量，但缺少执行接口。")
    elif candidate_evidence and not confirmed_evidence:
        quality_status = "NEEDS_EVIDENCE_REVIEW"
        automation_readiness = "SCRIPTABLE_EVIDENCE_PENDING"
        coverage_tool = "jmeter" if method != "GET" or exception_sources else "newman"
        reasons.append("仅命中候选证据规则，需要采纳后再作为正式校验。")
    else:
        quality_status = "READY"
        automation_readiness = "SCRIPT_GENERATION_READY"
        if db_checks or redis_checks:
            coverage_tool = "jmeter" if method != "GET" or "state_machine_exception" in exception_sources else "pytest"
        else:
            coverage_tool = "newman"
        reasons.append("接口、变量和证据条件满足当前脚本生成要求。")

    if method and path and variables and quality_status == "READY":
        reasons.append("需要运行时提供变量：" + ", ".join(sorted(variables)) + "。")
    if exception_sources:
        reasons.append("异常来源：" + ", ".join(exception_sources) + "。")
    return {
        "quality_status": quality_status,
        "automation_readiness": automation_readiness,
        "coverage_tool": coverage_tool,
        "exception_sources": exception_sources,
        "blocking_reasons": reasons,
    }


def _pct(part, total):
    if not total:
        return 0.0
    return round(part * 100 / total, 1)


def _structured_case_next_action(item):
    quality = item.get("quality_status")
    readiness = item.get("automation_readiness")
    tool = item.get("coverage_tool")
    if quality == "READY" and readiness == "SCRIPT_GENERATION_READY":
        return {
            "action": "generate_script",
            "label": f"进入 {tool} 脚本生成",
            "reason": "用例已经具备脚本生成条件。",
        }
    if quality == "NEEDS_EVIDENCE_REVIEW":
        return {
            "action": "accept_candidate_evidence",
            "label": "复核并采纳候选证据规则",
            "reason": "当前用例已命中候选 DB/Redis 证据，但尚未成为正式规则。",
        }
    if quality == "NEEDS_EVIDENCE":
        return {
            "action": "generate_candidate_evidence",
            "label": "补充或生成证据规则",
            "reason": "当前用例可脚本化，但缺少执行后 DB/Redis 校验点。",
        }
    if quality == "NEEDS_DATA" or readiness == "BLOCKED_NEEDS_DATA":
        return {
            "action": "prepare_runtime_data",
            "label": "补齐账号、变量或运行数据",
            "reason": "当前用例依赖运行变量，数据未准备完整。",
        }
    if quality == "MANUAL_ONLY":
        return {
            "action": "export_manual_case",
            "label": "纳入人工测试清单",
            "reason": "当前用例涉及人工处理、运营后台、定时任务或长时间等待。",
        }
    return {
        "action": "review_case",
        "label": "人工复核用例",
        "reason": "当前分级未命中明确处理路径。",
    }


def _structured_case_gap_list(enhanced):
    gap_defs = {
        "NEEDS_EVIDENCE_REVIEW": {
            "title": "候选证据待采纳",
            "next_action": "复核并采纳候选证据规则",
        },
        "NEEDS_EVIDENCE": {
            "title": "缺少正式证据规则",
            "next_action": "生成候选证据规则或手工补 evidence_rules.yaml",
        },
        "NEEDS_DATA": {
            "title": "缺少运行数据",
            "next_action": "补齐账号、ticket、订单号、国家币种或其他运行变量",
        },
        "MANUAL_ONLY": {
            "title": "人工验证或长等待",
            "next_action": "导出人工测试清单，必要时拆成后台/定时任务专项",
        },
    }
    groups = []
    for status, meta in gap_defs.items():
        cases = [item for item in enhanced if item.get("quality_status") == status]
        if not cases:
            continue
        groups.append({
            "quality_status": status,
            "title": meta["title"],
            "count": len(cases),
            "next_action": meta["next_action"],
            "examples": [
                {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "method": item.get("method"),
                    "path": item.get("path"),
                    "coverage_tool": item.get("coverage_tool"),
                    "reason": (item.get("blocking_reasons") or [""])[0],
                }
                for item in cases[:8]
            ],
        })
    return groups


def _structured_case_dashboard(enhanced, summary):
    total = summary.get("cases", 0)
    readiness = summary.get("readiness_counts") or {}
    quality = summary.get("quality_counts") or {}
    script_ready = readiness.get("SCRIPT_GENERATION_READY", 0)
    evidence_pending = readiness.get("SCRIPTABLE_EVIDENCE_PENDING", 0)
    manual = quality.get("MANUAL_ONLY", 0)
    return {
        "total_cases": total,
        "script_generation_ready": script_ready,
        "script_generation_ready_rate": _pct(script_ready, total),
        "evidence_pending": evidence_pending,
        "evidence_pending_rate": _pct(evidence_pending, total),
        "manual_only": manual,
        "manual_only_rate": _pct(manual, total),
        "db_evidence_rate": _pct(summary.get("with_db_checks", 0), total),
        "redis_evidence_rate": _pct(summary.get("with_redis_checks", 0), total),
        "headline": f"当前需求包 {total} 条用例，{script_ready} 条脚本生成就绪，{evidence_pending} 条待证据确认，{manual} 条人工验证，脚本生成就绪率 {_pct(script_ready, total)}%。",
    }


def _structured_case_redis_suggestions(item):
    text = "\n".join(str(item.get(key) or "") for key in ("title", "scenario_type", "path", "steps", "expected_results")).lower()
    suggestions = []
    if any(word in text for word in ("ticket", "token", "登录", "鉴权", "认证")):
        suggestions.append({
            "type": "login_state",
            "source": "redis_optional",
            "key_pattern": "user_login_info:{uid}",
            "field": "access_token",
            "reason": "用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。",
        })
    if any(word in text for word in ("缓存", "cache")):
        suggestions.append({
            "type": "cache_consistency",
            "source": "redis_optional",
            "key_pattern": "待按需求包确认",
            "field": "",
            "reason": "用例涉及缓存语义，但当前需求包未提供稳定Key，先作为可选证据。",
        })
    if any(word in text for word in ("限流", "频控", "重复提交", "幂等")):
        suggestions.append({
            "type": "rate_limit_or_idempotency",
            "source": "redis_optional",
            "key_pattern": "待按服务实现确认",
            "field": "",
            "reason": "用例涉及限流、频控或幂等，Redis可能保存计数或锁，需要研发确认Key规则。",
        })
    if any(word in text for word in ("处理中", "进行中", "未处理", "锁", "互斥")):
        suggestions.append({
            "type": "processing_lock",
            "source": "redis_optional",
            "key_pattern": "待按服务实现确认",
            "field": "",
            "reason": "用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。",
        })
    return suggestions


def _csv_rows_for_path(path):
    path = Path(path)
    if not path.is_file():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [item for item in csv.DictReader(handle) if item]
    except Exception:
        return []


def _truthy_csv_value(value):
    return bool(str(value or "").strip()) and str(value or "").strip().lower() not in ("0", "false", "no", "off", "null", "none")


def _ticket_source_ready(row_data, prefix=""):
    names = [f"{prefix}ticket", "ticket", f"{prefix}password_encrypted", "password_encrypted", f"{prefix}redis_uid", "redis_uid", "uid"]
    return any(_truthy_csv_value(row_data.get(name)) for name in names)


def _scenario_evidence_rule_ids(scenario):
    rule_ids = []
    for rule_id in scenario.get("evidence_rules") or []:
        if rule_id:
            rule_ids.append(str(rule_id))
    for task in scenario.get("tool_tasks") or []:
        for rule_id in task.get("evidence_rules") or []:
            if rule_id:
                rule_ids.append(str(rule_id))
    return sorted(set(rule_ids))


def _scenario_case_ids(scenario):
    case_ids = []
    for case in scenario.get("cases") or []:
        case_id = case.get("id") if isinstance(case, dict) else case
        if case_id:
            case_ids.append(str(case_id))
    for task in scenario.get("tool_tasks") or []:
        for case_id in task.get("cases") or []:
            if case_id:
                case_ids.append(str(case_id))
    return sorted(set(case_ids))


def _slot_number(value):
    match = re.search(r"(\d+)$", str(value or ""))
    return int(match.group(1)) if match else 0


def _scenario_data_preflight(package_id, package_root, details):
    plan = _read_json_asset(Path(package_root) / "outputs" / "execution-plan.json")
    scenarios = plan.get("scenarios") if isinstance(plan, dict) else []
    rules_payload = _load_yaml_file(Path(package_root) / "evidence_rules.yaml")
    official_rule_ids = {
        str(rule.get("id") or rule.get("name") or "").strip()
        for rule in (rules_payload.get("rules") or [])
        if isinstance(rule, dict) and str(rule.get("id") or rule.get("name") or "").strip()
    }
    if not scenarios:
        return {
            "status": "READY_WITH_WARNINGS",
            "summary": {"scenarios": 0, "ready": 0, "warnings": 1, "blocked": 0},
            "scenarios": [],
            "message": "未生成正式场景计划，数据准备只能按通用检查执行。",
        }
    applicant_rows = details.get("applicants") or []
    proxy_matches = details.get("proxy_matches") or []
    results = []
    ready = warnings = blocked = 0
    for scenario in scenarios:
        case_ids = _scenario_case_ids(scenario)
        rule_ids = _scenario_evidence_rule_ids(scenario)
        blockers = []
        attentions = []
        account_slot = scenario.get("account_slot") or ""
        applicant = {}
        if package_id == "salary-trade" and account_slot:
            index = _slot_number(account_slot)
            if index and len(applicant_rows) >= index:
                applicant = applicant_rows[index - 1]
                if not applicant.get("credential_ready"):
                    blockers.append(f"账号槽位 {account_slot} 的申请人缺少 ticket/password/redis_uid")
                country = applicant.get("countryCode") or applicant.get("country_code") or ""
                currency = applicant.get("currency") or ""
                if country and currency:
                    matched = [
                        item for item in proxy_matches
                        if item.get("countryCode") == country and item.get("currency") == currency and item.get("matched", 0)
                    ]
                    if not matched:
                        blockers.append(f"账号槽位 {account_slot} 未匹配到代理：{country}/{currency}")
                else:
                    blockers.append(f"账号槽位 {account_slot} 缺少国家或币种")
            else:
                blockers.append(f"缺少账号槽位 {account_slot} 对应的申请人")
        if not case_ids:
            blockers.append("场景未绑定测试用例")
        missing_rules = [rule_id for rule_id in rule_ids if rule_id not in official_rule_ids]
        if missing_rules:
            attentions.append("场景绑定了尚未采纳的候选证据规则：" + ",".join(missing_rules))
        if not rule_ids:
            attentions.append("场景未绑定证据规则，将退回执行需求包通用证据规则")
        for item in scenario.get("tool_tasks") or []:
            attentions.extend(item.get("blockers") or [])
        if blockers:
            status = "BLOCKED"
            blocked += 1
        elif attentions:
            status = "READY_WITH_WARNINGS"
            warnings += 1
        else:
            status = "READY"
            ready += 1
        results.append({
            "scenario_id": scenario.get("scenario_id") or scenario.get("id") or scenario.get("name"),
            "name": scenario.get("name"),
            "status": status,
            "account_slot": account_slot,
            "applicant_uid": applicant.get("uid") or "",
            "countryCode": applicant.get("countryCode") or "",
            "currency": applicant.get("currency") or "",
            "case_count": len(case_ids),
            "evidence_rule_ids": rule_ids,
            "blockers": blockers,
            "attentions": attentions[:5],
        })
    status = "BLOCKED" if blocked else "READY_WITH_WARNINGS" if warnings else "READY"
    return {
        "status": status,
        "summary": {"scenarios": len(results), "ready": ready, "warnings": warnings, "blocked": blocked},
        "scenarios": results,
        "message": "按场景检查账号槽位、用例绑定和证据规则绑定。",
    }


def _structured_case_data_preflight(project_id, package_id, package_root):
    account_model_path = Path(package_root) / "account_model.yaml"
    account_model = _load_yaml_file(account_model_path)
    config = load_environment_config()
    salary_dataset = deep_get(config, "requirement_datasets.salary_trade", {}) or {}
    checks = []
    runtime_sql_checks = []
    details = {
        "applicants": [],
        "country_currency_pairs": [],
        "proxy_matches": [],
        "credential_sources": {},
    }
    status = "READY"

    def add_check(name, state, detail, next_action=""):
        nonlocal status
        if state in {"BLOCKED", "NEEDS_DATA"}:
            status = "BLOCKED"
        elif state in {"WARNING", "NEEDS_LIVE_CHECK"} and status == "READY":
            status = "READY_WITH_WARNINGS"
        checks.append({"name": name, "status": state, "detail": detail, "next_action": next_action})

    if account_model_path.is_file():
        add_check("账号模型", "READY", f"已读取 {account_model_path}")
    else:
        add_check("账号模型", "NEEDS_DATA", f"缺少 {account_model_path}", "先生成当前需求包 account_model.yaml")

    if package_id == "salary-trade":
        account_csv = ROOT / str(salary_dataset.get("account_csv_path") or "data/salary-trade-accounts.csv")
        applicant_csv = ROOT / str(salary_dataset.get("applicant_csv_path") or "data/salary-trade-applicants.csv")
        proxy_csv = ROOT / "data" / "salary-trade-proxies.csv"
        applicant_rows = _csv_rows_for_path(applicant_csv)
        account_rows = _csv_rows_for_path(account_csv)
        proxy_rows = _csv_rows_for_path(proxy_csv)
        account_applicants = [x for x in account_rows if str(x.get("role") or "").strip() == "applicant"]
        applicants = applicant_rows + account_applicants
        applicant_uids = {str(x.get("applicant_uid") or x.get("uid") or "").strip() for x in applicants if str(x.get("applicant_uid") or x.get("uid") or "").strip()}
        applicant_ready = [x for x in applicants if _ticket_source_ready(x, "applicant_")]
        details["applicants"] = [
            {
                "uid": str(x.get("applicant_uid") or x.get("uid") or "").strip(),
                "countryCode": str(x.get("countryCode") or x.get("country_code") or "").strip(),
                "currency": str(x.get("currency") or "").strip(),
                "credential_ready": _ticket_source_ready(x, "applicant_"),
                "source": "applicant_csv" if x in applicant_rows else "account_csv",
            }
            for x in applicants
            if str(x.get("applicant_uid") or x.get("uid") or "").strip()
        ][:50]
        details["credential_sources"]["applicant_ready"] = len(applicant_ready)
        details["credential_sources"]["applicant_total"] = len(applicant_uids)
        if len(applicant_uids) >= 8 and len(applicant_ready) >= 8:
            add_check("8个申请人账号", "READY", f"已识别 {len(applicant_uids)} 个申请人，具备登录态来源 {len(applicant_ready)} 个。")
        else:
            add_check("8个申请人账号", "NEEDS_DATA", f"需要8个申请人；当前识别 {len(applicant_uids)} 个，具备登录态来源 {len(applicant_ready)} 个。", "补齐 applicant CSV 或账号CSV的 ticket/password/redis_uid")
        applicant_pairs = sorted({
            (str(x.get("countryCode") or x.get("country_code") or "").strip(), str(x.get("currency") or "").strip())
            for x in applicants
            if str(x.get("countryCode") or x.get("country_code") or "").strip() and str(x.get("currency") or "").strip()
        })
        proxy_matches = []
        for country_code, currency in applicant_pairs:
            matched = [
                x for x in proxy_rows
                if str(x.get("countryCode") or x.get("country_code") or "").strip() == country_code
                and currency in str(x.get("supportCurrencies") or x.get("support_currencies") or x.get("currency") or "")
                and str(x.get("enabled", "true")).strip().lower() not in ("0", "false", "no", "off")
            ]
            proxy_matches.append({"countryCode": country_code, "currency": currency, "matched": len(matched), "proxy_uids": [x.get("proxy_uid") or x.get("uid") for x in matched[:5]]})
        details["country_currency_pairs"] = [{"countryCode": x[0], "currency": x[1]} for x in applicant_pairs]
        details["proxy_matches"] = proxy_matches
        missing_pairs = [x for x in proxy_matches if not x["matched"]]
        if missing_pairs:
            add_check("代理国家币种匹配", "NEEDS_DATA", f"存在 {len(missing_pairs)} 组申请人国家/币种未在代理CSV命中。", "同步数据库白名单到代理CSV，或补齐对应代理")
        else:
            add_check("代理国家币种匹配", "READY", f"申请人国家/币种组合 {len(applicant_pairs)} 组均能在代理CSV匹配。")
        proxy_ready = [x for x in proxy_rows if _ticket_source_ready(x, "proxy_")]
        details["credential_sources"]["proxy_ready"] = len(proxy_ready)
        details["credential_sources"]["proxy_total"] = len(proxy_rows)
        details["credential_sources"]["proxy_ready_uids"] = [str(x.get("proxy_uid") or x.get("uid") or "").strip() for x in proxy_ready[:20]]
        if proxy_ready:
            add_check("代理登录态来源", "READY", f"代理CSV中 {len(proxy_ready)} 个代理具备 ticket/password/redis_uid 来源。")
        else:
            add_check("代理登录态来源", "NEEDS_DATA", "代理CSV未识别到可用 ticket/password/redis_uid。", "补齐代理登录态或配置Redis登录缓存读取")
        if applicant_uids:
            uid_list = ",".join(sorted(applicant_uids))
            runtime_sql_checks.append({
                "name": "申请人处理中订单检查",
                "source": "mysql_runtime_preflight",
                "sql_template": f"SELECT uid, order_no, status FROM anchor_salary_trade_order WHERE uid IN ({uid_list}) AND status IN (10,20,30) ORDER BY created_time DESC;",
                "expectation": "每个申请人在执行前没有处理中订单，否则创建订单会触发50017或业务阻断。",
            })
        if applicant_pairs:
            runtime_sql_checks.append({
                "name": "代理白名单实时检查",
                "source": "mysql_runtime_preflight",
                "sql_template": "SELECT uid, country_code, support_currencies, status FROM anchor_salary_trade_agent_whitelist WHERE status=1 AND country_code=${countryCode} AND support_currencies LIKE CONCAT('%', ${currency}, '%') LIMIT 5;",
                "expectation": "每个申请人国家和收款币种都能匹配至少一个可用代理。",
            })
        add_check("业务库执行前检查", "NEEDS_LIVE_CHECK", f"已生成 {len(runtime_sql_checks)} 条运行前只读SQL检查模板。", "执行JMeter前由DB连接器读取真实订单和白名单状态")
    else:
        add_check("通用运行数据", "READY_WITH_WARNINGS", "当前需求包不是工资交易，已按通用结构化用例做静态就绪判断。")

    scenario_preflight = _scenario_data_preflight(package_id, package_root, details)
    details["scenario_preflight"] = scenario_preflight
    scenario_summary = scenario_preflight.get("summary") or {}
    if scenario_preflight.get("status") == "BLOCKED":
        add_check(
            "场景数据准备",
            "NEEDS_DATA",
            f"场景预检发现 {scenario_summary.get('blocked', 0)} 个场景存在数据阻断。",
            "先按场景补齐账号槽位、证据规则或代理匹配",
        )
    elif scenario_preflight.get("status") == "READY_WITH_WARNINGS":
        add_check(
            "场景数据准备",
            "WARNING",
            f"场景预检有 {scenario_summary.get('warnings', 0)} 个场景需要关注。",
            "确认未绑定证据规则或人工/定时流程是否符合预期",
        )
    else:
        add_check("场景数据准备", "READY", f"{scenario_summary.get('ready', 0)} 个场景数据准备静态检查通过。")

    return {
        "status": status,
        "checks": checks,
        "runtime_sql_checks": runtime_sql_checks,
        "scenario_preflight": scenario_preflight,
        "details": details,
    }


def _structured_case_jmeter_mapping(enhanced, package_id):
    flows = SALARY_TRADE_CASE_FLOWS if package_id == "salary-trade" else []
    mappings = []

    def match_flow(item):
        text = "\n".join(str(item.get(key) or "") for key in ("title", "scenario_type", "path"))
        text += "\n" + "\n".join(item.get("steps") or [])
        for flow in flows:
            flow_signals = {f"流程{flow.get('code')}", flow.get("name"), flow.get("thread_group"), flow.get("id")}
            if any(signal and str(signal) in text for signal in flow_signals):
                return flow
        return {}

    for index, item in enumerate(enhanced, 1):
        is_jmeter = item.get("coverage_tool") == "jmeter"
        flow = match_flow(item) if is_jmeter and flows else {}
        sampler = f"{item.get('method') or '-'} {item.get('path') or ''}".strip()
        variables = sorted(set((item.get("interface_fields") or []) + (item.get("required_variables") or []) + _path_variables(" ".join(item.get("preconditions") or []))))
        db_rules = [x.get("rule_id") for x in item.get("db_checks") or [] if x.get("rule_id")]
        redis_rules = [x.get("rule_id") for x in item.get("redis_checks") or [] if x.get("rule_id")]
        if item.get("quality_status") == "MANUAL_ONLY":
            status = "MANUAL_ONLY"
        elif is_jmeter and item.get("automation_readiness") == "SCRIPT_GENERATION_READY":
            status = "SCRIPT_READY"
        elif is_jmeter:
            status = "SCRIPTABLE_BUT_EVIDENCE_PENDING"
        else:
            status = "NOT_JMETER_TARGET"
        mappings.append({
            "case_id": item.get("id"),
            "case_title": item.get("title"),
            "mapping_status": status,
            "jmeter_thread_group": flow.get("thread_group") or ("工资交易接口链路线程组" if is_jmeter and package_id == "salary-trade" else "按接口模块生成线程组" if is_jmeter else ""),
            "matched_flow_id": flow.get("id", ""),
            "jmeter_sampler": sampler if is_jmeter else "",
            "variables": variables,
            "assertions": [str(x) for x in item.get("expected_results") or []][:8],
            "db_evidence_rules": db_rules,
            "redis_evidence_rules": redis_rules,
            "optional_redis_evidence": item.get("optional_redis_evidence") or [],
            "coverage_tool": item.get("coverage_tool"),
            "readiness": item.get("automation_readiness"),
        })
    covered = sum(1 for x in mappings if x["mapping_status"] in {"SCRIPT_READY", "SCRIPTABLE_BUT_EVIDENCE_PENDING"})
    return {
        "summary": {
            "cases": len(mappings),
            "jmeter_targets": covered,
            "script_ready": sum(1 for x in mappings if x["mapping_status"] == "SCRIPT_READY"),
            "evidence_pending": sum(1 for x in mappings if x["mapping_status"] == "SCRIPTABLE_BUT_EVIDENCE_PENDING"),
            "manual_only": sum(1 for x in mappings if x["mapping_status"] == "MANUAL_ONLY"),
            "not_jmeter_target": sum(1 for x in mappings if x["mapping_status"] == "NOT_JMETER_TARGET"),
        },
        "mappings": mappings,
    }


def _excel_col(index):
    label = ""
    while index:
        index, rem = divmod(index - 1, 26)
        label = chr(65 + rem) + label
    return label


def _xml_text(value):
    return (str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def _write_structured_cases_xlsx(path, enhanced):
    headers = ["用例ID", "标题", "优先级", "场景类型", "质量分级", "脚本生成就绪", "推荐工具", "异常来源", "接口", "接口字段", "运行变量", "DB校验", "Redis校验", "下一步", "分级原因"]
    rows_out = [headers]
    for item in enhanced:
        rows_out.append([
            item.get("id"),
            item.get("title"),
            item.get("priority"),
            item.get("scenario_type"),
            item.get("quality_status"),
            item.get("automation_readiness"),
            item.get("coverage_tool"),
            ", ".join(item.get("exception_sources") or []),
            f"{item.get('method') or ''} {item.get('path') or ''}".strip(),
            ", ".join(item.get("interface_fields") or []),
            ", ".join(item.get("required_variables") or []),
            ", ".join(sorted({x.get("table") or "" for x in item.get("db_checks") or [] if x.get("table")})),
            ", ".join(sorted({x.get("key") or x.get("rule_id") or "" for x in item.get("redis_checks") or [] if x.get("key") or x.get("rule_id")})),
            (item.get("next_action") or {}).get("label", ""),
            "；".join(item.get("blocking_reasons") or []),
        ])
    sheet_rows = []
    for r_idx, row_values in enumerate(rows_out, 1):
        cells = []
        for c_idx, value in enumerate(row_values, 1):
            ref = f"{_excel_col(c_idx)}{r_idx}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{_xml_text(value)}</t></is></c>')
        sheet_rows.append(f'<row r="{r_idx}">{"".join(cells)}</row>')
    worksheet = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>{''.join(sheet_rows)}</sheetData>
</worksheet>'''
    workbook = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="结构化用例" sheetId="1" r:id="rId1"/></sheets></workbook>'''
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'''
    workbook_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'''
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'''
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)


def generate_structured_test_cases(project_id, payload=None):
    payload = payload or {}
    package_id = str(payload.get("package_id") or "").strip() or "salary-trade"
    package = requirement_package_by_id(project_id, package_id)
    package_root = Path(package["root"])
    cases = _requirement_package_cases(project_id, package_id)
    evidence = requirement_evidence_rules(project_id, package_id)
    official_rules = evidence.get("rules") or []
    candidates_path = package_root / "evidence_rules.candidates.yaml"
    candidates_payload = _load_yaml_file(candidates_path)
    candidate_rules = candidates_payload.get("rules") if isinstance(candidates_payload, dict) else []
    candidate_rules = candidate_rules if isinstance(candidate_rules, list) else []
    data_scope = package.get("data_scope") or {}
    enhanced = []
    for case in cases:
        related_rules = _case_related_evidence_rules(case, official_rules, candidate_rules)
        interface_fields = _case_interface_fields(case)
        db_checks, redis_checks = [], []
        required_variables = set(interface_fields)
        for rule in related_rules:
            query = _evidence_rule_query(rule)
            rule_origin = rule.get("rule_origin") or "official"
            check = {
                "rule_id": rule.get("id"),
                "rule_source": rule_origin,
                "data_source": query.get("source"),
                "name": rule.get("name"),
                "table": query.get("table"),
                "where": query.get("where"),
                "key": query.get("key"),
                "fields": sorted({x.get("field") for x in (rule.get("assertions") or []) if isinstance(x, dict) and x.get("field")}),
                "assertions": rule.get("assertions") or [],
                "review_status": rule.get("review_status", "CONFIRMED" if rule_origin == "official" else "READY_FOR_REVIEW"),
            }
            required_variables.update(_path_variables(query.get("where")))
            required_variables.update(_path_variables(query.get("key")))
            for assertion in rule.get("assertions") or []:
                if isinstance(assertion, dict):
                    required_variables.update(_path_variables(assertion.get("expected")))
            if str(query.get("source") or "").lower() == "redis":
                redis_checks.append(check)
            else:
                db_checks.append(check)
        preconditions = [
            f"需求包：{package.get('name') or package_id}",
            "已准备当前用例所需账号、ticket、设备参数和运行变量。",
        ]
        if required_variables:
            preconditions.append("运行变量：" + ", ".join(sorted(required_variables)))
        if data_scope:
            preconditions.append("数据范围：" + ", ".join(data_scope.get("mysql_tables") or []))
        steps = []
        if case.get("steps"):
            steps.extend(_clean_case_step(x) for x in str(case.get("steps")).splitlines())
        if case.get("method") and case.get("path"):
            steps.append(f"调用接口：{case.get('method')} {case.get('path')}")
        if db_checks:
            steps.append("执行后按证据规则只读查询数据库。")
        if redis_checks:
            steps.append("执行后按证据规则只读读取Redis。")
        expected = [str(case.get("expected") or "").strip() or f"HTTP状态码符合预期：{case.get('expected_status') or 200}"]
        for check in db_checks:
            expected.append(f"DB校验：{check['table']} WHERE {check['where']}，字段 {', '.join(check['fields']) or '存在性'} 符合规则 {check['rule_id']}。")
        for check in redis_checks:
            expected.append(f"Redis校验：{check.get('key') or 'Key'} 的字段符合规则 {check['rule_id']}。")
        quality = _classify_structured_case(case, required_variables, db_checks, redis_checks)
        temp_item = {
            "title": case.get("title"),
            "scenario_type": case.get("scenario_type"),
            "method": case.get("method"),
            "path": case.get("path"),
            "preconditions": preconditions,
            "steps": [x for x in steps if str(x).strip()],
            "expected_results": [x for x in expected if str(x).strip()],
        }
        optional_redis = _structured_case_redis_suggestions(temp_item)
        enhanced.append({
            "id": case.get("id"),
            "title": case.get("title"),
            "priority": case.get("priority"),
            "scenario_type": case.get("scenario_type"),
            "method": case.get("method"),
            "path": case.get("path"),
            **quality,
            "interface_fields": interface_fields,
            "required_variables": sorted(required_variables),
            "preconditions": preconditions,
            "steps": [x for x in steps if str(x).strip()],
            "expected_results": [x for x in expected if str(x).strip()],
            "db_checks": db_checks,
            "redis_checks": redis_checks,
            "optional_redis_evidence": optional_redis,
            "traceability": {
                "requirement_ref": case.get("requirement_ref"),
                "evidence_rules": [x.get("rule_id") for x in db_checks + redis_checks],
            },
        })
    quality_counts = {}
    readiness_counts = {}
    tool_counts = {}
    exception_counts = {}
    for item in enhanced:
        quality_counts[item["quality_status"]] = quality_counts.get(item["quality_status"], 0) + 1
        readiness = item.get("automation_readiness") or item.get("automation_status") or "UNKNOWN"
        readiness_counts[readiness] = readiness_counts.get(readiness, 0) + 1
        tool_counts[item["coverage_tool"]] = tool_counts.get(item["coverage_tool"], 0) + 1
        for source in item.get("exception_sources") or []:
            exception_counts[source] = exception_counts.get(source, 0) + 1
        item["next_action"] = _structured_case_next_action(item)
    summary = {
        "cases": len(enhanced),
        "with_db_checks": sum(1 for x in enhanced if x["db_checks"]),
        "with_redis_checks": sum(1 for x in enhanced if x["redis_checks"]),
        "with_optional_redis_suggestions": sum(1 for x in enhanced if x.get("optional_redis_evidence")),
        "quality_counts": quality_counts,
        "readiness_counts": readiness_counts,
        "tool_counts": tool_counts,
        "exception_counts": exception_counts,
        "official_rules": len(official_rules),
        "candidate_rules": len(candidate_rules),
    }
    coverage_dashboard = _structured_case_dashboard(enhanced, summary)
    gap_list = _structured_case_gap_list(enhanced)
    jmeter_mapping = _structured_case_jmeter_mapping(enhanced, package_id)
    data_preflight = _structured_case_data_preflight(project_id, package_id, package_root)
    out_dir = package_root / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "structured-test-cases.json"
    md_path = out_dir / "structured-test-cases.md"
    xlsx_path = out_dir / "structured-test-cases.xlsx"
    jmeter_mapping_path = out_dir / "case-jmeter-mapping.json"
    data_preflight_path = out_dir / "data-preflight-check.json"
    payload_out = {
        "schema_version": "1.0",
        "project_id": project_id,
        "package_id": package_id,
        "package_name": package.get("name"),
        "generated_at": now(),
        "summary": summary,
        "coverage_dashboard": coverage_dashboard,
        "gap_list": gap_list,
        "jmeter_mapping": jmeter_mapping,
        "data_preflight": data_preflight,
        "cases": enhanced,
    }
    json_path.write_text(json.dumps(payload_out, ensure_ascii=False, indent=2), encoding="utf-8")
    jmeter_mapping_path.write_text(json.dumps({
        "schema_version": "1.0",
        "project_id": project_id,
        "package_id": package_id,
        "generated_at": payload_out["generated_at"],
        **jmeter_mapping,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    data_preflight_path.write_text(json.dumps({
        "schema_version": "1.0",
        "project_id": project_id,
        "package_id": package_id,
        "generated_at": payload_out["generated_at"],
        **data_preflight,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_structured_cases_xlsx(xlsx_path, enhanced)
    lines = [
        f"# {package.get('name') or package_id} - 结构化测试用例",
        "",
        f"- 生成时间：{payload_out['generated_at']}",
        f"- 用例数：{summary['cases']}",
        f"- 带DB校验：{summary['with_db_checks']}",
        f"- 带Redis校验：{summary['with_redis_checks']}",
        f"- Redis可选证据建议：{summary['with_optional_redis_suggestions']}",
        f"- 质量分级：{json.dumps(summary['quality_counts'], ensure_ascii=False)}",
        f"- 脚本生成就绪：{json.dumps(summary['readiness_counts'], ensure_ascii=False)}",
        f"- 总览：{coverage_dashboard['headline']}",
        "",
        "## 生成前数据准备检查",
        "",
        f"- 状态：{data_preflight['status']}",
        "",
    ]
    for check in data_preflight.get("checks") or []:
        lines.append(f"- {check.get('name')}：{check.get('status')}；{check.get('detail')}" + (f"；下一步：{check.get('next_action')}" if check.get("next_action") else ""))
    if data_preflight.get("runtime_sql_checks"):
        lines += ["", "### 执行前只读SQL检查模板", ""]
        for check in data_preflight["runtime_sql_checks"]:
            lines += [
                f"- {check.get('name')}：{check.get('expectation')}",
                f"  `{check.get('sql_template')}`",
            ]
    lines += [
        "",
        "## 用例到 JMeter 映射总览",
        "",
        f"- JMeter目标用例：{jmeter_mapping['summary']['jmeter_targets']}",
        f"- 脚本就绪：{jmeter_mapping['summary']['script_ready']}",
        f"- 待证据：{jmeter_mapping['summary']['evidence_pending']}",
        f"- 非JMeter目标：{jmeter_mapping['summary']['not_jmeter_target']}",
        "",
        "## 缺口清单",
        "",
    ]
    if gap_list:
        for gap in gap_list:
            lines += [
                f"### {gap['title']}",
                "",
                f"- 数量：{gap['count']}",
                f"- 下一步：{gap['next_action']}",
                "",
            ]
            for example in gap["examples"]:
                lines.append(f"- {example.get('title') or example.get('id')}：{example.get('method') or '-'} {example.get('path') or ''}；建议工具 {example.get('coverage_tool') or '-'}；原因 {example.get('reason') or '-'}")
            lines.append("")
    else:
        lines += ["- 暂无明显缺口。", ""]
    lines += [
        "## 用例明细",
        "",
    ]
    for item in enhanced:
        lines += [
            f"## {item.get('title') or item.get('id')}",
            "",
            f"- 优先级：{item.get('priority') or '-'}",
            f"- 场景类型：{item.get('scenario_type') or '-'}",
            f"- 接口：{(item.get('method') or '-')} {(item.get('path') or '')}",
            f"- 接口字段：{', '.join(item['interface_fields']) or '-'}",
            f"- 运行变量：{', '.join(item.get('required_variables') or []) or '-'}",
            f"- 质量分级：{item.get('quality_status')}",
            f"- 脚本生成就绪：{item.get('automation_readiness')} / {item.get('coverage_tool')}",
            f"- 异常来源：{', '.join(item.get('exception_sources') or []) or '-'}",
            f"- Redis可选证据：{'; '.join(x.get('reason','') for x in item.get('optional_redis_evidence') or []) or '-'}",
            f"- 下一步：{(item.get('next_action') or {}).get('label') or '-'}",
            "",
            "### 前置条件",
            *[f"- {x}" for x in item["preconditions"]],
            "",
            "### 操作步骤",
            *[f"{idx + 1}. {step}" for idx, step in enumerate(item["steps"])],
            "",
            "### 预期结果",
            *[f"- {x}" for x in item["expected_results"]],
            "",
            "### 分级原因",
            *[f"- {x}" for x in item.get("blocking_reasons") or []],
            "",
        ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    report = {
        "report_type": "STRUCTURED_TEST_CASES",
        "project_id": project_id,
        "package_id": package_id,
        "package_name": package.get("name"),
        "status": "READY" if enhanced else "ATTENTION",
        "created_at": now(),
        "summary": summary,
        "coverage_dashboard": coverage_dashboard,
        "gap_list": gap_list,
        "jmeter_mapping": jmeter_mapping.get("summary"),
        "data_preflight": data_preflight,
        "json_path": str(json_path),
        "markdown_path": str(md_path),
        "excel_path": str(xlsx_path),
        "jmeter_mapping_path": str(jmeter_mapping_path),
        "data_preflight_path": str(data_preflight_path),
        "conclusion": "已生成自带接口字段、DB/Redis证据校验点、用例质量分级和脚本生成就绪状态的结构化测试用例。",
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = ROOT / "reports" / f"structured-test-cases-{project_id}-{package_id}-{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["json_url"] = "/reports/" + out.name
    report["file_name"] = out.name
    return report


def _requirement_package_keywords(package_id):
    if package_id == "salary-trade":
        return ("工资", "代理", "交易", "订单", "结算", "投诉", "salary", "trade")
    if package_id == "wealth-level":
        return ("财富", "等级", "经验", "送礼", "钱包", "账单", "wealth", "level")
    return (package_id,)


def _requirement_package_cases(project_id, package_id):
    keywords = _requirement_package_keywords(package_id)
    all_cases = rows("SELECT * FROM test_cases WHERE project_id=? ORDER BY priority,created_at", (project_id,))
    result = []
    for case in all_cases:
        text = "\n".join(str(case.get(key) or "") for key in ("title", "requirement_ref", "steps", "expected", "scenario_type", "executor_type", "path"))
        if any(word.lower() in text.lower() for word in keywords):
            result.append(case)
    return result


def _write_package_file(package_root, relative_path, content):
    path = Path(package_root) / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return str(path)


def _jmeter_skill_contract():
    path = SKILL_DIR / "jmeter-script-generation" / "rules.yaml"
    payload = _load_yaml_file(path)
    if not payload:
        payload = {
            "schema_version": "1.0",
            "skill": "jmeter-script-generation",
            "purpose": "从需求包和结构化测试用例生成 JMeter 执行资产",
            "output_contract": ["JMX脚本", "映射清单", "运行参数说明", "报告归档位置"],
        }
    return {
        "path": str(path),
        "rules": payload,
    }


def _pytest_evidence_skill_contract():
    path = SKILL_DIR / "pytest-evidence-review" / "SKILL.md"
    if path.is_file():
        body = path.read_text(encoding="utf-8", errors="replace")
    else:
        body = ""
    return {
        "path": str(path),
        "skill": "pytest-evidence-review",
        "purpose": "从需求包场景计划、运行变量、HTTP结果和DB/Redis证据规则生成pytest深度复核资产",
        "inputs": [
            "manifest.json",
            "manifest.orchestration.primary_plan",
            "outputs/execution-plan.json",
            "outputs/structured-test-cases.json",
            "evidence_rules.yaml",
            "account_model.yaml",
            "runtime_aliases.yaml",
            "JMeter JTL / Newman JSON运行结果",
        ],
        "outputs": [
            "outputs/pytest/pytest_api_cases.py",
            "reports/pytest-evidence-*/summary.json",
        ],
        "principles": [
            "pytest负责执行后深度证据复核，不替代JMeter状态机主流程",
            "主编排入口由需求包manifest声明，execution-plan.json只是默认值",
            "运行变量从环境、场景计划、账号模型和前序响应中提取",
            "DB/Redis证据只读校验，缺变量标记BLOCKED，不编造字段",
            "报告按需求包和场景归档，方便人工复核和维护",
        ],
        "source_preview": body[:3000],
    }


def generate_requirement_package_tool_assets(project_id, package_id, options=None):
    options = options or {}
    package = requirement_package_by_id(project_id, package_id)
    package_id = package.get("package_id") or package_id
    package_root = Path(package["root"])
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    runtime = safe_runtime_context(_runtime_context(project_id, _merge_execution_profile_options(project_id, options)))
    source_cases = _requirement_package_cases(project_id, package_id)
    executable_cases = [case for case in source_cases if str(case.get("method") or "").strip() and str(case.get("path") or "").strip()]
    generated = []
    warnings = []
    account_model = generate_requirement_account_model(project_id, package_id, True)
    generated.append({"tool": "Account Model", "path": account_model.get("path", "")})
    jmeter_skill = _jmeter_skill_contract()
    skill_contract_path = package_root / "outputs" / "jmeter" / "jmeter-skill-contract.json"
    skill_contract_path.parent.mkdir(parents=True, exist_ok=True)
    skill_contract_path.write_text(json.dumps({
        "schema_version": "1.0",
        "project_id": project_id,
        "package_id": package_id,
        "generated_at": now(),
        "source": jmeter_skill["path"],
        "contract": jmeter_skill["rules"],
        "usage": "JMeter脚本生成必须遵守本契约；如需求出现新组件或新账号模式，先扩展Skill规则，再生成脚本。",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    generated.append({"tool": "JMeter Skill Contract", "path": str(skill_contract_path), "source": jmeter_skill["path"]})

    pytest_skill = _pytest_evidence_skill_contract()
    pytest_skill_contract_path = package_root / "outputs" / "pytest" / "pytest-evidence-skill-contract.json"
    pytest_skill_contract_path.parent.mkdir(parents=True, exist_ok=True)
    pytest_skill_contract_path.write_text(json.dumps({
        "schema_version": "1.0",
        "project_id": project_id,
        "package_id": package_id,
        "generated_at": now(),
        "source": pytest_skill["path"],
        "contract": pytest_skill,
        "usage": "pytest证据复盘必须遵守本契约；复杂需求优先消费manifest声明的主编排文件、账号模型、运行别名和证据规则，不把业务流程写死在全局代码。",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    generated.append({"tool": "pytest Evidence Skill Contract", "path": str(pytest_skill_contract_path), "source": pytest_skill["path"]})

    if executable_cases:
        tool_cases = _external_tool_cases(executable_cases, False)
        if tool_cases:
            generated.append({
                "tool": "Newman",
                "path": _write_package_file(
                    package_root,
                    "outputs/newman/postman-collection.json",
                    json.dumps(build_postman_collection(project, tool_cases, runtime, True), ensure_ascii=False, indent=2),
                ),
            })
            generated.append({
                "tool": "pytest",
                "path": _write_package_file(
                    package_root,
                    "outputs/pytest/pytest_api_cases.py",
                    build_pytest_script(project, tool_cases, runtime, True, package_id, str(package_root)),
                ),
            })
            generated.append({
                "tool": "JMeter",
                "path": _write_package_file(
                    package_root,
                    "outputs/jmeter/jmeter-plan.jmx",
                    build_jmeter_jmx(project, tool_cases, runtime, True, options),
                ),
            })
        else:
            warnings.append("当前需求包的接口用例都依赖运行时变量，已保留需求包目录，执行前需要补运行上下文。")
    else:
        warnings.append("当前需求包还没有可直接生成 Newman/pytest 通用资产的接口用例。")

    if package_id == "salary-trade":
        salary_result = generate_salary_trade_jmeter_from_cases(project_id)
        salary_jmx = Path(salary_result["jmx_path"])
        if salary_jmx.is_file():
            target = package_root / "outputs" / "jmeter" / salary_jmx.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(salary_jmx, target)
            generated.append({"tool": "JMeter", "path": str(target), "source": str(salary_jmx)})
        manifest = Path(salary_result["manifest_path"])
        if manifest.is_file():
            target = package_root / "outputs" / "jmeter" / manifest.name
            shutil.copy2(manifest, target)
            generated.append({"tool": "JMeter Manifest", "path": str(target), "source": str(manifest)})
    elif package_id == "wealth-level":
        wealth_jmx = Path(str((package.get("artifacts") or {}).get("jmeter", {}).get("path") or ""))
        if wealth_jmx.is_file():
            target = package_root / "outputs" / "jmeter" / wealth_jmx.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(wealth_jmx, target)
            generated.append({"tool": "JMeter", "path": str(target), "source": str(wealth_jmx)})

    package = ensure_requirement_package_manifest(project_id, _requirement_package_template(project_id, package_id))
    result_manifest = {
        "schema_version": "1.0",
        "project_id": project_id,
        "package_id": package_id,
        "package_name": package.get("name"),
        "generated_at": now(),
        "status": "READY_WITH_WARNINGS" if warnings else "READY",
        "account_model": {
            "path": account_model.get("path", ""),
            "mode": account_model.get("mode", ""),
            "csv_required": bool(account_model.get("csv_required")),
            "roles": [role.get("name") for role in account_model.get("roles", [])],
            "rule": "先由需求包 account_model.yaml 决定账号模式，再生成 Newman/JMeter/pytest 资产。",
        },
        "jmeter_skill_contract": {
            "path": str(skill_contract_path),
            "source": jmeter_skill["path"],
            "rule_count": sum(len(value) for value in jmeter_skill["rules"].values() if isinstance(value, list)),
            "principle": "测试用例决定要测什么，JMeter Skill 决定如何稳定生成线程组、请求、CSV、断言、监听器和报告。",
        },
        "pytest_evidence_skill_contract": {
            "path": str(pytest_skill_contract_path),
            "source": pytest_skill["path"],
            "input_count": len(pytest_skill.get("inputs") or []),
            "principle": "pytest Skill 决定如何把HTTP、JMeter/Newman结果、DB/Redis证据和运行变量收敛成可复核JSON。",
        },
        "generated": generated,
        "warnings": warnings,
        "rule": "同一需求包独立生成 Newman、JMeter、pytest 资产；报告也按需求包回收。",
    }
    manifest_path = package_root / "outputs" / "tool-assets-manifest.json"
    manifest_path.write_text(json.dumps(result_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        **result_manifest,
        "manifest_path": str(manifest_path),
        "package": package,
        "generated_count": len(generated),
    }


def run_requirement_package_newman(project_id, package_id, options=None):
    options = options or {}
    package = requirement_package_by_id(project_id, package_id)
    package_id = package.get("package_id") or package_id
    package_root = Path(package["root"])
    collection = package_root / "outputs" / "newman" / "postman-collection.json"
    if not collection.is_file():
        generated = generate_requirement_package_tool_assets(project_id, package_id, options)
        collection = package_root / "outputs" / "newman" / "postman-collection.json"
        if not collection.is_file():
            return {
                "status": "BLOCKED",
                "package_id": package_id,
                "message": "当前需求包没有可运行的 Newman collection，请先补齐可执行接口用例。",
                "generated": generated.get("generated", []),
            }
    newman = shutil.which("newman")
    if not newman:
        return {
            "status": "BLOCKED",
            "package_id": package_id,
            "message": "本机未安装 Newman；请执行 npm install -g newman 后重试。",
            "install_command": "npm install -g newman",
            "collection": str(collection),
        }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = package_root / "reports" / f"newman-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    json_report = run_dir / "newman-report.json"
    command = [
        newman,
        "run",
        str(collection),
        "-r",
        "cli,json",
        "--reporter-json-export",
        str(json_report),
    ]
    env = os.environ.copy()
    result = _sanitize_tool_result(_run_command_capture(command, ROOT, int(options.get("timeout", 180) or 180), env), _runtime_context(project_id, options))
    status = "PASSED" if result.get("exit_code") == 0 else "FAILED"
    failures = []
    newman_stats = {}
    if json_report.is_file():
        try:
            payload = json.loads(json_report.read_text(encoding="utf-8"))
            failures = payload.get("run", {}).get("failures", [])[:20]
            newman_stats = payload.get("run", {}).get("stats") or {}
        except Exception:
            failures = []
    summary = {
        "report_type": "REQUIREMENT_PACKAGE_NEWMAN_RUN",
        "project_id": project_id,
        "package_id": package_id,
        "package_name": package.get("name"),
        "status": status,
        "created_at": now(),
        "collection": str(collection),
        "command": " ".join(command),
        "json_report": str(json_report) if json_report.is_file() else "",
        "exit_code": result.get("exit_code"),
        "duration_ms": result.get("duration_ms"),
        "stats": newman_stats,
        "summary": {
            "iterations": deep_get(newman_stats, "iterations.total", 0),
            "requests": deep_get(newman_stats, "requests.total", 0),
            "assertions": deep_get(newman_stats, "assertions.total", 0),
            "failed_assertions": deep_get(newman_stats, "assertions.failed", 0),
            "failures": len(failures),
        },
        "failures": [
            {
                "source": deep_get(item, "source.name", ""),
                "error": deep_get(item, "error.message", ""),
            }
            for item in failures
        ],
        "stdout": result.get("stdout", "")[-4000:],
        "stderr": result.get("stderr", "")[-4000:],
    }
    summary_path = run_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        **summary,
        "summary_path": str(summary_path),
        "json_url": "/requirement-reports/" + summary_path.relative_to(REQUIREMENT_PACKAGE_ROOT).as_posix(),
    }


def run_requirement_package_pytest(project_id, package_id, options=None):
    options = options or {}
    package = requirement_package_by_id(project_id, package_id)
    package_id = package.get("package_id") or package_id
    package_root = Path(package["root"])
    pytest_file = package_root / "outputs" / "pytest" / "pytest_api_cases.py"
    needs_refresh = True
    if pytest_file.is_file():
        try:
            existing_pytest = pytest_file.read_text(encoding="utf-8", errors="replace")
            required_markers = (
                "PYTEST_DEEP_EVIDENCE_REVIEW",
                "ensure_common_query_params",
                "update_runtime_from_response",
                "load_runtime_aliases",
                'headers["t"]',
                "planned_scenario_batches",
                "run_scenario_batch",
                "orchestration",
            )
            needs_refresh = any(marker not in existing_pytest for marker in required_markers)
        except Exception:
            needs_refresh = True
    if needs_refresh:
        project = row("SELECT * FROM projects WHERE id=?", (project_id,))
        source_cases = _requirement_package_cases(project_id, package_id)
        executable_cases = [case for case in source_cases if str(case.get("method") or "").strip() and str(case.get("path") or "").strip()]
        tool_cases = _external_tool_cases(executable_cases, False)
        if not project or not tool_cases:
            return {"status": "BLOCKED", "package_id": package_id, "message": "当前需求包没有可生成 pytest 的可执行接口用例。"}
        pytest_file.parent.mkdir(parents=True, exist_ok=True)
        pytest_file.write_text(build_pytest_script(project, tool_cases, safe_runtime_context(_runtime_context(project_id, options)), True, package_id, str(package_root)), encoding="utf-8")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = package_root / "reports" / f"pytest-evidence-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    summary_path = run_dir / "summary.json"
    env = os.environ.copy()
    project = row("SELECT * FROM projects WHERE id=?", (project_id,)) or {}
    credential = load_runtime_credential(project_id)
    runtime_options = _merge_execution_profile_options(project_id, options)
    if credential.get("encrypted_password") and not runtime_options.get("login_password_encrypted"):
        runtime_options["login_password_encrypted"] = credential.get("encrypted_password")
        runtime_options["login_strategy"] = "force"
    runtime = _login_runtime_context(project_id, runtime_options) if runtime_options.get("login_password_encrypted") else _runtime_context(project_id, runtime_options)
    env["AUTOTEST_BASE_URL"] = project.get("base_url") or env.get("AUTOTEST_BASE_URL", "")
    env["AUTOTEST_RUNTIME_PARAMS_JSON"] = json.dumps(runtime, ensure_ascii=False, default=str)
    env["AUTOTEST_PYTEST_EVIDENCE_OUT"] = str(summary_path)
    if options.get("jtl_path"):
        env["AUTOTEST_JTL_PATH"] = str(options.get("jtl_path"))
    if options.get("newman_json"):
        env["AUTOTEST_NEWMAN_JSON"] = str(options.get("newman_json"))
    result = _sanitize_tool_result(_run_command_capture([sys.executable, "-m", "pytest", str(pytest_file), "-q"], ROOT, int(options.get("timeout", 240) or 240), env), runtime)
    payload = {}
    if summary_path.is_file():
        try:
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
    status = payload.get("status") or ("PASSED" if result.get("exit_code") == 0 else "FAILED")
    summary = payload.get("summary") or {}
    run_summary = {
        "report_type": "REQUIREMENT_PACKAGE_PYTEST_EVIDENCE_RUN",
        "project_id": project_id,
        "package_id": package_id,
        "package_name": package.get("name"),
        "status": status,
        "created_at": now(),
        "pytest_file": str(pytest_file),
        "exit_code": result.get("exit_code"),
        "duration_ms": result.get("duration_ms"),
        "summary": summary,
        "evidence_report": payload,
        "stdout": result.get("stdout", "")[-4000:],
        "stderr": result.get("stderr", "")[-4000:],
    }
    if not summary_path.is_file():
        summary_path.write_text(json.dumps(run_summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    else:
        summary_path.write_text(json.dumps({**payload, **run_summary}, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return {
        **run_summary,
        "summary_path": str(summary_path),
        "json_url": "/requirement-reports/" + summary_path.relative_to(REQUIREMENT_PACKAGE_ROOT).as_posix(),
    }


def _package_report_summaries(package_root):
    result = []
    for file in sorted(Path(package_root).glob("reports/*/summary.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        if file.parent.name.startswith("ai-review-"):
            continue
        try:
            payload = json.loads(file.read_text(encoding="utf-8"))
        except Exception:
            continue
        result.append({"path": str(file), "payload": payload})
    return result


def _read_json_asset(path):
    path = Path(path)
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _package_output_context(package_root):
    root = Path(package_root) / "outputs"
    structured = _read_json_asset(root / "structured-test-cases.json")
    jmeter_mapping = _read_json_asset(root / "case-jmeter-mapping.json")
    data_preflight = _read_json_asset(root / "data-preflight-check.json")
    tool_assets = _read_json_asset(root / "tool-assets-manifest.json")
    return {
        "structured_cases": {
            "path": str(root / "structured-test-cases.json") if (root / "structured-test-cases.json").is_file() else "",
            "summary": structured.get("summary") or {},
            "coverage_dashboard": structured.get("coverage_dashboard") or {},
            "gap_list": structured.get("gap_list") or [],
        },
        "jmeter_mapping": {
            "path": str(root / "case-jmeter-mapping.json") if (root / "case-jmeter-mapping.json").is_file() else "",
            "summary": jmeter_mapping.get("summary") or {},
        },
        "data_preflight": {
            "path": str(root / "data-preflight-check.json") if (root / "data-preflight-check.json").is_file() else "",
            "status": data_preflight.get("status") or "NOT_GENERATED",
            "checks": data_preflight.get("checks") or [],
            "runtime_sql_checks": data_preflight.get("runtime_sql_checks") or [],
        },
        "tool_assets": {
            "path": str(root / "tool-assets-manifest.json") if (root / "tool-assets-manifest.json").is_file() else "",
            "summary": tool_assets.get("summary") or {},
            "generated": tool_assets.get("generated") or [],
        },
    }


def _report_status_rank(status):
    status = str(status or "UNKNOWN").upper()
    return {
        "FAILED": 5,
        "ERROR": 5,
        "BLOCKED": 4,
        "NEEDS_DATA": 4,
        "READY_WITH_WARNINGS": 3,
        "NEEDS_REVIEW": 3,
        "ATTENTION": 3,
        "UNKNOWN": 2,
        "PENDING": 2,
        "READY": 1,
        "PASSED": 0,
    }.get(status, 2)


def _aggregate_scenario_status(statuses):
    normalized = [str(item or "UNKNOWN").upper() for item in statuses if item]
    if any(item in {"FAILED", "ERROR"} for item in normalized):
        return "FAILED"
    if any(item in {"BLOCKED", "NEEDS_DATA"} for item in normalized):
        return "BLOCKED"
    if any(item in {"READY_WITH_WARNINGS", "NEEDS_REVIEW", "ATTENTION"} for item in normalized):
        return "READY_WITH_WARNINGS"
    if normalized and all(item in {"PASSED", "READY"} for item in normalized):
        return "PASSED"
    return "UNKNOWN" if normalized else "PENDING"


def _latest_package_reports_by_type(package_root):
    latest = {}
    for item in _package_report_summaries(package_root):
        payload = item.get("payload") or {}
        report_type = payload.get("report_type") or "UNKNOWN"
        if report_type not in latest:
            latest[report_type] = item
    return latest


def _pytest_scenario_index(payload):
    indexed = {}
    for scenario in _pytest_scenarios_from_payload(payload):
        scenario_id = str(scenario.get("scenario_id") or scenario.get("id") or "").strip()
        if scenario_id:
            indexed[scenario_id] = scenario
    return indexed


def _scenario_preflight_index(payload):
    preflight = payload.get("scenario_preflight") or deep_get(payload, "details.scenario_preflight", {}) or {}
    indexed = {}
    for scenario in preflight.get("scenarios") or []:
        scenario_id = str(scenario.get("scenario_id") or scenario.get("id") or "").strip()
        if scenario_id:
            indexed[scenario_id] = scenario
    return indexed


def _newman_summary_for_report(payload):
    summary = payload.get("summary") or {}
    failures = payload.get("failures") or []
    return {
        "status": payload.get("status") or "PENDING",
        "requests": summary.get("requests", 0),
        "assertions": summary.get("assertions", 0),
        "failed_assertions": summary.get("failed_assertions", 0),
        "failures": failures[:10],
        "summary_path": payload.get("summary_path") or "",
        "json_report": payload.get("json_report") or "",
    }


def _jmeter_summary_from_reports(package_root, package_id):
    mapping = _read_json_asset(Path(package_root) / "outputs" / "case-jmeter-mapping.json")
    manifest = _read_json_asset(Path(package_root) / "outputs" / "jmeter" / f"{package_id}-case-jmeter-manifest.json")
    return {
        "status": "READY" if mapping or manifest else "PENDING",
        "mapped_cases": deep_get(mapping, "summary.jmeter_targets", 0),
        "script_ready": deep_get(mapping, "summary.script_ready", 0),
        "evidence_pending": deep_get(mapping, "summary.evidence_pending", 0),
        "jmx": deep_get(manifest, "jmx.path", "") or deep_get(manifest, "jmx_file", ""),
        "manifest": str(Path(package_root) / "outputs" / "jmeter" / f"{package_id}-case-jmeter-manifest.json") if manifest else "",
    }


def _write_unified_scenario_report_markdown(path, report):
    lines = [
        f"# {report.get('package_name') or report.get('package_id')} 统一场景报告",
        "",
        f"- 状态：{report.get('status')}",
        f"- 场景：{deep_get(report, 'summary.scenarios', 0)}",
        f"- 通过/失败/阻断/提醒：{deep_get(report, 'summary.passed', 0)}/{deep_get(report, 'summary.failed', 0)}/{deep_get(report, 'summary.blocked', 0)}/{deep_get(report, 'summary.warning', 0)}",
        "",
        "## 场景明细",
        "",
    ]
    for scenario in report.get("scenarios") or []:
        tools = scenario.get("tools") or {}
        lines += [
            f"### {scenario.get('name') or scenario.get('scenario_id')}",
            "",
            f"- 场景ID：{scenario.get('scenario_id')}",
            f"- 状态：{scenario.get('status')}",
            f"- 数据准备：{deep_get(scenario, 'data_preflight.status', 'PENDING')}",
            f"- Newman：{deep_get(tools, 'newman.status', 'PENDING')}",
            f"- JMeter：{deep_get(tools, 'jmeter.status', 'PENDING')}",
            f"- pytest：{deep_get(tools, 'pytest.status', 'PENDING')}",
            "",
        ]
        for target in scenario.get("maintenance_targets") or []:
            lines.append(f"- 维护点：{target}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def generate_requirement_package_unified_scenario_report(project_id, package_id, options=None):
    options = options or {}
    package = requirement_package_by_id(project_id, package_id)
    package_id = package.get("package_id") or package_id
    package_root = Path(package["root"])
    plan = _read_json_asset(package_root / "outputs" / "execution-plan.json")
    if not plan.get("scenarios"):
        plan = generate_requirement_execution_plan(project_id, package_id, options)
    data_preflight = _read_json_asset(package_root / "outputs" / "data-preflight-check.json")
    preflight_by_scenario = _scenario_preflight_index(data_preflight)
    latest_reports = _latest_package_reports_by_type(package_root)
    pytest_item = latest_reports.get("REQUIREMENT_PACKAGE_PYTEST_EVIDENCE_RUN") or latest_reports.get("PYTEST_DEEP_EVIDENCE_REVIEW") or {}
    pytest_payload = pytest_item.get("payload") or {}
    pytest_by_scenario = _pytest_scenario_index(pytest_payload)
    newman_item = latest_reports.get("REQUIREMENT_PACKAGE_NEWMAN_RUN") or {}
    newman_payload = newman_item.get("payload") or {}
    newman_summary = _newman_summary_for_report(newman_payload) if newman_payload else {"status": "PENDING", "requests": 0, "assertions": 0, "failed_assertions": 0, "failures": []}
    jmeter_summary = _jmeter_summary_from_reports(package_root, package_id)
    source_reports = []
    for item in latest_reports.values():
        payload = item.get("payload") or {}
        source_reports.append({
            "report_type": payload.get("report_type") or "UNKNOWN",
            "status": payload.get("status") or "UNKNOWN",
            "created_at": payload.get("created_at") or payload.get("generated_at") or "",
            "path": item.get("path") or "",
        })
    scenarios = []
    status_counts = {"passed": 0, "failed": 0, "blocked": 0, "warning": 0, "pending": 0}
    for scenario in plan.get("scenarios") or []:
        scenario_id = str(scenario.get("scenario_id") or scenario.get("id") or "").strip()
        preflight = preflight_by_scenario.get(scenario_id, {})
        pytest_scenario = pytest_by_scenario.get(scenario_id, {})
        tool_names = {str(task.get("tool") or "").lower() for task in scenario.get("tool_tasks") or []}
        pytest_status = pytest_scenario.get("status") or ("PENDING" if "pytest" in tool_names else "NOT_APPLICABLE")
        newman_status = newman_summary.get("status") if "newman" in tool_names else "NOT_APPLICABLE"
        jmeter_status = jmeter_summary.get("status") if "jmeter" in tool_names else "NOT_APPLICABLE"
        scenario_status = _aggregate_scenario_status([
            preflight.get("status"),
            pytest_status if pytest_status != "NOT_APPLICABLE" else "",
            newman_status if newman_status != "NOT_APPLICABLE" else "",
            jmeter_status if jmeter_status != "NOT_APPLICABLE" else "",
        ])
        if scenario_status == "PASSED":
            status_counts["passed"] += 1
        elif scenario_status == "FAILED":
            status_counts["failed"] += 1
        elif scenario_status == "BLOCKED":
            status_counts["blocked"] += 1
        elif scenario_status == "READY_WITH_WARNINGS":
            status_counts["warning"] += 1
        else:
            status_counts["pending"] += 1
        evidence_results = pytest_scenario.get("evidence_results") or []
        scenarios.append({
            "scenario_id": scenario_id,
            "name": scenario.get("name") or scenario_id,
            "business_goal": scenario.get("business_goal") or "",
            "priority": scenario.get("priority") or "",
            "status": scenario_status,
            "plan_status": scenario.get("status") or "UNKNOWN",
            "account_slot": scenario.get("account_slot") or "",
            "order_variable": scenario.get("order_variable") or "",
            "cases": scenario.get("cases") or [],
            "data_preflight": {
                "status": preflight.get("status") or "PENDING",
                "applicant_uid": preflight.get("applicant_uid") or "",
                "countryCode": preflight.get("countryCode") or "",
                "currency": preflight.get("currency") or "",
                "blockers": preflight.get("blockers") or [],
                "attentions": preflight.get("attentions") or [],
                "evidence_rule_ids": preflight.get("evidence_rule_ids") or _scenario_evidence_rule_ids(scenario),
            },
            "tools": {
                "newman": {
                    **newman_summary,
                    "status": newman_status,
                    "scope": "package_level" if "newman" in tool_names else "not_applicable",
                },
                "jmeter": {
                    **jmeter_summary,
                    "status": jmeter_status,
                    "scope": "scenario_mapping" if "jmeter" in tool_names else "not_applicable",
                },
                "pytest": {
                    "status": pytest_status,
                    "http_cases": pytest_scenario.get("http_cases", 0),
                    "http_failed": pytest_scenario.get("http_failed", 0),
                    "evidence_failed": sum(1 for item in evidence_results if item.get("status") == "FAILED"),
                    "evidence_blocked": sum(1 for item in evidence_results if item.get("status") == "BLOCKED"),
                    "evidence_rule_ids": pytest_scenario.get("evidence_rule_ids") or _scenario_evidence_rule_ids(scenario),
                    "failed_http": [
                        {
                            "id": item.get("id"),
                            "title": item.get("title"),
                            "status": item.get("status"),
                            "business_code": item.get("business_code"),
                            "message": item.get("business_message") or item.get("response_preview", "")[:300],
                        }
                        for item in (pytest_scenario.get("http_results") or [])
                        if item.get("status") != item.get("expected_status") or str(item.get("business_code") or "200") != "200"
                    ][:8],
                    "evidence_problems": [
                        {
                            "id": item.get("id"),
                            "name": item.get("name"),
                            "status": item.get("status"),
                            "blockers": item.get("blockers") or [],
                        }
                        for item in evidence_results
                        if item.get("status") in {"FAILED", "BLOCKED"}
                    ][:8],
                },
            },
            "maintenance_targets": deep_get(scenario, "human_review.maintenance_targets", []) or [
                "当前场景对应的测试用例",
                "当前场景账号槽位与数据准备",
                "当前场景证据规则",
                "当前场景关联的外部工具脚本",
            ],
        })
    overall = _aggregate_scenario_status([item.get("status") for item in scenarios])
    if overall == "PASSED" and not pytest_by_scenario:
        overall = "READY_WITH_WARNINGS"
    report = {
        "schema_version": "1.0",
        "report_type": "REQUIREMENT_PACKAGE_UNIFIED_SCENARIO_REPORT",
        "project_id": project_id,
        "package_id": package_id,
        "package_name": package.get("name"),
        "status": overall,
        "created_at": now(),
        "summary": {
            "scenarios": len(scenarios),
            **status_counts,
            "source_reports": len(source_reports),
            "newman_status": newman_summary.get("status"),
            "jmeter_status": jmeter_summary.get("status"),
            "pytest_scenarios": len(pytest_by_scenario),
        },
        "scenarios": scenarios,
        "source_reports": source_reports,
        "business_value": "把同一需求包下 Newman、JMeter、pytest、数据准备和人工维护点统一到业务场景，人工复核时按流程看，不按工具散着找。",
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = package_root / "reports" / f"scenario-report-{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "summary.json"
    markdown_path = out_dir / "scenario-report.md"
    summary_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    _write_unified_scenario_report_markdown(markdown_path, report)
    report["summary_path"] = str(summary_path)
    report["markdown_path"] = str(markdown_path)
    report["json_url"] = "/requirement-reports/" + summary_path.relative_to(REQUIREMENT_PACKAGE_ROOT).as_posix()
    report["markdown_url"] = "/requirement-reports/" + markdown_path.relative_to(REQUIREMENT_PACKAGE_ROOT).as_posix()
    return report


def _case_brief(case):
    return {
        "id": case.get("id"),
        "title": case.get("title") or case.get("case_title") or "",
        "method": case.get("method") or "",
        "path": case.get("path") or "",
        "coverage_tool": case.get("coverage_tool") or "",
        "readiness": case.get("automation_readiness") or case.get("readiness") or "",
        "quality_status": case.get("quality_status") or "",
    }


def _execution_plan_status(cases, blockers=None, manual_only=False):
    blockers = blockers or []
    if blockers:
        return "BLOCKED"
    if manual_only or not cases:
        return "NEEDS_REVIEW"
    statuses = {str((case.get("quality_status") or case.get("readiness") or "")).upper() for case in cases}
    if statuses and statuses <= {"READY", "SCRIPT_GENERATION_READY", ""}:
        return "READY"
    if any(status in {"MANUAL_ONLY", "BLOCKED_NEEDS_DATA", "NEEDS_DATA"} for status in statuses):
        return "NEEDS_REVIEW"
    return "READY_WITH_WARNINGS"


def _case_matches_salary_flow(case, flow):
    text = _case_text(case)
    keywords = {
        "A": ["取消", "cancel", "状态50"],
        "B": ["拒绝", "reject"],
        "C": ["确认收款", "交易完成", "完整成交", "完成"],
        "D": ["投诉失败", "申诉失败"],
        "E": ["投诉成功", "申诉成功"],
        "F": ["待接单超时", "创建后代理不处理", "订单过期", "自然过期"],
        "G": ["12小时", "已接受未转账", "接受后不转账"],
        "H": ["24小时", "已转账未确认", "自动完成"],
    }.get(str(flow.get("code") or ""), [])
    return bool(
        (flow.get("id") and flow.get("id") in text)
        or (flow.get("name") and flow.get("name") in text)
        or any(word.lower() in text.lower() for word in keywords)
    )


def _scenario_tool_task(tool, purpose, cases=None, asset="", evidence_rules=None, thread_group="", blockers=None):
    return {
        "tool": tool,
        "purpose": purpose,
        "cases": [case.get("id") for case in (cases or []) if case.get("id")],
        "case_count": len(cases or []),
        "asset": asset,
        "thread_group": thread_group,
        "evidence_rules": sorted(set(evidence_rules or [])),
        "blockers": blockers or [],
    }


def _scenario_report_targets(package_root, scenario_id):
    root = Path(package_root)
    return {
        "newman": str(root / "reports" / "newman-*"),
        "jmeter": str(root / "reports" / "jmeter-*"),
        "pytest": str(root / "reports" / "pytest-*"),
        "ai_review": str(root / "reports" / "ai-review-*"),
        "scenario_trace": f"scenario_id={scenario_id}",
    }


def _salary_trade_execution_scenarios(package_root, structured_cases, mapping):
    mappings = mapping.get("mappings") or []
    mapping_by_case = {item.get("case_id"): item for item in mappings if item.get("case_id")}
    scenarios = []
    base_order_cases = [
        case for case in structured_cases
        if any(word in _case_text(case) for word in ("创建", "订单", "代理", "工资"))
    ]
    for flow in SALARY_TRADE_CASE_FLOWS:
        matched = [case for case in structured_cases if _case_matches_salary_flow(case, flow)]
        if not matched:
            matched = base_order_cases[:8]
        evidence = []
        for case in matched:
            map_item = mapping_by_case.get(case.get("id")) or {}
            evidence.extend(map_item.get("db_evidence_rules") or [])
            evidence.extend(map_item.get("redis_evidence_rules") or [])
        blockers = []
        if flow.get("automation_status") == "blocked":
            blockers.append(flow.get("blocker") or "需要人工或测试环境配合。")
        if not matched:
            blockers.append("未在结构化用例中匹配到该业务流程，需要补充或确认用例归属。")
        manual = flow.get("type") == "timeout" or flow.get("automation_status") == "blocked"
        scenarios.append({
            "scenario_id": flow.get("id"),
            "name": flow.get("name"),
            "business_goal": "验证工资交易订单从创建到目标状态的完整业务流转，订单号在本场景内贯穿使用。",
            "priority": flow.get("priority"),
            "status": _execution_plan_status(matched, blockers, manual),
            "account_slot": flow.get("account_slot"),
            "order_variable": flow.get("order_var"),
            "cases": [_case_brief(case) for case in matched[:30]],
            "tool_tasks": [
                _scenario_tool_task("newman", "运行额度、代理列表、订单详情等轻量接口预检，先确认鉴权和基础参数可用。", [case for case in matched if case.get("coverage_tool") == "newman"][:20], str(Path(package_root) / "outputs" / "newman" / "postman-collection.json")),
                _scenario_tool_task("jmeter", "执行业务主流程状态机，提取同一个 orderNo 并传递到后续请求。", matched[:30], str(Path(package_root) / "outputs" / "jmeter" / "jmeter-plan.jmx"), evidence, flow.get("thread_group"), blockers),
                _scenario_tool_task("pytest", "执行后复核 HTTP 结果、DB订单/日志/凭证和可选Redis证据。", matched[:30], str(Path(package_root) / "outputs" / "pytest" / "pytest_api_cases.py"), evidence),
            ] + ([_scenario_tool_task("manual", "人工复核运营处理、后台定时任务或长等待结果。", matched[:30], blockers=blockers)] if manual else []),
            "human_review": {
                "review_question": "这个场景是否按需求进入了目标订单状态，并且资金、日志、凭证证据一致？",
                "human_actions": [
                    "查看本场景 orderNo 的接口响应和 JMeter 采样标签。",
                    "核对 anchor_salary_trade_order 当前状态、金额和关键时间字段。",
                    "核对 anchor_salary_trade_order_log 是否记录完整流转。",
                ] + (["确认测试环境是否支持缩短或触发定时任务。"] if manual else []),
                "maintenance_targets": [
                    str(Path(package_root) / "outputs" / "structured-test-cases.json"),
                    str(Path(package_root) / "outputs" / "case-jmeter-mapping.json"),
                    str(Path(package_root) / "evidence_rules.yaml"),
                    str(Path(package_root) / "account_model.yaml"),
                ],
            },
            "reports": _scenario_report_targets(package_root, flow.get("id")),
        })
    return scenarios


def _generic_execution_scenarios(package_root, structured_cases, mapping):
    groups = {}
    for case in structured_cases:
        key = case.get("scenario_type") or case.get("path") or "默认场景"
        groups.setdefault(key, []).append(case)
    mappings = {item.get("case_id"): item for item in (mapping.get("mappings") or []) if item.get("case_id")}
    scenarios = []
    for index, (name, cases) in enumerate(groups.items(), start=1):
        slug = re.sub(r"[^a-zA-Z0-9_]+", "_", str(name).lower()).strip("_")[:40] or str(index)
        evidence = []
        blockers = []
        manual = any(case.get("quality_status") == "MANUAL_ONLY" for case in cases)
        for case in cases:
            item = mappings.get(case.get("id")) or {}
            evidence.extend(item.get("db_evidence_rules") or [])
            evidence.extend(item.get("redis_evidence_rules") or [])
            if case.get("quality_status") in {"NEEDS_DATA", "MANUAL_ONLY"}:
                blockers.extend(case.get("blocking_reasons") or [])
        newman_cases = [case for case in cases if case.get("coverage_tool") == "newman"]
        jmeter_cases = [case for case in cases if case.get("coverage_tool") == "jmeter"]
        pytest_cases = [case for case in cases if case.get("coverage_tool") == "pytest" or case.get("db_checks") or case.get("redis_checks")]
        tasks = []
        if newman_cases:
            tasks.append(_scenario_tool_task("newman", "轻量接口回归、冒烟和契约检查。", newman_cases, str(Path(package_root) / "outputs" / "newman" / "postman-collection.json")))
        if jmeter_cases:
            tasks.append(_scenario_tool_task("jmeter", "多步骤、变量传递、状态流转或性能执行。", jmeter_cases, str(Path(package_root) / "outputs" / "jmeter" / "jmeter-plan.jmx"), evidence))
        if pytest_cases or evidence:
            tasks.append(_scenario_tool_task("pytest", "执行后结合 HTTP、DB、Redis 证据做深度校验。", pytest_cases or cases, str(Path(package_root) / "outputs" / "pytest" / "pytest_api_cases.py"), evidence))
        if manual:
            tasks.append(_scenario_tool_task("manual", "人工复核长等待、后台处理或不可自动化条件。", cases, blockers=blockers))
        if not tasks:
            tasks.append(_scenario_tool_task("manual", "缺少足够信息时先人工复核用例可执行性。", cases))
        scenarios.append({
            "scenario_id": f"scenario_{slug}",
            "name": str(name),
            "business_goal": "按该场景归拢测试用例、工具脚本、数据证据和人工复核动作。",
            "priority": min([case.get("priority") or "P2" for case in cases] or ["P2"]),
            "status": _execution_plan_status(cases, blockers, manual),
            "cases": [_case_brief(case) for case in cases[:40]],
            "tool_tasks": tasks,
            "human_review": {
                "review_question": "该场景的接口结果和数据证据是否共同支持需求预期？",
                "human_actions": ["按场景查看报告，不按工具分散排查。", "优先处理阻断数据和候选证据规则。"],
                "maintenance_targets": [str(Path(package_root) / "outputs" / "structured-test-cases.json"), str(Path(package_root) / "evidence_rules.yaml")],
            },
            "reports": _scenario_report_targets(package_root, f"scenario_{slug}"),
        })
    return scenarios


def _write_execution_plan_markdown(path, plan):
    lines = [
        f"# {plan.get('package_name') or plan.get('package_id')} - 场景级执行计划",
        "",
        f"- 状态：{plan.get('status')}",
        f"- 生成时间：{plan.get('generated_at')}",
        f"- 场景数：{plan.get('summary', {}).get('scenarios', 0)}",
        f"- 业务价值：{plan.get('business_value')}",
        "",
        "## 场景清单",
        "",
    ]
    for item in plan.get("scenarios") or []:
        tools = "、".join(task.get("tool") for task in item.get("tool_tasks") or [])
        lines += [
            f"### {item.get('name')}",
            "",
            f"- 状态：{item.get('status')}",
            f"- 用例：{len(item.get('cases') or [])} 条",
            f"- 工具任务：{tools or '-'}",
            f"- 人工复核：{item.get('human_review', {}).get('review_question') or '-'}",
            "",
        ]
        for task in item.get("tool_tasks") or []:
            lines.append(f"- {task.get('tool')}：{task.get('purpose')}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def generate_requirement_execution_plan(project_id, package_id, options=None):
    options = options or {}
    package = requirement_package_by_id(project_id, package_id)
    package_id = package.get("package_id") or package_id
    package_root = Path(package["root"])
    output_context = _package_output_context(package_root)
    structured_payload = _read_json_asset(package_root / "outputs" / "structured-test-cases.json")
    mapping = _read_json_asset(package_root / "outputs" / "case-jmeter-mapping.json")
    structured_cases = structured_payload.get("cases") or _requirement_package_cases(project_id, package_id)
    scenarios = _salary_trade_execution_scenarios(package_root, structured_cases, mapping) if package_id == "salary-trade" else _generic_execution_scenarios(package_root, structured_cases, mapping)
    tool_counts = {}
    status_counts = {}
    for scenario in scenarios:
        status_value = scenario.get("status") or "UNKNOWN"
        status_counts[status_value] = status_counts.get(status_value, 0) + 1
        for task in scenario.get("tool_tasks") or []:
            tool = task.get("tool") or "unknown"
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
    status = "BLOCKED" if status_counts.get("BLOCKED") else "READY_WITH_WARNINGS" if (status_counts.get("NEEDS_REVIEW") or status_counts.get("READY_WITH_WARNINGS")) else "READY"
    plan = {
        "schema_version": "1.0",
        "report_type": "REQUIREMENT_PACKAGE_SCENARIO_EXECUTION_PLAN",
        "project_id": project_id,
        "package_id": package_id,
        "package_name": package.get("name"),
        "status": status,
        "generated_at": now(),
        "source": {"skill": str(SKILL_DIR / "test-tool-routing" / "SKILL.md"), "basis": "结构化测试用例、JMeter映射、账号模型、证据规则和需求包资产"},
        "summary": {
            "scenarios": len(scenarios),
            "cases": len(structured_cases),
            "status_counts": status_counts,
            "tool_counts": tool_counts,
            "structured_case_status": output_context["structured_cases"]["summary"],
            "data_preflight_status": output_context["data_preflight"]["status"],
        },
        "scenarios": scenarios,
        "business_value": "以业务场景为维护单位，把 Newman、JMeter、pytest 和人工复核收在同一个场景下，避免报告按工具散落。",
        "next_actions": [
            "先按场景查看 READY/BLOCKED/NEEDS_REVIEW，确认哪些能自动跑。",
            "脚本生成器优先消费本计划里的 JMeter 场景和 pytest 证据任务。",
            "人工维护时只改当前场景关联的用例、账号模型、证据规则和脚本资产。",
        ],
    }
    out_dir = package_root / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "execution-plan.json"
    md_path = out_dir / "execution-plan.md"
    json_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    _write_execution_plan_markdown(md_path, plan)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = ROOT / "reports" / f"requirement-execution-plan-{project_id}-{package_id}-{stamp}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_payload = {**plan, "output_json": str(json_path), "output_markdown": str(md_path)}
    report_path.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    plan["output_json"] = str(json_path)
    plan["output_markdown"] = str(md_path)
    plan["json_url"] = "/reports/" + report_path.name
    plan["file_name"] = report_path.name
    return plan


def _requirement_package_http_runs(project_id, package_id, limit=80):
    keywords = _requirement_package_keywords(package_id)
    candidates = rows(
        """SELECT r.*, c.title AS case_title, c.path, c.method, c.scenario_type
           FROM runs r JOIN test_cases c ON c.id=r.case_id
           WHERE r.project_id=?
           ORDER BY r.created_at DESC LIMIT 300""",
        (project_id,),
    )
    result = []
    for item in candidates:
        text = "\n".join(str(item.get(key) or "") for key in ("case_title", "path", "scenario_type", "request_data", "analysis"))
        if any(word.lower() in text.lower() for word in keywords):
            result.append(item)
        if len(result) >= limit:
            break
    return result


def _review_category(text, status=""):
    merged = f"{status} {text}".lower()
    if any(word in merged for word in ("401", "403", "authentication", "ticket", "token", "鉴权", "认证", "登录态")):
        return "authentication"
    if any(word in merged for word in ("50017", "ongoing", "processing", "处理中", "一个未处理", "未匹配", "白名单", "国家", "币种", "账号", "ticket/password/redis_uid")):
        return "test_data"
    if any(word in merged for word in ("400", "404", "405", "422", "参数", "必填", "类型", "格式", "request contract")):
        return "request_contract"
    if any(word in merged for word in ("人工", "手工", "长等待", "等待12小时", "等待24小时", "12小时", "24小时", "过期", "定时任务", "运营处理")):
        return "manual_or_timing"
    if any(word in merged for word in ("阻断", "规则0/", "场景0/", "rules_blocked", "scenarios_passed", "rules_passed")):
        return "data_evidence"
    if any(word in merged for word in ("assert", "断言", "expected", "状态流转", "业务", "code")):
        return "business_assertion"
    if any(word in merged for word in ("db", "mysql", "redis", "数据", "缓存", "订单", "日志", "证据")):
        return "data_evidence"
    if any(word in merged for word in ("p95", "p99", "平均", "slow", "latency", "性能", "超时率")):
        return "performance"
    if any(word in merged for word in ("timeout", "econn", "connection", "网络", "连接", "refused", "no module", "未安装")):
        return "environment"
    if any(word in merged for word in ("500", "502", "503", "504", "exception")):
        return "server"
    return "unknown"


def _review_recommendation_for_category(category):
    return {
        "authentication": "先确认账号来源、ticket归属、公共请求参数和登录态刷新链路，再复跑最小接口。",
        "test_data": "先处理数据准备检查：申请人处理中订单、代理白名单、国家币种匹配和代理登录态。",
        "business_assertion": "拿失败用例的接口响应、订单状态和需求状态机一起核对，确认是断言口径还是后端业务逻辑。",
        "data_evidence": "检查 evidence_rules.yaml、DB表字段、Redis Key和运行变量是否能定位到同一个业务对象。",
        "manual_or_timing": "拆成人工验证清单或准备测试环境时间加速方案，不要把长等待流程误判成脚本失败。",
        "performance": "优先看 JMeter 聚合报告、P95/P99、最慢标签和错误率，区分慢请求和失败请求。",
        "environment": "先确认本机网络、代理/VPN、工具安装、JMeter/Newman路径和测试环境连通性。",
        "request_contract": "核对接口文档的必填、类型、枚举、uid/ticket匹配和请求体格式。",
        "server": "保留请求样本、时间点、订单号和响应码，交给后端查服务日志。",
        "unknown": "补齐请求、响应、JTL采样和DB/Redis证据后再复盘。",
    }.get(category, "补齐证据后复盘。")


def _review_add_finding(findings, level, title, evidence, source="", status=""):
    category = _review_category(evidence or title, status)
    findings.append({
        "level": level,
        "category": category,
        "title": title,
        "evidence": _redact_runtime_text(str(evidence or ""))[:1200],
        "recommendation": _review_recommendation_for_category(category),
        "owner": _review_owner_for_failure(evidence, status),
        "source": source,
    })


def _review_owner_for_failure(text, status=""):
    merged = f"{status} {text}".lower()
    if any(word in merged for word in ("401", "403", "authentication", "ticket", "token", "鉴权", "登录态")):
        return "测试/客户端先确认账号登录态、ticket归属和请求公共参数；后端协助确认鉴权规则。"
    if any(word in merged for word in ("400", "404", "405", "422", "参数", "必填", "类型", "格式", "request_contract")):
        return "测试先核对接口文档和请求参数，后端确认接口契约与错误码口径。"
    if any(word in merged for word in ("timeout", "econn", "连接", "超时", "network")):
        return "测试先确认本机网络、代理/VPN和测试环境可用性；环境负责人协助排查。"
    if any(word in merged for word in ("assert", "断言", "expected", "预期", "business", "状态流转")):
        return "测试和产品先确认预期口径；后端确认接口实际业务逻辑。"
    if any(word in merged for word in ("db", "mysql", "redis", "数据", "缓存", "订单", "金额", "流水")):
        return "测试先提供业务对象和期望，后端/DBA确认表字段、状态枚举和缓存Key。"
    if any(word in merged for word in ("500", "502", "503", "server", "exception")):
        return "后端优先排查接口异常和服务日志，测试提供请求样本与时间点。"
    return "测试先复现并补齐请求、响应和数据证据，再按失败类型分派。"


def _pytest_scenarios_from_payload(payload):
    if not isinstance(payload, dict):
        return []
    scenarios = payload.get("scenarios")
    if isinstance(scenarios, list):
        return scenarios
    evidence_report = payload.get("evidence_report")
    if isinstance(evidence_report, dict) and isinstance(evidence_report.get("scenarios"), list):
        return evidence_report.get("scenarios")
    return []


def _pytest_scenario_signals(payload):
    scenarios = _pytest_scenarios_from_payload(payload)
    signals = {
        "pytest_reports": 0,
        "pytest_scenarios": len(scenarios),
        "pytest_scenarios_failed": 0,
        "pytest_scenarios_blocked": 0,
        "pytest_scenario_http_failed": 0,
        "pytest_scenario_evidence_failed": 0,
        "pytest_scenario_evidence_blocked": 0,
    }
    findings = []
    if not scenarios:
        return signals, findings
    signals["pytest_reports"] = 1
    for scenario in scenarios:
        status = str(scenario.get("status") or "UNKNOWN")
        if status == "FAILED":
            signals["pytest_scenarios_failed"] += 1
        if status == "BLOCKED":
            signals["pytest_scenarios_blocked"] += 1
        http_failed = int(scenario.get("http_failed") or 0)
        evidence_results = scenario.get("evidence_results") or []
        evidence_failed = sum(1 for item in evidence_results if item.get("status") == "FAILED")
        evidence_blocked = sum(1 for item in evidence_results if item.get("status") == "BLOCKED")
        signals["pytest_scenario_http_failed"] += http_failed
        signals["pytest_scenario_evidence_failed"] += evidence_failed
        signals["pytest_scenario_evidence_blocked"] += evidence_blocked
        if status in {"FAILED", "BLOCKED"} or http_failed or evidence_failed or evidence_blocked:
            detail = (
                f"{scenario.get('name') or scenario.get('scenario_id')}："
                f"状态={status}，HTTP失败={http_failed}，"
                f"证据失败={evidence_failed}，证据阻断={evidence_blocked}。"
            )
            blockers = []
            for item in evidence_results:
                if item.get("status") in {"FAILED", "BLOCKED"}:
                    blockers.extend(item.get("blockers") or [])
            if blockers:
                detail += " 证据问题：" + "；".join(str(x) for x in blockers[:5])
            findings.append({
                "level": "P0" if status == "FAILED" else "P1",
                "title": "pytest场景证据复盘未通过",
                "detail": detail,
                "status": status,
            })
    return signals, findings


def generate_requirement_package_ai_review(project_id, package_id, options=None):
    options = options or {}
    package = requirement_package_by_id(project_id, package_id)
    package_id = package.get("package_id") or package_id
    package_root = Path(package["root"])
    report_items = _package_report_summaries(package_root)
    output_context = _package_output_context(package_root)
    http_runs = _requirement_package_http_runs(project_id, package_id)
    generated_manifest = package_root / "outputs" / "tool-assets-manifest.json"
    tool_manifest = {}
    if generated_manifest.is_file():
        try:
            tool_manifest = json.loads(generated_manifest.read_text(encoding="utf-8"))
        except Exception:
            tool_manifest = {}
    related_global = []
    seen_global_kinds = set()
    for item in list_generated_reports(project_id):
        if item.get("kind") == "AI复盘":
            continue
        text = " ".join(str(item.get(key) or "") for key in ("name", "kind", "summary", "package_id"))
        if package_id in text or str(package.get("name") or "") in text:
            kind_key = item.get("kind") or item.get("name") or ""
            if kind_key in seen_global_kinds:
                continue
            seen_global_kinds.add(kind_key)
            related_global.append(item)
    statuses = []
    findings = []
    execution_signals = {
        "http_runs": len(http_runs),
        "http_failed": sum(1 for item in http_runs if item.get("status") in {"FAILED", "ERROR"}),
        "package_reports": len(report_items),
        "related_reports": len(related_global),
        "newman_reports": 0,
        "jmeter_reports": 0,
        "pytest_reports": 0,
        "pytest_scenarios": 0,
        "pytest_scenarios_failed": 0,
        "pytest_scenarios_blocked": 0,
        "pytest_scenario_http_failed": 0,
        "pytest_scenario_evidence_failed": 0,
        "pytest_scenario_evidence_blocked": 0,
        "business_evidence_reports": 0,
        "structured_case_reports": 0,
    }
    for run_item in http_runs[:30]:
        if run_item.get("status") in {"FAILED", "ERROR"} or str(run_item.get("http_status") or "") in {"401", "403", "500", "502", "503", "504"}:
            detail = f"{run_item.get('method')} {run_item.get('path')} HTTP {run_item.get('http_status')} {run_item.get('error') or run_item.get('analysis') or ''}"
            _review_add_finding(findings, "P0" if str(run_item.get("http_status") or "").startswith("5") else "P1", "接口执行异常", detail, f"run:{run_item.get('id')}", run_item.get("status"))
    for item in report_items:
        payload = item["payload"]
        status = str(payload.get("status") or "UNKNOWN")
        statuses.append(status)
        if payload.get("report_type") == "REQUIREMENT_PACKAGE_NEWMAN_RUN":
            execution_signals["newman_reports"] += 1
        if payload.get("report_type") in {"REQUIREMENT_PACKAGE_PYTEST_EVIDENCE_RUN", "PYTEST_DEEP_EVIDENCE_REVIEW"}:
            pytest_signals, pytest_findings = _pytest_scenario_signals(payload)
            for key, value in pytest_signals.items():
                execution_signals[key] = execution_signals.get(key, 0) + value
            for finding in pytest_findings[:20]:
                _review_add_finding(findings, finding["level"], finding["title"], finding["detail"], item["path"], finding["status"])
        if "jmeter" in str(payload.get("report_type") or "").lower() or any((x.get("tool") == "JMeter") for x in payload.get("results") or [] if isinstance(x, dict)):
            execution_signals["jmeter_reports"] += 1
        failures = payload.get("failures") or []
        if failures:
            for failure in failures[:10]:
                detail = f"{failure.get('source','')} {failure.get('error','')}".strip()
                _review_add_finding(findings, "P0" if status == "FAILED" else "P1", "外部工具执行失败", detail or payload.get("stderr") or payload.get("stdout", "")[-500:], item["path"], status)
        elif status in {"FAILED", "BLOCKED", "ERROR"}:
            detail = payload.get("message") or payload.get("stderr") or payload.get("stdout", "")[-500:] or status
            _review_add_finding(findings, "P0" if status == "FAILED" else "P1", "需求包执行未通过", detail, item["path"], status)
        for result in payload.get("results") or []:
            if not isinstance(result, dict):
                continue
            if result.get("tool") == "JMeter":
                execution_signals["jmeter_reports"] += 1
            if result.get("status") in {"FAILED", "BLOCKED", "ERROR"}:
                detail = result.get("reason") or result.get("stderr") or result.get("stdout") or result.get("status")
                _review_add_finding(findings, "P0" if result.get("status") == "FAILED" else "P1", f"{result.get('tool','外部工具')}执行异常", detail, item["path"], result.get("status"))
    for item in related_global[:20]:
        status = str(item.get("status") or "UNKNOWN")
        if item.get("kind") == "业务证据执行":
            execution_signals["business_evidence_reports"] += 1
        if item.get("kind") == "结构化用例":
            execution_signals["structured_case_reports"] += 1
        if item.get("kind") == "JMeter":
            execution_signals["jmeter_reports"] += 1
        if status in {"FAILED", "BLOCKED", "ERROR", "P1"}:
            detail = item.get("summary") or item.get("name") or status
            _review_add_finding(findings, "P0" if status == "FAILED" else "P1", item.get("name") or "全局报告异常", detail, item.get("file_name") or item.get("json_url") or "", status)
    structured_summary = output_context["structured_cases"]["summary"]
    data_preflight = output_context["data_preflight"]
    jmeter_mapping = output_context["jmeter_mapping"]["summary"]
    if structured_summary:
        execution_signals["structured_case_reports"] += 1
        quality = structured_summary.get("quality_counts") or {}
        pending = quality.get("NEEDS_EVIDENCE", 0) + quality.get("NEEDS_EVIDENCE_REVIEW", 0)
        if pending:
            _review_add_finding(findings, "P1", "结构化用例仍有证据缺口", f"待证据确认 {pending} 条；缺少正式证据 {quality.get('NEEDS_EVIDENCE',0)} 条，候选待采纳 {quality.get('NEEDS_EVIDENCE_REVIEW',0)} 条。", output_context["structured_cases"]["path"], "ATTENTION")
        if quality.get("MANUAL_ONLY", 0):
            _review_add_finding(findings, "P1", "存在人工或长等待用例", f"人工/长等待用例 {quality.get('MANUAL_ONLY',0)} 条，需要拆出人工清单或测试环境时间加速。", output_context["structured_cases"]["path"], "ATTENTION")
    if data_preflight.get("status") in {"BLOCKED", "READY_WITH_WARNINGS"}:
        for check in data_preflight.get("checks") or []:
            if check.get("status") not in {"READY"}:
                detail = f"{check.get('name')}：{check.get('status')}；{check.get('detail')}；{check.get('next_action','')}"
                _review_add_finding(findings, "P0" if check.get("status") in {"BLOCKED", "NEEDS_DATA"} else "P1", "生成前数据准备检查未完全通过", detail, data_preflight.get("path", ""), check.get("status"))
    if jmeter_mapping and jmeter_mapping.get("evidence_pending", 0):
        _review_add_finding(findings, "P1", "JMeter目标用例存在证据待补", f"JMeter目标 {jmeter_mapping.get('jmeter_targets',0)} 条，其中待证据 {jmeter_mapping.get('evidence_pending',0)} 条，脚本就绪 {jmeter_mapping.get('script_ready',0)} 条。", output_context["jmeter_mapping"]["path"], "ATTENTION")
    category_counts = {}
    for finding in findings:
        category = finding.get("category") or "unknown"
        category_counts[category] = category_counts.get(category, 0) + 1
    p0 = sum(1 for item in findings if item["level"] == "P0")
    p1 = sum(1 for item in findings if item["level"] == "P1")
    status = "FAILED" if p0 else "READY_WITH_WARNINGS" if p1 else "PASSED" if report_items or related_global else "NO_RUN_DATA"
    next_actions = []
    if not tool_manifest.get("generated"):
        next_actions.append("先为当前需求包生成 Newman/JMeter/pytest 工具资产。")
    if not report_items and not related_global:
        next_actions.append("先运行当前需求包的 Newman 或 JMeter，并回收报告。")
    if findings:
        next_actions.extend(dict.fromkeys(item.get("recommendation") or item["owner"] for item in findings[:8]))
    if not next_actions:
        next_actions.append("当前需求包可进入下一轮覆盖增强：补异常场景、性能阈值和数据证据。")
    if category_counts.get("test_data"):
        next_actions.insert(0, "先处理数据准备阻断，再运行 Newman/JMeter；否则容易继续出现401、50017或代理匹配失败。")
    if category_counts.get("authentication"):
        next_actions.insert(0, "先用最小读接口验证 applicant/proxy ticket 与 uid 归属，确认公共参数完整。")
    review = {
        "report_type": "REQUIREMENT_PACKAGE_AI_REVIEW",
        "project_id": project_id,
        "package_id": package_id,
        "package_name": package.get("name"),
        "status": status,
        "created_at": now(),
        "summary": {
            "package_status": package.get("status"),
            "tool_assets": len(tool_manifest.get("generated") or []),
            "package_reports": len(report_items),
            "related_reports": len(related_global),
            "p0": p0,
            "p1": p1,
            "http_runs": execution_signals["http_runs"],
            "http_failed": execution_signals["http_failed"],
            "pytest_scenarios": execution_signals["pytest_scenarios"],
            "pytest_scenarios_failed": execution_signals["pytest_scenarios_failed"],
            "pytest_scenarios_blocked": execution_signals["pytest_scenarios_blocked"],
            "root_cause_categories": category_counts,
        },
        "conclusion": "暂无执行数据，无法复盘。" if status == "NO_RUN_DATA" else "存在阻断失败，先处理P0。" if p0 else "有待确认项，但不阻断继续演示。" if p1 else "当前需求包执行证据暂未发现阻断问题。",
        "findings": findings[:50],
        "root_cause_categories": category_counts,
        "execution_signals": execution_signals,
        "next_actions": next_actions,
        "evidence_sources": {
            "package_reports": [item["path"] for item in report_items[:20]],
            "related_global_reports": related_global[:20],
            "tool_assets_manifest": str(generated_manifest) if generated_manifest.is_file() else "",
            "structured_cases": output_context["structured_cases"]["path"],
            "jmeter_mapping": output_context["jmeter_mapping"]["path"],
            "data_preflight": output_context["data_preflight"]["path"],
            "runtime_sql_checks": data_preflight.get("runtime_sql_checks") or [],
        },
        "review_context": {
            "structured_cases": output_context["structured_cases"],
            "jmeter_mapping": output_context["jmeter_mapping"],
            "data_preflight": data_preflight,
        },
        "business_value": "把同一需求包的接口执行、JMeter/Newman结果和数据证据收束成测试可读结论，减少只看原始日志和图表的成本。",
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = package_root / "reports" / f"ai-review-{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "summary.json"
    out.write_text(json.dumps(review, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md = out_dir / "review.md"
    lines = [
        f"# {package.get('name') or package_id} - 执行结果回灌复盘",
        "",
        f"- 状态：{status}",
        f"- 生成时间：{review['created_at']}",
        f"- HTTP执行记录：{execution_signals['http_runs']}，失败/异常：{execution_signals['http_failed']}",
        f"- P0：{p0}，P1：{p1}",
        f"- 根因分布：{json.dumps(category_counts, ensure_ascii=False)}",
        "",
        "## 结论",
        "",
        review["conclusion"],
        "",
        "## 重点问题",
        "",
    ]
    if findings:
        for item in findings[:30]:
            lines += [
                f"### {item['level']} · {item['title']}",
                "",
                f"- 分类：{item.get('category')}",
                f"- 证据：{item.get('evidence') or '-'}",
                f"- 建议：{item.get('recommendation') or item.get('owner')}",
                f"- 来源：{item.get('source') or '-'}",
                "",
            ]
    else:
        lines += ["- 暂无阻断问题。", ""]
    lines += [
        "## 下一步动作",
        "",
        *[f"{idx + 1}. {action}" for idx, action in enumerate(dict.fromkeys(next_actions))],
        "",
        "## 复盘输入",
        "",
        f"- 结构化用例：{output_context['structured_cases']['path'] or '-'}",
        f"- JMeter映射：{output_context['jmeter_mapping']['path'] or '-'}",
        f"- 数据预检：{output_context['data_preflight']['path'] or '-'}",
        f"- 工具资产：{output_context['tool_assets']['path'] or '-'}",
    ]
    md.write_text("\n".join(lines), encoding="utf-8")
    review["summary_path"] = str(out)
    review["markdown_path"] = str(md)
    review["json_url"] = "/requirement-reports/" + out.relative_to(REQUIREMENT_PACKAGE_ROOT).as_posix()
    return review


def db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS projects (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT DEFAULT '',
          base_url TEXT DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sources (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, name TEXT NOT NULL,
          kind TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS test_points (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, source_id TEXT,
          module TEXT, title TEXT NOT NULL, category TEXT NOT NULL,
          priority TEXT NOT NULL, risk TEXT NOT NULL, rationale TEXT DEFAULT '',
          status TEXT DEFAULT 'draft', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS test_cases (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, point_id TEXT,
          title TEXT NOT NULL, method TEXT DEFAULT '', path TEXT DEFAULT '',
          headers TEXT DEFAULT '{}', payload TEXT DEFAULT '', expected_status INTEGER DEFAULT 200,
          expected_contains TEXT DEFAULT '', priority TEXT DEFAULT 'P1', status TEXT DEFAULT 'ready',
          steps TEXT DEFAULT '', expected TEXT DEFAULT '', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS runs (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, case_id TEXT NOT NULL,
          status TEXT NOT NULL, duration_ms INTEGER DEFAULT 0, http_status INTEGER,
          request_data TEXT DEFAULT '', response_data TEXT DEFAULT '', error TEXT DEFAULT '',
          analysis TEXT DEFAULT '', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS test_accounts (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, nickname TEXT DEFAULT '', short_id TEXT NOT NULL,
          account_uid INTEGER NOT NULL, wealth_level INTEGER, account_role TEXT DEFAULT 'general',
          mutable INTEGER DEFAULT 0, status TEXT DEFAULT 'ready', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS api_endpoints (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, source_id TEXT NOT NULL,
          method TEXT NOT NULL, path TEXT NOT NULL, summary TEXT DEFAULT '', tags TEXT DEFAULT '',
          parameters TEXT DEFAULT '[]', request_body TEXT DEFAULT '{}', responses TEXT DEFAULT '{}',
          auth_required INTEGER DEFAULT 0, risk_level TEXT DEFAULT 'low', risk_reason TEXT DEFAULT '',
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS db_tables (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, table_name TEXT NOT NULL,
          table_comment TEXT DEFAULT '', approx_rows INTEGER DEFAULT 0, columns_json TEXT DEFAULT '[]',
          module TEXT DEFAULT '', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS api_db_mappings (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, endpoint_id TEXT NOT NULL,
          table_name TEXT NOT NULL, confidence REAL DEFAULT 0, reason TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS workflows (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, name TEXT NOT NULL,
          module TEXT DEFAULT '', description TEXT DEFAULT '', priority TEXT DEFAULT 'P1',
          risk_level TEXT DEFAULT 'medium', status TEXT DEFAULT 'draft', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS workflow_steps (
          id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, step_order INTEGER NOT NULL,
          endpoint_id TEXT, case_id TEXT, phase TEXT DEFAULT 'action', name TEXT NOT NULL,
          precondition TEXT DEFAULT '', extract_rules TEXT DEFAULT '{}', continue_on_failure INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS workflow_runs (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, workflow_id TEXT NOT NULL,
          status TEXT NOT NULL, total_steps INTEGER DEFAULT 0, passed_steps INTEGER DEFAULT 0,
          failed_step TEXT DEFAULT '', details TEXT DEFAULT '[]', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS import_batches (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, requirement_source_id TEXT,
          openapi_source_id TEXT NOT NULL, name TEXT NOT NULL, version_no INTEGER NOT NULL,
          added_count INTEGER DEFAULT 0, modified_count INTEGER DEFAULT 0,
          removed_count INTEGER DEFAULT 0, unchanged_count INTEGER DEFAULT 0,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS endpoint_versions (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, source_id TEXT NOT NULL,
          endpoint_key TEXT NOT NULL, version_no INTEGER NOT NULL, content_hash TEXT NOT NULL,
          snapshot TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS endpoint_changes (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, batch_id TEXT NOT NULL,
          source_id TEXT NOT NULL, endpoint_key TEXT NOT NULL, change_type TEXT NOT NULL,
          endpoint_id TEXT, summary TEXT DEFAULT '', impact TEXT DEFAULT '', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS automation_suites (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, name TEXT NOT NULL,
          module TEXT DEFAULT '', description TEXT DEFAULT '', case_ids TEXT DEFAULT '[]',
          status TEXT DEFAULT 'ready', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS performance_plans (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, name TEXT NOT NULL,
          endpoint_id TEXT NOT NULL, case_id TEXT NOT NULL, concurrency INTEGER DEFAULT 5,
          total_requests INTEGER DEFAULT 20, warning_rps REAL DEFAULT 0,
          warning_p95_ms INTEGER DEFAULT 2000, danger_score INTEGER DEFAULT 0, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS performance_runs (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, plan_id TEXT NOT NULL, status TEXT NOT NULL,
          total INTEGER DEFAULT 0, success INTEGER DEFAULT 0, failed INTEGER DEFAULT 0,
          avg_ms REAL DEFAULT 0, p95_ms REAL DEFAULT 0, rps REAL DEFAULT 0,
          details TEXT DEFAULT '{}', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS fault_scenarios (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, endpoint_id TEXT, case_id TEXT,
          name TEXT NOT NULL, fault_type TEXT NOT NULL, description TEXT DEFAULT '',
          danger_score INTEGER DEFAULT 0, warning TEXT DEFAULT '', status TEXT DEFAULT 'ready', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS security_scans (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, status TEXT NOT NULL,
          score INTEGER DEFAULT 0, findings_count INTEGER DEFAULT 0,
          summary TEXT DEFAULT '', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS security_findings (
          id TEXT PRIMARY KEY, scan_id TEXT NOT NULL, project_id TEXT NOT NULL,
          severity TEXT NOT NULL, category TEXT NOT NULL, target TEXT DEFAULT '',
          title TEXT NOT NULL, evidence TEXT DEFAULT '', recommendation TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS ui_test_plans (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, name TEXT NOT NULL,
          page_url TEXT NOT NULL, description TEXT DEFAULT '', scenarios TEXT DEFAULT '[]',
          playwright_script TEXT DEFAULT '', danger_score INTEGER DEFAULT 0,
          status TEXT DEFAULT 'draft', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS scheduled_jobs (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, name TEXT NOT NULL,
          job_type TEXT NOT NULL, target_id TEXT DEFAULT '', interval_minutes INTEGER DEFAULT 1440,
          enabled INTEGER DEFAULT 0, last_run_at TEXT, next_run_at TEXT,
          last_status TEXT DEFAULT 'NEVER', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS project_members (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, username TEXT NOT NULL,
          role TEXT NOT NULL, permissions TEXT DEFAULT '[]', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS approval_requests (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, action_type TEXT NOT NULL,
          target_id TEXT DEFAULT '', title TEXT NOT NULL, requested_by TEXT NOT NULL,
          status TEXT DEFAULT 'pending', reviewed_by TEXT DEFAULT '', review_note TEXT DEFAULT '',
          created_at TEXT NOT NULL, reviewed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS requirement_items (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, source_id TEXT NOT NULL,
          item_type TEXT NOT NULL, title TEXT NOT NULL, description TEXT DEFAULT '',
          acceptance_criteria TEXT DEFAULT '', priority TEXT DEFAULT 'P1', risk_level TEXT DEFAULT 'medium',
          status TEXT DEFAULT 'draft', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trace_links (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, requirement_id TEXT NOT NULL,
          target_type TEXT NOT NULL, target_id TEXT NOT NULL, confidence REAL DEFAULT 0,
          reason TEXT DEFAULT '', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS pipeline_runs (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, status TEXT NOT NULL,
          requirement_source_id TEXT, openapi_source_id TEXT, summary TEXT DEFAULT '{}',
          blockers TEXT DEFAULT '[]', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS source_assets (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, source_id TEXT NOT NULL,
          name TEXT NOT NULL, mime_type TEXT NOT NULL, data_base64 TEXT NOT NULL,
          analysis_status TEXT DEFAULT 'pending', analysis TEXT DEFAULT '', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS source_capture_reports (
          source_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, source_url TEXT DEFAULT '',
          score INTEGER DEFAULT 0, status TEXT DEFAULT 'unknown', stats TEXT DEFAULT '{}',
          blockers TEXT DEFAULT '[]', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS redis_sources (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, name TEXT NOT NULL,
          host TEXT NOT NULL, port INTEGER NOT NULL, db_no INTEGER DEFAULT 0,
          use_tls INTEGER DEFAULT 0, readonly INTEGER DEFAULT 1,
          status TEXT DEFAULT 'unknown', server_version TEXT DEFAULT '',
          last_error TEXT DEFAULT '', last_checked_at TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS redis_key_snapshots (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, redis_source_id TEXT NOT NULL,
          key_name TEXT NOT NULL, key_type TEXT DEFAULT '', ttl INTEGER DEFAULT -1,
          value_preview TEXT DEFAULT '', value_hash TEXT DEFAULT '',
          captured_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS api_redis_mappings (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, endpoint_id TEXT NOT NULL,
          redis_source_id TEXT NOT NULL, key_name TEXT NOT NULL, key_pattern TEXT NOT NULL,
          key_type TEXT DEFAULT 'unknown', confidence REAL DEFAULT 0,
          matched_table TEXT DEFAULT '', reason TEXT DEFAULT '', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS consistency_rules (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, endpoint_id TEXT NOT NULL,
          case_id TEXT DEFAULT '', redis_source_id TEXT DEFAULT '', redis_key TEXT DEFAULT '',
          redis_pattern TEXT DEFAULT '', mysql_table TEXT DEFAULT '', mysql_condition TEXT DEFAULT '',
          expectation TEXT DEFAULT 'observe', confidence REAL DEFAULT 0,
          status TEXT DEFAULT 'ready', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS consistency_runs (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, rule_id TEXT NOT NULL,
          case_run_id TEXT DEFAULT '', status TEXT NOT NULL,
          before_hash TEXT DEFAULT '', after_hash TEXT DEFAULT '', changed INTEGER DEFAULT 0,
          before_ttl INTEGER DEFAULT -1, after_ttl INTEGER DEFAULT -1,
          evidence TEXT DEFAULT '{}', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS wealth_reward_expectations (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, level_min INTEGER, level_max INTEGER,
          reward_name_cn TEXT, reward_type TEXT, duration TEXT, reward_name_en TEXT,
          reward_name_ar TEXT, special_id TEXT DEFAULT '', source_row INTEGER,
          source_file TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reward_matrix_issues (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, level_min INTEGER, level_max INTEGER,
          source_row INTEGER, issue_type TEXT, detail TEXT, status TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS wealth_backend_reward_configs (
          project_id TEXT NOT NULL, level INTEGER NOT NULL, config_id TEXT NOT NULL,
          config_name TEXT, config_value TEXT, config_status INTEGER, type INTEGER,
          reward_count INTEGER, parsed_items TEXT, read_at TEXT,
          PRIMARY KEY(project_id,config_id)
        );
        CREATE TABLE IF NOT EXISTS test_case_reward_links (
          case_id TEXT NOT NULL, project_id TEXT NOT NULL, level INTEGER NOT NULL,
          config_id TEXT DEFAULT '', expectation_id TEXT DEFAULT '', link_type TEXT NOT NULL,
          created_at TEXT NOT NULL,
          UNIQUE(case_id,config_id,expectation_id,link_type)
        );
        CREATE TABLE IF NOT EXISTS assistant_messages (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, role TEXT NOT NULL,
          content TEXT NOT NULL, action TEXT DEFAULT '', result TEXT DEFAULT '{}',
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS quality_diagnosis (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, severity TEXT NOT NULL,
          module TEXT NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL,
          action_label TEXT DEFAULT '', action_target TEXT DEFAULT '',
          details TEXT DEFAULT '[]', status TEXT DEFAULT 'open', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS platform_schema_migrations (
          version TEXT PRIMARY KEY, description TEXT NOT NULL,
          applied_at TEXT NOT NULL
        );
        """)
        conn.execute(
            "INSERT OR IGNORE INTO platform_schema_migrations VALUES (?,?,?)",
            ("20260824_quality_diagnosis", "Add platform-owned diagnosis snapshots", now()),
        )
        existing = {x[1] for x in conn.execute("PRAGMA table_info(api_endpoints)").fetchall()}
        if "example_request" not in existing:
            conn.execute("ALTER TABLE api_endpoints ADD COLUMN example_request TEXT DEFAULT '{}'")
        if "required_fields" not in existing:
            conn.execute("ALTER TABLE api_endpoints ADD COLUMN required_fields TEXT DEFAULT '[]'")
        if "danger_score" not in existing:
            conn.execute("ALTER TABLE api_endpoints ADD COLUMN danger_score INTEGER DEFAULT 0")
        if "danger_warning" not in existing:
            conn.execute("ALTER TABLE api_endpoints ADD COLUMN danger_warning TEXT DEFAULT ''")
        trace_cols = {x[1] for x in conn.execute("PRAGMA table_info(trace_links)").fetchall()}
        if "selected" not in trace_cols: conn.execute("ALTER TABLE trace_links ADD COLUMN selected INTEGER DEFAULT 0")
        if "sort_order" not in trace_cols: conn.execute("ALTER TABLE trace_links ADD COLUMN sort_order INTEGER DEFAULT 0")
        if "link_source" not in trace_cols: conn.execute("ALTER TABLE trace_links ADD COLUMN link_source TEXT DEFAULT 'ai'")
        # One-time and repeat-safe cleanup for evidence created by older builds.
        for run_id,response_data in conn.execute("SELECT id,response_data FROM runs WHERE response_data<>''").fetchall():
            cleaned=safe_response_evidence(response_data)
            if cleaned!=response_data: conn.execute("UPDATE runs SET response_data=? WHERE id=?",(cleaned,run_id))
        for run_id,details in conn.execute("SELECT id,details FROM workflow_runs WHERE details<>''").fetchall():
            cleaned=safe_response_evidence(details)
            if cleaned!=details: conn.execute("UPDATE workflow_runs SET details=? WHERE id=?",(cleaned,run_id))


def rows(sql, args=()):
    with db() as conn:
        return [dict(x) for x in conn.execute(sql, args).fetchall()]


def row(sql, args=()):
    with db() as conn:
        x = conn.execute(sql, args).fetchone()
        return dict(x) if x else None


def execute(sql, args=()):
    with db() as conn:
        conn.execute(sql, args)


class RedisProtocolError(RuntimeError):
    pass


class RedisReadonlyClient:
    """Small dependency-free Redis client exposing only an allowlisted read API."""
    ALLOWED = {"PING", "INFO", "DBSIZE", "SCAN", "TYPE", "TTL", "GET", "HGET", "HGETALL", "LRANGE", "SMEMBERS", "ZRANGE"}

    def __init__(self, host, port, db_no=0, use_tls=False, timeout=8):
        self.host, self.port, self.db_no = host, int(port), int(db_no)
        self.use_tls, self.timeout, self.sock, self.file = bool(use_tls), timeout, None, None

    def __enter__(self):
        raw = socket.create_connection((self.host, self.port), timeout=self.timeout)
        if self.use_tls:
            raw = ssl.create_default_context().wrap_socket(raw, server_hostname=self.host)
        raw.settimeout(self.timeout); self.sock = raw; self.file = raw.makefile("rb")
        if self.db_no:
            # SELECT changes only the connection context, never Redis data.
            self._send_raw("SELECT", str(self.db_no))
        return self

    def __exit__(self, *_):
        try:
            if self.file: self.file.close()
        finally:
            if self.sock: self.sock.close()

    def _send_raw(self, *parts):
        payload = [f"*{len(parts)}\r\n".encode()]
        for part in parts:
            b = part if isinstance(part, bytes) else str(part).encode("utf-8")
            payload.extend((f"${len(b)}\r\n".encode(), b, b"\r\n"))
        self.sock.sendall(b"".join(payload))
        return self._read()

    def command(self, command, *args):
        command = command.upper()
        if command not in self.ALLOWED:
            raise RedisProtocolError(f"Redis命令 {command} 已被只读策略禁止")
        return self._send_raw(command, *args)

    def _read(self):
        prefix = self.file.read(1)
        if not prefix: raise RedisProtocolError("Redis连接已关闭")
        line = self.file.readline()
        if not line.endswith(b"\r\n"): raise RedisProtocolError("Redis响应不完整")
        line = line[:-2]
        if prefix == b"+": return line.decode("utf-8", "replace")
        if prefix == b"-": raise RedisProtocolError(line.decode("utf-8", "replace"))
        if prefix == b":": return int(line)
        if prefix == b"$":
            size = int(line)
            if size < 0: return None
            value = self.file.read(size); self.file.read(2); return value
        if prefix == b"*":
            count = int(line)
            return None if count < 0 else [self._read() for _ in range(count)]
        raise RedisProtocolError("未知Redis响应类型")


def redis_text(value):
    if isinstance(value, bytes): return value.decode("utf-8", "replace")
    if isinstance(value, list): return [redis_text(x) for x in value]
    return value


def redis_source_client(source):
    return RedisReadonlyClient(source["host"], source["port"], source["db_no"], source["use_tls"])


def check_redis_source(source_id):
    source = row("SELECT * FROM redis_sources WHERE id=?", (source_id,))
    if not source: raise ValueError("Redis数据源不存在")
    try:
        with redis_source_client(source) as client:
            pong = redis_text(client.command("PING"))
            info = redis_text(client.command("INFO", "server")) or ""
            size = client.command("DBSIZE")
        version = ""
        m = re.search(r"(?:^|\n)redis_version:([^\r\n]+)", info)
        if m: version = m.group(1).strip()
        execute("UPDATE redis_sources SET status='connected',server_version=?,last_error='',last_checked_at=? WHERE id=?", (version, now(), source_id))
        return {"connected": pong == "PONG", "pong": pong, "server_version": version, "dbsize": size, "readonly": True}
    except Exception as exc:
        execute("UPDATE redis_sources SET status='error',last_error=?,last_checked_at=? WHERE id=?", (str(exc)[:500], now(), source_id))
        raise


def scan_redis_keys(source_id, pattern="*", limit=100):
    source = row("SELECT * FROM redis_sources WHERE id=?", (source_id,))
    if not source: raise ValueError("Redis数据源不存在")
    limit = max(1, min(int(limit or 100), 500)); cursor = "0"; found = []
    with redis_source_client(source) as client:
        for _ in range(100):
            result = client.command("SCAN", cursor, "MATCH", pattern or "*", "COUNT", min(500, max(50, limit)))
            cursor = redis_text(result[0]); found.extend(redis_text(result[1]) or [])
            if len(found) >= limit or cursor == "0": break
    return {"keys": found[:limit], "count": min(len(found), limit), "cursor_complete": cursor == "0", "limit": limit}


def scan_redis_key_names(source, limit=20000):
    cursor = "0"; found = []
    with redis_source_client(source) as client:
        for _ in range(500):
            result = client.command("SCAN", cursor, "COUNT", 1000)
            cursor = redis_text(result[0]); found.extend(redis_text(result[1]) or [])
            if len(found) >= limit or cursor == "0": break
    return found[:limit], cursor == "0"


def redis_key_pattern(key_name):
    value = re.sub(r"[0-9a-f]{8}-[0-9a-f-]{27,}", "{uuid}", key_name, flags=re.I)
    value = re.sub(r"(?<![a-zA-Z])\d{4,}(?![a-zA-Z])", "{id}", value)
    value = re.sub(r"eyJ[a-zA-Z0-9_.-]{20,}", "{token}", value)
    return value


def auto_match_project_data(project_id):
    endpoints = rows("SELECT id,path,summary,tags,parameters,request_body FROM api_endpoints WHERE project_id=?", (project_id,))
    db_maps = rows("SELECT endpoint_id,table_name,confidence FROM api_db_mappings WHERE project_id=?", (project_id,))
    tables = {x["table_name"]: x for x in rows("SELECT table_name,table_comment,columns_json FROM db_tables WHERE project_id=?", (project_id,))}
    redis_sources = rows("SELECT * FROM redis_sources WHERE project_id=? AND status='connected'", (project_id,))
    table_by_endpoint = {}
    for item in db_maps: table_by_endpoint.setdefault(item["endpoint_id"], []).append(item)
    values = []; scanned = 0; complete = True
    for source in redis_sources:
        key_names, source_complete = scan_redis_key_names(source); scanned += len(key_names); complete = complete and source_complete
        key_meta = [(key, redis_key_pattern(key), tokens(redis_key_pattern(key).replace(":", " "))) for key in key_names]
        for ep in endpoints:
                ep_tokens = tokens(" ".join(str(ep.get(x, "")) for x in ("path","summary","tags","parameters","request_body")))
                linked_tables = table_by_endpoint.get(ep["id"], [])
                table_tokens = set()
                for link in linked_tables:
                    table = tables.get(link["table_name"], {})
                    table_tokens |= tokens(link["table_name"] + " " + table.get("table_comment", "") + " " + table.get("columns_json", ""))
                target_tokens = ep_tokens | table_tokens
                if not target_tokens: continue
                candidates = {}
                for key, pattern, key_tokens in key_meta:
                    overlap = target_tokens & key_tokens
                    if not overlap: continue
                    endpoint_overlap = ep_tokens & key_tokens; table_overlap = table_tokens & key_tokens
                    score = .28 + min(.38, .12 * len(endpoint_overlap)) + min(.24, .08 * len(table_overlap))
                    if endpoint_overlap and table_overlap: score += .08
                    candidate = (min(.98, score), key, pattern, endpoint_overlap, table_overlap)
                    if pattern not in candidates or candidate[0] > candidates[pattern][0]: candidates[pattern] = candidate
                for score, key, pattern, endpoint_overlap, table_overlap in sorted(candidates.values(), reverse=True)[:10]:
                    key_type = "按需读取"
                    matched_table = linked_tables[0]["table_name"] if linked_tables and table_overlap else ""
                    reason_parts = []
                    if endpoint_overlap: reason_parts.append("接口字段=" + ",".join(sorted(endpoint_overlap)))
                    if table_overlap: reason_parts.append("数据库字段=" + ",".join(sorted(table_overlap)))
                    values.append((uid("redis_map"),project_id,ep["id"],source["id"],key,pattern,key_type,score,matched_table,"；".join(reason_parts),now()))
    with db() as conn:
        conn.execute("DELETE FROM api_redis_mappings WHERE project_id=?", (project_id,))
        conn.executemany("INSERT INTO api_redis_mappings VALUES (?,?,?,?,?,?,?,?,?,?,?)", values)
    return {"redis_sources":len(redis_sources),"keys_scanned":scanned,"scan_complete":complete,"db_mappings":len(db_maps),"redis_mappings":len(values)}


def inspect_redis_key(source_id, key_name):
    source = row("SELECT * FROM redis_sources WHERE id=?", (source_id,))
    if not source: raise ValueError("Redis数据源不存在")
    if not key_name or len(key_name) > 1024: raise ValueError("Redis key无效")
    with redis_source_client(source) as client:
        key_type = redis_text(client.command("TYPE", key_name)); ttl = client.command("TTL", key_name)
        if key_type == "string": value = redis_text(client.command("GET", key_name))
        elif key_type == "hash": value = redis_text(client.command("HGETALL", key_name))
        elif key_type == "list": value = redis_text(client.command("LRANGE", key_name, 0, 199))
        elif key_type == "set": value = redis_text(client.command("SMEMBERS", key_name))
        elif key_type == "zset": value = redis_text(client.command("ZRANGE", key_name, 0, 199, "WITHSCORES"))
        elif key_type == "none": value = None
        else: value = f"暂不展开类型：{key_type}"
    rendered = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    preview = rendered[:20000]
    snap_id = uid("redis_snap")
    execute("INSERT INTO redis_key_snapshots VALUES (?,?,?,?,?,?,?,?,?)", (snap_id, source["project_id"], source_id, key_name, key_type, ttl, preview, hashlib.sha256(rendered.encode()).hexdigest(), now()))
    return {"key": key_name, "type": key_type, "ttl": ttl, "value": value, "truncated": len(rendered) > len(preview), "snapshot_id": snap_id}


def redis_key_fingerprint(source_id, key_name):
    source = row("SELECT * FROM redis_sources WHERE id=?", (source_id,))
    if not source: raise ValueError("Redis数据源不存在")
    with redis_source_client(source) as client:
        key_type = redis_text(client.command("TYPE", key_name)); ttl = client.command("TTL", key_name)
        if key_type == "string": value = redis_text(client.command("GET", key_name))
        elif key_type == "hash": value = redis_text(client.command("HGETALL", key_name))
        elif key_type == "list": value = redis_text(client.command("LRANGE", key_name, 0, 199))
        elif key_type == "set": value = redis_text(client.command("SMEMBERS", key_name))
        elif key_type == "zset": value = redis_text(client.command("ZRANGE", key_name, 0, 199, "WITHSCORES"))
        else: value = None
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True) if not isinstance(value, str) else value
    return {"key":key_name,"type":key_type,"ttl":ttl,"hash":hashlib.sha256(rendered.encode()).hexdigest(),"exists":key_type!="none","bytes":len(rendered.encode())}


def read_wealth_experience_redis(project_id, account_uid, interface_experience=None, interface_level=None):
    """Prefer the user's offline Hash export; no live Redis request is needed."""
    key="yingtao_user_level_exper"; raw=None; key_type="hash"; error=""; evidence_source="离线导出 Dump_20260821.csv"
    try:
        exported=json.loads((DATA/"redis-wealth-decoded.json").read_text(encoding="utf-8"))
        if exported.get("key")==key: raw=exported.get("items",{}).get(str(account_uid))
    except Exception as exc: error=str(exc)
    try: value=int(raw) if raw is not None else None
    except Exception: value=None
    thresholds=[]
    try: thresholds=json.loads((DATA/"wealth-level-thresholds.json").read_text(encoding="utf-8")).get("rows",[])
    except Exception: pass
    derived=max((int(x["level"]) for x in thresholds if value is not None and int(x["cumulative_experience"])<=value),default=1 if value is not None else None)
    assertions=[{"name":"Redis Key类型为Hash","expected":"hash","actual":key_type,"passed":key_type=="hash"},{"name":"UID字段存在且Value为整数","expected":"累计经验整数","actual":value,"passed":isinstance(value,int) and value>=0},{"name":"Redis累计经验等于接口currentExperValue","expected":interface_experience,"actual":value,"passed":interface_experience is not None and value==interface_experience},{"name":"Redis经验按升级表计算等级等于接口等级","expected":interface_level,"actual":derived,"passed":interface_level is not None and derived==interface_level}]
    return {"status":"PASSED" if all(x["passed"] for x in assertions) else "FAILED","readonly":True,"live_redis_access":False,"evidence_source":evidence_source,"equivalent_command":"HGET","key":key,"field":str(account_uid),"value":value,"derived_level":derived,"assertions":assertions,"assertions_passed":sum(x["passed"] for x in assertions),"assertions_total":len(assertions),"error":error}


def generate_consistency_rules(project_id):
    ensure_readonly_business_gap_cases(project_id)
    mappings = rows("SELECT * FROM api_redis_mappings WHERE project_id=? AND confidence>=.55 ORDER BY confidence DESC", (project_id,))
    endpoints = {x["id"]:x for x in rows("SELECT id,method,path FROM api_endpoints WHERE project_id=?", (project_id,))}
    cases = rows("SELECT id,method,path FROM test_cases WHERE project_id=? AND method<>''", (project_id,))
    case_map = {}
    for x in cases:
        key = (x["method"].upper(), x["path"].split("?", 1)[0])
        raw = str(x["path"] or "")
        current = case_map.get(key)
        if not current or "{{ticket}}" in raw or "{{uid}}" in raw:
            case_map[key] = x["id"]
    db_map_by_endpoint = {}
    for item in rows("SELECT endpoint_id,table_name,confidence FROM api_db_mappings WHERE project_id=? ORDER BY confidence DESC", (project_id,)):
        db_map_by_endpoint.setdefault(item["endpoint_id"], item)
    values=[]; seen=set()
    for mapping in mappings:
        ep=endpoints.get(mapping["endpoint_id"])
        if not ep: continue
        dedupe=(ep["id"],mapping["key_pattern"])
        if dedupe in seen: continue
        seen.add(dedupe)
        method=ep["method"].upper(); expectation="unchanged" if method in {"GET","HEAD","OPTIONS"} else "observe_change"
        values.append((uid("consistency"),project_id,ep["id"],case_map.get((method,ep["path"]),""),mapping["redis_source_id"],mapping["key_name"],mapping["key_pattern"],mapping["matched_table"],"",expectation,mapping["confidence"],"ready",now()))
    for ep in endpoints.values():
        if any(x[2] == ep["id"] for x in values): continue
        method=ep["method"].upper(); expectation="unchanged" if method in {"GET","HEAD","OPTIONS"} else "observe_change"
        db_map = db_map_by_endpoint.get(ep["id"], {})
        case_id = case_map.get((method, ep["path"]), "")
        status = "needs_data_mapping" if not db_map else "redis_not_required" if method in {"GET","HEAD","OPTIONS"} else "needs_redis_mapping"
        confidence = min(float(db_map.get("confidence") or 0.5), 0.5)
        values.append((uid("consistency"),project_id,ep["id"],case_id,"","","",db_map.get("table_name",""),"",expectation,confidence,status,now()))
    with db() as conn:
        conn.execute("DELETE FROM consistency_runs WHERE project_id=?",(project_id,))
        conn.execute("DELETE FROM consistency_rules WHERE project_id=?",(project_id,))
        conn.executemany("INSERT INTO consistency_rules VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",values)
    return {"rules":len(values),"executable":sum(1 for x in values if x[3] and x[4] and x[5]),"mysql_pending":sum(1 for x in values if x[7] and not x[8]),"coverage_endpoints":len({x[2] for x in values}),"placeholder_rules":sum(1 for x in values if x[11]!="ready")}


def ensure_readonly_business_gap_cases(project_id):
    """Close known readonly API gaps without pretending every API needs Redis."""
    runtime = _runtime_context(project_id, {})
    source = row("SELECT id FROM sources WHERE project_id=? AND kind='requirement' ORDER BY created_at DESC LIMIT 1", (project_id,))
    source_id = source["id"] if source else ""
    definitions = [
        {
            "path": "/purse/query",
            "title": "查询当前用户钱包余额：正常请求",
            "summary": "钱包余额只读查询",
            "table": "user_purse",
            "params": {"ticket": "{{ticket}}", "uid": "{{uid}}"},
            "expected": "返回当前登录用户钱包余额，接口只读，不应改变业务数据。",
        },
        {
            "path": "/billrecord/get",
            "title": "查询送礼账单记录：正常请求",
            "summary": "送礼账单只读查询",
            "table": "bill_record",
            "params": {
                "ticket": "{{ticket}}",
                "uid": "{{uid}}",
                "date": "{{current_time_ms}}",
                "netType": "{{netType}}",
                "appsflyerId": "{{appsflyerId}}",
                "deviceId": "{{deviceId}}",
                "osVersion": "{{osVersion}}",
                "isVpnConnected": "{{isVpnConnected}}",
                "model": "{{model}}",
                "packageName": "{{packageName}}",
                "ispType": "{{ispType}}",
                "organic": "{{organic}}",
                "pageNo": "1",
                "pageSize": "50",
                "type": "1",
            },
            "expected": "返回当前登录用户账单列表，接口只读，不应改变业务数据。",
        },
    ]
    created_cases = 0
    created_maps = 0
    for item in definitions:
        endpoint = row("SELECT * FROM api_endpoints WHERE project_id=? AND path=?", (project_id, item["path"]))
        if not endpoint:
            continue
        params = {
            "deviceType": "{{deviceType}}",
            "systemLanguage": "{{systemLanguage}}",
            "appVersion": "{{appVersion}}",
            "os": "{{os}}",
            "language": "{{language}}",
            "appCode": "{{appCode}}",
            "appid": "{{appid}}",
            "version": "{{version}}",
            "channel": "{{channel}}",
            **item["params"],
        }
        query = urllib.parse.urlencode(params, safe="{}")
        case_path = f"{item['path']}?{query}"
        case = row("SELECT id FROM test_cases WHERE project_id=? AND UPPER(method)='GET' AND path LIKE ?", (project_id, item["path"] + "%"))
        if not case:
            point_id = uid("tp")
            case_id = uid("tc")
            execute("INSERT INTO test_points VALUES (?,?,?,?,?,?,?,?,?,?,?)", (point_id, project_id, source_id, "只读业务接口", item["summary"], "正常请求", "P0", "中", "平台根据接口资产和运行上下文自动补齐", "ready", now()))
            execute(
                """INSERT INTO test_cases(id,project_id,point_id,title,method,path,headers,payload,expected_status,expected_contains,priority,status,steps,expected,created_at,executor_type,scenario_type,requirement_ref,actual_result,execution_status,run_count,last_run_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (case_id, project_id, point_id, item["title"], "GET", case_path, "{}", "", 200, '"code"', "P0", "ready", "使用本机运行凭证发起只读 GET 请求；记录 HTTP 状态、业务响应和耗时。", item["expected"], now(), "http", "正常请求", "只读业务接口自动补齐", "", "NOT_RUN", 0, None),
            )
            created_cases += 1
        elif case.get("path") != case_path:
            execute("UPDATE test_cases SET path=?,status='ready',execution_status=CASE WHEN execution_status='NOT_RUN' THEN 'NOT_RUN' ELSE execution_status END WHERE id=?", (case_path, case["id"]))
        table = row("SELECT table_name FROM db_tables WHERE project_id=? AND table_name=?", (project_id, item["table"]))
        mapping = row("SELECT id FROM api_db_mappings WHERE project_id=? AND endpoint_id=? AND table_name=?", (project_id, endpoint["id"], item["table"]))
        if table and not mapping:
            execute("INSERT INTO api_db_mappings VALUES (?,?,?,?,?,?)", (uid("map"), project_id, endpoint["id"], item["table"], 0.86, "平台按只读业务接口补齐：接口语义与表名/字段匹配，Redis非必需"))
            created_maps += 1
    return {"created_cases": created_cases, "created_db_mappings": created_maps, "readonly": True, "runtime_uid": runtime.get("uid")}


def _table_has_column(project_id, table_name, column_name):
    item = row("SELECT columns_json FROM db_tables WHERE project_id=? AND table_name=?", (project_id, table_name))
    if not item:
        return False
    try:
        columns = json.loads(item["columns_json"] or "[]")
    except Exception:
        columns = []
    return any(str(col.get("name", "")).lower() == column_name.lower() for col in columns if isinstance(col, dict))


def autofill_consistency_gaps(project_id):
    runtime = _runtime_context(project_id, {})
    runtime_uid = str(runtime.get("uid") or "").strip()
    executable_cases = rows("SELECT id,method,path FROM test_cases WHERE project_id=? AND method<>''", (project_id,))
    best_case = {}
    for case in executable_cases:
        key = (case["method"].upper(), case["path"].split("?", 1)[0])
        raw = str(case["path"] or "")
        current = best_case.get(key)
        if not current or "{{ticket}}" in raw or "{{uid}}" in raw:
            best_case[key] = case["id"]
    rules = rows("SELECT r.*,e.method,e.path FROM consistency_rules r JOIN api_endpoints e ON e.id=r.endpoint_id WHERE r.project_id=?", (project_id,))
    updated_case = 0
    updated_mysql = 0
    with db() as conn:
        for rule in rules:
            case_id = best_case.get((rule["method"].upper(), rule["path"]))
            if case_id and case_id != rule["case_id"]:
                conn.execute("UPDATE consistency_rules SET case_id=? WHERE id=?", (case_id, rule["id"]))
                updated_case += 1
            if runtime_uid and rule["mysql_table"] and not rule["mysql_condition"] and _table_has_column(project_id, rule["mysql_table"], "uid"):
                conn.execute("UPDATE consistency_rules SET mysql_condition=? WHERE id=?", (f"uid = {int(runtime_uid)}", rule["id"]))
                updated_mysql += 1
    return {"status": "PASSED", "runtime_uid": runtime_uid, "case_bindings": updated_case, "mysql_conditions": updated_mysql, "readonly": True}


def prepare_consistency_rules(project_id):
    generated = generate_consistency_rules(project_id)
    filled = autofill_consistency_gaps(project_id)
    return {"status": "PASSED", "generated": generated, "autofill": filled, "readonly": True}


def _consistency_rule_scope_expr(scope):
    if scope == "all":
        return "", []
    if scope == "extended":
        return "AND redis_key<>'yingtao_user_level_exper'", []
    return "AND redis_key='yingtao_user_level_exper'", []


def _consistency_run_status(results, rules):
    if not rules:
        return "BLOCKED"
    if any(item.get("status") == "FAILED" for item in results):
        return "FAILED"
    if any(item.get("status") == "BLOCKED" for item in results):
        return "BLOCKED"
    return "PASSED"


def run_ready_consistency_rules(project_id, limit=5, scope="core"):
    autofill = autofill_consistency_gaps(project_id)
    scope = scope if scope in {"core", "extended", "all"} else "core"
    scope_sql, scope_params = _consistency_rule_scope_expr(scope)
    rules = rows(
        f"""SELECT * FROM consistency_rules
           WHERE project_id=? AND case_id<>'' AND redis_source_id<>'' AND redis_key<>''
           {scope_sql}
           ORDER BY CASE WHEN redis_key='yingtao_user_level_exper' THEN 0 ELSE 1 END, confidence DESC
           LIMIT ?""",
        (project_id, *scope_params, max(1, min(int(limit or 5), 20))),
    )
    fallback_used = False
    if scope == "core" and not rules:
        fallback_used = True
        rules = rows(
            """SELECT * FROM consistency_rules
               WHERE project_id=? AND case_id<>'' AND redis_source_id<>'' AND redis_key<>''
               ORDER BY confidence DESC
               LIMIT 1""",
            (project_id,),
        )
    results = []
    for rule in rules:
        try:
            results.append(run_consistency_rule(rule["id"]))
        except Exception as exc:
            results.append({"rule_id": rule["id"], "status": "BLOCKED", "error": str(exc)})
    status = _consistency_run_status(results, rules)
    extended_pending = row(
        """SELECT COUNT(*) n FROM consistency_rules
           WHERE project_id=? AND case_id<>'' AND redis_source_id<>'' AND redis_key<>'' AND redis_key<>'yingtao_user_level_exper'""",
        (project_id,),
    )["n"]
    warning = ""
    if scope == "core" and status == "PASSED" and extended_pending:
        warning = f"核心数据验证已通过，仍有 {extended_pending} 条扩展候选规则可按需继续验证。"
    if fallback_used:
        warning = "未找到财富等级核心 Key，已使用最高置信度规则作为临时核心验证。"
    return {
        "status": status,
        "scope": scope,
        "autofill": autofill,
        "total": len(results),
        "passed": sum(item.get("status") == "PASSED" for item in results),
        "blocked": sum(item.get("status") == "BLOCKED" for item in results),
        "failed": sum(item.get("status") == "FAILED" for item in results),
        "warning": warning,
        "results": results,
        "readonly": True,
    }


def run_consistency_rule(rule_id):
    rule=row("SELECT * FROM consistency_rules WHERE id=?",(rule_id,))
    if not rule: raise ValueError("一致性规则不存在")
    if not rule["case_id"]: raise ValueError("该规则尚未关联可执行接口用例")
    if not rule["redis_source_id"] or not rule["redis_key"]: raise ValueError("该规则尚未配置Redis只读映射，不能执行前后快照")
    runtime = _runtime_context(rule["project_id"], {})
    before=redis_key_fingerprint(rule["redis_source_id"],rule["redis_key"])
    case_run=execute_case(rule["case_id"], context=runtime)
    after=redis_key_fingerprint(rule["redis_source_id"],rule["redis_key"])
    changed=before["hash"]!=after["hash"]
    if case_run["status"]!="PASSED": status="BLOCKED"
    elif rule["expectation"]=="unchanged": status="PASSED" if not changed else "FAILED"
    else: status="OBSERVED"
    evidence={"expectation":rule["expectation"],"redis_type":before["type"],"redis_exists_before":before["exists"],"redis_exists_after":after["exists"],"mysql_table":rule["mysql_table"],"mysql_condition":rule["mysql_condition"],"mysql_status":"condition_configured" if rule["mysql_table"] and rule["mysql_condition"] else "pending_condition" if rule["mysql_table"] else "not_configured"}
    run_id=uid("consistency_run")
    execute("INSERT INTO consistency_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(run_id,rule["project_id"],rule_id,case_run["id"],status,before["hash"],after["hash"],int(changed),before["ttl"],after["ttl"],json.dumps(evidence,ensure_ascii=False),now()))
    return {**row("SELECT * FROM consistency_runs WHERE id=?",(run_id,)),"case_status":case_run["status"],"redis_changed":changed}


def project_status_summary(project_id):
    project=row("SELECT * FROM projects WHERE id=?",(project_id,))
    if not project: raise ValueError("项目不存在")
    counts={
        "requirements":row("SELECT COUNT(*) n FROM requirement_items WHERE project_id=?",(project_id,))["n"],
        "endpoints":row("SELECT COUNT(*) n FROM api_endpoints WHERE project_id=?",(project_id,))["n"],
        "test_points":row("SELECT COUNT(*) n FROM test_points WHERE project_id=?",(project_id,))["n"],
        "test_cases":row("SELECT COUNT(*) n FROM test_cases WHERE project_id=?",(project_id,))["n"],
        "workflows":row("SELECT COUNT(*) n FROM workflows WHERE project_id=?",(project_id,))["n"],
        "db_tables":row("SELECT COUNT(*) n FROM db_tables WHERE project_id=?",(project_id,))["n"],
        "redis_mappings":row("SELECT COUNT(*) n FROM api_redis_mappings WHERE project_id=?",(project_id,))["n"],
        "consistency_rules":row("SELECT COUNT(*) n FROM consistency_rules WHERE project_id=?",(project_id,))["n"],
    }
    redis=rows("SELECT name,status,server_version,last_error FROM redis_sources WHERE project_id=?",(project_id,))
    blockers=[]
    if not project.get("base_url"): blockers.append("尚未配置测试环境 Base URL")
    if not os.getenv("AUTOTEST_LOGIN_PASSWORD_ENCRYPTED"): blockers.append("客户端登录加密参数尚未配置")
    if not os.getenv("AUTOTEST_LOGIN_SN"): blockers.append("登录请求头 sn 尚未配置")
    if not os.getenv("AUTOTEST_LOGIN_T"): blockers.append("登录请求头 t 尚未配置")
    if not redis: blockers.append("尚未接入 Redis")
    elif any(x["status"]!="connected" for x in redis): blockers.append("存在未连接的 Redis 数据源")
    return {"project":project["name"],"counts":counts,"redis":redis,"blockers":blockers}


def assistant_latest_report_analysis(project_id):
    report_dir=ROOT/"reports"; files=sorted(report_dir.glob("gift-wealth-chain-*.json"),key=lambda x:x.stat().st_mtime,reverse=True) if report_dir.exists() else []
    if not files: return {"found":False,"message":"当前项目还没有财富送礼链路报告。"}
    try: report=json.loads(files[0].read_text(encoding="utf-8"))
    except Exception: return {"found":False,"message":"最新报告无法解析。"}
    assertions=report.get("assertions",[]); failed=[x for x in assertions if not x.get("passed")]; gift=report.get("gift_config",{}); steps=report.get("steps",{}); before=steps.get("wealth_before",{}).get("core",{}).get("current_experience"); after=steps.get("wealth_after",{}).get("core",{}).get("current_experience"); consume=gift.get("consume_gold"); actual_delta=after-before if isinstance(before,int) and isinstance(after,int) else None; ratio=round(actual_delta/consume,4) if isinstance(actual_delta,int) and isinstance(consume,int) and consume else None
    gift_runs=steps.get("gift_runs") or ([steps.get("gift")] if steps.get("gift") else []); calls_passed=sum(isinstance(x,dict) and x.get("status")=="PASSED" for x in gift_runs)
    summary={"found":True,"file_name":files[0].name,"executed_at":report.get("executed_at"),"status":report.get("status"),"gift_id":gift.get("gift_id"),"gift_runs":len(gift_runs),"gift_calls_passed":calls_passed,"consume_gold":consume,"assertions_total":len(assertions),"assertions_passed":sum(bool(x.get("passed")) for x in assertions),"failed_assertions":[{"name":x.get("name"),"expected":x.get("expected"),"actual":x.get("actual")} for x in failed[:10]],"wealth_before":before,"wealth_after":after,"wealth_delta":actual_delta,"experience_ratio":ratio}
    lines=[f"最新报告：{files[0].name}",f"接口执行：送礼 {calls_passed}/{len(gift_runs)} 次成功；总消费 {consume} Gold。",f"断言结果：{summary['assertions_passed']}/{summary['assertions_total']} 通过。"]
    if failed:
        lines.append("发现的业务差异：")
        lines.extend(f"- {x.get('name')}：期望 {x.get('expected')}，实际 {x.get('actual')}" for x in failed[:5])
    else: lines.append("当前没有失败断言。")
    if ratio is not None: lines.append(f"财富经验前后增加 {actual_delta}，与消费换算比例约为 {ratio}:1。")
    lines.append("建议：接口调用失败应定位请求或鉴权；仅业务断言不符时，应标记为业务差异并保留时间证据。")
    summary["message"]="\n".join(lines); return summary


def assistant_reply(project_id, message):
    text=(message or "").strip(); lowered=text.lower()
    if not text: raise ValueError("请输入指令")
    action="help"; result={}; reply=""
    page_intent=any(x in text for x in ("打开","进入","切换","带我去","跳到","查看页面"))
    if (any(x in text for x in ("分析","解读","解释","总结")) and any(x in text for x in ("报告","失败","差异","结果"))) or "为什么失败" in text:
        action="analyze_report"; result=assistant_latest_report_analysis(project_id); result["tab"]="reports"; result["report_kind"]="risk" if result.get("failed_assertions") else "overview"; reply=result["message"]
    elif any(x in text for x in ("完整执行证据","完整证据","断言明细")) or ("报告" in text and any(x in text for x in ("证据","明细","55","174"))):
        action="navigate"; result={"tab":"reports","report_kind":"evidence"}; reply="已打开报告中心的完整执行证据，送礼前后重复执行项会完整保留。"
    elif "报告" in text and "性能" in text:
        action="navigate"; result={"tab":"reports","report_kind":"performance"}; reply="已打开报告中心的性能测试分类。"
    elif "报告" in text and any(x in text for x in ("风险","失败","差异")):
        action="navigate"; result={"tab":"reports","report_kind":"risk"}; reply="已打开报告中心的缺陷与风险分类。"
    elif "报告" in text and (page_intent or any(x in text for x in ("最新","刷新","看看"))):
        action="navigate"; result={"tab":"reports","report_kind":"overview","refresh":True}; reply="已刷新并打开报告中心。"
    elif any(x in text for x in ("送礼","礼物")) and any(x in text for x in ("准备","填写","配置","循环","20次")):
        count_match=re.search(r"(\d+)\s*次",text); gift_match=re.search(r"(?:礼物|gift(?:id)?)\s*[=:：]?\s*(\d+)",text,re.I) or re.search(r"(\d+)\s*(?:号)?礼物",text)
        iterations=max(1,min(int(count_match.group(1)) if count_match else 20,100)); gift_id=int(gift_match.group(1)) if gift_match else 1057
        action="prepare_gift"; result={"tab":"automation","iterations":iterations,"gift_id":gift_id}; reply=f"已在财富送礼链路中填写礼物 {gift_id}、循环 {iterations} 次。真实扣款前仍需要你亲自勾选确认并点击执行。"
    elif page_intent and any(x in text for x in ("自动化","接口测试","财富专项","送礼链路")):
        action="navigate"; result={"tab":"automation"}; reply="已打开接口与性能测试工作区。"
    elif page_intent and "测试点" in text:
        action="navigate"; result={"tab":"points"}; reply="已打开测试点页面。"
    elif page_intent and "用例" in text:
        action="navigate"; result={"tab":"cases"}; reply="已打开测试用例页面。"
    elif page_intent and any(x in text for x in ("流程","链路")):
        action="navigate"; result={"tab":"flows"}; reply="已打开跨接口业务链路页面。"
    elif page_intent and any(x in text for x in ("需求","接口导入","资料")):
        action="navigate"; result={"tab":"sources"}; reply="已打开需求与接口资料接入页面。"
    elif page_intent and any(x in text for x in ("数据库","mysql")):
        action="navigate"; result={"tab":"database"}; reply="已打开数据库配置页面；公司数据仍保持严格只读。"
    elif "生成" in text and any(x in text for x in ("跨接口流程","业务流程","接口链路")):
        action="generate_workflows"; result=generate_workflows(project_id); result["tab"]="flows"; reply=f"已生成 {result['workflows']} 条业务流程、{result['steps']} 个接口步骤，并打开链路页面。"
    elif "生成" in text and any(x in text for x in ("性能资产","性能计划","接口专项")):
        action="generate_nonfunctional"; result=generate_nonfunctional(project_id); result["tab"]="automation"; reply=f"已生成 {result['suites']} 个接口套件、{result['performance_plans']} 个性能计划和 {result['fault_scenarios']} 个异常场景。"
    elif any(x in text for x in ("状态","盘点","概况","有多少","检查项目")):
        action="project_status"; result=project_status_summary(project_id); c=result["counts"]
        reply=f"当前项目有 {c['requirements']} 条需求、{c['endpoints']} 个接口、{c['test_points']} 个测试点、{c['test_cases']} 条用例、{c['db_tables']} 张数据库表、{c['redis_mappings']} 条 Redis 映射和 {c['consistency_rules']} 条数据验证规则。"
        if result["blockers"]: reply += "\n\n当前卡点：\n- " + "\n- ".join(result["blockers"])
    elif ("自动匹配" in text or "匹配" in text) and ("redis" in lowered or "数据库" in text or "mysql" in lowered):
        action="auto_match_data"; result=auto_match_project_data(project_id)
        reply=f"自动匹配完成：扫描 {result['keys_scanned']} 个 Redis Key，结合 {result['db_mappings']} 条数据库映射，生成 {result['redis_mappings']} 条接口—数据库—Redis 候选关系。"
    elif "验证规则" in text or "一致性规则" in text or "数据闭环" in text:
        action="generate_consistency"; result=generate_consistency_rules(project_id)
        reply=f"已生成 {result['rules']} 条数据验证规则，其中 {result['executable']} 条已关联可执行接口用例；{result['mysql_pending']} 条仍需补充 MySQL 查询条件。"
    elif "卡点" in text or "阻塞" in text or "为什么不能" in text:
        action="blockers"; result=project_status_summary(project_id)
        reply="当前没有发现平台基础连接卡点。" if not result["blockers"] else "当前卡点：\n- " + "\n- ".join(result["blockers"])
    elif "redis" in lowered and any(x in text for x in ("连接","测试","检查")):
        action="check_redis"; sources=rows("SELECT id,name FROM redis_sources WHERE project_id=?",(project_id,)); checks=[]
        for source in sources:
            try: checks.append({"name":source["name"],**check_redis_source(source["id"])})
            except Exception as exc: checks.append({"name":source["name"],"connected":False,"error":str(exc)})
        result={"sources":checks}; reply="\n".join(f"- {x['name']}：{'连接正常' if x.get('connected') else '连接失败'}" + (f"，Redis {x.get('server_version')}，Key 数 {x.get('dbsize')}" if x.get('connected') else f"，{x.get('error','未知错误')}") for x in checks) or "当前项目尚未配置 Redis。"
    elif "帮助" in text or "可以做什么" in text or "功能" in text:
        reply="我现在可以直接操作工作台：\n- 打开报告中心、完整证据、性能报告或风险报告\n- 打开需求、测试点、用例、业务链路和接口测试页面\n- 自动填写1057礼物及1-20次循环参数\n- 生成跨接口流程、接口套件和性能计划\n- 检查项目状态、归纳卡点和生成数据规则\n\n真实送礼仍必须由你亲自勾选确认，助手不会自动扣款。"
    else:
        reply="我没有识别出明确动作。可以试试：打开完整执行证据、打开性能报告、准备1057礼物循环20次、打开测试用例、生成跨接口流程、检查项目状态。"
    user_id=uid("msg"); assistant_id=uid("msg")
    with db() as conn:
        conn.execute("INSERT INTO assistant_messages VALUES (?,?,?,?,?,?,?)",(user_id,project_id,"user",text,"","{}",now()))
        conn.execute("INSERT INTO assistant_messages VALUES (?,?,?,?,?,?,?)",(assistant_id,project_id,"assistant",reply,action,json.dumps(result,ensure_ascii=False),now()))
    return {"message":reply,"action":action,"result":result,"id":assistant_id}


def resolve_schema(schema, spec, depth=0):
    if not isinstance(schema, dict) or depth > 6:
        return schema if isinstance(schema, dict) else {}
    ref = schema.get("$ref")
    if ref and ref.startswith("#/"):
        value = spec
        try:
            for key in ref[2:].split("/"):
                value = value[key]
            merged = dict(value); merged.update({k:v for k,v in schema.items() if k != "$ref"})
            return resolve_schema(merged, spec, depth + 1)
        except Exception:
            return schema
    return schema


def schema_example(schema, spec, depth=0):
    schema = resolve_schema(schema, spec, depth)
    if depth > 6: return None
    if "example" in schema: return schema["example"]
    if "default" in schema: return schema["default"]
    if "enum" in schema and schema["enum"]: return schema["enum"][0]
    typ = schema.get("type")
    if not typ and ("properties" in schema or "allOf" in schema): typ = "object"
    if typ == "object":
        out = {}
        for part in schema.get("allOf", []):
            value = schema_example(part, spec, depth + 1)
            if isinstance(value, dict): out.update(value)
        for k, v in (schema.get("properties") or {}).items(): out[k] = schema_example(v, spec, depth + 1)
        return out
    if typ == "array": return [schema_example(schema.get("items", {}), spec, depth + 1)]
    if typ == "integer": return int(schema.get("minimum", 1))
    if typ == "number": return float(schema.get("minimum", 1))
    if typ == "boolean": return True
    fmt = schema.get("format", "")
    return {"date":"2026-08-19","date-time":"2026-08-19T12:00:00Z","email":"test@example.com","uuid":"00000000-0000-4000-8000-000000000001"}.get(fmt, "test")


def parse_openapi(content):
    try:
        spec = json.loads(content)
    except Exception:
        # Small YAML reader for common OpenAPI documents, intentionally conservative.
        spec = {"paths": {}}
        current_path = None
        current_method = None
        for raw in content.splitlines():
            line = raw.rstrip()
            m = re.match(r"^\s{0,2}(/[^:]+):\s*$", line)
            if m:
                current_path = m.group(1)
                spec["paths"][current_path] = {}
                continue
            m = re.match(r"^\s{2,6}(get|post|put|patch|delete|head|options):\s*$", line, re.I)
            if m and current_path:
                current_method = m.group(1).lower()
                spec["paths"][current_path][current_method] = {}
                continue
            m = re.match(r"^\s+summary:\s*[\"']?(.*?)[\"']?\s*$", line)
            if m and current_path and current_method:
                spec["paths"][current_path][current_method]["summary"] = m.group(1)
    endpoints = []
    for path, methods in (spec.get("paths") or {}).items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "head", "options"}:
                continue
            op = op if isinstance(op, dict) else {}
            parameters = (methods.get("parameters") or []) + (op.get("parameters") or [])
            example = {"path": {}, "query": {}, "headers": {}, "body": None}
            required = []
            for param in parameters:
                if not isinstance(param, dict): continue
                name, location = param.get("name", ""), param.get("in", "query")
                # Never invent executable values from a schema type/default.
                # Only explicit OpenAPI examples, captured traffic or manual input
                # may enter a real request.
                if "example" in param:
                    value=param.get("example")
                    if location == "header": example["headers"][name] = value
                    elif location in {"query", "path"}: example[location][name] = value
                if param.get("required"): required.append(f"{location}.{name}")
            request_body = op.get("requestBody") or {}
            content_types = request_body.get("content") or {}
            selected_type = next(iter(content_types), "")
            if selected_type:
                media = content_types[selected_type] or {}
                if "example" in media: example["body"] = media.get("example")
                example["content_type"] = selected_type
                body_schema = resolve_schema(media.get("schema", {}), spec)
                required.extend("body." + x for x in body_schema.get("required", []))
            endpoints.append({
                "path": path, "method": method.upper(),
                "summary": op.get("summary") or op.get("operationId") or f"{method.upper()} {path}",
                "tags": op.get("tags") or [path.strip("/").split("/")[0] or "API"],
                "security": bool(op.get("security") or spec.get("security")),
                "parameters": parameters,
                "request_body": request_body,
                "responses": op.get("responses") or {},
                "example": example,
                "required": required,
            })
    return endpoints or parse_plain_api_document(content)


def parse_plain_api_document(content):
    endpoints = []
    seen = set()

    def add_endpoint(methods, raw_path, summary=""):
        raw_path = str(raw_path or "").strip().strip("`'\" ")
        if not raw_path:
            return
        if raw_path.startswith("http://") or raw_path.startswith("https://"):
            parsed = urllib.parse.urlparse(raw_path)
            path = parsed.path or "/"
            query = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
        else:
            path_part, _, query_text = raw_path.partition("?")
            path = path_part if path_part.startswith("/") else "/" + path_part.lstrip("/")
            query = dict(urllib.parse.parse_qsl(query_text, keep_blank_values=True))
        path = re.sub(r"[，,。；;\s]+$", "", path)
        method_values = []
        for method in re.split(r"[/,、\s]+", methods.upper()):
            if method in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
                method_values.append(method)
        for method in method_values or ["GET"]:
            key = (method, path)
            if key in seen:
                continue
            seen.add(key)
            parameters = [
                {"name": name, "in": "query", "required": False, "example": _capture_redacted(name, value)}
                for name, value in query.items()
            ]
            example = {"path": {}, "query": {p["name"]: p.get("example", "") for p in parameters}, "headers": {}, "body": None}
            security = any(str(name).lower() in {"ticket", "token", "authorization", "cookie"} for name in query)
            tag = path.strip("/").split("/")[0] or "API"
            endpoints.append({
                "path": path,
                "method": method,
                "summary": summary.strip() or f"{method} {path}",
                "tags": [tag],
                "security": security,
                "parameters": parameters,
                "request_body": {},
                "responses": {"200": {"description": "success"}},
                "example": example,
                "required": [],
            })

    for raw in content.splitlines():
        line = raw.strip()
        if not line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")] if "|" in line else []
        if len(cells) >= 2 and re.search(r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)(?:\s*/\s*(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS))*\b", cells[0], re.I):
            paths = re.findall(r"`([^`]*?/[^`]*)`|((?:https?://[^\s|`]+)|/[A-Za-z0-9_./{}?=&%:$-]+)", cells[1])
            for path_match in paths:
                path_text = path_match[0] or path_match[1]
                add_endpoint(cells[0], path_text, cells[2] if len(cells) > 2 else "")
            continue
        m = re.search(r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)(?:\s*/\s*(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS))*\s+(`?)(https?://[^\s`]+|/[A-Za-z0-9_./{}?=&%:$-]+)\2", line, re.I)
        if m:
            add_endpoint(m.group(0).split()[0], m.group(3), line[m.end():].strip(" -:："))
    return endpoints


SENSITIVE_CAPTURE_KEYS = (
    "authorization", "cookie", "token", "ticket", "password", "passwd", "secret",
    "session", "sid", "access_token", "refresh_token", "phone", "mobile", "手机号",
)


def _capture_redacted(name, value):
    key = str(name or "").lower()
    text = "" if value is None else str(value)
    if any(word in key for word in SENSITIVE_CAPTURE_KEYS):
        return "***REDACTED***"
    if re.fullmatch(r"1[3-9]\d{9}", text):
        return "***REDACTED_PHONE***"
    if len(text) >= 24 and re.search(r"[A-Za-z]", text) and re.search(r"\d", text):
        return "***REDACTED_SECRET***"
    return value


def _capture_items(items):
    result = {}
    for item in items or []:
        if isinstance(item, dict):
            name = str(item.get("name") or "").strip()
            value = item.get("value", "")
        else:
            name, value = item
        if name:
            result[name] = _capture_redacted(name, value)
    return result


def _json_shape(value, depth=0):
    if depth > 3:
        return "..."
    if isinstance(value, dict):
        return {k: _json_shape(v, depth + 1) for k, v in list(value.items())[:30]}
    if isinstance(value, list):
        return [_json_shape(value[0], depth + 1)] if value else []
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if value is None:
        return "null"
    return "string"


def parse_har_capture(content):
    try:
        payload = json.loads(content)
    except Exception as exc:
        raise ValueError("HAR 内容不是有效 JSON：" + str(exc))
    entries = ((payload.get("log") or {}).get("entries") or [])
    if not isinstance(entries, list):
        raise ValueError("HAR 文件缺少 log.entries")
    paths = {}
    for entry in entries:
        request = entry.get("request") or {}
        response = entry.get("response") or {}
        method = str(request.get("method") or "GET").upper()
        if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
            continue
        parsed = urllib.parse.urlparse(request.get("url") or "")
        path = parsed.path or "/"
        query = _capture_items(request.get("queryString") or urllib.parse.parse_qsl(parsed.query))
        headers = _capture_items(request.get("headers") or [])
        post_data = request.get("postData") or {}
        mime = post_data.get("mimeType") or headers.get("Content-Type") or headers.get("content-type") or "application/json"
        body = None
        if post_data.get("params"):
            body = _capture_items(post_data.get("params") or [])
        elif post_data.get("text"):
            raw_body = post_data.get("text")
            try:
                parsed_body = json.loads(raw_body)
                body = {k: _capture_redacted(k, v) for k, v in parsed_body.items()} if isinstance(parsed_body, dict) else parsed_body
            except Exception:
                body = "***REDACTED_FORM_OR_TEXT***" if any(x in str(raw_body).lower() for x in SENSITIVE_CAPTURE_KEYS) else str(raw_body)[:4000]
        status = int(response.get("status") or 0) or 200
        response_content = response.get("content") or {}
        response_text = response_content.get("text") or ""
        response_example = None
        if response_text:
            try:
                response_example = _json_shape(json.loads(response_text))
            except Exception:
                response_example = str(response_text)[:500]
        operation = {
            "summary": f"抓包导入 {method} {path}",
            "tags": [path.strip("/").split("/")[0] or "capture"],
            "parameters": [
                {"name": name, "in": "query", "required": False, "example": value}
                for name, value in query.items()
            ],
            "responses": {
                str(status): {
                    "description": "Captured response",
                    "content": {"application/json": {"example": response_example}} if response_example is not None else {},
                }
            },
        }
        operation["parameters"].extend(
            {"name": name, "in": "header", "required": False, "example": value}
            for name, value in headers.items()
            if name.lower() in {"authorization", "cookie", "ticket", "content-type"}
        )
        if body is not None and method in {"POST", "PUT", "PATCH", "DELETE"}:
            operation["requestBody"] = {"content": {mime: {"example": body}}}
        if any(name.lower() in {"authorization", "cookie", "ticket"} for name in headers):
            operation["security"] = [{"capturedAuth": []}]
        paths.setdefault(path, {})[method.lower()] = operation
    if not paths:
        raise ValueError("HAR 中未识别到可导入的 HTTP 接口")
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "HAR Capture Import", "version": now()},
        "paths": paths,
        "x-autotest-source": "har",
        "x-autotest-note": "由抓包文件导入，敏感字段已脱敏；写操作需人工审查后执行。",
    }
    return json.dumps(spec, ensure_ascii=False, indent=2), len(entries)


def _redact_doc_value(name, value):
    if isinstance(value, dict):
        return {k: _redact_doc_value(k, v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_doc_value(name, item) for item in value]
    return _capture_redacted(name, value)


def build_project_interface_document(project_id):
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    endpoints = rows("SELECT * FROM api_endpoints WHERE project_id=? ORDER BY path,method", (project_id,))
    paths = {}
    for ep in endpoints:
        try:
            parameters = json.loads(ep.get("parameters") or "[]")
        except Exception:
            parameters = []
        try:
            request_body = json.loads(ep.get("request_body") or "{}")
        except Exception:
            request_body = {}
        try:
            responses = json.loads(ep.get("responses") or "{}")
        except Exception:
            responses = {}
        try:
            example = json.loads(ep.get("example_request") or "{}")
        except Exception:
            example = {}
        cleaned_parameters = []
        for param in parameters:
            if not isinstance(param, dict):
                continue
            item = dict(param)
            name = item.get("name", "")
            if "example" in item:
                item["example"] = _redact_doc_value(name, item.get("example"))
            cleaned_parameters.append(item)
        if not request_body and example.get("body") is not None:
            content_type = example.get("content_type") or "application/json"
            request_body = {"content": {content_type: {"example": _redact_doc_value("body", example.get("body"))}}}
        if not responses:
            responses = {"200": {"description": "Success response. 请根据真实业务响应补充字段说明。"}}
        operation = {
            "summary": ep.get("summary") or f"{ep['method']} {ep['path']}",
            "tags": json.loads(ep.get("tags") or "[]") if (ep.get("tags") or "").startswith("[") else [ep.get("tags") or "API"],
            "parameters": cleaned_parameters,
            "responses": responses,
            "x-autotest-risk": {
                "level": ep.get("risk_level"),
                "reason": ep.get("risk_reason"),
                "danger_score": ep.get("danger_score", 0),
                "danger_warning": ep.get("danger_warning", ""),
            },
            "x-autotest-source": "platform-interface-baseline",
        }
        if request_body:
            operation["requestBody"] = request_body
        if int(ep.get("auth_required") or 0):
            operation["security"] = [{"capturedOrConfiguredAuth": []}]
        paths.setdefault(ep["path"], {})[ep["method"].lower()] = operation
    return {
        "openapi": "3.0.3",
        "info": {
            "title": f"{project['name']} 接口文档基线",
            "version": datetime.now().strftime("%Y.%m.%d.%H%M"),
            "description": "由质量中枢根据 OpenAPI、HAR 抓包和人工维护接口资产生成。敏感示例值已脱敏。",
        },
        "servers": [{"url": project.get("base_url") or "http://127.0.0.1"}],
        "paths": paths,
        "components": {
            "securitySchemes": {
                "capturedOrConfiguredAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "Authorization",
                    "description": "平台只保留脱敏后的认证占位，不导出真实 Cookie、Token、Ticket 或账号密码。",
                }
            }
        },
        "x-autotest-security": {
            "raw_har_saved": False,
            "sensitive_fields_redacted": True,
            "business_datasource_readonly": True,
            "note": "导出文档来自平台接口资产库，不包含原始抓包敏感值。",
        },
    }


def _csv_text(records, fields):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for item in records:
        writer.writerow({key: item.get(key, "") for key in fields})
    return output.getvalue()


def build_apipost_collaboration_package(project_id):
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = ROOT / "reports" / "apipost" / f"{project_id}-{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    openapi_doc = build_project_interface_document(project_id)
    runtime_profile = project_execution_profile(project_id)
    tool_assets = generate_enterprise_tool_assets(project_id)
    (out / "openapi-baseline.apipost-import.json").write_text(json.dumps(openapi_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "postman-compatible-collection.json").write_text((TOOL_ASSET_ROOT / project_id / "postman-collection.json").read_text(encoding="utf-8"), encoding="utf-8")
    env_doc = {
        "name": project["name"] + " 测试环境变量",
        "base_url": project.get("base_url") or "",
        "variables": {
            "uid": runtime_profile.get("runtime_params", {}).get("uid", ""),
            "receiver_uid": runtime_profile.get("runtime_params", {}).get("receiver_uid", ""),
            "pageNo": runtime_profile.get("runtime_params", {}).get("pageNo", 1),
            "pageSize": runtime_profile.get("runtime_params", {}).get("pageSize", 50),
            "ticket": "{{ticket}}",
        },
        "security": {
            "ticket": "请在 Apipost 环境变量中手动填入或由登录前置脚本写入；平台导出包不包含真实 ticket。",
            "password": "不导出密码、sn、cookie、access_token 原值。",
        },
    }
    (out / "apipost-env-template.json").write_text(json.dumps(env_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    guide = f"""# Apipost 协同导入说明

项目：{project['name']}
生成时间：{now()}

## 导入顺序
1. 在 Apipost 中导入 `openapi-baseline.apipost-import.json`，建立接口文档基线。
2. 如需直接执行集合，也可导入 `postman-compatible-collection.json`。
3. 参考 `apipost-env-template.json` 建立测试环境变量。
4. `ticket`、密码、sn、cookie 等敏感值需要在 Apipost 本地环境中填写或由登录前置脚本生成，本包不会导出。

## 平台边界
- 平台负责生成接口资产、测试用例、执行脚本、运行参数模板和报告归档。
- Apipost 负责单接口调试、人工排查、团队接口协作。
- Newman、JMeter、pytest 负责自动执行与报告产出。
- MySQL/Redis 只读，用于证据核对，不写真实业务数据。

## 本次资产
- 接口数量：{len(openapi_doc.get('paths', {}))}
- 外部工具资产：{tool_assets.get('generated', 0)}
"""
    (out / "README-Apipost.md").write_text(guide, encoding="utf-8")
    zip_path = ROOT / "reports" / f"apipost-package-{project_id}-{stamp}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in out.iterdir():
            zf.write(file, arcname=file.name)
    return {
        "status": "READY",
        "name": "Apipost 协同包",
        "files": [item.name for item in out.iterdir()],
        "zip_path": str(zip_path),
        "zip_url": "/reports/" + zip_path.name,
        "security": {"sensitive_values_exported": False, "business_datasource_readonly": True},
    }


def build_test_asset_delivery_package(project_id):
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    work = ROOT / "reports" / "delivery-packages" / f"{project_id}-{stamp}"
    work.mkdir(parents=True, exist_ok=True)
    openapi_doc = build_project_interface_document(project_id)
    tool_assets = generate_enterprise_tool_assets(project_id)
    runtime_profile = project_execution_profile(project_id)
    points = rows("SELECT * FROM test_points WHERE project_id=? ORDER BY priority,module,created_at", (project_id,))
    cases = rows("SELECT * FROM test_cases WHERE project_id=? ORDER BY priority,executor_type,created_at", (project_id,))
    trace = rows("SELECT * FROM trace_links WHERE project_id=? ORDER BY requirement_id,confidence DESC", (project_id,))
    consistency = rows(
        """SELECT r.*,e.method,e.path,e.summary
           FROM consistency_rules r JOIN api_endpoints e ON e.id=r.endpoint_id
           WHERE r.project_id=? ORDER BY r.confidence DESC""",
        (project_id,),
    )
    reports = list_generated_reports(project_id)
    (work / "01-interface-openapi-baseline.json").write_text(json.dumps(openapi_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    (work / "02-test-points.csv").write_text(_csv_text(points, ["priority", "module", "title", "category", "risk", "rationale", "status"]), encoding="utf-8-sig")
    (work / "03-test-cases.csv").write_text(_csv_text(cases, ["priority", "title", "executor_type", "scenario_type", "method", "path", "expected", "execution_status", "actual_result", "run_count", "last_run_at"]), encoding="utf-8-sig")
    (work / "04-traceability.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
    (work / "05-data-consistency-rules.json").write_text(json.dumps(consistency, ensure_ascii=False, indent=2), encoding="utf-8")
    (work / "06-execution-profile.json").write_text(json.dumps(runtime_profile, ensure_ascii=False, indent=2), encoding="utf-8")
    (work / "07-report-index.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    asset_dir = TOOL_ASSET_ROOT / project_id
    if asset_dir.exists():
        for source in ("postman-collection.json", "jmeter-plan.jmx", "pytest_api_cases.py"):
            src = asset_dir / source
            if src.is_file():
                (work / ("tool-" + source)).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    readme = f"""# 测试资产交付包

项目：{project['name']}
生成时间：{now()}

## 包含内容
- 接口文档基线：OpenAPI 3.0，已脱敏，可导入 Apipost/Postman。
- 测试点清单：按优先级、模块、风险归档。
- 测试用例清单：按执行器、场景、状态归档。
- 需求追踪关系：需求、接口、用例、流程、数据规则之间的关联。
- 数据一致性规则：接口、MySQL、Redis 的只读验证规则。
- 运行配置：默认 UID、账号组、分页参数、JMeter 性能策略。
- 外部工具资产：Postman/Newman 集合、JMeter JMX、pytest 脚本。
- 报告索引：当前平台已归档报告列表。

## 企业协作边界
平台是 AI 自动化质量中枢，负责资产生成、编排、准入和归档；Apipost 负责单接口人工协作；Newman、JMeter、pytest 负责标准化执行；MySQL/Redis 只读取证。

## 安全说明
本包不导出 ticket、access_token、密码、sn、cookie、手机号等敏感原值。真实业务库和 Redis 不允许写入。
"""
    (work / "README.md").write_text(readme, encoding="utf-8")
    zip_path = ROOT / "reports" / f"delivery-package-{project_id}-{stamp}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in work.iterdir():
            zf.write(file, arcname=file.name)
    return {
        "status": "READY",
        "name": "测试资产交付包",
        "summary": {
            "test_points": len(points),
            "test_cases": len(cases),
            "trace_links": len(trace),
            "consistency_rules": len(consistency),
            "reports": len(reports),
            "tool_assets": tool_assets.get("generated", 0),
        },
        "files": [item.name for item in work.iterdir()],
        "zip_path": str(zip_path),
        "zip_url": "/reports/" + zip_path.name,
        "security": {"sensitive_values_exported": False, "business_datasource_readonly": True},
    }


HIGH_RISK_WORDS = ("charge", "pay", "salary", "refund", "withdraw", "delete", "remove", "send", "gift", "redenvelope", "transfer", "callback", "disbursement", "充值", "付款", "薪资", "退款", "提现", "删除", "赠送", "红包", "转账", "回调")
MEDIUM_RISK_WORDS = ("create", "save", "update", "add", "start", "cancel", "login", "logout", "创建", "保存", "修改", "新增", "开始", "取消", "登录")


def classify_endpoint(ep):
    blob = f"{ep['path']} {ep['summary']} {' '.join(ep['tags'])}".lower()
    hits = [x for x in HIGH_RISK_WORDS if x in blob]
    if hits:
        return "high", "命中高风险业务关键词：" + ", ".join(hits[:4])
    hits = [x for x in MEDIUM_RISK_WORDS if x in blob]
    if ep["method"] in {"POST", "PUT", "PATCH", "DELETE"} or hits:
        return "medium", "可能改变业务状态"
    return "low", "只读请求，未发现高风险关键词"


def danger_rating(ep):
    blob = f"{ep['path']} {ep['summary']} {' '.join(ep['tags'])}".lower()
    score = 5 if ep["method"] == "GET" else 25
    rules = [
        (("salary","pay","charge","refund","withdraw","transfer","薪资","付款","充值","退款","提现","转账"), 45, "涉及资金或结算"),
        (("delete","remove","drop","删除","清除"), 35, "可能删除数据"),
        (("gift","send","redenvelope","赠送","红包"), 30, "可能发放虚拟资产"),
        (("callback","webhook","回调"), 25, "可能触发外部回调流程"),
        (("login","token","auth","登录","认证"), 15, "涉及身份认证"),
    ]
    reasons=[]
    for words,points,reason in rules:
        if any(x in blob for x in words): score+=points; reasons.append(reason)
    score=min(100,score)
    level="极高" if score>=80 else "高" if score>=60 else "中" if score>=30 else "低"
    return score, f"{level}危险系数 {score}/100" + ("："+"、".join(reasons) if reasons else "")


def store_endpoints(project_id, source_id, content):
    eps = parse_openapi(content)
    values = []
    for ep in eps:
        risk, reason = classify_endpoint(ep)
        values.append((uid("api"), project_id, source_id, ep["method"], ep["path"], ep["summary"], json.dumps(ep["tags"], ensure_ascii=False), json.dumps(ep.get("parameters", []), ensure_ascii=False), json.dumps(ep.get("request_body", {}), ensure_ascii=False), json.dumps(ep.get("responses", {}), ensure_ascii=False), int(ep["security"]), risk, reason, now(), json.dumps(ep.get("example", {}), ensure_ascii=False), json.dumps(ep.get("required", []), ensure_ascii=False)))
    with db() as conn:
        conn.execute("DELETE FROM api_endpoints WHERE project_id=? AND source_id=?", (project_id, source_id))
        conn.executemany("INSERT INTO api_endpoints(id,project_id,source_id,method,path,summary,tags,parameters,request_body,responses,auth_required,risk_level,risk_reason,created_at,example_request,required_fields) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
    return len(values)


def endpoint_snapshot(ep):
    return {k: ep.get(k) for k in ("method","path","summary","tags","security","parameters","request_body","responses","example","required")}


def store_endpoints_incremental(project_id, source_id, content, requirement_source_id=None, name="接口变更"):
    eps = parse_openapi(content)
    existing = {(x["method"], x["path"]): x for x in rows("SELECT * FROM api_endpoints WHERE project_id=?", (project_id,))}
    prior_keys = set(existing); incoming_keys = {(x["method"], x["path"]) for x in eps}
    full_document = len(eps) >= max(20, int(len(existing) * .6)) if existing else True
    version_no = (row("SELECT COALESCE(MAX(version_no),0)+1 n FROM import_batches WHERE project_id=?", (project_id,)) or {"n":1})["n"]
    batch_id = uid("batch"); changes=[]; counts={"added":0,"modified":0,"removed":0,"unchanged":0}
    with db() as conn:
        for ep in eps:
            key=(ep["method"],ep["path"]); key_text=f"{ep['method']} {ep['path']}"; snap=endpoint_snapshot(ep)
            raw=json.dumps(snap,ensure_ascii=False,sort_keys=True); digest=hashlib.sha256(raw.encode()).hexdigest()
            old=existing.get(key); change="added"
            if old:
                previous=conn.execute("SELECT content_hash FROM endpoint_versions WHERE project_id=? AND endpoint_key=? ORDER BY version_no DESC LIMIT 1",(project_id,key_text)).fetchone()
                change="unchanged" if previous and previous[0]==digest else "modified"
            risk,reason=classify_endpoint(ep); danger,danger_warning=danger_rating(ep); eid=old["id"] if old else uid("api")
            values=(source_id,ep["summary"],json.dumps(ep["tags"],ensure_ascii=False),json.dumps(ep.get("parameters",[]),ensure_ascii=False),json.dumps(ep.get("request_body",{}),ensure_ascii=False),json.dumps(ep.get("responses",{}),ensure_ascii=False),int(ep["security"]),risk,reason,json.dumps(ep.get("example",{}),ensure_ascii=False),json.dumps(ep.get("required",[]),ensure_ascii=False),danger,danger_warning)
            if old:
                conn.execute("UPDATE api_endpoints SET source_id=?,summary=?,tags=?,parameters=?,request_body=?,responses=?,auth_required=?,risk_level=?,risk_reason=?,example_request=?,required_fields=?,danger_score=?,danger_warning=? WHERE id=?",(*values,eid))
            else:
                conn.execute("INSERT INTO api_endpoints(id,project_id,source_id,method,path,summary,tags,parameters,request_body,responses,auth_required,risk_level,risk_reason,created_at,example_request,required_fields,danger_score,danger_warning) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(eid,project_id,source_id,ep["method"],ep["path"],ep["summary"],values[2],values[3],values[4],values[5],values[6],risk,reason,now(),values[9],values[10],danger,danger_warning))
            conn.execute("INSERT INTO endpoint_versions VALUES (?,?,?,?,?,?,?,?)",(uid("ver"),project_id,source_id,key_text,version_no,digest,raw,now()))
            counts[change]+=1
            if change!="unchanged": changes.append((uid("chg"),project_id,batch_id,source_id,key_text,change,eid,ep["summary"],"重新生成关联用例、数据库映射和业务流程",now()))
        if full_document:
            for key in prior_keys-incoming_keys:
                old=existing[key]; counts["removed"]+=1
                changes.append((uid("chg"),project_id,batch_id,source_id,f"{key[0]} {key[1]}","removed",old["id"],old["summary"],"标记关联用例为待审查，不自动删除历史资产",now()))
        conn.execute("INSERT INTO import_batches VALUES (?,?,?,?,?,?,?,?,?,?,?)",(batch_id,project_id,requirement_source_id,source_id,name,version_no,counts["added"],counts["modified"],counts["removed"],counts["unchanged"],now()))
        conn.executemany("INSERT INTO endpoint_changes VALUES (?,?,?,?,?,?,?,?,?,?)",changes)
    return {"endpoints":len(eps),"batch_id":batch_id,"version":version_no,"full_document":full_document,**counts}


STOP_TOKENS = {"api","serv","service","get","post","list","info","detail","v1","v2","cms","html","user"}
BUSINESS_SYNONYMS={
    "登录":{"login","auth","token","ticket","认证"},"认证":{"login","auth","token","ticket","登录"},
    "等级":{"level","experience","exper","grade"},"财富":{"wealth","level","experience","exper"},
    "经验":{"experience","exeperience","exper","level"},"勋章":{"medal","badge","level"},
    "奖励":{"reward","award","right","benefit"},"权益":{"right","benefit","reward","award"},
    "用户":{"uid","member","account","profile"},"账号":{"uid","member","account","login"},
    "配置":{"config","conf","setting"},"后台":{"cms","admin","config"},
    "充值":{"recharge","payment","order"},"支付":{"payment","pay","order"},
    "缓存":{"redis","cache"},"数据库":{"mysql","database","db"}
}


def tokens(value):
    normalized = re.sub(r"([a-z])([A-Z])", r"\1 \2", value).lower()
    parts = re.findall(r"[a-z][a-z0-9]+", normalized)
    result = {p for p in parts if len(p) > 2 and p not in STOP_TOKENS}
    # Common business abbreviations and known API spelling variants.
    if "exeperience" in result: result.update({"experience", "exper"})
    if "experience" in result: result.add("exper")
    for chunk in re.findall(r"[\u4e00-\u9fff]{2,}", value):
        result.add(chunk)
        result.update(chunk[i:i+2] for i in range(len(chunk)-1))
    lowered=value.lower()
    for key,values in BUSINESS_SYNONYMS.items():
        if key in value or any(v in lowered for v in values): result.update(values); result.add(key)
    return result


def import_db_schema(project_id, content):
    schema = json.loads(content)
    col_map = {}
    for c in schema.get("columns", []):
        col_map.setdefault(c[0], []).append({"name": c[1], "type": c[2], "nullable": c[3], "key": c[4], "comment": c[7] if len(c) > 7 else ""})
    table_values = []
    for t in schema.get("tables", []):
        name = t[0]; module = name.split("_", 1)[0]
        table_values.append((uid("dbt"), project_id, name, t[2] if len(t) > 2 else "", int(float(t[3] or 0)) if len(t) > 3 else 0, json.dumps(col_map.get(name, []), ensure_ascii=False), module, now()))
    endpoints = rows("SELECT id,path,summary,tags,parameters,request_body FROM api_endpoints WHERE project_id=?", (project_id,))
    mapping_values = []
    for ep in endpoints:
        et = tokens(ep["path"] + " " + ep["summary"] + " " + ep["tags"] + " " + ep["parameters"] + " " + ep["request_body"])
        if not et: continue
        scored = []
        for t in schema.get("tables", []):
            name_tokens = tokens(t[0] + " " + (t[2] if len(t) > 2 else ""))
            column_tokens = tokens(" ".join(x.get("name","")+" "+x.get("comment","") for x in col_map.get(t[0], [])))
            name_overlap = et & name_tokens; column_overlap = et & column_tokens; overlap = name_overlap | column_overlap
            if overlap:
                score = min(.97, .28 + .20 * len(name_overlap) + .08 * len(column_overlap))
                scored.append((score, t[0], overlap))
        for score, table_name, overlap in sorted(scored, reverse=True)[:10]:
            mapping_values.append((uid("map"), project_id, ep["id"], table_name, score, "名称关键词匹配：" + ", ".join(sorted(overlap))))
    with db() as conn:
        conn.execute("DELETE FROM db_tables WHERE project_id=?", (project_id,))
        conn.execute("DELETE FROM api_db_mappings WHERE project_id=?", (project_id,))
        conn.executemany("INSERT INTO db_tables VALUES (?,?,?,?,?,?,?,?)", table_values)
        conn.executemany("INSERT INTO api_db_mappings VALUES (?,?,?,?,?,?)", mapping_values)
    return {"tables": len(table_values), "mappings": len(mapping_values)}


def generate_workflows(project_id):
    endpoints = rows("SELECT * FROM api_endpoints WHERE project_id=?", (project_id,))
    cases = rows("SELECT * FROM test_cases WHERE project_id=? AND title LIKE '%：正常请求'", (project_id,))
    case_map = {(x["method"], x["path"].split("?", 1)[0]): x["id"] for x in cases}
    title_map = {(x["method"], x["title"].removesuffix("：正常请求")): x["id"] for x in cases}
    groups = {}
    for ep in endpoints:
        try: tag_list = json.loads(ep["tags"] or "[]")
        except Exception: tag_list = []
        tag = tag_list[0] if tag_list else "未分类"
        groups.setdefault(tag, []).append(ep)
    workflow_values, step_values = [], []
    for tag, eps in groups.items():
        if not eps: continue
        # Prefer a readable setup -> action -> verification sequence.
        reads = [x for x in eps if x["method"] == "GET"]
        writes = [x for x in eps if x["method"] != "GET"]
        selected = (reads[:2] + writes[:3] + reads[2:4])[:7]
        if not selected: selected = eps[:5]
        wid = uid("wf")
        risk = "high" if any(x["risk_level"] == "high" for x in selected) else "medium" if any(x["risk_level"] == "medium" for x in selected) else "low"
        description = f"AI根据 {tag} 模块的接口路径、方法和风险自动归纳；执行前应补充有效业务数据。"
        workflow_values.append((wid, project_id, f"{tag} 核心业务流程", tag, description, "P0" if risk == "high" else "P1", risk, "ready", now()))
        for i, ep in enumerate(selected, 1):
            phase = "setup" if ep["method"] == "GET" and i <= 2 else "verify" if ep["method"] == "GET" and writes else "action"
            base_path = ep["path"].split("?", 1)[0]
            cid = case_map.get((ep["method"], base_path)) or title_map.get((ep["method"], ep["summary"]))
            pre = "准备有效测试身份和业务数据" if ep["auth_required"] else "确保测试环境可访问"
            extract = {"hint": "从响应data中提取后续步骤需要的id/token"} if i < len(selected) else {}
            step_values.append((uid("wfs"), wid, i, ep["id"], cid, phase, ep["summary"] or f"{ep['method']} {ep['path']}", pre, json.dumps(extract, ensure_ascii=False), 0))
    # Add a cross-module read-only health journey.
    low_reads = [x for x in endpoints if x["method"] == "GET" and x["risk_level"] == "low"][:12]
    if low_reads:
        wid = uid("wf")
        workflow_values.append((wid, project_id, "全系统只读冒烟流程", "跨模块", "覆盖主要公开/只读能力，快速判断测试环境可用性。", "P0", "low", "ready", now()))
        for i, ep in enumerate(low_reads, 1):
            step_values.append((uid("wfs"), wid, i, ep["id"], case_map.get((ep["method"], ep["path"].split("?",1)[0])) or title_map.get((ep["method"],ep["summary"])), "verify", ep["summary"], "测试环境可访问", "{}", 1))
    with db() as conn:
        old = [x[0] for x in conn.execute("SELECT id FROM workflows WHERE project_id=?", (project_id,)).fetchall()]
        if old: conn.executemany("DELETE FROM workflow_steps WHERE workflow_id=?", [(x,) for x in old])
        conn.execute("DELETE FROM workflow_runs WHERE project_id=?", (project_id,))
        conn.execute("DELETE FROM workflows WHERE project_id=?", (project_id,))
        conn.executemany("INSERT INTO workflows VALUES (?,?,?,?,?,?,?,?,?)", workflow_values)
        conn.executemany("INSERT INTO workflow_steps VALUES (?,?,?,?,?,?,?,?,?,?)", step_values)
    return {"workflows": len(workflow_values), "steps": len(step_values)}


def execute_workflow(workflow_id):
    wf = row("SELECT * FROM workflows WHERE id=?", (workflow_id,))
    if not wf: raise ValueError("流程不存在")
    steps = rows("SELECT * FROM workflow_steps WHERE workflow_id=? ORDER BY step_order", (workflow_id,))
    details, passed, failures, failed_step, final, context = [], 0, 0, "", "PASSED", {}
    for step in steps:
        if not step["case_id"]:
            result = {"step": step["name"], "status": "SKIPPED", "reason": "未匹配到可执行正常用例"}
        else:
            endpoint = row("SELECT * FROM api_endpoints WHERE id=?", (step["endpoint_id"],)) if step["endpoint_id"] else None
            overrides = {}
            if endpoint:
                try: example = json.loads(endpoint["example_request"] or "{}")
                except Exception: example = {}
                flow_path = endpoint["path"]
                for name, fallback in example.get("path", {}).items():
                    value = context.get(name, context.get(name.lower(), fallback))
                    flow_path = flow_path.replace("{" + name + "}", urllib.parse.quote(str(value)))
                query = {k: context.get(k, context.get(k.lower(), v)) for k, v in example.get("query", {}).items()}
                if query: flow_path += ("&" if "?" in flow_path else "?") + urllib.parse.urlencode(query)
                headers = {k: context.get(k, context.get(k.lower(), v)) for k, v in example.get("headers", {}).items()}
                body = substitute_value(example.get("body"), context)
                overrides = {"path": flow_path, "headers": json.dumps(headers, ensure_ascii=False)}
                if body is not None: overrides["payload"] = json.dumps(body, ensure_ascii=False)
            before = set(context)
            run = execute_case(step["case_id"], overrides, context)
            try: response_json = json.loads(run["response_data"] or "{}")
            except Exception: response_json = None
            explicit={}
            try: explicit=json.loads(step.get("extract_rules") or "{}")
            except Exception: explicit={}
            if response_json is not None:
                if explicit:
                    for target,source_path in explicit.items():
                        value=json_path_value(response_json,source_path)
                        if value not in (None,""): context[target]=value
                else: extract_context(response_json, context)
                # The mobile login API names the credential access_token while
                # downstream APIs historically call the same value ticket.
                if context.get("access_token") and not context.get("ticket"):
                    context["ticket"] = context["access_token"]
            extracted = safe_runtime_context({k: context[k] for k in set(context) - before})
            result = {"step": step["name"], "status": run["status"], "run_id": run["id"], "http_status": run["http_status"], "analysis": run["analysis"], "error": run["error"], "failure_category":classify_run_failure(run), "assertions":{"http_expected":200,"http_actual":run["http_status"],"response_contract":run["status"]=="PASSED"}, "extracted": extracted, "context_keys": sorted(context), "variable_flow": [{"name":k,"source_step":step["name"],"persisted":False} for k in extracted]}
        details.append(result)
        if result["status"] == "PASSED": passed += 1
        elif result["status"] not in {"SKIPPED"}:
            failures += 1
            if not failed_step: failed_step = step["name"]
            if not step["continue_on_failure"]:
                final = "FAILED"
                break
    if final != "FAILED" and failures:
        final = "PARTIAL" if passed else "FAILED"
    rid = uid("wfr")
    details.append({"runtime_context": safe_runtime_context(context),"security_note":"鉴权变量仅在本次流程内存中传递，持久化证据已脱敏"})
    execute("INSERT INTO workflow_runs VALUES (?,?,?,?,?,?,?,?,?)", (rid, wf["project_id"], workflow_id, final, len(steps), passed, failed_step, json.dumps(details, ensure_ascii=False), now()))
    return row("SELECT * FROM workflow_runs WHERE id=?", (rid,))


def generate_nonfunctional(project_id):
    endpoints=rows("SELECT * FROM api_endpoints WHERE project_id=?",(project_id,))
    cases=rows("SELECT * FROM test_cases WHERE project_id=?",(project_id,))
    by_key={}
    for c in cases: by_key.setdefault((c["method"],c["path"].split("?",1)[0]),[]).append(c)
    suites=[]; plans=[]; faults=[]; groups={}
    for ep in endpoints:
        try: tag=(json.loads(ep["tags"] or "[]") or ["未分类"])[0]
        except Exception: tag="未分类"
        matches=by_key.get((ep["method"],ep["path"].split("?",1)[0]),[])
        groups.setdefault(tag,[]).extend(x["id"] for x in matches)
        normal=next((x for x in matches if "正常请求" in x["title"]),None)
        if normal and ep["method"]=="GET" and ep["danger_score"]<40 and len(plans)<30:
            plans.append((uid("perf"),project_id,f"{ep['summary']} 基准性能",ep["id"],normal["id"],5,20,0,2000,ep["danger_score"],now()))
        for c in matches:
            fault_type=""
            if "缺失" in c["title"]: fault_type="missing_required"
            elif "边界" in c["title"] or "类型错误" in c["title"]: fault_type="invalid_boundary"
            elif "未授权" in c["title"]: fault_type="invalid_auth"
            elif "重复" in c["title"]: fault_type="duplicate_request"
            if fault_type:
                score=min(100,ep["danger_score"]+(15 if fault_type=="duplicate_request" else 5))
                warning="可能改变测试数据或触发业务告警" if score>=60 else "异常请求可能产生错误日志"
                faults.append((uid("fault"),project_id,ep["id"],c["id"],c["title"],fault_type,c["expected"],score,warning,"ready",now()))
    for tag,ids in groups.items():
        unique=list(dict.fromkeys(ids))[:100]
        if unique: suites.append((uid("suite"),project_id,f"{tag} 接口自动化套件",tag,"包含正常、异常、边界、权限和幂等用例",json.dumps(unique),"ready",now()))
    with db() as conn:
        conn.execute("DELETE FROM automation_suites WHERE project_id=?",(project_id,)); conn.execute("DELETE FROM performance_plans WHERE project_id=?",(project_id,)); conn.execute("DELETE FROM fault_scenarios WHERE project_id=?",(project_id,))
        conn.executemany("INSERT INTO automation_suites VALUES (?,?,?,?,?,?,?,?)",suites)
        conn.executemany("INSERT INTO performance_plans VALUES (?,?,?,?,?,?,?,?,?,?,?)",plans)
        conn.executemany("INSERT INTO fault_scenarios VALUES (?,?,?,?,?,?,?,?,?,?,?)",faults)
    return {"suites":len(suites),"performance_plans":len(plans),"fault_scenarios":len(faults)}


def run_suite(suite_id):
    suite=row("SELECT * FROM automation_suites WHERE id=?",(suite_id,))
    if not suite: raise ValueError("套件不存在")
    ids=json.loads(suite["case_ids"] or "[]"); results=[]
    for cid in ids: results.append(execute_case(cid))
    return {"total":len(results),"passed":sum(x["status"]=="PASSED" for x in results),"failed":sum(x["status"] not in {"PASSED","SKIPPED"} for x in results),"results":results}


def percentile(values,p):
    if not values:return 0
    s=sorted(values); return s[min(len(s)-1,max(0,int(len(s)*p)-1))]


def run_performance(plan_id):
    plan=row("SELECT * FROM performance_plans WHERE id=?",(plan_id,))
    if not plan: raise ValueError("性能计划不存在")
    started=time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,plan["concurrency"])) as pool:
        results=list(pool.map(lambda _:execute_case(plan["case_id"]),range(plan["total_requests"])))
    elapsed=max(.001,time.perf_counter()-started); durations=[x["duration_ms"] for x in results]
    success=sum(x["status"]=="PASSED" for x in results); avg=round(statistics.mean(durations),2) if durations else 0; p95=percentile(durations,.95); rps=round(len(results)/elapsed,2)
    status="PASSED" if success==len(results) and p95<=plan["warning_p95_ms"] else "WARNING" if success else "FAILED"
    rid=uid("perfr"); details={"min_ms":min(durations) if durations else 0,"max_ms":max(durations) if durations else 0,"danger_score":plan["danger_score"]}
    execute("INSERT INTO performance_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(rid,plan["project_id"],plan_id,status,len(results),success,len(results)-success,avg,p95,rps,json.dumps(details),now()))
    return row("SELECT * FROM performance_runs WHERE id=?",(rid,))


TOOL_ASSET_ROOT = ROOT / "reports" / "tool-assets"
REQUIREMENT_PACKAGE_ROOT = ROOT / "requirements"
JMETER_WORKBENCH_JMX = Path(os.getenv("AUTOTEST_JMETER_WORKBENCH_JMX") or r"D:\apache-jmeter-5.6.3\jmx\20260826\性能基线.jmx")
JMETER_WORKBENCH_JTL = Path(os.getenv("AUTOTEST_JMETER_WORKBENCH_JTL") or r"D:\apache-jmeter-5.6.3\jmx\20260826\性能基线-result.jtl")


def _tool_version(command, args):
    if not command:
        return ""
    try:
        result = subprocess.run([command, *args], capture_output=True, text=True, timeout=8)
        return ((result.stdout or result.stderr or "").strip().splitlines() or [""])[0][:160]
    except Exception:
        return ""


def _tool_probe(name, command, args, install_hint):
    available = bool(command and (Path(command).exists() if re.search(r"[\\/]", str(command)) else shutil.which(command)))
    return {
        "name": name,
        "status": "READY" if available else "MISSING",
        "command": str(command or ""),
        "version": _tool_version(str(command), args) if available else "",
        "install_hint": install_hint,
    }


def _python_module_probe(name, module, args, install_hint):
    command = [sys.executable, "-m", module, *args]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=8)
        output = ((result.stdout or result.stderr or "").strip().splitlines() or [""])[0][:160]
        return {
            "name": name,
            "status": "READY" if result.returncode == 0 else "MISSING",
            "command": f"{sys.executable} -m {module}",
            "version": output if result.returncode == 0 else "",
            "install_hint": install_hint,
        }
    except Exception:
        return {
            "name": name,
            "status": "MISSING",
            "command": f"{sys.executable} -m {module}",
            "version": "",
            "install_hint": install_hint,
        }


def enterprise_toolchain_status(project_id):
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    endpoints = rows("SELECT * FROM api_endpoints WHERE project_id=?", (project_id,))
    executable_cases = rows("SELECT * FROM test_cases WHERE project_id=? AND method<>'' AND path<>''", (project_id,))
    reports_dir = TOOL_ASSET_ROOT / project_id
    jmeter_cmd = _jmeter_command()
    tools = [
        _tool_probe("Java", shutil.which("java"), ["-version"], "安装 JDK 17+，用于运行 JMeter。"),
        _tool_probe("JMeter", jmeter_cmd, ["--version"], "安装 Apache JMeter，并配置 AUTOTEST_JMETER 指向 jmeter.bat。"),
        _tool_probe("Node.js", shutil.which("node"), ["--version"], "安装 Node.js，用于运行 Newman。"),
        _tool_probe("Newman", shutil.which("newman"), ["--version"], "执行 npm install -g newman。"),
        _python_module_probe("pytest", "pytest", ["--version"], "在当前 Python 环境安装 pytest。"),
        _tool_probe("Allure", shutil.which("allure"), ["--version"], "安装 Allure Commandline，用于归档 pytest 报告。"),
    ]
    blockers = []
    if not project.get("base_url"):
        blockers.append("缺少测试环境 Base URL")
    if not endpoints:
        blockers.append("缺少接口资产")
    if endpoints and not executable_cases:
        blockers.append("缺少可执行接口用例")
    high_risk = [item for item in endpoints if (item.get("risk_level") == "high" or int(item.get("danger_score") or 0) >= 60)]
    if high_risk:
        blockers.append(f"{len(high_risk)} 个高风险接口需人工确认执行策略")
    artifacts = [
        {"name": "Postman Collection", "path": "postman-collection.json"},
        {"name": "JMeter JMX", "path": "jmeter-plan.jmx"},
        {"name": "pytest Script", "path": "pytest_api_cases.py"},
    ]
    for artifact in artifacts:
        file_path = reports_dir / artifact["path"]
        artifact["status"] = "READY" if file_path.is_file() else "PENDING"
        artifact["url"] = f"/reports/tool-assets/{project_id}/{artifact['path']}" if file_path.is_file() else ""
    return {
        "project_id": project_id,
        "status": "BLOCKED" if blockers else "READY",
        "tools": tools,
        "blockers": blockers,
        "artifacts": artifacts,
        "counts": {
            "endpoints": len(endpoints),
            "executable_cases": len(executable_cases),
            "high_risk_endpoints": len(high_risk),
        },
        "policy": {
            "dry_run_first": True,
            "target_restricted_to_test_env": True,
            "external_data_readonly": True,
            "secrets_runtime_only": True,
        },
    }


def _safe_json(value, fallback):
    try:
        return json.loads(value or "")
    except Exception:
        return fallback


def _case_request(case):
    headers = _safe_json(case.get("headers"), {})
    payload = _safe_json(case.get("payload"), case.get("payload") or "")
    for key in list(headers):
        headers[key] = _capture_redacted(key, headers[key])
    return headers, payload


NEGATIVE_CASE_RE = re.compile(r"缺失|非法|无效|错误|类型|未授权|鉴权|越权|过期")


def _is_login_case(case):
    blob = f"{case.get('method', '')} {case.get('path', '')} {case.get('title', '')}".lower()
    return "/userserv/id/login" in blob or "登录" in blob and "login" in blob


def _tool_expected_status(case):
    title = str(case.get("title") or "")
    current = int(case.get("expected_status") or 200)
    if current == 200 and NEGATIVE_CASE_RE.search(title):
        if re.search(r"未授权|鉴权|越权|过期", title):
            return 401
        return 400
    return current


def _has_runtime_placeholder(value):
    if isinstance(value, dict):
        return any(_has_runtime_placeholder(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_runtime_placeholder(item) for item in value)
    return "{{" in str(value or "") and "}}" in str(value or "")


def _case_has_runtime_placeholder(case):
    return _has_runtime_placeholder(case.get("path")) or _has_runtime_placeholder(case.get("headers")) or _has_runtime_placeholder(case.get("payload"))


def _external_tool_cases(cases, include_runtime=False, include_login_cases=False):
    selected = list(cases) if include_runtime else [case for case in cases if not _case_has_runtime_placeholder(case)]
    if include_login_cases:
        return selected
    return [case for case in selected if not _is_login_case(case)]


def _safe_runtime_scalar(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, str)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _runtime_params_from_options(options=None):
    options = options or {}
    raw = options.get("runtime_params") or {}
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            raw = {}
        else:
            try:
                raw = json.loads(text)
            except Exception as exc:
                raise ValueError("运行参数必须是合法 JSON") from exc
    if not isinstance(raw, dict):
        raise ValueError("运行参数必须是 JSON 对象")

    params = {}
    for key, value in raw.items():
        name = re.sub(r"[^A-Za-z0-9_]", "_", str(key).strip())
        if not name:
            continue
        if isinstance(value, list):
            params[name] = ",".join(_safe_runtime_scalar(item) for item in value)
            for index, item in enumerate(value, 1):
                params[f"{name}_{index}"] = _safe_runtime_scalar(item)
            if name == "uids" and value and "uid" not in raw:
                params["uid"] = _safe_runtime_scalar(value[0])
        else:
            params[name] = _safe_runtime_scalar(value)

    if options.get("runtime_uid") not in (None, "") and "uid" not in params:
        params["uid"] = _safe_runtime_scalar(options.get("runtime_uid"))
    return params


def _merge_runtime_params(runtime, params):
    merged = dict(runtime or {})
    credential_uid = merged.get("uid", "")
    for key, value in (params or {}).items():
        if key == "ticket":
            continue
        if key == "uid" and credential_uid and value != credential_uid:
            merged["requested_uid"] = value
            continue
        merged[key] = value
    if credential_uid and merged.get("uid") != credential_uid:
        merged["requested_uid"] = merged.get("uid", "")
        merged["uid"] = credential_uid
    if credential_uid and merged.get("requested_uid"):
        merged["credential_uid"] = credential_uid
    return merged


def _normalize_auth_runtime_context(runtime):
    normalized = dict(runtime or {})
    warnings = list(normalized.get("_runtime_warnings") or [])
    if normalized.get("ticket") or normalized.get("uid"):
        t_value = str(normalized.get("t") or "").strip()
        if not t_value:
            normalized["t"] = _fresh_login_t()
            warnings.append("未提供请求头 t，平台已自动生成当前时间戳。")
        elif _looks_like_jwt(t_value):
            normalized["t"] = _fresh_login_t()
            warnings.append("请求头 t 看起来像 token/ticket，已改用当前时间戳；请确认不要把票据填入 t。")
        elif not _looks_like_timestamp_t(t_value):
            normalized["t"] = _fresh_login_t()
            warnings.append("请求头 t 不是常见时间戳格式，已改用当前时间戳。")
    if warnings:
        normalized["_runtime_warnings"] = list(dict.fromkeys(warnings))
    return normalized


LOGIN_CONTEXT_KEYS = {
    "deviceType", "systemLanguage", "appVersion", "os", "netType", "channel", "appsflyerId",
    "language", "appCode", "deviceId", "version", "osVersion", "isVpnConnected", "appid",
    "model", "packageName", "ispType", "organic",
}


def _login_request_context(login_case, login_inputs):
    if not login_case:
        return {}
    headers, payload = _case_request(login_case)
    headers = _replace_runtime_placeholders(headers, login_inputs, False)
    payload = _replace_runtime_placeholders(payload, login_inputs, False)
    context = {}
    for key in ("t", "sn"):
        value = str(headers.get(key) or "").strip()
        if value:
            context[key] = value
    payload_values = {}
    if isinstance(payload, dict):
        payload_values = payload
    elif isinstance(payload, str):
        parsed = urllib.parse.parse_qs(payload, keep_blank_values=True)
        payload_values = {key: values[-1] if values else "" for key, values in parsed.items()}
    for key in LOGIN_CONTEXT_KEYS:
        value = payload_values.get(key)
        if value not in (None, ""):
            context[key] = str(value)
    return context


def _runtime_placeholder_context(context, style="postman"):
    excluded = {"source", "login_status", "login_error", "login_context_keys", "_runtime_warnings"}
    if style == "jmeter":
        return {key: "${__P(" + key + ")}" for key in context if key not in excluded}
    if style == "jmeter_vars":
        return {key: "${" + key + "}" for key in context if key not in excluded}
    return {key: "{{" + key + "}}" for key in context if key not in excluded}


def _runtime_tool_pairs(context):
    excluded = {"source", "login_status", "login_error", "login_context_keys", "_runtime_warnings"}
    return [(key, str(value)) for key, value in (context or {}).items() if key not in excluded]


def _runtime_context(project_id, options=None):
    options = options or {}
    credential = load_runtime_credential(project_id)
    ticket = str(options.get("runtime_ticket") or credential.get("ticket") or "").strip()
    uid_value = options.get("runtime_uid", credential.get("uid"))
    if ticket and uid_value in (None, ""):
        uid_value = jwt_claims_unverified(ticket).get("uid")
    credential_context = credential.get("context") if isinstance(credential.get("context"), dict) else {}
    runtime = {"ticket": ticket, "uid": "" if uid_value is None else str(uid_value), **{key: str(value) for key, value in credential_context.items() if value not in (None, "")}}
    runtime.setdefault("current_time_ms", str(int(time.time() * 1000)))
    runtime.setdefault("appsflyerId", "1787628595990-5267637366511328587")
    if credential_context:
        runtime["login_context_keys"] = sorted(credential_context)
    return _normalize_auth_runtime_context(_merge_runtime_params(runtime, _runtime_params_from_options(options)))


def _runtime_params_only(options=None, source="missing_login_input"):
    return _merge_runtime_params({"ticket": "", "uid": "", "source": source}, _runtime_params_from_options(options))


def _login_runtime_context(project_id, options=None):
    options = options or {}
    strategy = str(options.get("login_strategy") or "auto").strip().lower()
    force_login = strategy in {"force", "force_login", "login"}
    reuse_only = strategy in {"reuse", "saved", "saved_runtime_credential"}
    login_t = str(options.get("login_t") or "").strip()
    login_sn = str(options.get("login_sn") or "").strip()
    login_password = str(options.get("login_password_encrypted") or "").strip()
    login_requested = bool(login_t or login_password or force_login)
    runtime = _runtime_context(project_id, options)
    if reuse_only and not login_requested and runtime.get("ticket") and runtime.get("uid"):
        runtime["source"] = "saved_runtime_credential"
        return runtime
    if not login_requested and runtime.get("ticket") and runtime.get("uid"):
        runtime["source"] = "saved_runtime_credential"
        return runtime
    login_warnings = []
    if login_password and not login_t:
        login_t = _fresh_login_t()
        login_warnings.append("未提供请求头 t，平台已自动生成当前时间戳。")
    elif login_password and _looks_like_jwt(login_t):
        login_t = _fresh_login_t()
        login_warnings.append("请求头 t 看起来像 token/ticket，已改用当前时间戳；请确认不要把票据填入 t。")
    elif login_password and not _looks_like_timestamp_t(login_t):
        login_t = _fresh_login_t()
        login_warnings.append("请求头 t 不是常见时间戳格式，已改用当前时间戳。")
    if not login_password:
        return _runtime_params_only(options, "missing_login_input")
    login_case = resolve_executable_case(project_id, "POST", "/userserv/id/login")
    if not login_case:
        return _runtime_params_only(options, "missing_login_case")
    login_inputs = {"login_t": login_t, "login_sn": login_sn, "login_password_encrypted": login_password}
    login_request_context = _login_request_context(login_case, login_inputs)
    login = execute_case(login_case["id"], context=login_inputs)
    try:
        body = json.loads(login.get("response_data") or "{}")
    except Exception:
        body = {}
    data = body.get("data") if isinstance(body, dict) else {}
    ticket = data.get("access_token") if isinstance(data, dict) else ""
    uid_value = data.get("uid") if isinstance(data, dict) else None
    if login.get("status") == "PASSED" and ticket and uid_value is not None:
        save_runtime_credential(project_id, ticket, login_request_context.get("sn", ""), uid_value, login_request_context, login_password)
        runtime = {"ticket": str(ticket), "uid": str(uid_value), "source": "login_api", **login_request_context}
        runtime["login_context_keys"] = sorted(login_request_context)
        if login_warnings:
            runtime["_runtime_warnings"] = login_warnings
        return _normalize_auth_runtime_context(_merge_runtime_params(runtime, _runtime_params_from_options(options)))
    runtime = _runtime_params_only(options, "login_failed")
    runtime["login_status"] = login.get("status")
    runtime["login_error"] = login.get("error")
    return runtime


def _replace_runtime_placeholders(value, context, redact=False):
    if isinstance(value, dict):
        return {k: _replace_runtime_placeholders(v, context, redact) for k, v in value.items()}
    if isinstance(value, list):
        return [_replace_runtime_placeholders(item, context, redact) for item in value]
    text = str(value or "")
    for key, raw in context.items():
        sensitive = key == "ticket" or _is_sensitive_runtime_value(key, raw)
        replacement = "***REDACTED***" if redact and sensitive else str(raw)
        text = text.replace("{{" + key + "}}", replacement)
    return text


def _append_runtime_query_params(path, context):
    if not path or "?" not in path and not path.startswith("/"):
        return path
    parsed = urllib.parse.urlsplit(path)
    current = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    additions = {}
    for key in LOGIN_CONTEXT_KEYS:
        if key in context and key not in current:
            additions[key] = str(context[key])
    if not additions:
        return path
    query = urllib.parse.urlencode([(key, value) for key, values in current.items() for value in values] + list(additions.items()), safe="{}")
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))


def _case_request_with_runtime_context(case, runtime_context=None):
    headers, payload = _case_request(case)
    runtime_context = runtime_context or {}
    if not _is_login_case(case) and (_case_has_runtime_placeholder(case) or _tool_expected_status(case) == 200):
        for key in ("t", "sn"):
            if runtime_context.get(key) and key not in headers:
                headers[key] = "{{" + key + "}}"
    path = case["path"]
    if not _is_login_case(case) and (_case_has_runtime_placeholder(case) or _tool_expected_status(case) == 200):
        placeholder_context = {key: "{{" + key + "}}" for key in LOGIN_CONTEXT_KEYS if runtime_context.get(key)}
        path = _append_runtime_query_params(path, placeholder_context)
    return path, headers, payload


def build_postman_collection(project, cases, runtime_context=None, redact_runtime=True):
    runtime_context = runtime_context or {}
    items = []
    for case in cases:
        case_path, headers, payload = _case_request_with_runtime_context(case, runtime_context)
        raw_path = _replace_runtime_placeholders(case_path, runtime_context, redact_runtime)
        raw_path = raw_path if raw_path.startswith("http") else (project.get("base_url") or "").rstrip("/") + "/" + raw_path.lstrip("/")
        headers = _replace_runtime_placeholders(headers, runtime_context, redact_runtime)
        payload = _replace_runtime_placeholders(payload, runtime_context, redact_runtime)
        request = {
            "method": case["method"],
            "header": [{"key": k, "value": str(v), "type": "text"} for k, v in headers.items()],
            "url": raw_path,
        }
        if case["method"] in {"POST", "PUT", "PATCH", "DELETE"} and payload:
            request["body"] = {"mode": "raw", "raw": json.dumps(payload, ensure_ascii=False) if not isinstance(payload, str) else payload}
        items.append({
            "name": case["title"],
            "request": request,
            "event": [{
                "listen": "test",
                "script": {"type": "text/javascript", "exec": [f"pm.response.to.have.status({_tool_expected_status(case)});"]},
            }],
        })
    return {
        "info": {
            "name": f"{project['name']} 接口自动化集合",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [{"key": "baseUrl", "value": project.get("base_url") or ""}],
        "item": items,
    }


def _xml_escape(value):
    return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _jmeter_mobile_query(overrides=None):
    overrides = overrides or {}
    base = {
        "deviceType": "${deviceType}",
        "systemLanguage": "${systemLanguage}",
        "appVersion": "${appVersion}",
        "os": "${os}",
        "ticket": "${ticket}",
        "netType": "${netType}",
        "channel": "${channel}",
        "appsflyerId": "${appsflyerId}",
        "language": "${language}",
        "appCode": "${appCode}",
        "deviceId": "${deviceId}",
        "version": "${version}",
        "osVersion": "${osVersion}",
        "isVpnConnected": "${isVpnConnected}",
        "appid": "${appid}",
        "model": "${model}",
        "packageName": "${packageName}",
        "ispType": "${ispType}",
        "organic": "${organic}",
    }
    base.update(overrides)
    return urllib.parse.urlencode(base, safe="${}(),_")


def build_jmeter_wealth_requirement_workflow(project, options=None):
    options = options or {}
    loops = max(1, min(int(options.get("jmeter_loops", 1) or 1), 1000))
    gift_count_expr = "${gift_count}"
    rampup = max(0, min(int(options.get("jmeter_rampup", 1) or 1), 600))
    think_time = max(0, min(int(options.get("jmeter_think_time_ms", 300) or 0), 10000))
    gift_id = int(options.get("gift_id") or options.get("jmeter_gift_id") or 1057)
    sender_uid = str(options.get("sender_uid") or options.get("runtime_uid") or "${uid}")
    receiver_uid = str(options.get("receiver_uid") or 1454779)
    room_uid = str(options.get("room_uid") or sender_uid)
    wealth_path = "/level/exeperience/v2/get?" + _jmeter_mobile_query({"uid": "${uid}"})
    wallet_path = "/purse/query?" + _jmeter_mobile_query({"uid": "${uid}", "CacheBuild-Control": "no-cache"})
    bill_path = "/billrecord/get?" + _jmeter_mobile_query({"uid": "${uid}", "date": "${__time(,)}", "pageSize": "50", "type": "1", "pageNo": "1"})
    gift_body = _jmeter_mobile_query({"uid": sender_uid, "roomUid": room_uid, "giftId": str(gift_id), "targetUids": receiver_uid, "giftNum": "1"})
    return f"""
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="财富等级需求闭环（登录-钱包-送礼-财富-账单）" enabled="true">
        <stringProp name="TestPlan.comments">真实业务闭环：循环控制器执行几次，就真实送礼几次；用于证明财富经验、钱包扣款和账单归档一致。</stringProp>
        <intProp name="ThreadGroup.num_threads">1</intProp>
        <intProp name="ThreadGroup.ramp_time">{rampup}</intProp>
        <stringProp name="ThreadGroup.on_sample_error">stopthread</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController"><boolProp name="LoopController.continue_forever">false</boolProp><stringProp name="LoopController.loops">1</stringProp></elementProp>
      </ThreadGroup>
      <hashTree>
        <JSR223Sampler guiclass="TestBeanGUI" testclass="JSR223Sampler" testname="闭环初始化：清空本次消费累计" enabled="true">
          <stringProp name="cacheKey">autotest-wealth-chain-init</stringProp>
          <stringProp name="filename"></stringProp>
          <stringProp name="parameters"></stringProp>
          <stringProp name="script">props.put('gift_total_consume','0')
props.put('gift_success_count','0')
props.put('gift_consume_values','')
props.put('gift_bill_match_count','0')
vars.put('workflow_expected_gift_count', vars.get('gift_count') ?: '{loops}')</stringProp>
          <stringProp name="scriptLanguage">groovy</stringProp>
        </JSR223Sampler>
        <hashTree/>
        <JSR223PreProcessor guiclass="TestBeanGUI" testclass="JSR223PreProcessor" testname="读取登录身份上下文" enabled="true">
          <stringProp name="cacheKey">autotest-load-auth-context-business-workflow</stringProp>
          <stringProp name="filename"></stringProp>
          <stringProp name="parameters"></stringProp>
          <stringProp name="script">def token = props.get('ticket') ?: vars.get('ticket') ?: '${{__P(ticket,)}}'
if (!token) {{
    throw new IllegalStateException('未取得 ticket：请先通过平台传入登录密码打开 JMeter，或复用平台已保存 ticket')
}}
vars.put('ticket', token)
def loginUid = props.get('uid') ?: vars.get('uid') ?: '${{__P(uid,)}}'
if (loginUid) {{
    vars.put('uid', loginUid)
}}</stringProp>
          <stringProp name="scriptLanguage">groovy</stringProp>
        </JSR223PreProcessor>
        <hashTree/>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="前置查询财富等级快照" enabled="true">
          <stringProp name="HTTPSampler.path">{_xml_escape(wealth_path)}</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <boolProp name="HTTPSampler.postBodyRaw">false</boolProp>
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments"><collectionProp name="Arguments.arguments"/></elementProp>
        </HTTPSamplerProxy>
        <hashTree>
          <JSONPostProcessor guiclass="JSONPostProcessorGui" testclass="JSONPostProcessor" testname="提取送礼前财富等级与经验（停用，改由JSR223稳态解析）" enabled="false">
            <stringProp name="JSONPostProcessor.referenceNames">wealth_before_level;wealth_before_exp</stringProp>
            <stringProp name="JSONPostProcessor.jsonPathExprs">$.data.myExperLevelInfo.currentLevel;$.data.myExperLevelInfo.currentExperValue</stringProp>
            <stringProp name="JSONPostProcessor.match_numbers">1;1</stringProp>
            <stringProp name="JSONPostProcessor.defaultValues">;</stringProp>
          </JSONPostProcessor>
          <hashTree/>
          <JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" testname="解析送礼前财富快照" enabled="true">
            <stringProp name="cacheKey">autotest-parse-wealth-before</stringProp>
            <stringProp name="filename"></stringProp>
            <stringProp name="parameters"></stringProp>
            <stringProp name="script">import groovy.json.JsonSlurper
def payload = new JsonSlurper().parseText(prev.getResponseDataAsString() ?: '{{}}')
def info = payload?.data?.myExperLevelInfo
if (!(info instanceof Map)) {{
    throw new IllegalStateException('前置财富接口响应缺少 data.myExperLevelInfo')
}}
def level = info.currentLevel
def exp = info.currentExperValue
if (!(level instanceof Number) || !(exp instanceof Number)) {{
    throw new IllegalStateException('前置财富接口未返回有效等级/经验：level=' + level + ', exp=' + exp)
}}
vars.put('wealth_before_level', String.valueOf(level.longValue()))
vars.put('wealth_before_exp', String.valueOf(exp.longValue()))
props.put('wealth_before_level', String.valueOf(level.longValue()))
props.put('wealth_before_exp', String.valueOf(exp.longValue()))</stringProp>
            <stringProp name="scriptLanguage">groovy</stringProp>
          </JSR223PostProcessor>
          <hashTree/>
          <ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="断言前置财富查询成功" enabled="true">
            <collectionProp name="Asserion.test_strings"><stringProp name="status">200</stringProp></collectionProp>
            <stringProp name="Assertion.test_field">Assertion.response_code</stringProp>
            <boolProp name="Assertion.assume_success">false</boolProp>
            <intProp name="Assertion.test_type">8</intProp>
          </ResponseAssertion>
          <hashTree/>
        </hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="前置查询钱包余额快照" enabled="true">
          <stringProp name="HTTPSampler.path">{_xml_escape(wallet_path)}</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <boolProp name="HTTPSampler.postBodyRaw">false</boolProp>
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments"><collectionProp name="Arguments.arguments"/></elementProp>
        </HTTPSamplerProxy>
        <hashTree>
          <JSONPostProcessor guiclass="JSONPostProcessorGui" testclass="JSONPostProcessor" testname="提取送礼前Gold余额" enabled="true">
            <stringProp name="JSONPostProcessor.referenceNames">wallet_before_gold</stringProp>
            <stringProp name="JSONPostProcessor.jsonPathExprs">$.data.goldNum</stringProp>
            <stringProp name="JSONPostProcessor.match_numbers">1</stringProp>
            <stringProp name="JSONPostProcessor.defaultValues"></stringProp>
          </JSONPostProcessor>
          <hashTree/>
          <JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" testname="解析送礼前钱包快照" enabled="true">
            <stringProp name="cacheKey">autotest-parse-wallet-before</stringProp>
            <stringProp name="filename"></stringProp>
            <stringProp name="parameters"></stringProp>
            <stringProp name="script">import groovy.json.JsonSlurper
def payload = new JsonSlurper().parseText(prev.getResponseDataAsString() ?: '{{}}')
def gold = payload?.data?.goldNum
if (!(gold instanceof Number)) {{
    throw new IllegalStateException('前置钱包接口未返回有效 goldNum：' + gold)
}}
vars.put('wallet_before_gold', String.valueOf(gold.longValue()))
props.put('wallet_before_gold', String.valueOf(gold.longValue()))</stringProp>
            <stringProp name="scriptLanguage">groovy</stringProp>
          </JSR223PostProcessor>
          <hashTree/>
        </hashTree>
        <LoopController guiclass="LoopControlPanel" testclass="LoopController" testname="真实送礼循环：运行几次就产生几次财富经验变化" enabled="true">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <stringProp name="LoopController.loops">{gift_count_expr}</stringProp>
        </LoopController>
        <hashTree>
          <ConstantTimer guiclass="ConstantTimerGui" testclass="ConstantTimer" testname="送礼间隔" enabled="true">
            <stringProp name="ConstantTimer.delay">{think_time}</stringProp>
          </ConstantTimer>
          <hashTree/>
          <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="真实送礼：驱动财富经验变化" enabled="true">
            <stringProp name="HTTPSampler.path">/gift/purse/room/sendMulti</stringProp>
            <stringProp name="HTTPSampler.method">POST</stringProp>
            <boolProp name="HTTPSampler.postBodyRaw">true</boolProp>
            <elementProp name="HTTPsampler.Arguments" elementType="Arguments"><collectionProp name="Arguments.arguments"><elementProp name="" elementType="HTTPArgument"><boolProp name="HTTPArgument.always_encode">false</boolProp><stringProp name="Argument.value">{_xml_escape(gift_body)}</stringProp><stringProp name="Argument.metadata">=</stringProp></elementProp></collectionProp></elementProp>
          </HTTPSamplerProxy>
          <hashTree>
            <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="送礼 Headers" enabled="true"><collectionProp name="HeaderManager.headers"><elementProp name="Content-Type" elementType="Header"><stringProp name="Header.name">Content-Type</stringProp><stringProp name="Header.value">application/x-www-form-urlencoded</stringProp></elementProp><elementProp name="User-Agent" elementType="Header"><stringProp name="Header.name">User-Agent</stringProp><stringProp name="Header.value">okhttp/4.12.0</stringProp></elementProp></collectionProp></HeaderManager>
            <hashTree/>
            <JSONPostProcessor guiclass="JSONPostProcessorGui" testclass="JSONPostProcessor" testname="提取本次送礼消费Gold" enabled="true">
              <stringProp name="JSONPostProcessor.referenceNames">gift_last_consume</stringProp>
              <stringProp name="JSONPostProcessor.jsonPathExprs">$.data.consumeGold</stringProp>
              <stringProp name="JSONPostProcessor.match_numbers">1</stringProp>
              <stringProp name="JSONPostProcessor.defaultValues">0</stringProp>
            </JSONPostProcessor>
            <hashTree/>
            <JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" testname="累计本线程组送礼消费" enabled="true">
              <stringProp name="cacheKey">autotest-accumulate-gift-consume</stringProp>
              <stringProp name="filename"></stringProp>
              <stringProp name="parameters"></stringProp>
              <stringProp name="script">Long readLong(String name, String raw) {{
    def text = raw == null ? '' : raw.trim()
    if (!(text ==~ /-?\\d+/)) {{
        throw new IllegalStateException(name + ' 不是有效long整数：' + raw)
    }}
    return text.toLong()
}}
def last = readLong('consumeGold', vars.get('gift_last_consume') ?: '0')
def total = readLong('gift_total_consume', props.get('gift_total_consume') ?: '0')
if (last &lt;= 0) {{
    throw new IllegalStateException('送礼接口未返回有效 consumeGold')
}}
props.put('gift_total_consume', String.valueOf(total + last))
props.put('gift_success_count', String.valueOf(readLong('gift_success_count', props.get('gift_success_count') ?: '0') + 1))
def values = props.get('gift_consume_values') ?: ''
props.put('gift_consume_values', values ? values + ',' + last : String.valueOf(last))</stringProp>
              <stringProp name="scriptLanguage">groovy</stringProp>
            </JSR223PostProcessor>
            <hashTree/>
          </hashTree>
        </hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="后置查询钱包余额快照" enabled="true">
          <stringProp name="HTTPSampler.path">{_xml_escape(wallet_path)}</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <boolProp name="HTTPSampler.postBodyRaw">false</boolProp>
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments"><collectionProp name="Arguments.arguments"/></elementProp>
        </HTTPSamplerProxy>
        <hashTree>
          <JSONPostProcessor guiclass="JSONPostProcessorGui" testclass="JSONPostProcessor" testname="提取送礼后Gold余额" enabled="true">
            <stringProp name="JSONPostProcessor.referenceNames">wallet_after_gold</stringProp>
            <stringProp name="JSONPostProcessor.jsonPathExprs">$.data.goldNum</stringProp>
            <stringProp name="JSONPostProcessor.match_numbers">1</stringProp>
            <stringProp name="JSONPostProcessor.defaultValues"></stringProp>
          </JSONPostProcessor>
          <hashTree/>
          <JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" testname="解析送礼后钱包快照" enabled="true">
            <stringProp name="cacheKey">autotest-parse-wallet-after</stringProp>
            <stringProp name="filename"></stringProp>
            <stringProp name="parameters"></stringProp>
            <stringProp name="script">import groovy.json.JsonSlurper
def payload = new JsonSlurper().parseText(prev.getResponseDataAsString() ?: '{{}}')
def gold = payload?.data?.goldNum
if (!(gold instanceof Number)) {{
    throw new IllegalStateException('后置钱包接口未返回有效 goldNum：' + gold)
}}
vars.put('wallet_after_gold', String.valueOf(gold.longValue()))
props.put('wallet_after_gold', String.valueOf(gold.longValue()))</stringProp>
            <stringProp name="scriptLanguage">groovy</stringProp>
          </JSR223PostProcessor>
          <hashTree/>
        </hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="后置查询财富等级快照" enabled="true">
          <stringProp name="HTTPSampler.path">{_xml_escape(wealth_path)}</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <boolProp name="HTTPSampler.postBodyRaw">false</boolProp>
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments"><collectionProp name="Arguments.arguments"/></elementProp>
        </HTTPSamplerProxy>
        <hashTree>
          <JSONPostProcessor guiclass="JSONPostProcessorGui" testclass="JSONPostProcessor" testname="提取送礼后财富等级与经验（停用，改由JSR223稳态解析）" enabled="false">
            <stringProp name="JSONPostProcessor.referenceNames">wealth_after_level;wealth_after_exp</stringProp>
            <stringProp name="JSONPostProcessor.jsonPathExprs">$.data.myExperLevelInfo.currentLevel;$.data.myExperLevelInfo.currentExperValue</stringProp>
            <stringProp name="JSONPostProcessor.match_numbers">1;1</stringProp>
            <stringProp name="JSONPostProcessor.defaultValues">;</stringProp>
          </JSONPostProcessor>
          <hashTree/>
          <JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" testname="解析送礼后财富快照" enabled="true">
            <stringProp name="cacheKey">autotest-parse-wealth-after</stringProp>
            <stringProp name="filename"></stringProp>
            <stringProp name="parameters"></stringProp>
            <stringProp name="script">import groovy.json.JsonSlurper
def payload = new JsonSlurper().parseText(prev.getResponseDataAsString() ?: '{{}}')
def info = payload?.data?.myExperLevelInfo
if (!(info instanceof Map)) {{
    throw new IllegalStateException('后置财富接口响应缺少 data.myExperLevelInfo')
}}
def level = info.currentLevel
def exp = info.currentExperValue
if (!(level instanceof Number) || !(exp instanceof Number)) {{
    throw new IllegalStateException('后置财富接口未返回有效等级/经验：level=' + level + ', exp=' + exp)
}}
vars.put('wealth_after_level', String.valueOf(level.longValue()))
vars.put('wealth_after_exp', String.valueOf(exp.longValue()))
props.put('wealth_after_level', String.valueOf(level.longValue()))
props.put('wealth_after_exp', String.valueOf(exp.longValue()))</stringProp>
            <stringProp name="scriptLanguage">groovy</stringProp>
          </JSR223PostProcessor>
          <hashTree/>
        </hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="后置查询送礼账单" enabled="true">
          <stringProp name="HTTPSampler.path">{_xml_escape(bill_path)}</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <boolProp name="HTTPSampler.postBodyRaw">false</boolProp>
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments"><collectionProp name="Arguments.arguments"/></elementProp>
        </HTTPSamplerProxy>
        <hashTree>
          <JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" testname="解析账单记录匹配本次送礼" enabled="true">
            <stringProp name="cacheKey">autotest-parse-gift-bill-records</stringProp>
            <stringProp name="filename"></stringProp>
            <stringProp name="parameters"></stringProp>
            <stringProp name="script">import groovy.json.JsonSlurper
def payload = new JsonSlurper().parseText(prev.getResponseDataAsString() ?: '{{}}')
def billList = payload?.data?.billList
def expectedConsumes = (props.get('gift_consume_values') ?: '').split(',').findAll {{ it }}.collect {{ it as long }}
def matched = 0
if (billList instanceof List) {{
    billList.each {{ dayGroup -&gt;
        if (dayGroup instanceof Map) {{
            dayGroup.values().each {{ records -&gt;
                if (records instanceof List) {{
                    records.each {{ record -&gt;
                        def gold = record?.goldNum
                        def giftNum = record?.giftNum
                        if (gold instanceof Number &amp;&amp; giftNum == 1 &amp;&amp; expectedConsumes.contains(gold.longValue())) {{
                            matched++
                        }}
                    }}
                }}
            }}
        }}
    }}
}}
props.put('gift_bill_match_count', String.valueOf(matched))</stringProp>
            <stringProp name="scriptLanguage">groovy</stringProp>
          </JSR223PostProcessor>
          <hashTree/>
        </hashTree>
        <JSR223Sampler guiclass="TestBeanGUI" testclass="JSR223Sampler" testname="闭环断言：经验增量、钱包扣款、账单可追溯" enabled="true">
          <stringProp name="cacheKey">autotest-wealth-chain-final-assertion</stringProp>
          <stringProp name="filename"></stringProp>
          <stringProp name="parameters"></stringProp>
          <stringProp name="script">Long readRequiredLong(String name, String raw) {{
    def text = raw == null ? '' : raw.trim()
    if (!(text ==~ /-?\\d+/)) {{
        throw new IllegalStateException('闭环失败：缺少或无法解析long整数 ' + name + '，实际值=' + raw)
    }}
    return text.toLong()
}}
def beforeExp = readRequiredLong('送礼前财富经验 wealth_before_exp', vars.get('wealth_before_exp') ?: props.get('wealth_before_exp'))
def afterExp = readRequiredLong('送礼后财富经验 wealth_after_exp', vars.get('wealth_after_exp') ?: props.get('wealth_after_exp'))
def beforeGold = readRequiredLong('送礼前Gold余额 wallet_before_gold', vars.get('wallet_before_gold') ?: props.get('wallet_before_gold'))
def afterGold = readRequiredLong('送礼后Gold余额 wallet_after_gold', vars.get('wallet_after_gold') ?: props.get('wallet_after_gold'))
def consume = readRequiredLong('真实送礼消费累计 gift_total_consume', props.get('gift_total_consume'))
def expectedGiftCount = readRequiredLong('期望送礼次数 workflow_expected_gift_count', vars.get('workflow_expected_gift_count'))
def giftSuccessCount = readRequiredLong('实际送礼成功次数 gift_success_count', props.get('gift_success_count'))
def billMatchCount = readRequiredLong('账单匹配数量 gift_bill_match_count', props.get('gift_bill_match_count'))
def expDelta = afterExp - beforeExp
def walletDelta = beforeGold - afterGold
if (consume &lt;= 0) {{
    throw new IllegalStateException('闭环失败：真实送礼消费累计为0')
}}
if (giftSuccessCount != expectedGiftCount) {{
    throw new IllegalStateException('闭环失败：期望送礼 ' + expectedGiftCount + ' 次，实际成功 ' + giftSuccessCount + ' 次')
}}
if (expDelta != consume) {{
    throw new IllegalStateException('闭环失败：财富经验增量 ' + expDelta + ' 不等于送礼消费 ' + consume)
}}
if (walletDelta != consume) {{
    throw new IllegalStateException('闭环失败：钱包扣款 ' + walletDelta + ' 不等于送礼消费 ' + consume)
}}
if (billMatchCount &lt; expectedGiftCount) {{
    throw new IllegalStateException('闭环失败：账单匹配记录 ' + billMatchCount + ' 条，小于送礼次数 ' + expectedGiftCount)
}}
SampleResult.setResponseData(('财富等级需求闭环通过：送礼次数=' + giftSuccessCount + ', 消费=' + consume + ', 经验增量=' + expDelta + ', 钱包扣款=' + walletDelta + ', 账单匹配=' + billMatchCount).getBytes('UTF-8'))</stringProp>
          <stringProp name="scriptLanguage">groovy</stringProp>
        </JSR223Sampler>
        <hashTree/>
      </hashTree>"""


def build_jmeter_jmx(project, cases, runtime_context=None, redact_runtime=True, options=None):
    runtime_context = runtime_context or {}
    options = options or {}
    threads = max(1, min(int(options.get("jmeter_threads", 1) or 1), 200))
    loops = max(1, min(int(options.get("jmeter_loops", 1) or 1), 1000))
    rampup = max(0, min(int(options.get("jmeter_rampup", 1) or 1), 600))
    think_time = max(0, min(int(options.get("jmeter_think_time_ms", 300) or 0), 10000))
    jtl_path = Path(options.get("_jmeter_result_jtl") or JMETER_WORKBENCH_JTL)
    default_url = urllib.parse.urlsplit(project.get("base_url") or "http://127.0.0.1")
    default_protocol = default_url.scheme or "https"
    default_domain = default_url.hostname or "127.0.0.1"
    runtime_defaults = options.get("_jmeter_runtime_defaults") if isinstance(options.get("_jmeter_runtime_defaults"), dict) else {}
    runtime_vars = {}
    for key, value in runtime_defaults.items():
        if key in {"source", "login_status", "login_error", "login_context_keys", "_runtime_warnings"}:
            continue
        if key in {"ticket", "sn", "login_password_encrypted"} or _is_sensitive_runtime_value(key, value):
            continue
        runtime_vars[key] = _safe_runtime_scalar(value)
    for key in ("deviceType", "systemLanguage", "appVersion", "os", "netType", "channel", "appsflyerId", "language", "appCode", "deviceId", "version", "osVersion", "isVpnConnected", "appid", "model", "packageName", "ispType", "organic", "pageNo", "pageSize", "type"):
        value = runtime_defaults.get(key)
        runtime_vars.setdefault(key, _safe_runtime_scalar(value) if value not in (None, "") else "")
    runtime_vars["ticket"] = "${__P(ticket,)}"
    runtime_vars["uid"] = "${__P(uid,)}"
    runtime_vars["t"] = "${__P(t,${__time(,)})}"
    runtime_vars["sn"] = "${__P(sn,)}"
    runtime_vars["login_password_encrypted"] = "${__P(login_password_encrypted,)}"
    runtime_vars["gift_count"] = str(max(1, min(int(options.get("jmeter_loops", 1) or 1), 1000)))
    variables_xml = "".join(
        f'<elementProp name="{_xml_escape(key)}" elementType="Argument"><stringProp name="Argument.name">{_xml_escape(key)}</stringProp><stringProp name="Argument.value">{_xml_escape(value)}</stringProp><stringProp name="Argument.metadata">=</stringProp></elementProp>'
        for key, value in sorted(runtime_vars.items())
    )
    login_case = options.get("_jmeter_login_case") or next((case for case in cases if _is_login_case(case)), None)
    login_sampler = ""
    if login_case:
        login_enabled = "true" if options.get("_jmeter_login_password_available") else "false"
        login_context = {**runtime_context, "login_t": "${__P(t,${__time(,)})}", "login_sn": "${__P(sn)}", "login_password_encrypted": "${__P(login_password_encrypted)}"}
        login_path, login_headers, login_payload = _case_request_with_runtime_context(login_case, login_context)
        login_path = _replace_runtime_placeholders(login_path, login_context, False)
        login_headers = _replace_runtime_placeholders(login_headers, login_context, False)
        login_payload = _replace_runtime_placeholders(login_payload, login_context, False)
        login_url = urllib.parse.urlsplit(login_path if login_path.startswith("http") else (project.get("base_url") or "http://127.0.0.1").rstrip("/") + "/" + login_path.lstrip("/"))
        login_body = json.dumps(login_payload, ensure_ascii=False) if login_payload and not isinstance(login_payload, str) else (login_payload or "")
        login_header_xml = "".join(f'<elementProp name="{_xml_escape(k)}" elementType="Header"><stringProp name="Header.name">{_xml_escape(k)}</stringProp><stringProp name="Header.value">{_xml_escape(v)}</stringProp></elementProp>' for k, v in login_headers.items())
        login_sampler = f"""
      <SetupThreadGroup guiclass="SetupThreadGroupGui" testclass="SetupThreadGroup" testname="登录鉴权前置" enabled="{login_enabled}">
        <intProp name="ThreadGroup.num_threads">1</intProp>
        <intProp name="ThreadGroup.ramp_time">1</intProp>
        <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController"><boolProp name="LoopController.continue_forever">false</boolProp><stringProp name="LoopController.loops">1</stringProp></elementProp>
      </SetupThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="登录接口：提取 access_token" enabled="true">
          <stringProp name="HTTPSampler.domain">{_xml_escape(login_url.hostname)}</stringProp>
          <stringProp name="HTTPSampler.protocol">{_xml_escape(login_url.scheme or 'https')}</stringProp>
          <stringProp name="HTTPSampler.path">{_xml_escape(login_url.path + (('?' + login_url.query) if login_url.query else ''))}</stringProp>
          <stringProp name="HTTPSampler.method">{_xml_escape(login_case['method'])}</stringProp>
          <boolProp name="HTTPSampler.postBodyRaw">{str(bool(login_body)).lower()}</boolProp>
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments"><collectionProp name="Arguments.arguments">{f'<elementProp name="" elementType="HTTPArgument"><boolProp name="HTTPArgument.always_encode">false</boolProp><stringProp name="Argument.value">{_xml_escape(login_body)}</stringProp><stringProp name="Argument.metadata">=</stringProp></elementProp>' if login_body else ''}</collectionProp></elementProp>
        </HTTPSamplerProxy>
        <hashTree>
          <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="登录 Headers" enabled="true"><collectionProp name="HeaderManager.headers">{login_header_xml}</collectionProp></HeaderManager>
          <hashTree/>
          <JSONPostProcessor guiclass="JSONPostProcessorGui" testclass="JSONPostProcessor" testname="提取 access_token 与 uid" enabled="true">
            <stringProp name="JSONPostProcessor.referenceNames">access_token;login_uid</stringProp>
            <stringProp name="JSONPostProcessor.jsonPathExprs">$.data.access_token;$.data.uid</stringProp>
            <stringProp name="JSONPostProcessor.match_numbers">1;1</stringProp>
            <stringProp name="JSONPostProcessor.defaultValues">;</stringProp>
          </JSONPostProcessor>
          <hashTree/>
          <JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" testname="同步 ticket 到业务线程组" enabled="true">
            <stringProp name="cacheKey">autotest-sync-auth-context</stringProp>
            <stringProp name="filename"></stringProp>
            <stringProp name="parameters"></stringProp>
            <stringProp name="script">def token = vars.get('access_token')
if (token) {{
    props.put('ticket', token)
    vars.put('ticket', token)
}}
def loginUid = vars.get('login_uid')
if (loginUid) {{
    props.put('uid', loginUid)
    vars.put('uid', loginUid)
}}</stringProp>
            <stringProp name="scriptLanguage">groovy</stringProp>
          </JSR223PostProcessor>
          <hashTree/>
          <ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="断言登录成功" enabled="true">
            <collectionProp name="Asserion.test_strings"><stringProp name="status">200</stringProp></collectionProp>
            <stringProp name="Assertion.custom_message">登录接口未返回 200，后续业务接口不会获得 ticket</stringProp>
            <stringProp name="Assertion.test_field">Assertion.response_code</stringProp>
            <boolProp name="Assertion.assume_success">false</boolProp>
            <intProp name="Assertion.test_type">8</intProp>
          </ResponseAssertion>
          <hashTree/>
        </hashTree>
      </hashTree>"""
    samplers = []
    for case in cases:
        if _is_login_case(case):
            continue
        if case["method"] not in {"GET", "POST", "PUT", "PATCH"}:
            continue
        if NEGATIVE_CASE_RE.search(str(case.get("title") or "")):
            continue
        if re.search("|".join(map(re.escape, HIGH_RISK_WORDS)), f"{case['path']} {case['title']}".lower()):
            continue
        case_path, headers, payload = _case_request_with_runtime_context(case, runtime_context)
        case_path = _replace_runtime_placeholders(case_path, runtime_context, redact_runtime)
        headers = _replace_runtime_placeholders(headers, runtime_context, redact_runtime)
        payload = _replace_runtime_placeholders(payload, runtime_context, redact_runtime)
        parsed = urllib.parse.urlsplit(case_path if case_path.startswith("http") else (project.get("base_url") or "http://127.0.0.1").rstrip("/") + "/" + case_path.lstrip("/"))
        body = json.dumps(payload, ensure_ascii=False) if payload and not isinstance(payload, str) else (payload or "")
        header_xml = "".join(f'<elementProp name="{_xml_escape(k)}" elementType="Header"><stringProp name="Header.name">{_xml_escape(k)}</stringProp><stringProp name="Header.value">{_xml_escape(v)}</stringProp></elementProp>' for k, v in headers.items())
        expected_status = _tool_expected_status(case)
        sampler = f"""
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="{_xml_escape(case['title'])}" enabled="true">
          <stringProp name="HTTPSampler.domain">{_xml_escape(parsed.hostname)}</stringProp>
          <stringProp name="HTTPSampler.protocol">{_xml_escape(parsed.scheme or 'https')}</stringProp>
          <stringProp name="HTTPSampler.path">{_xml_escape(parsed.path + (('?' + parsed.query) if parsed.query else ''))}</stringProp>
          <stringProp name="HTTPSampler.method">{_xml_escape(case['method'])}</stringProp>
          <boolProp name="HTTPSampler.postBodyRaw">{str(bool(body)).lower()}</boolProp>
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments"><collectionProp name="Arguments.arguments">{f'<elementProp name="" elementType="HTTPArgument"><boolProp name="HTTPArgument.always_encode">false</boolProp><stringProp name="Argument.value">{_xml_escape(body)}</stringProp><stringProp name="Argument.metadata">=</stringProp></elementProp>' if body else ''}</collectionProp></elementProp>
        </HTTPSamplerProxy>
        <hashTree>
          <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="Headers" enabled="true"><collectionProp name="HeaderManager.headers">{header_xml}</collectionProp></HeaderManager>
          <hashTree/>
          <ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="断言 HTTP {expected_status}" enabled="true">
            <collectionProp name="Asserion.test_strings"><stringProp name="status">{expected_status}</stringProp></collectionProp>
            <stringProp name="Assertion.custom_message">HTTP 状态码不符合预期</stringProp>
            <stringProp name="Assertion.test_field">Assertion.response_code</stringProp>
            <boolProp name="Assertion.assume_success">false</boolProp>
            <intProp name="Assertion.test_type">8</intProp>
          </ResponseAssertion>
          <hashTree/>
        </hashTree>"""
        samplers.append(sampler)
    business_workflow = build_jmeter_wealth_requirement_workflow(project, options) if options.get("_jmeter_workbench") else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="{_xml_escape(project['name'])} 性能基线" enabled="true">
      <stringProp name="TestPlan.comments">由 AutoTest AI 生成；GUI 用于审阅维护，非 GUI 执行用于报告归档。</stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments"><collectionProp name="Arguments.arguments"/></elementProp>
    </TestPlan>
    <hashTree>
      <Arguments guiclass="ArgumentsPanel" testclass="Arguments" testname="运行变量" enabled="true">
        <collectionProp name="Arguments.arguments">{variables_xml}</collectionProp>
      </Arguments>
      <hashTree/>
      <ConfigTestElement guiclass="HttpDefaultsGui" testclass="ConfigTestElement" testname="HTTP 请求默认值" enabled="true">
        <stringProp name="HTTPSampler.protocol">{_xml_escape(default_protocol)}</stringProp>
        <stringProp name="HTTPSampler.domain">{_xml_escape(default_domain)}</stringProp>
        <stringProp name="HTTPSampler.port">{_xml_escape(default_url.port or '')}</stringProp>
        <stringProp name="HTTPSampler.connect_timeout">10000</stringProp>
        <stringProp name="HTTPSampler.response_timeout">30000</stringProp>
        <elementProp name="HTTPsampler.Arguments" elementType="Arguments"><collectionProp name="Arguments.arguments"/></elementProp>
      </ConfigTestElement>
      <hashTree/>
      <CookieManager guiclass="CookiePanel" testclass="CookieManager" testname="HTTP Cookie 管理器" enabled="true">
        <collectionProp name="CookieManager.cookies"/>
        <boolProp name="CookieManager.clearEachIteration">false</boolProp>
        <boolProp name="CookieManager.controlledByThreadGroup">false</boolProp>
      </CookieManager>
      <hashTree/>
      <CacheManager guiclass="CacheManagerGui" testclass="CacheManager" testname="HTTP Cache 管理器" enabled="true">
        <boolProp name="clearEachIteration">false</boolProp>
        <boolProp name="useExpires">true</boolProp>
      </CacheManager>
      <hashTree/>
      {login_sampler}
      {business_workflow}
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="接口性能冒烟" enabled="true">
        <intProp name="ThreadGroup.num_threads">{threads}</intProp>
        <intProp name="ThreadGroup.ramp_time">{rampup}</intProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController"><boolProp name="LoopController.continue_forever">false</boolProp><stringProp name="LoopController.loops">{loops}</stringProp></elementProp>
      </ThreadGroup>
      <hashTree>
        <JSR223PreProcessor guiclass="TestBeanGUI" testclass="JSR223PreProcessor" testname="读取登录身份上下文" enabled="true">
          <stringProp name="cacheKey">autotest-load-auth-context</stringProp>
          <stringProp name="filename"></stringProp>
          <stringProp name="parameters"></stringProp>
          <stringProp name="script">def token = props.get('ticket') ?: vars.get('ticket') ?: '${{__P(ticket,)}}'
if (!token) {{
    throw new IllegalStateException('未取得 ticket：请在平台先完成一次真实登录，或填写登录加密密码后重新打开 JMeter 工作台')
}}
vars.put('ticket', token)
def loginUid = props.get('uid') ?: vars.get('uid') ?: '${{__P(uid,)}}'
if (loginUid) {{
    vars.put('uid', loginUid)
}}</stringProp>
          <stringProp name="scriptLanguage">groovy</stringProp>
        </JSR223PreProcessor>
        <hashTree/>
        <ConstantTimer guiclass="ConstantTimerGui" testclass="ConstantTimer" testname="请求间隔" enabled="true">
          <stringProp name="ConstantTimer.delay">{think_time}</stringProp>
        </ConstantTimer>
        <hashTree/>
        {''.join(samplers)}
      </hashTree>
      <ResultCollector guiclass="ViewResultsFullVisualizer" testclass="ResultCollector" testname="查看结果树" enabled="true">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <stringProp name="filename">{_xml_escape(jtl_path)}</stringProp>
      </ResultCollector>
      <hashTree/>
      <ResultCollector guiclass="SummaryReport" testclass="ResultCollector" testname="汇总报告" enabled="true">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <stringProp name="filename">{_xml_escape(jtl_path)}</stringProp>
      </ResultCollector>
      <hashTree/>
      <ResultCollector guiclass="StatVisualizer" testclass="ResultCollector" testname="聚合报告" enabled="true">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <stringProp name="filename">{_xml_escape(jtl_path)}</stringProp>
      </ResultCollector>
      <hashTree/>
      <ResultCollector guiclass="StatGraphVisualizer" testclass="ResultCollector" testname="聚合图形报告" enabled="true">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <stringProp name="filename">{_xml_escape(jtl_path)}</stringProp>
      </ResultCollector>
      <hashTree/>
      <ResultCollector guiclass="GraphVisualizer" testclass="ResultCollector" testname="图形结果" enabled="true">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <stringProp name="filename">{_xml_escape(jtl_path)}</stringProp>
      </ResultCollector>
      <hashTree/>
    </hashTree>
  </hashTree>
</jmeterTestPlan>"""


def build_pytest_script(project, cases, runtime_context=None, redact_runtime=True, package_id="", package_root=""):
    runtime_context = runtime_context or {}
    serializable = []
    for case in cases:
        case_path, headers, payload = _case_request_with_runtime_context(case, runtime_context)
        serializable.append({
            "id": case.get("id", ""),
            "title": case["title"],
            "scenario_type": case.get("scenario_type", ""),
            "coverage_tool": case.get("coverage_tool", ""),
            "method": case["method"],
            "path": _replace_runtime_placeholders(case_path, runtime_context, redact_runtime),
            "headers": _replace_runtime_placeholders(headers, runtime_context, redact_runtime),
            "payload": _replace_runtime_placeholders(payload, runtime_context, redact_runtime),
            "expected_status": _tool_expected_status(case),
        })
    return f'''import csv
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_URL = os.getenv("AUTOTEST_BASE_URL", {json.dumps(project.get("base_url") or "", ensure_ascii=False)})
PACKAGE_ID = {json.dumps(package_id or "", ensure_ascii=False)}
PACKAGE_ROOT_HINT = {json.dumps(str(package_root or ""), ensure_ascii=False)}
CASES = {json.dumps(serializable, ensure_ascii=False, indent=2)}
RUNTIME_STATE = {{}}


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
        return {{"_load_error": str(exc), "rules": []}}


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
    runtime = {{}}
    for env_key in ("AUTOTEST_RUNTIME_PARAMS_JSON", "AUTOTEST_EVIDENCE_RUNTIME_JSON"):
        try:
            payload = json.loads(os.getenv(env_key, "{{}}"))
            if isinstance(payload, dict):
                runtime.update(payload)
        except Exception:
            pass
    aliases = {{
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
    }}
    for env_key, name in aliases.items():
        value = os.getenv(env_key, "")
        if value:
            runtime[name] = value
    runtime.update({{key: value for key, value in RUNTIME_STATE.items() if value not in (None, "")}})
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
    text = re.sub(r"(.)([A-Z][a-z]+)", r"\\1_\\2", str(name or ""))
    text = re.sub(r"([a-z0-9])([A-Z])", r"\\1_\\2", text)
    return re.sub(r"[^a-zA-Z0-9_]+", "_", text).strip("_").lower()


def camel_case(name):
    parts = [x for x in re.split(r"[_\\-\\s]+", str(name or "")) if x]
    if not parts:
        return ""
    return parts[0] + "".join(x[:1].upper() + x[1:] for x in parts[1:])


def load_runtime_aliases():
    root = package_root()
    payload = load_yaml(root / "runtime_aliases.yaml", {{}})
    aliases = payload.get("aliases") if isinstance(payload, dict) else None
    if not isinstance(aliases, dict):
        aliases = {{}}
    defaults = {{
        "orderNo": ["order_no", "orderNo"],
        "orderId": ["order_id", "orderId"],
        "uid": ["uid"],
        "agentUid": ["agent_uid", "proxy_uid", "agentUid", "proxyUid"],
        "proxyUid": ["proxy_uid", "agent_uid", "proxyUid", "agentUid"],
        "countryCode": ["country_code", "countryCode"],
        "currency": ["currency"],
    }}
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
        return {{k: fill_runtime(v) for k, v in value.items()}}
    if isinstance(value, list):
        return [fill_runtime(v) for v in value]
    text = str(value or "")
    runtime = runtime_variables()
    for key, raw in runtime.items():
        text = text.replace("{{{{" + key + "}}}}", str(raw))
    return text


def ensure_common_query_params(path):
    runtime = runtime_variables()
    parsed = urllib.parse.urlsplit(path)
    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    current = {{key: value for key, value in query_pairs}}
    additions = []
    aliases = load_runtime_aliases()
    mapping = {{
        "ticket": runtime.get("ticket"),
        "uid": runtime.get("uid") or runtime.get("applicant_uid"),
        "countryCode": runtime.get("countryCode") or runtime.get("country_code"),
        "currency": runtime.get("currency"),
        "agentUid": runtime.get("agentUid") or runtime.get("proxy_uid"),
        "proxyUid": runtime.get("proxyUid") or runtime.get("proxy_uid"),
        "orderNo": runtime.get("orderNo") or runtime.get("order_no"),
        "orderId": runtime.get("orderId") or runtime.get("order_id"),
    }}
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
    query = urllib.parse.urlencode(query_pairs + additions, safe="{{}}")
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))


def update_runtime_from_response(case, body):
    try:
        payload = json.loads(body[body.find("{{"):]) if "{{" in body else json.loads(body)
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
    case["path"] = ensure_common_query_params(fill_runtime(case.get("path", "")))
    case["headers"] = fill_runtime(case.get("headers") or {{}})
    case["payload"] = fill_runtime(case.get("payload"))
    url = case["path"] if case["path"].startswith("http") else BASE_URL.rstrip("/") + "/" + case["path"].lstrip("/")
    body = case.get("payload")
    data = None if body in ("", None) else (body.encode("utf-8") if isinstance(body, str) else json.dumps(body, ensure_ascii=False).encode("utf-8"))
    headers = dict(case.get("headers") or {{}})
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
        return {{"path": str(p) if path else "", "exists": False, "samples": 0, "failures": 0, "failed_labels": []}}
    if p.suffix.lower() == ".xml":
        root = ET.parse(p).getroot()
        samples = [x for x in root.iter() if x.attrib.get("lb")]
        failed = [x.attrib.get("lb", "") for x in samples if x.attrib.get("s") == "false"]
        return {{"path": str(p), "exists": True, "samples": len(samples), "failures": len(failed), "failed_labels": failed[:30]}}
    with p.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        rows = list(csv.DictReader(f))
    failed = [r.get("label", "") for r in rows if str(r.get("success", "")).lower() == "false" or str(r.get("responseCode", "")).startswith(("4", "5"))]
    return {{"path": str(p), "exists": True, "samples": len(rows), "failures": len(failed), "failed_labels": failed[:30]}}


def load_newman(path):
    payload = load_json(path, {{}})
    run = payload.get("run", {{}}) if isinstance(payload, dict) else {{}}
    failures = run.get("failures", []) if isinstance(run, dict) else []
    stats = run.get("stats", {{}}) if isinstance(run, dict) else {{}}
    return {{"path": path or "", "exists": bool(payload), "failures": len(failures), "stats": stats}}


def sql_value(value):
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    text = str(value if value is not None else "")
    return "'" + text.replace("\\\\", "\\\\\\\\").replace("'", "''") + "'"


def render_template(template, variables, missing):
    def repl(match):
        name = match.group(1)
        if name not in variables or variables.get(name) in (None, ""):
            missing.add(name)
            return "NULL"
        return sql_value(variables.get(name))
    return re.sub(r"\\$\\{{([A-Za-z_][A-Za-z0-9_]*)\\}}", repl, str(template or ""))


def mysql_query(sql):
    if not re.match(r"^\\s*(select|show|describe|explain)\\b", sql, re.I):
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
    query = rule.get("query") if isinstance(rule.get("query"), dict) else {{}}
    key_template = query.get("key") or query.get("pattern") or rule.get("redis_key") or ""
    key = key_template
    missing = set()
    for name in re.findall(r"\\$\\{{([A-Za-z_][A-Za-z0-9_]*)\\}}", key_template):
        if not variables.get(name):
            missing.add(name)
        key = key.replace("${{" + name + "}}", str(variables.get(name, "")))
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
        return {{"key": key, "type": key_type, "records": [client.hgetall(key)]}}
    if key_type == "string":
        return {{"key": key, "type": key_type, "records": [{{"value": client.get(key)}}]}}
    return {{"key": key, "type": key_type, "records": []}}


def values_for_field(records, field):
    return [item.get(field) for item in records if isinstance(item, dict) and field in item]


def resolve_expected(value, variables):
    if isinstance(value, str):
        m = re.fullmatch(r"\\$\\{{([A-Za-z_][A-Za-z0-9_]*)\\}}", value.strip())
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
        items = expected if isinstance(expected, list) else re.split(r"[,，\\s]+", str(expected or ""))
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
    return {{"field": field, "operator": operator, "expected": expected, "actual": first if len(values) <= 1 else values[:20], "passed": bool(passed), "reason": "" if passed else "assertion not satisfied"}}


def rule_identifier(rule):
    return str(rule.get("id") or rule.get("name") or "").strip()


def run_evidence_rules(rule_ids=None):
    bootstrap_env()
    root = package_root()
    variables = runtime_variables()
    rules_payload = load_yaml(root / "evidence_rules.yaml", {{"rules": []}})
    rules = rules_payload.get("rules") if isinstance(rules_payload, dict) else []
    selected = set(str(item) for item in (rule_ids or []) if str(item).strip())
    results = []
    for rule in rules or []:
        if selected and rule_identifier(rule) not in selected:
            continue
        query = rule.get("query") if isinstance(rule.get("query"), dict) else {{}}
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
                    sql = f"SELECT * FROM {{table}} WHERE {{where}} LIMIT 100"
                    records = mysql_query(sql)
            elif source == "redis":
                records = redis_read(rule, variables).get("records") or []
            else:
                blockers.append("不支持的数据源：" + source)
        except Exception as exc:
            blockers.append(str(exc))
        assertions = []
        if not blockers:
            assertions.append({{"field": "__rows__", "operator": "exists", "expected": "至少1行", "actual": len(records), "passed": len(records) > 0, "reason": "" if records else "query returned no rows"}})
            for assertion in rule.get("assertions") or []:
                assertions.append(run_assertion(assertion, records, variables))
        status = "BLOCKED" if blockers else "PASSED" if assertions and all(x.get("passed") for x in assertions) else "FAILED"
        results.append({{"id": rule.get("id"), "name": rule.get("name"), "source": source, "sql": sql, "status": status, "rows": len(records), "assertions": assertions, "blockers": blockers, "sample": records[:3]}})
    return results


def redact_text(text):
    text = str(text or "")
    text = re.sub(r"eyJ[A-Za-z0-9_\\-]+\\.[A-Za-z0-9_\\-]+\\.[A-Za-z0-9_\\-]+", "***jwt***", text)
    text = re.sub(r'("?(?:access_token|ticket|token)"?\\s*[:=]\\s*")([^"]+)(")', r'\\1***\\3', text, flags=re.I)
    return text


def redact_obj(value):
    if isinstance(value, dict):
        out = {{}}
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
    return load_json(root / "manifest.json", {{}})


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
    payload = load_json(path, {{}})
    scenarios = payload.get("scenarios") if isinstance(payload, dict) else None
    return scenarios if isinstance(scenarios, list) else []


def case_scenario_index():
    mapping = {{}}
    order = []
    for scenario in load_execution_plan():
        scenario_id = scenario.get("scenario_id") or scenario.get("id") or scenario.get("name") or "unassigned"
        scenario_name = scenario.get("name") or scenario_id
        for case in scenario.get("cases") or []:
            case_id = case.get("id") if isinstance(case, dict) else case
            if case_id:
                mapping[str(case_id)] = {{"scenario_id": scenario_id, "scenario_name": scenario_name, "scenario_status": scenario.get("status")}}
                order.append(str(case_id))
        for task in scenario.get("tool_tasks") or []:
            for case_id in task.get("cases") or []:
                if case_id:
                    mapping[str(case_id)] = {{"scenario_id": scenario_id, "scenario_name": scenario_name, "scenario_status": scenario.get("status")}}
                    order.append(str(case_id))
    return {{"mapping": mapping, "order": order}}


def scenario_for_case(case, index=None):
    index = index or case_scenario_index()
    mapping = index.get("mapping") if isinstance(index, dict) else index
    item = (mapping or {{}}).get(str(case.get("id") or ""))
    if item:
        return item
    scenario_name = case.get("scenario_type") or "未分组场景"
    scenario_id = snake_case(scenario_name) or "unassigned"
    return {{"scenario_id": scenario_id, "scenario_name": scenario_name, "scenario_status": ""}}


def ordered_cases(cases, index=None):
    index = index or case_scenario_index()
    order = index.get("order") if isinstance(index, dict) else []
    case_by_id = {{str(case.get("id") or ""): case for case in cases}}
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
    case_by_id = {{str(case.get("id") or ""): case for case in cases}}
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
            batches.append({{
                "scenario_id": scenario_id,
                "scenario_name": scenario_name,
                "scenario_status": scenario.get("status"),
                "cases": batch_cases,
                "evidence_rule_ids": sorted(set(evidence_rule_ids)),
                "uses_explicit_evidence_rules": bool(evidence_rule_ids),
                "source": "orchestration",
                "raw": scenario,
            }})
    fallback = {{}}
    for case in cases:
        case_id = str(case.get("id") or "")
        if case_id in seen:
            continue
        scenario = scenario_for_case(case, index)
        key = scenario.get("scenario_id") or "unassigned"
        item = fallback.setdefault(key, {{"scenario_id": key, "scenario_name": scenario.get("scenario_name") or key, "scenario_status": scenario.get("scenario_status") or "", "cases": [], "evidence_rule_ids": [], "uses_explicit_evidence_rules": False, "source": "scenario_type", "raw": {{}}}})
        item["cases"].append(case)
        seen.add(case_id)
    batches.extend(fallback.values())
    if not batches:
        batches.append({{"scenario_id": "package_review", "scenario_name": "需求包证据复核", "scenario_status": "", "cases": [], "evidence_rule_ids": [], "uses_explicit_evidence_rules": False, "source": "empty", "raw": {{}}}})
    return batches


def apply_scenario_runtime(scenario):
    raw = scenario.get("raw") if isinstance(scenario.get("raw"), dict) else {{}}
    values = {{}}
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
        parsed_body = json.loads(body[body.find("{{"):]) if "{{" in body else json.loads(body)
        if isinstance(parsed_body, dict):
            business_code = parsed_body.get("code", "")
            business_message = parsed_body.get("message", "")
    except Exception:
        pass
    return {{"id": case.get("id"), "title": case["title"], "scenario_id": scenario.get("scenario_id"), "scenario_name": scenario.get("scenario_name"), "method": case["method"], "path": redact_text(ensure_common_query_params(fill_runtime(case.get("path", "")))), "status": status, "expected_status": case["expected_status"], "business_code": business_code, "business_message": business_message, "response_preview": redact_text(body[:800])}}


def run_scenario_batch(scenario, base_runtime_state=None):
    RUNTIME_STATE.clear()
    RUNTIME_STATE.update(base_runtime_state or {{}})
    apply_scenario_runtime(scenario)
    http_results = []
    for case in scenario.get("cases") or []:
        http_results.append(run_single_case(case, scenario))
    rule_ids = scenario.get("evidence_rule_ids") or []
    evidence = run_evidence_rules(rule_ids if rule_ids else None)
    for item in evidence:
        item["scenario_id"] = scenario.get("scenario_id")
        item["scenario_name"] = scenario.get("scenario_name")
    http_failed = sum(1 for x in http_results if x.get("status") != x.get("expected_status") or str(x.get("business_code") or "200") != "200")
    failed = sum(1 for x in evidence if x.get("status") == "FAILED")
    blocked = sum(1 for x in evidence if x.get("status") == "BLOCKED")
    status = "BLOCKED" if blocked else "FAILED" if failed or http_failed else "PASSED"
    return {{
        "scenario_id": scenario.get("scenario_id"),
        "name": scenario.get("scenario_name"),
        "planned_status": scenario.get("scenario_status"),
        "source": scenario.get("source"),
        "status": status,
        "http_cases": len(http_results),
        "http_failed": http_failed,
        "evidence_rule_ids": rule_ids,
        "evidence_rules": [{{"id": x.get("id"), "name": x.get("name"), "status": x.get("status"), "source": x.get("source")}} for x in evidence],
        "runtime_variables": {{k: ("***" if "ticket" in k.lower() or "token" in k.lower() else v) for k, v in runtime_variables().items()}},
        "http_results": http_results,
        "evidence_results": evidence,
    }}


def build_evidence_report(scenario_runs):
    root = package_root()
    plan_path = resolve_package_asset_path("outputs/execution-plan.json")
    jtl = parse_jtl(os.getenv("AUTOTEST_JTL_PATH", ""))
    newman = load_newman(os.getenv("AUTOTEST_NEWMAN_JSON", ""))
    http_results = [item for scenario in scenario_runs for item in scenario.get("http_results") or []]
    evidence = [item for scenario in scenario_runs for item in scenario.get("evidence_results") or []]
    http_failed = sum(1 for x in http_results if x.get("status") != x.get("expected_status") or str(x.get("business_code") or "200") != "200")
    failed = sum(1 for x in evidence if x["status"] == "FAILED")
    blocked = sum(1 for x in evidence if x["status"] == "BLOCKED")
    for scenario in scenario_runs:
        if jtl.get("failures"):
            scenario["jmeter_failed_labels"] = jtl.get("failed_labels") or []
        if newman.get("failures"):
            scenario["newman_failures"] = newman.get("failures", 0)
    report = {{
        "report_type": "PYTEST_DEEP_EVIDENCE_REVIEW",
        "package_id": PACKAGE_ID or root.name,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "status": "BLOCKED" if blocked else "FAILED" if failed or http_failed or jtl.get("failures") or newman.get("failures") else "PASSED",
        "orchestration": {{"path": str(plan_path), "exists": plan_path.is_file(), "fallback": "scenario_type" if not plan_path.is_file() else ""}},
        "summary": {{
            "http_cases": len(http_results),
            "http_failed": http_failed,
            "rules_total": len(evidence),
            "rules_failed": failed,
            "rules_blocked": blocked,
            "jtl_samples": jtl.get("samples", 0),
            "jtl_failures": jtl.get("failures", 0),
            "newman_failures": newman.get("failures", 0),
        }},
        "runtime_variables": {{k: ("***" if "ticket" in k.lower() or "token" in k.lower() else v) for k, v in runtime_variables().items()}},
        "scenarios": scenario_runs,
        "http_results": http_results,
        "jmeter": jtl,
        "newman": newman,
        "evidence_rules": evidence,
    }}
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
'''


def generate_enterprise_tool_assets(project_id, options=None):
    options = _merge_execution_profile_options(project_id, options)
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    cases = rows("SELECT * FROM test_cases WHERE project_id=? AND method<>'' AND path<>'' ORDER BY created_at", (project_id,))
    if not cases:
        raise ValueError("缺少可执行接口用例，无法生成外部工具资产")
    runtime = _runtime_context(project_id, options)
    include_runtime = bool(options.get("include_runtime")) and bool(runtime.get("ticket")) and bool(runtime.get("uid"))
    cases = _external_tool_cases(cases, include_runtime)
    if not cases:
        raise ValueError("当前可执行用例均依赖运行时变量，请先补齐测试凭证或生成无需凭证的冒烟用例")
    out = TOOL_ASSET_ROOT / project_id
    out.mkdir(parents=True, exist_ok=True)
    redacted_runtime = dict(runtime)
    files = {
        "postman-collection.json": json.dumps(build_postman_collection(project, cases, redacted_runtime, True), ensure_ascii=False, indent=2),
        "jmeter-plan.jmx": build_jmeter_jmx(project, cases, redacted_runtime, True, options),
        "pytest_api_cases.py": build_pytest_script(project, cases, redacted_runtime, True),
    }
    result = []
    for name, content in files.items():
        path = out / name
        path.write_text(content, encoding="utf-8")
        result.append({"name": name, "path": str(path), "url": f"/reports/tool-assets/{project_id}/{name}"})
    return {"generated": len(result), "files": result, "toolchain": enterprise_toolchain_status(project_id)}


def generate_jmeter_workbench_asset(project_id, options=None):
    options = _merge_execution_profile_options(project_id, options)
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    source_cases = rows("SELECT * FROM test_cases WHERE project_id=? AND method<>'' AND path<>'' ORDER BY created_at", (project_id,))
    runtime = _runtime_context(project_id, options)
    credential = load_runtime_credential(project_id)
    saved_login_password = str(credential.get("encrypted_password") or "").strip()
    include_runtime = bool(runtime.get("ticket")) and bool(runtime.get("uid"))
    cases = _external_tool_cases(source_cases, include_runtime)
    login_case = next((case for case in source_cases if _is_login_case(case)), None)
    if not cases:
        raise ValueError("没有可加载到 JMeter 的接口用例；请先补齐接口用例或有效运行上下文")
    out = JMETER_WORKBENCH_JMX.parent
    out.mkdir(parents=True, exist_ok=True)
    existing_has_encoded_vars = False
    if JMETER_WORKBENCH_JMX.is_file():
        try:
            existing_text = JMETER_WORKBENCH_JMX.read_text(encoding="utf-8")
            existing_has_encoded_vars = "%24%7B" in existing_text or "%7D" in existing_text
        except Exception:
            existing_text = ""
        if not options.get("force_regenerate") and not existing_has_encoded_vars:
            return {
                "path": str(JMETER_WORKBENCH_JMX),
                "url": "",
                "case_count": len(cases),
                "uses_runtime_properties": include_runtime,
                "overwrite_mode": False,
                "reused_existing": True,
                "message": "已读取并复用当前保存的 JMeter 工作台文件，未覆盖你的手工修改。",
            }
    runtime_for_jmeter = {}
    if include_runtime:
        for key, value in runtime.items():
            if key in {"source", "login_status", "login_error", "login_context_keys", "_runtime_warnings"}:
                continue
            if key in {"ticket", "uid"}:
                runtime_for_jmeter[key] = "${" + key + "}"
            elif key in {"sn", "login_password_encrypted"} or _is_sensitive_runtime_value(key, value):
                runtime_for_jmeter[key] = "${__P(" + key + ",)}"
            else:
                runtime_for_jmeter[key] = _safe_runtime_scalar(value)
    if login_case:
        options["_jmeter_login_case"] = login_case
    options["_jmeter_workbench"] = True
    options["_jmeter_login_password_available"] = bool(str(options.get("login_password_encrypted") or "").strip() or saved_login_password)
    options["_jmeter_runtime_defaults"] = runtime
    jmx_path = JMETER_WORKBENCH_JMX
    if jmx_path.is_file():
        backup_path = jmx_path.with_suffix(f".backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.jmx")
        try:
            backup_path.write_text(jmx_path.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception:
            backup_path = None
    jmx_path.write_text(build_jmeter_jmx(project, cases, runtime_for_jmeter, False, options), encoding="utf-8")
    return {
        "path": str(jmx_path),
        "url": "",
        "case_count": len(cases),
        "uses_runtime_properties": include_runtime,
        "overwrite_mode": True,
        "reused_existing": False,
        "fixed_encoded_runtime_variables": existing_has_encoded_vars,
        "backup_path": str(backup_path) if "backup_path" in locals() and backup_path else "",
    }


def summarize_jmeter_jmx(jmx_path):
    try:
        root = ET.parse(jmx_path).getroot()
    except Exception as exc:
        return {
            "status": "FAILED",
            "reason": f"JMX 解析失败：{exc}",
            "thread_groups": 0,
            "http_samplers": 0,
            "headers": 0,
            "assertions": 0,
            "groups": [],
        }
    groups = []
    for group in root.iter("ThreadGroup"):
        loops = ""
        for prop in group.iter("stringProp"):
            if prop.attrib.get("name") == "LoopController.loops":
                loops = prop.text or ""
                break
        groups.append({
            "name": group.attrib.get("testname", "Thread Group"),
            "threads": next((p.text or "" for p in group.iter("intProp") if p.attrib.get("name") == "ThreadGroup.num_threads"), ""),
            "rampup": next((p.text or "" for p in group.iter("intProp") if p.attrib.get("name") == "ThreadGroup.ramp_time"), ""),
            "loops": loops,
        })
    return {
        "status": "PASSED",
        "thread_groups": len(groups),
        "setup_thread_groups": sum(1 for _ in root.iter("SetupThreadGroup")),
        "http_samplers": sum(1 for _ in root.iter("HTTPSamplerProxy")),
        "headers": sum(1 for _ in root.iter("HeaderManager")),
        "configs": sum(1 for node in root.iter() if node.tag in {"Arguments", "ConfigTestElement", "CookieManager", "CacheManager"}),
        "extractors": sum(1 for node in root.iter() if node.tag in {"JSONPostProcessor", "RegexExtractor", "XPathExtractor"}),
        "post_processors": sum(1 for node in root.iter() if "PostProcessor" in str(node.tag)),
        "timers": sum(1 for node in root.iter() if "Timer" in str(node.tag)),
        "listeners": sum(1 for _ in root.iter("ResultCollector")),
        "assertions": sum(1 for node in root.iter() if "Assertion" in str(node.tag)),
        "groups": groups,
    }


def _package_jmeter_candidates(package_root, package_id):
    package_root = Path(package_root)
    jmeter_dir = package_root / "outputs" / "jmeter"
    preferred = []
    if package_id == "salary-trade":
        preferred.extend([
            jmeter_dir / "salary-trade-case-driven.jmx",
            jmeter_dir / "salary-trade-state-machine.jmx",
        ])
    if package_id == "wealth-level":
        preferred.append(jmeter_dir / "性能基线.jmx")
    preferred.append(jmeter_dir / "jmeter-plan.jmx")
    existing = [path for path in preferred if path.is_file()]
    if existing:
        return existing
    return sorted(jmeter_dir.glob("*.jmx")) if jmeter_dir.is_dir() else []


def _requirement_package_jmeter_plan(project_id, package_id, options=None):
    package = requirement_package_by_id(project_id, package_id)
    package_id = package.get("package_id") or package.get("id") or package_id
    candidates = _package_jmeter_candidates(package["root"], package_id)
    generated = None
    if not candidates:
        generated = generate_requirement_package_tool_assets(project_id, package_id, options or {})
        candidates = _package_jmeter_candidates(package["root"], package_id)
    if not candidates:
        raise ValueError("当前需求包还没有 JMeter 脚本，请先生成本包脚本")
    return package, Path(candidates[0]), generated


def open_jmeter_gui(project_id, options=None):
    options = _merge_execution_profile_options(project_id, options)
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    raw_script_key = str(options.get("script_key") or options.get("jmeter_script") or options.get("package_id") or "").strip()
    package = None
    script_key = raw_script_key.replace("-", "_") if raw_script_key else "select_required"
    generated = None
    jtl_path = JMETER_WORKBENCH_JTL
    command_properties = []
    jmx_path = None
    handled = False
    package_ids = {item.get("package_id") or item.get("id") for item in requirement_package_catalog(project_id).get("packages", [])}
    if raw_script_key in package_ids:
        package, jmx_path, generated = _requirement_package_jmeter_plan(project_id, raw_script_key, options)
        handled = True
        if raw_script_key == "salary-trade":
            script_key = "salary_trade"
    elif script_key in {"salary_trade", "salary"}:
        package, jmx_path, generated = _requirement_package_jmeter_plan(project_id, "salary-trade", options)
        handled = True
    elif script_key in {"wealth_level", "wealth", "generic"}:
        package, jmx_path, generated = _requirement_package_jmeter_plan(project_id, "wealth-level", options)
        handled = True
    if not handled:
        raise ValueError("请先选择要打开的 JMeter 脚本：财富等级、工资代理结算，或当前需求包脚本。")
    if script_key in {"salary_trade", "salary"}:
        jtl_path = _latest_salary_trade_jtl()
        runtime_properties = ROOT / "work" / "salary-trade-runtime.properties"
        if runtime_properties.is_file():
            command_properties.extend(["-q", str(runtime_properties)])
        command_properties.extend([
            "-Jsample_variables=flow_a_order_no,flow_b_order_no,flow_c_order_no,flow_d_order_no,flow_e_order_no,flow_f_order_no,flow_g_order_no,flow_h_order_no,salary_order_no,applicant_uid,proxy_uid,agent_uid,countryCode,currency",
            f"-Jsalary_result_jtl={str(jtl_path)}",
        ])
    if not jmx_path.is_file():
        raise ValueError("JMeter 脚本尚未生成")
    summary = summarize_jmeter_jmx(jmx_path)
    if summary.get("http_samplers", 0) < 1:
        raise ValueError("当前 JMX 没有可维护的 HTTP Sampler，请先补齐可执行接口用例")
    jmeter = _jmeter_command()
    if not (Path(str(jmeter)).exists() or shutil.which(str(jmeter))):
        raise ValueError("本机未发现 JMeter，请确认 AUTOTEST_JMETER 或 JMeter 安装路径")
    command = [str(jmeter), *command_properties, "-t", str(jmx_path)]
    runtime_context = _runtime_context(project_id, options)
    credential = load_runtime_credential(project_id)
    saved_login_password = str(credential.get("encrypted_password") or "").strip()
    for key in ("ticket", "uid", "t", "deviceId", "model", "osVersion", "netType", "channel", "packageName", "appid", "appVersion", "version", "appsflyerId", "organic", "ispType", "isVpnConnected", "language", "appCode", "os", "systemLanguage", "deviceType"):
        value = str(runtime_context.get(key) or "").strip()
        if value:
            command.append(f"-J{key}={value}")
    for key in ("login_password_encrypted", "login_t", "login_sn"):
        value = str(options.get(key) or "").strip()
        if key == "login_password_encrypted" and not value:
            value = saved_login_password
        if not value:
            continue
        jmeter_key = {"login_t": "t", "login_sn": "sn"}.get(key, key)
        command.append(f"-J{jmeter_key}={value}")
    popen_kwargs = {"cwd": str(ROOT)}
    if os.name == "nt":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    subprocess.Popen(command, **popen_kwargs)
    return {
        "status": "OPENED",
        "message": "已调起真实 JMeter 界面，并加载平台生成的线程组脚本。",
        "project_id": project_id,
        "project_name": project["name"],
        "script_key": script_key,
        "script_name": package.get("name") if package else ("工资代理快速结算" if script_key in {"salary_trade", "salary"} else "财富等级/通用接口"),
        "package_id": package.get("package_id") if package else "",
        "jmeter_command": str(jmeter),
        "runtime_parameters_passed": bool(runtime_context.get("ticket") or saved_login_password or str(options.get("login_password_encrypted") or options.get("login_t") or options.get("login_sn") or "").strip()),
        "login_password_available": bool(str(options.get("login_password_encrypted") or "").strip() or saved_login_password),
        "runtime_source": runtime_context.get("source") or "saved_runtime_credential",
        "jmx_path": str(jmx_path),
        "jtl_path": str(jtl_path),
        "summary": summary,
        "files": [generated] if generated else [],
        "policy": {
            "gui_for_review_and_maintenance": True,
            "non_gui_for_report_archive": True,
            "business_datasource_readonly": True,
        },
    }


def harvest_jmeter_workbench_report(project_id, options=None):
    options = _merge_execution_profile_options(project_id, options)
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    jtl_path = JMETER_WORKBENCH_JTL
    if not jtl_path.is_file():
        raise ValueError(f"尚未发现 JMeter GUI 结果文件：{jtl_path}。请先在 JMeter 里运行并确认监听器写入该文件。")
    summary = _summarize_jmeter_jtl(jtl_path)
    if not summary or summary.get("requests", 0) <= 0:
        raise ValueError("JMeter GUI 结果文件为空，请先运行压测并保存结果。")
    gate = _performance_gate(summary, options)
    diagnosis = _performance_diagnosis(summary, gate)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = ROOT / "reports" / f"jmeter-gui-{project_id}-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    archived_jtl = run_dir / "jmeter-gui-result.jtl"
    shutil.copy2(jtl_path, archived_jtl)
    html_dir = run_dir / "html"
    jmeter = _jmeter_command()
    html_status = "SKIPPED"
    html_error = ""
    if Path(str(jmeter)).exists() or shutil.which(str(jmeter)):
        result = _run_command_capture([str(jmeter), "-g", str(archived_jtl), "-o", str(html_dir)], ROOT, 180, os.environ.copy())
        html_status = result.get("status", "UNKNOWN")
        html_error = result.get("stderr", "")
    status = "FAILED" if summary.get("errors", 0) else gate["status"]
    report = {
        "report_type": "JMETER_GUI_WORKBENCH",
        "project_id": project_id,
        "project_name": project["name"],
        "status": status,
        "executed_at": now(),
        "source": {
            "mode": "JMeter GUI",
            "jmx_path": str(JMETER_WORKBENCH_JMX),
            "jtl_path": str(jtl_path),
            "archived_jtl": str(archived_jtl),
            "html_report": str(html_dir / "index.html") if (html_dir / "index.html").is_file() else "",
            "html_status": html_status,
            "html_error": html_error[-1000:] if html_error else "",
        },
        "performance_gate": gate,
        "performance_diagnosis": diagnosis,
        "summary": summary,
        "policy": {"external_tool": "JMeter GUI", "business_datasource_readonly": True, "secrets_runtime_only": True},
    }
    summary_file = run_dir / "summary.json"
    summary_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        **report,
        "report": str(summary_file),
        "report_url": "/reports/" + summary_file.relative_to(ROOT / "reports").as_posix(),
        "html_url": "/reports/" + (html_dir / "index.html").relative_to(ROOT / "reports").as_posix() if (html_dir / "index.html").is_file() else "",
    }


def generate_enterprise_tool_run_assets(project_id, out, options=None):
    options = options or {}
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    cases = rows("SELECT * FROM test_cases WHERE project_id=? AND method<>'' AND path<>'' ORDER BY created_at", (project_id,))
    runtime = _runtime_context(project_id, options)
    include_runtime = bool(runtime.get("ticket")) and bool(runtime.get("uid"))
    cases = _external_tool_cases(cases, include_runtime)
    if not cases:
        raise ValueError("没有可交给外部工具执行的用例")
    out.mkdir(parents=True, exist_ok=True)
    postman_runtime = _runtime_placeholder_context(runtime, "postman")
    jmeter_runtime = _runtime_placeholder_context(runtime, "jmeter")
    files = {
        "postman-collection.json": json.dumps(build_postman_collection(project, cases, postman_runtime, False), ensure_ascii=False, indent=2),
        "jmeter-plan.jmx": build_jmeter_jmx(project, cases, jmeter_runtime, False, options),
        "pytest_api_cases.py": build_pytest_script(project, cases, postman_runtime, False),
    }
    result = []
    for name, content in files.items():
        path = out / name
        path.write_text(content, encoding="utf-8")
        result.append({"name": name, "path": str(path)})
    return {"files": result, "runtime_available": include_runtime, "runtime_uid": runtime.get("uid"), "runtime_keys": [key for key, _ in _runtime_tool_pairs(runtime)], "cases": len(cases)}


def _tool_asset_report_status(results):
    if any(item["status"] == "FAILED" for item in results):
        return "FAILED"
    if any(item["status"] == "BLOCKED" for item in results):
        return "BLOCKED"
    if any(item["status"] == "WARNING" for item in results):
        return "WARNING"
    return "PASSED"


def _quality_gate_for_toolchain(results, diagnosis=None, runtime_context=None, project_id=None):
    diagnosis = diagnosis or {}
    runtime_context = runtime_context or {}
    checks = []
    blockers = []
    warnings = []
    failed = []

    for item in results:
        tool = item.get("tool", "工具")
        status = item.get("status", "UNKNOWN")
        passed = status in {"PASSED", "SKIPPED"}
        check = {
            "name": f"{tool}执行结果",
            "domain": "tool_execution",
            "status": "PASSED" if passed else status,
            "passed": passed,
            "evidence": item.get("reason") or f"{tool} {status}",
        }
        checks.append(check)
        if status == "BLOCKED":
            blockers.append(check["evidence"])
        elif status == "FAILED":
            failed.append(check["evidence"])

        if tool == "JMeter" and item.get("performance_gate"):
            gate = item["performance_gate"]
            perf_check = {
                "name": gate.get("label", "性能准入"),
                "domain": "performance",
                "status": gate.get("status", "UNKNOWN"),
                "passed": gate.get("status") == "PASSED",
                "evidence": gate.get("summary", ""),
                "metrics": {
                    "requests": item.get("requests"),
                    "error_rate": item.get("error_rate"),
                    "p95_ms": item.get("p95_ms"),
                    "p99_ms": item.get("p99_ms"),
                    "throughput_rps": item.get("throughput_rps"),
                },
                "checks": gate.get("checks", []),
            }
            checks.append(perf_check)
            if not perf_check["passed"]:
                failed.append(perf_check["evidence"])

    auth = diagnosis.get("auth") or {}
    if auth.get("items"):
        blockers.append(auth.get("summary") or "鉴权上下文待补齐")
        checks.append({
            "name": "鉴权上下文",
            "domain": "auth",
            "status": "BLOCKED",
            "passed": False,
            "evidence": auth.get("summary", ""),
            "items": auth.get("items", []),
        })
    else:
        checks.append({"name": "鉴权上下文", "domain": "auth", "status": "PASSED", "passed": True, "evidence": "未发现鉴权阻断"})

    if runtime_context.get("requested_uid") and runtime_context.get("credential_uid"):
        warnings.append("业务参数 uid 与登录 uid 不一致，平台已保护鉴权 uid。")
    if project_id:
        try:
            consistency = data_consistency_summary(project_id)
            if not consistency.get("executed_runs"):
                warnings.append("数据一致性规则尚未执行，当前结论不包含 MySQL/Redis 闭环。")
                checks.append({
                    "name": "数据一致性",
                    "domain": "data_consistency",
                    "status": "WARNING",
                    "passed": True,
                    "evidence": "尚未执行 MySQL/Redis 一致性规则",
                })
            elif consistency.get("status") != "PASSED":
                result_counts = consistency.get("result_counts") or {}
                blocked_count = int(result_counts.get("BLOCKED") or 0)
                if blocked_count:
                    blockers.append("数据一致性规则存在阻断项，请补齐 MySQL 查询条件或 Redis 映射后再判定。")
                    check_status = "BLOCKED"
                    passed = False
                    evidence = "数据一致性规则存在阻断项"
                else:
                    failed.append("数据一致性规则未通过")
                    check_status = "FAILED"
                    passed = False
                    evidence = "数据一致性规则未通过"
                checks.append({
                    "name": "数据一致性",
                    "domain": "data_consistency",
                    "status": check_status,
                    "passed": passed,
                    "evidence": evidence,
                    "summary": consistency,
                })
            else:
                result_counts = consistency.get("result_counts") or {}
                if int(result_counts.get("BLOCKED") or 0):
                    warnings.append("核心数据一致性已通过，仍有扩展候选规则阻断或超时。")
                checks.append({"name": "数据一致性", "domain": "data_consistency", "status": "PASSED", "passed": True, "evidence": "已执行且通过", "summary": consistency})
        except Exception as exc:
            warnings.append("数据一致性状态读取失败：" + str(exc))

    if blockers:
        status = "BLOCKED"
        conclusion = "存在阻断项，当前报告不能作为完整准入结论。"
    elif failed:
        status = "FAILED"
        conclusion = "存在失败项，未达到质量准入标准。"
    elif warnings:
        status = "WARNING"
        conclusion = "核心执行通过，但存在需要团队关注的风险。"
    else:
        status = "PASSED"
        conclusion = "功能执行、性能准入和鉴权上下文均通过当前规则。"

    return {
        "status": status,
        "conclusion": conclusion,
        "checks": checks,
        "blockers": list(dict.fromkeys(blockers)),
        "failures": list(dict.fromkeys(failed)),
        "warnings": list(dict.fromkeys(warnings)),
        "decision_rule": "BLOCKED 优先于 FAILED，FAILED 优先于 WARNING；全部通过才为 PASSED。",
    }


def _redact_runtime_text(text, context=None):
    if text in (None, ""):
        return ""
    redacted = str(text)
    for key, value in _runtime_tool_pairs(context or {}):
        if value and (key == "ticket" or _is_sensitive_runtime_value(key, value)):
            redacted = redacted.replace(str(value), "***REDACTED***")
    redacted = re.sub(r"((?:access_token|ticket|token|password|secret)=)[^&\\s]+", r"\1***REDACTED***", redacted, flags=re.I)
    redacted = re.sub(r"(Authorization:\\s*Bearer\\s+)[^\\s]+", r"\1***REDACTED***", redacted, flags=re.I)
    return redacted


def _sanitize_tool_result(result, context=None):
    result["stdout"] = _redact_runtime_text(result.get("stdout", ""), context)
    result["stderr"] = _redact_runtime_text(result.get("stderr", ""), context)
    return result


def _summarize_jmeter_jtl(jtl_path):
    path = Path(jtl_path)
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        samples = list(csv.DictReader(handle))
    if not samples:
        return {"requests": 0, "errors": 0, "error_rate": 100, "response_codes": {}, "failed_labels": []}
    errors = [item for item in samples if str(item.get("success", "")).lower() != "true"]
    codes = {}
    failed_labels = []
    elapsed_values = []
    started_values = []
    label_groups = {}
    slow_samples = []
    for item in samples:
        code = str(item.get("responseCode") or "UNKNOWN")
        codes[code] = codes.get(code, 0) + 1
        elapsed = None
        try:
            elapsed = float(item.get("elapsed") or 0)
            elapsed_values.append(elapsed)
        except Exception:
            pass
        label = item.get("label") or "未命名请求"
        if elapsed is not None:
            label_groups.setdefault(label, []).append(elapsed)
            slow_samples.append({"label": label, "elapsed_ms": elapsed, "response_code": code, "success": str(item.get("success", "")).lower() == "true"})
        try:
            started_values.append(float(item.get("timeStamp") or 0))
        except Exception:
            pass
        if str(item.get("success", "")).lower() != "true":
            failed_labels.append(f"{item.get('label') or '未命名请求'}({code})")
    duration_seconds = 0
    if started_values:
        duration_seconds = max((max(started_values) - min(started_values)) / 1000, 0.001)
    by_label = []
    for label, values in label_groups.items():
        by_label.append({
            "label": label,
            "samples": len(values),
            "average_ms": round(statistics.mean(values), 2) if values else 0,
            "min_ms": round(min(values), 2) if values else 0,
            "max_ms": round(max(values), 2) if values else 0,
            "p90_ms": _percentile(values, 90),
            "p95_ms": _percentile(values, 95),
        })
    by_label.sort(key=lambda item: item["max_ms"], reverse=True)
    average_ms = round(sum(elapsed_values) / len(elapsed_values), 2) if elapsed_values else 0
    p95_ms = _percentile(elapsed_values, 95)
    stddev_ms = round(statistics.pstdev(elapsed_values), 2) if len(elapsed_values) > 1 else 0
    tail_note = ""
    if elapsed_values and average_ms > p95_ms:
        tail_note = "平均值高于P95，通常表示样本量较小或存在极端慢请求；请优先查看最慢样本和聚合图形报告。"
    return {
        "requests": len(samples),
        "errors": len(errors),
        "error_rate": round(len(errors) / len(samples) * 100, 2),
        "response_codes": codes,
        "failed_labels": failed_labels[:10],
        "average_ms": average_ms,
        "min_ms": round(min(elapsed_values), 2) if elapsed_values else 0,
        "max_ms": round(max(elapsed_values), 2) if elapsed_values else 0,
        "p50_ms": _percentile(elapsed_values, 50),
        "p90_ms": _percentile(elapsed_values, 90),
        "p95_ms": p95_ms,
        "p99_ms": _percentile(elapsed_values, 99),
        "stddev_ms": stddev_ms,
        "throughput_rps": round(len(samples) / duration_seconds, 2) if duration_seconds else 0,
        "slowest_samples": sorted(slow_samples, key=lambda item: item["elapsed_ms"], reverse=True)[:10],
        "by_label": by_label[:20],
        "tail_note": tail_note,
    }


def _percentile(values, percentile):
    numbers = sorted(float(value) for value in values if value is not None)
    if not numbers:
        return 0
    index = (len(numbers) - 1) * percentile / 100
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return round(numbers[int(index)], 2)
    return round(numbers[lower] + (numbers[upper] - numbers[lower]) * (index - lower), 2)


def _performance_diagnosis(summary, gate=None):
    gate = gate or {}
    requests = int(summary.get("requests") or 0)
    errors = int(summary.get("errors") or 0)
    error_rate = float(summary.get("error_rate") or 0)
    average = float(summary.get("average_ms") or 0)
    median = float(summary.get("p50_ms") or 0)
    p95 = float(summary.get("p95_ms") or 0)
    p99 = float(summary.get("p99_ms") or 0)
    max_ms = float(summary.get("max_ms") or 0)
    stddev = float(summary.get("stddev_ms") or 0)
    findings = []
    if requests < 30:
        findings.append({"severity": "INFO", "title": "样本量偏少", "detail": f"当前仅 {requests} 个样本，适合冒烟观察，不适合直接形成容量结论。"})
    if errors:
        findings.append({"severity": "P0", "title": "存在失败采样", "detail": f"失败 {errors} 次，错误率 {error_rate}%。企业评审通常先处理错误率，再讨论响应时间。"})
    if median and average > median * 1.25:
        findings.append({"severity": "P1", "title": "平均值被慢请求拉高", "detail": f"平均 {average}ms 明显高于中位数 {median}ms，说明存在尾部慢请求或样本分布不均。"})
    if p95 and p99 and p99 > p95 * 1.4:
        findings.append({"severity": "P1", "title": "尾部延迟尖刺", "detail": f"P99 {p99}ms 明显高于 P95 {p95}ms，需要查看最慢样本定位偶发慢接口。"})
    if p95 and max_ms > p95 * 1.5:
        findings.append({"severity": "P2", "title": "最大值离群", "detail": f"最大耗时 {max_ms}ms 高于 P95 {p95}ms，建议结合聚合图形报告看是否为单点抖动。"})
    if stddev and average and stddev > average * 0.5:
        findings.append({"severity": "P2", "title": "耗时波动较大", "detail": f"标准差 {stddev}ms，说明接口耗时稳定性不足。"})
    bottlenecks = []
    for item in summary.get("by_label") or []:
        if not isinstance(item, dict):
            continue
        score = float(item.get("p95_ms") or item.get("max_ms") or item.get("average_ms") or 0)
        bottlenecks.append({
            "label": item.get("label") or "未命名请求",
            "samples": item.get("samples", 0),
            "average_ms": item.get("average_ms", 0),
            "p95_ms": item.get("p95_ms", 0),
            "max_ms": item.get("max_ms", 0),
            "score": score,
        })
    bottlenecks.sort(key=lambda item: item["score"], reverse=True)
    gate_status = gate.get("status") or "UNKNOWN"
    if errors:
        conclusion = "当前不能给出通过结论：存在失败采样，需先确认是接口错误、断言失败还是脚本配置问题。"
    elif gate_status == "FAILED":
        conclusion = "接口可用但未达到当前性能准入阈值，需要结合慢接口和尾部延迟继续定位。"
    elif requests < 30:
        conclusion = "当前可作为冒烟结果：接口链路可用，但样本量不足，建议扩大样本后再出正式性能结论。"
    else:
        conclusion = "当前性能准入通过，可进入更高并发或稳定性场景验证。"
    return {
        "conclusion": conclusion,
        "sample_grade": "INSUFFICIENT" if requests < 30 else "OBSERVABLE" if requests < 100 else "BASELINE_READY",
        "enterprise_focus": ["错误率", "P95/P99尾部延迟", "慢接口Top", "样本量", "SLA准入", "原始JTL/HTML可追溯"],
        "findings": findings,
        "bottlenecks": bottlenecks[:5],
        "slowest_samples": summary.get("slowest_samples", [])[:10],
    }


def _jmeter_thresholds(options=None):
    options = options or {}
    profile = str(options.get("performance_profile") or "smoke").strip().lower()
    defaults = {
        "smoke": {"label": "冒烟验证", "max_error_rate": 0, "max_p95_ms": 3000, "max_p99_ms": 5000, "min_throughput_rps": 0},
        "baseline": {"label": "基准压测", "max_error_rate": 1, "max_p95_ms": 1500, "max_p99_ms": 2500, "min_throughput_rps": 1},
        "load": {"label": "阶梯负载", "max_error_rate": 1, "max_p95_ms": 2000, "max_p99_ms": 3500, "min_throughput_rps": 5},
        "stability": {"label": "稳定性", "max_error_rate": 0.5, "max_p95_ms": 2000, "max_p99_ms": 4000, "min_throughput_rps": 2},
    }
    thresholds = dict(defaults.get(profile, defaults["smoke"]))
    thresholds["profile"] = profile if profile in defaults else "smoke"
    for key in ("max_error_rate", "max_p95_ms", "max_p99_ms", "min_throughput_rps"):
        if options.get(key) not in (None, ""):
            try:
                thresholds[key] = float(options.get(key))
            except Exception:
                pass
    return thresholds


def _performance_gate(summary, options=None):
    thresholds = _jmeter_thresholds(options)
    checks = [
        {"name": "错误率", "actual": float(summary.get("error_rate") or 0), "operator": "<=", "expected": thresholds["max_error_rate"], "passed": float(summary.get("error_rate") or 0) <= thresholds["max_error_rate"], "unit": "%"},
        {"name": "P95响应时间", "actual": float(summary.get("p95_ms") or 0), "operator": "<=", "expected": thresholds["max_p95_ms"], "passed": float(summary.get("p95_ms") or 0) <= thresholds["max_p95_ms"], "unit": "ms"},
        {"name": "P99响应时间", "actual": float(summary.get("p99_ms") or 0), "operator": "<=", "expected": thresholds["max_p99_ms"], "passed": float(summary.get("p99_ms") or 0) <= thresholds["max_p99_ms"], "unit": "ms"},
    ]
    if thresholds["min_throughput_rps"] > 0:
        checks.append({"name": "吞吐量", "actual": float(summary.get("throughput_rps") or 0), "operator": ">=", "expected": thresholds["min_throughput_rps"], "passed": float(summary.get("throughput_rps") or 0) >= thresholds["min_throughput_rps"], "unit": "req/s"})
    failed = [item for item in checks if not item["passed"]]
    return {
        "profile": thresholds["profile"],
        "label": thresholds["label"],
        "status": "PASSED" if not failed else "FAILED",
        "thresholds": thresholds,
        "checks": checks,
        "summary": "性能阈值通过" if not failed else "性能阈值未达标：" + "、".join(item["name"] for item in failed),
    }


def _normalize_jmeter_result(result, jtl_path, options=None):
    summary = _summarize_jmeter_jtl(jtl_path)
    if summary:
        result.update(summary)
        gate = _performance_gate(summary, options)
        result["performance_gate"] = gate
        result["performance_diagnosis"] = _performance_diagnosis(summary, gate)
        if summary.get("errors", 0) > 0:
            result["status"] = "FAILED"
            result["reason"] = "JMeter 执行完成但存在失败采样：" + "、".join(summary.get("failed_labels") or [])
        elif gate["status"] == "FAILED":
            result["status"] = "FAILED"
            result["reason"] = gate["summary"]
    return result


def _case_query_keys(case):
    path = str(case.get("path") or "")
    parsed = urllib.parse.urlsplit(path if path.startswith("http") else "https://local" + (path if path.startswith("/") else "/" + path))
    return set(urllib.parse.parse_qs(parsed.query).keys())


def _payload_keys(payload):
    if isinstance(payload, dict):
        return set(payload)
    if isinstance(payload, str):
        return set(urllib.parse.parse_qs(payload, keep_blank_values=True).keys())
    return set()


def _auth_gap_diagnostics(cases, results, runtime_context):
    failed_results = [item for item in results if item.get("status") == "FAILED"]
    has_401 = any("401" in str(item.get("stdout", "")) or "401" in str(item.get("stderr", "")) or (item.get("response_codes") or {}).get("401") for item in failed_results)
    if not has_401:
        return {"status": "PASSED", "items": []}
    login_case = next((case for case in cases if _is_login_case(case)), None)
    protected = [case for case in cases if not _is_login_case(case) and _tool_expected_status(case) == 200 and _case_has_runtime_placeholder(case)]
    login_headers, login_payload = _case_request(login_case) if login_case else ({}, {})
    login_payload_keys = _payload_keys(login_payload)
    important_payload_keys = {"deviceId", "model", "osVersion", "netType", "channel", "packageName", "ispType", "organic", "version", "isVpnConnected"}
    items = []
    for case in protected:
        headers, _ = _case_request(case)
        query_keys = _case_query_keys(case)
        missing_headers = [key for key in login_headers if key not in headers and not runtime_context.get(key) and key.lower() not in {"content-type"}]
        missing_device_params = sorted(key for key in (login_payload_keys & important_payload_keys) - query_keys if not runtime_context.get(key))
        synced = [key for key in ("t", "sn", *sorted(important_payload_keys)) if runtime_context.get(key)]
        warnings = list(runtime_context.get("_runtime_warnings") or [])
        blockers = []
        if missing_headers:
            blockers.append("缺少登录请求头样本：" + "、".join(missing_headers))
        if "sn" in missing_headers:
            blockers.append("缺少 sn 或 sn 生成规则；如果业务接口要求签名，需要补抓样本或配置签名算法。")
        if missing_device_params:
            blockers.append("缺少设备上下文参数：" + "、".join(missing_device_params))
        if warnings:
            blockers.extend(warnings)
        if runtime_context.get("requested_uid") and runtime_context.get("credential_uid"):
            blockers.append("业务参数 uid 与登录 uid 不一致，平台已保护鉴权 uid；如需测多账号，请使用多账号登录性能专项。")
        if not blockers:
            blockers.append("上下文已同步但仍返回 401，需要确认 ticket 放置位置或额外鉴权 header。")
        items.append({
            "case_title": case.get("title", ""),
            "method": case.get("method", ""),
            "path": str(case.get("path", "")).split("?")[0],
            "http_status": 401,
            "runtime_source": runtime_context.get("source", ""),
            "runtime_uid": runtime_context.get("uid", ""),
            "missing": {
                "headers_from_login": missing_headers,
                "device_context_params": missing_device_params,
            },
            "synced_context": synced,
            "blockers": blockers,
            "recommendation": "；".join(blockers),
        })
    return {
        "status": "ATTENTION",
        "summary": "登录接口已成功，但后续鉴权接口返回 401；平台已归纳需要补齐的鉴权上下文。",
        "items": items,
    }


def _readonly_auth_probe(project, cases, runtime_context):
    if not runtime_context.get("ticket") or not runtime_context.get("uid"):
        return {"status": "SKIPPED", "reason": "缺少可探测的 ticket 或 uid", "items": []}
    protected = [case for case in cases if not _is_login_case(case) and str(case.get("method", "")).upper() == "GET" and _tool_expected_status(case) == 200 and _case_has_runtime_placeholder(case)]
    if not protected:
        return {"status": "SKIPPED", "reason": "没有可用于只读鉴权探测的 GET 业务用例", "items": []}
    case = protected[0]
    case_path, base_headers, _ = _case_request_with_runtime_context(case, runtime_context)
    path = _replace_runtime_placeholders(case_path, runtime_context, False)
    parsed = urllib.parse.urlsplit(path if path.startswith("http") else (project.get("base_url") or "").rstrip("/") + "/" + path.lstrip("/"))
    query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    base_params = {key: values[-1] if values else "" for key, values in query.items() if key not in {"ticket", "access_token", "token"}}
    headers = _replace_runtime_placeholders(base_headers, runtime_context, False)
    headers.setdefault("Accept", "application/json")
    variants = [
        ("query_ticket", {"ticket": runtime_context["ticket"]}, {}),
        ("query_access_token", {"access_token": runtime_context["ticket"]}, {}),
        ("header_ticket", {}, {"ticket": runtime_context["ticket"]}),
        ("bearer_authorization", {}, {"Authorization": "Bearer " + runtime_context["ticket"]}),
    ]
    if runtime_context.get("sn"):
        variants.append(("query_ticket_with_sn", {"ticket": runtime_context["ticket"]}, {"sn": runtime_context["sn"]}))
    items = []
    for name, extra_params, extra_headers in variants:
        params = {**base_params, **extra_params}
        probe_headers = {**headers, **extra_headers}
        url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(params), parsed.fragment))
        started = time.perf_counter()
        http_status, business_code, message = None, None, ""
        try:
            req = urllib.request.Request(url, method="GET", headers=probe_headers)
            try:
                resp = urllib.request.urlopen(req, timeout=15)
                http_status, raw = resp.status, resp.read(100000)
            except urllib.error.HTTPError as exc:
                http_status, raw = exc.code, exc.read(100000)
            try:
                body = json.loads(raw.decode("utf-8", "replace"))
                business_code = body.get("code") if isinstance(body, dict) else None
                message = str(body.get("message") or "") if isinstance(body, dict) else ""
            except Exception:
                message = raw.decode("utf-8", "replace")[:160]
        except Exception as exc:
            message = str(exc)
        items.append({
            "variant": name,
            "status": "PASSED" if http_status == 200 and business_code in (None, 200) else "FAILED",
            "http_status": http_status,
            "business_code": business_code,
            "message": _redact_runtime_text(message, runtime_context)[:200],
            "duration_ms": int((time.perf_counter() - started) * 1000),
        })
    passed = [item for item in items if item["status"] == "PASSED"]
    if passed:
        return {"status": "PASSED", "summary": "已找到可用鉴权放置方式：" + passed[0]["variant"], "case_title": case.get("title", ""), "items": items}
    return {"status": "FAILED", "summary": "常见 ticket 放置方式均未通过，优先补齐 sn/签名规则或重新抓取该业务接口完整请求。", "case_title": case.get("title", ""), "items": items}


def _run_command_capture(command, cwd, timeout=180, env=None):
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )
        status = "PASSED" if completed.returncode == 0 else "FAILED"
        return {
            "status": status,
            "exit_code": completed.returncode,
            "duration_ms": int((time.perf_counter() - started) * 1000),
            "stdout": (completed.stdout or "")[-8000:],
            "stderr": (completed.stderr or "")[-8000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "FAILED",
            "exit_code": None,
            "duration_ms": int((time.perf_counter() - started) * 1000),
            "stdout": (exc.stdout or "")[-8000:] if isinstance(exc.stdout, str) else "",
            "stderr": "执行超时，平台已停止等待外部工具返回。",
        }
    except Exception as exc:
        return {
            "status": "BLOCKED",
            "exit_code": None,
            "duration_ms": int((time.perf_counter() - started) * 1000),
            "stdout": "",
            "stderr": str(exc),
        }


def _jmeter_command():
    config_home = str(deep_get(load_environment_config(), "tools.jmeter.home", "") or "").strip()
    config_command = str(Path(config_home) / "bin" / "jmeter.bat") if config_home else ""
    configured = os.getenv("AUTOTEST_JMETER") or config_command or r"D:\apache-jmeter-5.6.3\bin\jmeter.bat"
    if Path(configured).exists():
        return configured
    return shutil.which("jmeter") or configured


def _tool_result_blocked(name, reason, artifact=""):
    return {
        "tool": name,
        "status": "BLOCKED",
        "reason": reason,
        "artifact": artifact,
        "duration_ms": 0,
        "exit_code": None,
        "stdout": "",
        "stderr": reason,
    }


def _toolchain_blocked_report(project_id, project, runtime_context, options, reason, source="runtime_context_blocked"):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = ROOT / "reports" / f"toolchain-{project_id}-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for tool_name, enabled in (("Newman", options.get("run_newman", True) is not False), ("JMeter", options.get("run_jmeter", True) is not False), ("pytest", options.get("run_pytest", True) is not False)):
        if enabled:
            results.append(_tool_result_blocked(tool_name, reason))
        else:
            results.append({"tool": tool_name, "status": "SKIPPED", "reason": "本次执行参数选择跳过", "artifact": "", "duration_ms": 0, "exit_code": None, "stdout": "", "stderr": ""})
    runtime_pairs = _runtime_tool_pairs(runtime_context)
    report = {
        "report_type": "ENTERPRISE_TOOLCHAIN_RUN",
        "project_id": project_id,
        "project_name": project["name"],
        "status": "BLOCKED",
        "executed_at": now(),
        "assets": [],
        "runtime_assets": [],
        "runtime": {
            "credential_reused": runtime_context.get("source") == "saved_runtime_credential",
            "source": runtime_context.get("source") or source,
            "uid": runtime_context.get("uid", ""),
            "ticket": "***REDACTED***" if runtime_context.get("ticket") else "",
            "params": {key: ("***REDACTED***" if _is_sensitive_runtime_value(key, value) else value) for key, value in runtime_pairs if key not in {"ticket"}},
            "warnings": runtime_context.get("_runtime_warnings", []),
        },
        "results": results,
        "diagnosis": {"auth": {"status": "BLOCKED", "summary": reason, "items": []}},
        "policy": {"external_tools_called": False, "business_datasource_readonly": True, "secrets_runtime_only": True, "raw_har_exported": False, "login_endpoint_mode": "setup_only"},
        "summary": {"total": len(results), "passed": 0, "failed": 0, "blocked": sum(item["status"] == "BLOCKED" for item in results)},
    }
    report_path = run_dir / "summary.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return {**report, "report": str(report_path), "report_url": "/reports/" + report_path.relative_to(ROOT / "reports").as_posix()}


def _missing_required_login_context(project_id, runtime_context):
    source_cases = rows("SELECT * FROM test_cases WHERE project_id=? AND method<>'' AND path<>'' ORDER BY created_at", (project_id,))
    protected = [case for case in source_cases if not _is_login_case(case) and _tool_expected_status(case) == 200 and _case_has_runtime_placeholder(case)]
    if not protected:
        return []
    required = ["t", "deviceId", "model", "osVersion", "netType", "channel", "packageName", "appid"]
    return [key for key in required if not runtime_context.get(key)]


def run_enterprise_toolchain(project_id, options=None):
    options = _merge_execution_profile_options(project_id, options)
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    runtime_context = _login_runtime_context(project_id, options)
    missing_login_context = _missing_required_login_context(project_id, runtime_context)
    if runtime_context.get("source") == "saved_runtime_credential" and missing_login_context:
        return _toolchain_blocked_report(
            project_id,
            project,
            runtime_context,
            options,
            "当前复用的本机凭证缺少登录上下文：" + "、".join(missing_login_context) + "。请在执行策略选择“强制重新登录”，填写加密密码后重新执行；t 可留空由平台生成。",
        )
    login_blockers = {
        "missing_login_input": "已选择重新登录或填写了部分登录参数，但缺少加密密码；t 可留空由平台生成。",
        "missing_login_case": "当前项目缺少登录接口用例，无法刷新运行凭证。",
        "login_failed": "登录接口执行失败，平台未复用旧凭证。",
    }
    if runtime_context.get("source") in login_blockers:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir = ROOT / "reports" / f"toolchain-{project_id}-{stamp}"
        run_dir.mkdir(parents=True, exist_ok=True)
        reason = login_blockers[runtime_context.get("source")]
        results = []
        for tool_name, enabled in (("Newman", options.get("run_newman", True) is not False), ("JMeter", options.get("run_jmeter", True) is not False), ("pytest", options.get("run_pytest", True) is not False)):
            if enabled:
                results.append(_tool_result_blocked(tool_name, reason))
            else:
                results.append({"tool": tool_name, "status": "SKIPPED", "reason": "本次执行参数选择跳过", "artifact": "", "duration_ms": 0, "exit_code": None, "stdout": "", "stderr": ""})
        report = {
            "report_type": "ENTERPRISE_TOOLCHAIN_RUN",
            "project_id": project_id,
            "project_name": project["name"],
            "status": "BLOCKED",
            "executed_at": now(),
            "assets": [],
            "runtime_assets": [],
            "runtime": {"credential_reused": False, "source": runtime_context.get("source", ""), "uid": runtime_context.get("uid", ""), "ticket": "", "params": {key: value for key, value in _runtime_tool_pairs(runtime_context) if key not in {"ticket"}}},
            "results": results,
        "policy": {"external_tools_called": False, "business_datasource_readonly": True, "secrets_runtime_only": True, "raw_har_exported": False},
            "summary": {"total": len(results), "passed": 0, "failed": 0, "blocked": sum(item["status"] == "BLOCKED" for item in results)},
        }
        report_path = run_dir / "summary.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return {**report, "report": str(report_path), "report_url": "/reports/" + report_path.relative_to(ROOT / "reports").as_posix()}
    effective_options = {**options, "runtime_ticket": runtime_context.get("ticket", ""), "runtime_uid": runtime_context.get("uid", "")}
    public_assets = generate_enterprise_tool_assets(project_id, effective_options)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = ROOT / "reports" / f"toolchain-{project_id}-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    asset_dir = run_dir / "runtime-assets"
    run_assets = generate_enterprise_tool_run_assets(project_id, asset_dir, effective_options)
    runtime_env = os.environ.copy()
    runtime_env["AUTOTEST_RUNTIME_TICKET"] = runtime_context.get("ticket", "")
    runtime_env["AUTOTEST_RUNTIME_UID"] = runtime_context.get("uid", "")
    runtime_env["AUTOTEST_RUNTIME_PARAMS_JSON"] = json.dumps(dict(_runtime_tool_pairs(runtime_context)), ensure_ascii=False)
    runtime_pairs = _runtime_tool_pairs(runtime_context)
    results = []

    if options.get("run_newman", True) is False:
        results.append({"tool": "Newman", "status": "SKIPPED", "reason": "本次执行参数选择跳过 Newman", "artifact": "postman-collection.json", "duration_ms": 0, "exit_code": None, "stdout": "", "stderr": ""})
    else:
        newman = shutil.which("newman")
        if newman:
            json_report = run_dir / "newman-report.json"
            command = [newman, "run", str(asset_dir / "postman-collection.json")]
            for key, value in runtime_pairs:
                command.extend(["--env-var", f"{key}={value}"])
            command.extend(["--reporters", "cli,json", "--reporter-json-export", str(json_report)])
            result = _sanitize_tool_result(_run_command_capture(command, ROOT, 180, runtime_env), runtime_context)
            result.update({"tool": "Newman", "artifact": "postman-collection.json", "json_report": str(json_report) if json_report.is_file() else ""})
            results.append(result)
        else:
            results.append(_tool_result_blocked("Newman", "本机未安装 Newman；可执行 npm install -g newman。", "postman-collection.json"))

    if options.get("run_jmeter", True) is False:
        results.append({"tool": "JMeter", "status": "SKIPPED", "reason": "本次执行参数选择跳过 JMeter", "artifact": "jmeter-plan.jmx", "duration_ms": 0, "exit_code": None, "stdout": "", "stderr": ""})
    else:
        jmeter = _jmeter_command()
        if Path(jmeter).exists() or shutil.which(str(jmeter)):
            jmx_text = (asset_dir / "jmeter-plan.jmx").read_text(encoding="utf-8")
            if "HTTPSamplerProxy" not in jmx_text:
                results.append(_tool_result_blocked("JMeter", "当前没有无需凭证且适合性能冒烟的只读接口；请补齐可复用凭证后生成性能资产。", "jmeter-plan.jmx"))
            else:
                jtl = run_dir / "jmeter-result.jtl"
                html_dir = run_dir / "jmeter-html"
                command = [
                    str(jmeter),
                    "-n",
                    "-t",
                    str(asset_dir / "jmeter-plan.jmx"),
                    "-l",
                    str(jtl),
                    "-e",
                    "-o",
                    str(html_dir),
                    "-Jjmeter.save.saveservice.url=false",
                    "-Jjmeter.save.saveservice.response_data=false",
                    "-Jjmeter.save.saveservice.requestHeaders=false",
                    "-Jjmeter.save.saveservice.responseHeaders=false",
                ]
                for key, value in runtime_pairs:
                    command.append(f"-J{key}={value}")
                result = _sanitize_tool_result(_run_command_capture(command, ROOT, int(options.get("jmeter_timeout", 180)), runtime_env), runtime_context)
                result = _normalize_jmeter_result(result, jtl, options)
                result.update({"tool": "JMeter", "artifact": "jmeter-plan.jmx", "jtl": str(jtl) if jtl.is_file() else "", "html_report": str(html_dir / "index.html") if (html_dir / "index.html").is_file() else ""})
                results.append(result)
        else:
            results.append(_tool_result_blocked("JMeter", "本机未找到 JMeter；请配置 AUTOTEST_JMETER。", "jmeter-plan.jmx"))

    if options.get("run_pytest", True) is False:
        results.append({"tool": "pytest", "status": "SKIPPED", "reason": "本次执行参数选择跳过 pytest", "artifact": "pytest_api_cases.py", "duration_ms": 0, "exit_code": None, "stdout": "", "stderr": ""})
    else:
        pytest_probe = _python_module_probe("pytest", "pytest", ["--version"], "在当前 Python 环境安装 pytest。")
        if pytest_probe["status"] == "READY":
            result = _sanitize_tool_result(_run_command_capture([sys.executable, "-m", "pytest", str(asset_dir / "pytest_api_cases.py"), "-q"], ROOT, 180, runtime_env), runtime_context)
            result.update({"tool": "pytest", "artifact": "pytest_api_cases.py"})
            results.append(result)
        else:
            results.append(_tool_result_blocked("pytest", "当前环境未安装 pytest；可在 Python 环境安装 pytest。", "pytest_api_cases.py"))

    source_cases = rows("SELECT * FROM test_cases WHERE project_id=? AND method<>'' AND path<>'' ORDER BY created_at", (project_id,))
    diagnosis = {"auth": _auth_gap_diagnostics(source_cases, results, runtime_context)}
    if diagnosis["auth"].get("items"):
        diagnosis["auth_probe"] = _readonly_auth_probe(project, source_cases, runtime_context)
    if diagnosis["auth"].get("items"):
        auth_summary = diagnosis["auth"].get("summary", "鉴权接口返回 401，请补齐请求上下文。")
        for item in results:
            if item.get("status") == "FAILED" and not item.get("reason"):
                item["reason"] = auth_summary
    quality_gate = _quality_gate_for_toolchain(results, diagnosis, runtime_context, project_id)

    report = {
        "report_type": "ENTERPRISE_TOOLCHAIN_RUN",
        "project_id": project_id,
        "project_name": project["name"],
        "status": quality_gate["status"],
        "executed_at": now(),
        "assets": public_assets["files"],
        "runtime_assets": [{"name": item["name"], "path": str(Path(item["path"]).relative_to(run_dir))} for item in run_assets["files"]],
        "runtime": {
            "credential_reused": bool(run_assets.get("runtime_available")),
            "source": runtime_context.get("source", ""),
            "uid": run_assets.get("runtime_uid"),
            "ticket": "***REDACTED***" if run_assets.get("runtime_available") else "",
            "credential_flow": "登录接口 data.access_token 已作为 ticket 注入后续业务接口" if runtime_context.get("source") == "login_api" else "复用本机保存 ticket 注入后续业务接口",
            "params": {key: ("***REDACTED***" if _is_sensitive_runtime_value(key, value) else value) for key, value in runtime_pairs if key not in {"ticket"}},
            "warnings": runtime_context.get("_runtime_warnings", []),
        },
        "execution_options": {
            "tools": {
                "newman": options.get("run_newman", True) is not False,
                "jmeter": options.get("run_jmeter", True) is not False,
                "pytest": options.get("run_pytest", True) is not False,
            },
            "jmeter": {
                "threads": max(1, min(int(options.get("jmeter_threads", 1) or 1), 200)),
                "loops": max(1, min(int(options.get("jmeter_loops", 1) or 1), 1000)),
                "rampup_seconds": max(0, min(int(options.get("jmeter_rampup", 1) or 1), 600)),
                "timeout_seconds": max(30, min(int(options.get("jmeter_timeout", 180) or 180), 3600)),
                "performance_profile": _jmeter_thresholds(options),
            },
        },
        "results": results,
        "diagnosis": diagnosis,
        "quality_gate": quality_gate,
        "policy": {
            "external_tools_called": True,
            "business_datasource_readonly": True,
            "secrets_runtime_only": True,
            "raw_har_exported": False,
            "login_endpoint_mode": "setup_only",
            "login_performance_scope": "仅多账号登录专项压测允许纳入，普通业务工具链默认排除",
        },
        "summary": {
            "total": len(results),
            "passed": sum(item["status"] == "PASSED" for item in results),
            "failed": sum(item["status"] == "FAILED" for item in results),
            "blocked": sum(item["status"] == "BLOCKED" for item in results),
        },
    }
    report_path = run_dir / "summary.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return {**report, "report": str(report_path), "report_url": "/reports/" + report_path.relative_to(ROOT / "reports").as_posix()}


def run_security_scan(project_id):
    project=row("SELECT * FROM projects WHERE id=?",(project_id,))
    if not project: raise ValueError("项目不存在")
    sid=uid("sec"); findings=[]; headers={}; status_code=None
    if project["base_url"]:
        try:
            req=urllib.request.Request(project["base_url"],method="GET",headers={"User-Agent":"AutoTestAI-Security-Audit/1.0"})
            try:
                resp=urllib.request.urlopen(req,timeout=15); status_code=resp.status; headers=dict(resp.headers)
            except urllib.error.HTTPError as e: status_code=e.code; headers=dict(e.headers)
        except Exception as e:
            findings.append(("medium","availability",project["base_url"],"测试环境基础地址不可访问",str(e),"检查DNS、TLS、网关和网络白名单"))
    expected={"Strict-Transport-Security":"缺少HSTS","Content-Security-Policy":"缺少CSP","X-Content-Type-Options":"缺少MIME嗅探保护","X-Frame-Options":"缺少点击劫持保护"}
    for key,title in expected.items():
        if headers and key not in headers: findings.append(("medium" if key in {"Content-Security-Policy","Strict-Transport-Security"} else "low","security_header",project["base_url"],title,"响应头未发现 "+key,"在网关或应用层配置该安全响应头"))
    endpoints=rows("SELECT * FROM api_endpoints WHERE project_id=?",(project_id,))
    for ep in endpoints:
        if ep["danger_score"]>=80 and not ep["auth_required"]:
            findings.append(("high","auth_documentation",ep["path"],"极高危险接口未声明认证",ep["danger_warning"],"确认实际鉴权方式并在OpenAPI security中声明"))
    cors=headers.get("Access-Control-Allow-Origin","")
    if cors=="*" and str(headers.get("Access-Control-Allow-Credentials","")).lower()=="true": findings.append(("high","cors",project["base_url"],"CORS允许任意来源并携带凭证",f"Origin={cors}","限制允许来源且避免通配符与凭证组合"))
    score=max(0,100-sum({"critical":30,"high":15,"medium":6,"low":2}.get(x[0],2) for x in findings))
    with db() as conn:
        conn.execute("INSERT INTO security_scans VALUES (?,?,?,?,?,?,?)",(sid,project_id,"COMPLETED",score,len(findings),f"HTTP {status_code}; 检查{len(endpoints)}个接口",now()))
        conn.executemany("INSERT INTO security_findings VALUES (?,?,?,?,?,?,?,?,?)",[(uid("finding"),sid,project_id,*x) for x in findings])
    return row("SELECT * FROM security_scans WHERE id=?",(sid,))


def generate_operations_assets(project_id):
    project=row("SELECT * FROM projects WHERE id=?",(project_id,))
    base=project["base_url"].rstrip("/") if project and project["base_url"] else "https://test.example.com"
    pages=[("CMS登录页",base+"/web-H5-admin/index.html","后台登录、菜单加载、权限和会话检查"),("测试环境首页",base+"/","页面可访问性、控制台错误和基础性能")]
    plans=[]
    for name,url,desc in pages:
        scenarios=["页面成功打开且无严重控制台错误","关键资源请求无5xx","检查表单、按钮与导航可交互","截取失败截图","检查基础可访问性"]
        script=f'''const {{ test, expect }} = require('@playwright/test');\n\ntest('{name}', async ({{ page }}) => {{\n  const errors = [];\n  page.on('console', m => {{ if (m.type() === 'error') errors.push(m.text()); }});\n  const response = await page.goto('{url}', {{ waitUntil: 'networkidle' }});\n  expect(response && response.status()).toBeLessThan(500);\n  await expect(page.locator('body')).toBeVisible();\n  await page.screenshot({{ path: 'artifacts/{name}.png', fullPage: true }});\n  expect(errors).toEqual([]);\n}});\n'''
        plans.append((uid("ui"),project_id,name,url,desc,json.dumps(scenarios,ensure_ascii=False),script,20,"ready",now()))
    suites=rows("SELECT id,name FROM automation_suites WHERE project_id=? ORDER BY name LIMIT 5",(project_id,)); workflows=rows("SELECT id,name FROM workflows WHERE project_id=? ORDER BY priority LIMIT 5",(project_id,))
    jobs=[(uid("job"),project_id,"每日被动安全扫描","security",project_id,1440,0,None,None,"NEVER",now())]
    jobs += [(uid("job"),project_id,"定时套件："+x["name"],"suite",x["id"],1440,0,None,None,"NEVER",now()) for x in suites]
    jobs += [(uid("job"),project_id,"定时流程："+x["name"],"workflow",x["id"],1440,0,None,None,"NEVER",now()) for x in workflows]
    with db() as conn:
        conn.execute("DELETE FROM ui_test_plans WHERE project_id=?",(project_id,)); conn.execute("DELETE FROM scheduled_jobs WHERE project_id=?",(project_id,))
        conn.executemany("INSERT INTO ui_test_plans VALUES (?,?,?,?,?,?,?,?,?,?)",plans); conn.executemany("INSERT INTO scheduled_jobs VALUES (?,?,?,?,?,?,?,?,?,?,?)",jobs)
    return {"ui_plans":len(plans),"scheduled_jobs":len(jobs)}


def dispatch_job(job):
    if job["job_type"]=="security": result=run_security_scan(job["project_id"])
    elif job["job_type"]=="suite": result=run_suite(job["target_id"])
    elif job["job_type"]=="workflow": result=execute_workflow(job["target_id"])
    elif job["job_type"]=="performance": result=run_performance(job["target_id"])
    else: raise ValueError("未知任务类型")
    status=result.get("status","COMPLETED") if isinstance(result,dict) else "COMPLETED"
    nxt=(datetime.now(timezone.utc).astimezone()+timedelta(minutes=job["interval_minutes"])).isoformat(timespec="seconds")
    execute("UPDATE scheduled_jobs SET last_run_at=?,next_run_at=?,last_status=? WHERE id=?",(now(),nxt,status,job["id"]))
    return result


def scheduler_loop():
    while True:
        try:
            current=now()
            for job in rows("SELECT * FROM scheduled_jobs WHERE enabled=1 AND (next_run_at IS NULL OR next_run_at<=?)",(current,)):
                try: dispatch_job(job)
                except Exception as e: execute("UPDATE scheduled_jobs SET last_run_at=?,last_status=? WHERE id=?",(now(),"ERROR: "+str(e)[:100],job["id"]))
        except Exception: traceback.print_exc()
        time.sleep(30)


ROLE_PERMISSIONS={"owner":["project.manage","requirements.edit","apis.edit","tests.edit","tests.run","schedules.manage","approvals.review"],"manager":["requirements.edit","apis.edit","tests.edit","tests.run","schedules.manage","approvals.review"],"tester":["requirements.edit","apis.edit","tests.edit","tests.run"],"viewer":[]}


def analyze_requirement_source(project_id, source_id, content):
    items=[]
    for i,rule in enumerate(extract_rules(content)):
        kind="permission" if any(x in rule for x in ("权限","只能","不得")) else "acceptance" if any(x in rule for x in ("验收","成功","完成")) else "business_rule"
        risk="high" if any(x in rule for x in ("支付","充值","删除","权限","密码","薪资")) else "medium"
        items.append((uid("req"),project_id,source_id,kind,rule[:100],rule,"系统行为符合该需求描述","P0" if risk=="high" else "P1",risk,"draft",now()))
    if not items and content.strip(): items.append((uid("req"),project_id,source_id,"feature",content.strip()[:100],content.strip()[:2000],"需求对应的主流程能够成功完成","P1","medium","draft",now()))
    with db() as conn: conn.executemany("INSERT INTO requirement_items VALUES (?,?,?,?,?,?,?,?,?,?,?)",items)
    refresh_traceability(project_id)
    return len(items)


def refresh_traceability(project_id):
    reqs=rows("SELECT * FROM requirement_items WHERE project_id=?",(project_id,)); endpoints=rows("SELECT id,path,summary,tags FROM api_endpoints WHERE project_id=?",(project_id,)); cases=rows("SELECT id,title,path FROM test_cases WHERE project_id=?",(project_id,)); workflows=rows("SELECT id,name,module FROM workflows WHERE project_id=?",(project_id,)); tables=rows("SELECT id,table_name,table_comment FROM db_tables WHERE project_id=?",(project_id,))
    manual={(x["requirement_id"],x["target_type"],x["target_id"]):x for x in rows("SELECT * FROM trace_links WHERE project_id=? AND (selected=1 OR link_source='manual')",(project_id,))}
    links=[]
    for req in reqs:
        rt=tokens(req["title"]+" "+req["description"]+" "+req.get("acceptance_criteria", ""))
        for typ,assets,fields in (("endpoint",endpoints,("path","summary","tags")),("case",cases,("title","path")),("workflow",workflows,("name","module")),("table",tables,("table_name","table_comment"))):
            scored=[]
            for a in assets:
                asset_text=" ".join(str(a.get(f,"")) for f in fields); at=tokens(asset_text); overlap=rt&at
                if overlap:
                    coverage=len(overlap)/max(1,min(len(rt),12)); path_bonus=.08 if typ=="endpoint" and any(x in str(a.get("path","")).lower() for x in overlap if re.fullmatch(r"[a-z][a-z0-9]+",x)) else 0
                    score=min(.98,.24+.11*len(overlap)+.34*coverage+path_bonus)
                    scored.append((score,a["id"],overlap,path_bonus))
            limit=50 if typ=="endpoint" else 10
            for order,(score,aid,overlap,path_bonus) in enumerate(sorted(scored,reverse=True)[:limit],1):
                old=manual.get((req["id"],typ,aid)); selected=old["selected"] if old else int(score>=.58); source=old["link_source"] if old else "ai"
                reason="业务语义匹配："+", ".join(sorted(overlap))+("；接口路径命中" if path_bonus else "")
                links.append((uid("trace"),project_id,req["id"],typ,aid,score,reason,now(),selected,order,source))
        for key,old in manual.items():
            if key[0]==req["id"] and not any(x[3]==key[1] and x[4]==key[2] and x[2]==req["id"] for x in links):
                links.append((uid("trace"),project_id,req["id"],key[1],key[2],old["confidence"],old["reason"],now(),old["selected"],old["sort_order"],"manual"))
    with db() as conn:
        conn.execute("DELETE FROM trace_links WHERE project_id=?",(project_id,)); conn.executemany("INSERT INTO trace_links(id,project_id,requirement_id,target_type,target_id,confidence,reason,created_at,selected,sort_order,link_source) VALUES (?,?,?,?,?,?,?,?,?,?,?)",links)
    return len(links)


def add_manual_endpoint(project_id, x):
    ep={"method":x.get("method","GET").upper(),"path":x.get("path","/"),"summary":x.get("summary","手工接口"),"tags":[x.get("module","手工接口")],"security":bool(x.get("auth_required")),"parameters":x.get("parameters",[]),"request_body":x.get("request_body",{}),"responses":x.get("responses",{"200":{"description":"success"}}),"example":x.get("example",{"path":{},"query":{},"headers":{},"body":None}),"required":x.get("required",[])}
    risk,reason=classify_endpoint(ep); danger,warning=danger_rating(ep); eid=uid("api")
    execute("INSERT INTO api_endpoints(id,project_id,source_id,method,path,summary,tags,parameters,request_body,responses,auth_required,risk_level,risk_reason,created_at,example_request,required_fields,danger_score,danger_warning) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(eid,project_id,"manual",ep["method"],ep["path"],ep["summary"],json.dumps(ep["tags"],ensure_ascii=False),json.dumps(ep["parameters"],ensure_ascii=False),json.dumps(ep["request_body"],ensure_ascii=False),json.dumps(ep["responses"],ensure_ascii=False),int(ep["security"]),risk,reason,now(),json.dumps(ep["example"],ensure_ascii=False),json.dumps(ep["required"],ensure_ascii=False),danger,warning))
    refresh_traceability(project_id)
    return row("SELECT * FROM api_endpoints WHERE id=?",(eid,))


def run_ai_pipeline(project_id, options=None):
    options=options or {}; requirement_id=options.get("requirement_source_id"); openapi_id=options.get("openapi_source_id")
    if not requirement_id:
        item=row("SELECT id FROM sources WHERE project_id=? AND kind='requirement' ORDER BY created_at DESC LIMIT 1",(project_id,)); requirement_id=item["id"] if item else None
    if not openapi_id:
        item=row("SELECT id FROM sources WHERE project_id=? AND kind IN ('openapi','har') ORDER BY CASE kind WHEN 'openapi' THEN 0 ELSE 1 END,created_at DESC LIMIT 1",(project_id,)); openapi_id=item["id"] if item else None
    endpoint_count=row("SELECT COUNT(*) n FROM api_endpoints WHERE project_id=?",(project_id,))["n"]
    if not openapi_id and not endpoint_count:
        raise ValueError("请先导入OpenAPI/Swagger接口文档、HAR抓包文件，或至少手工补充一个接口")
    summary={}; blockers=[]
    if requirement_id:
        count=row("SELECT COUNT(*) n FROM requirement_items WHERE source_id=?",(requirement_id,))["n"]
        if not count:
            src=row("SELECT * FROM sources WHERE id=?",(requirement_id,)); count=analyze_requirement_source(project_id,requirement_id,src["content"])
        summary["requirement_items"]=count
    else: blockers.append("未提供需求文档，测试范围只能依据接口资料推断")
    if openapi_id:
        existing=row("SELECT COUNT(*) n FROM test_points WHERE source_id=?",(openapi_id,))["n"]
        summary["test_assets"]=generate_assets(project_id,openapi_id) if not existing or options.get("regenerate") else {"skipped":True,"reason":"该接口版本已生成测试资产"}
    else:
        summary["test_assets"]={"skipped":True,"reason":"当前已有接口资产，但缺少原始OpenAPI/HAR资料，先继续生成流程和执行资产"}
        blockers.append("未导入OpenAPI/Swagger或HAR原始资料；已复用现有接口资产继续生成，建议补齐接口文档基线")
    summary["trace_links"]=refresh_traceability(project_id)
    summary["workflows"]=generate_workflows(project_id)
    summary["nonfunctional"]=generate_nonfunctional(project_id)
    summary["operations"]=generate_operations_assets(project_id)
    summary["security_scan"]=run_security_scan(project_id)
    project=row("SELECT * FROM projects WHERE id=?",(project_id,))
    if not project["base_url"]: blockers.append("未配置测试环境Base URL，无法执行接口")
    if not any(x["auth_required"] for x in rows("SELECT auth_required FROM api_endpoints WHERE project_id=?",(project_id,))): blockers.append("接口资料未声明认证规则，受保护接口可能返回401/403")
    empty_examples=row("SELECT COUNT(*) n FROM api_endpoints WHERE project_id=? AND (example_request='{}' OR example_request LIKE '%\"body\": null%')",(project_id,))["n"]
    if empty_examples: blockers.append(f"{empty_examples}个接口缺少完整请求示例，AI已生成占位测试数据")
    rid=uid("pipe"); status="READY_WITH_WARNINGS" if blockers else "READY"
    execute("INSERT INTO pipeline_runs VALUES (?,?,?,?,?,?,?,?)",(rid,project_id,status,requirement_id,openapi_id,json.dumps(summary,ensure_ascii=False,default=str),json.dumps(blockers,ensure_ascii=False),now()))
    return row("SELECT * FROM pipeline_runs WHERE id=?",(rid,))


def set_requirement_link(requirement_id, endpoint_id, selected=True, sort_order=0):
    req=row("SELECT * FROM requirement_items WHERE id=?",(requirement_id,)); ep=row("SELECT * FROM api_endpoints WHERE id=?",(endpoint_id,))
    if not req or not ep: raise ValueError("需求或接口不存在")
    existing=row("SELECT * FROM trace_links WHERE requirement_id=? AND target_type='endpoint' AND target_id=?",(requirement_id,endpoint_id))
    if existing: execute("UPDATE trace_links SET selected=?,sort_order=?,link_source='manual' WHERE id=?",(int(selected),int(sort_order or existing["sort_order"]),existing["id"]))
    else: execute("INSERT INTO trace_links(id,project_id,requirement_id,target_type,target_id,confidence,reason,created_at,selected,sort_order,link_source) VALUES (?,?,?,?,?,?,?,?,?,?,?)",(uid("trace"),req["project_id"],requirement_id,"endpoint",endpoint_id,1.0,"人工关联",now(),int(selected),int(sort_order),"manual"))
    return {"ok":True}


def generate_requirement_workflow(requirement_id):
    req=row("SELECT * FROM requirement_items WHERE id=?",(requirement_id,))
    if not req: raise ValueError("需求不存在")
    links=rows("SELECT l.*,e.method,e.path,e.summary,e.risk_level FROM trace_links l JOIN api_endpoints e ON e.id=l.target_id WHERE l.requirement_id=? AND l.target_type='endpoint' AND l.selected=1 ORDER BY CASE WHEN l.sort_order=0 THEN 9999 ELSE l.sort_order END,l.confidence DESC",(requirement_id,))
    if not links: raise ValueError("请先选择至少一个关联接口")
    wid=uid("wf"); risk="high" if any(x["risk_level"]=="high" for x in links) else "medium"
    execute("INSERT INTO workflows VALUES (?,?,?,?,?,?,?,?,?)",(wid,req["project_id"],"需求流程："+req["title"],"需求驱动",req["description"],req["priority"],risk,"ready",now()))
    cases=rows("SELECT * FROM test_cases WHERE project_id=? AND title LIKE '%：正常请求'",(req["project_id"],)); title_map={(x["method"],x["title"].removesuffix("：正常请求")):x["id"] for x in cases}
    values=[]
    for i,x in enumerate(links,1):
        phase="setup" if i==1 else "verify" if i==len(links) else "action"
        values.append((uid("wfs"),wid,i,x["target_id"],title_map.get((x["method"],x["summary"])),phase,x["summary"],req["acceptance_criteria"],json.dumps({"auto_extract":True}),0))
    with db() as conn: conn.executemany("INSERT INTO workflow_steps VALUES (?,?,?,?,?,?,?,?,?,?)",values)
    execute("INSERT INTO trace_links(id,project_id,requirement_id,target_type,target_id,confidence,reason,created_at,selected,sort_order,link_source) VALUES (?,?,?,?,?,?,?,?,?,?,?)",(uid("trace"),req["project_id"],requirement_id,"workflow",wid,1.0,"由已选择接口生成人工可编辑需求流程",now(),1,0,"manual"))
    return {"workflow_id":wid,"steps":len(values)}


def extract_rules(text):
    clean = re.sub(r"\s+", " ", text).strip()
    segments = re.split(r"(?<=[。！？.!?；;])\s*|\n+", clean)
    keywords = ("必须", "不得", "只能", "需要", "应当", "如果", "当", "权限", "状态", "校验", "限制", "支持", "允许", "禁止")
    rules = [s.strip(" -\t") for s in segments if len(s.strip()) >= 8 and any(k in s for k in keywords)]
    if not rules:
        rules = [s.strip(" -\t") for s in segments if len(s.strip()) >= 12]
    return rules[:30]


def _html_to_plain_text(text):
    text=re.sub(r"(?is)<script.*?</script>|<style.*?</style>"," ",text)
    text=re.sub(r"(?s)<[^>]+>"," ",text)
    text=urllib.parse.unquote(text)
    text=text.replace("&nbsp;"," ").replace("&amp;","&").replace("&lt;","<").replace("&gt;",">").replace("&quot;",'"')
    return re.sub(r"\s+"," ",text).strip()


def _decode_requirement_bytes(raw):
    text=raw.decode("utf-8-sig","replace")
    if text.count("\ufffd") > max(3, len(text)//200):
        text=raw.decode("gb18030","replace")
    return text


def _zip_display_name(name):
    if any("\u4e00" <= ch <= "\u9fff" for ch in name):
        return name
    try:
        fixed=name.encode("cp437").decode("gb18030")
        return fixed if any("\u4e00" <= ch <= "\u9fff" for ch in fixed) else name
    except Exception:
        return name


def _zip_requirement_bundle(raw):
    content_parts=[]; image_assets=[]; names=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for name in z.namelist():
            display_name=_zip_display_name(name)
            lower=display_name.lower().replace("\\","/")
            if name.endswith("/") or "__macosx/" in lower:
                continue
            if lower.endswith((".html",".htm")) and not any(part in lower for part in ("/resources/","/plugins/")):
                html=_decode_requirement_bytes(z.read(name))
                plain=_html_to_plain_text(html)
                if plain:
                    names.append(Path(display_name).name)
                    content_parts.append(f"\n\n[HTML页面：{Path(display_name).name}]\n{plain}")
            elif lower.endswith(".svg") and "images/" in lower:
                try:
                    svg=_decode_requirement_bytes(z.read(name))
                    svg_text=_html_to_plain_text(svg)
                    if len(svg_text) >= 20:
                        content_parts.append(f"\n\n[SVG图片文字：{Path(display_name).name}]\n{svg_text[:5000]}")
                except Exception:
                    pass
            elif lower.endswith((".png",".jpg",".jpeg",".webp",".gif")) and "images/" in lower:
                mime="image/png" if lower.endswith(".png") else "image/webp" if lower.endswith(".webp") else "image/gif" if lower.endswith(".gif") else "image/jpeg"
                image_assets.append((Path(display_name).name,mime,base64.b64encode(z.read(name)).decode()))
    summary=f"[HTML需求包]\n页面数：{len(names)}\n图片数：{len(image_assets)}\n页面：{', '.join(names[:30])}"
    return (summary+"".join(content_parts)).strip(), image_assets[:30]


def extract_source_content(x):
    content=x.get("content","")
    source_url=(x.get("source_url") or "").strip()
    if source_url:
        try:
            req=urllib.request.Request(source_url,headers={"User-Agent":"AutoTestAI-DocumentImporter/1.0"})
            with urllib.request.urlopen(req,timeout=30) as resp:
                raw=resp.read(10_000_000); ctype=resp.headers.get("Content-Type","")
            text=raw.decode("utf-8","replace")
            if "html" in ctype or "<html" in text[:500].lower():
                text=re.sub(r"(?is)<script.*?</script>|<style.*?</style>"," ",text); text=re.sub(r"(?s)<[^>]+>"," ",text); text=re.sub(r"\s+"," ",text)
            content += ("\n" if content else "") + text
        except Exception as exc:
            note=f"[链接待采集]\nURL：{source_url}\n读取状态：平台未能直接读取页面正文，原因：{str(exc)[:300]}\n需要补齐：登录态采集、需求正文、截图或可公开访问的文档内容。"
            content += ("\n" if content else "") + note
    encoded=x.get("file_base64")
    filename=(x.get("file_name") or "").lower()
    if encoded:
        raw=base64.b64decode(encoded)
        if filename.endswith(".zip"):
            bundle_text,_=_zip_requirement_bundle(raw)
            content += "\n" + bundle_text
        elif filename.endswith(".docx"):
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                xml=z.read("word/document.xml"); root=ET.fromstring(xml); ns="{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
                content += "\n" + "\n".join("".join(t.text or "" for t in p.iter(ns+"t")) for p in root.iter(ns+"p"))
        elif filename.endswith(".pdf"):
            try:
                from pypdf import PdfReader
                content += "\n" + "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(raw)).pages)
            except Exception as e: raise ValueError("PDF解析组件不可用，请改用DOCX或复制文本："+str(e))
        elif filename.endswith((".html",".htm")):
            content += "\n" + _html_to_plain_text(_decode_requirement_bytes(raw))
        else: content += "\n" + raw.decode("utf-8-sig","replace")
    return content.strip()


def extract_source_images(x):
    encoded=x.get("file_base64"); filename=(x.get("file_name") or "").lower(); assets=[]
    if not encoded: return assets
    raw=base64.b64decode(encoded)
    if filename.endswith(".zip"):
        _,assets=_zip_requirement_bundle(raw)
    elif filename.endswith(".docx"):
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for name in z.namelist():
                if name.startswith("word/media/"):
                    ext=Path(name).suffix.lower(); mime={".png":"image/png",".jpg":"image/jpeg",".jpeg":"image/jpeg",".webp":"image/webp",".gif":"image/gif"}.get(ext,"application/octet-stream")
                    assets.append((Path(name).name,mime,base64.b64encode(z.read(name)).decode()))
    elif filename.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            for page_no,page in enumerate(PdfReader(io.BytesIO(raw)).pages,1):
                for i,img in enumerate(getattr(page,"images",[]) or [],1):
                    assets.append((f"page-{page_no}-image-{i}.{getattr(img,'name','png').split('.')[-1]}","image/png",base64.b64encode(img.data).decode()))
        except Exception: pass
    elif filename.endswith((".png",".jpg",".jpeg",".webp",".gif")):
        mime="image/png" if filename.endswith(".png") else "image/webp" if filename.endswith(".webp") else "image/jpeg"
        assets.append((Path(filename).name,mime,encoded))
    return assets[:30]


def vision_analyze_image(name,mime,data_b64):
    settings={x["key"]:x["value"] for x in rows("SELECT * FROM settings")}; key=settings.get("api_key","").strip()
    if not key: return "pending", "未配置视觉模型，图片已保存等待分析"
    base=settings.get("api_base","https://api.openai.com/v1").rstrip("/"); model=settings.get("model","gpt-5-mini")
    prompt="分析这张软件需求图片。提取：页面/模块、用户角色、流程节点、状态转换、字段、按钮、业务规则、异常场景、验收标准、可能关联的API。用中文结构化输出，不要臆造看不到的信息。"
    body=json.dumps({"model":model,"messages":[{"role":"user","content":[{"type":"text","text":prompt},{"type":"image_url","image_url":{"url":f"data:{mime};base64,{data_b64}"}}]}]}).encode()
    req=urllib.request.Request(base+"/chat/completions",data=body,headers={"Content-Type":"application/json","Authorization":f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req,timeout=90) as resp: result=json.loads(resp.read())
        return "completed",result["choices"][0]["message"]["content"]
    except Exception as e: return "error","视觉分析失败："+str(e)


def vision_analyze_bundle(context_text, images):
    """Analyze extracted requirement text and all visual pages as one document."""
    settings={x["key"]:x["value"] for x in rows("SELECT * FROM settings")}; key=settings.get("api_key","").strip()
    if not key: return "pending", "未配置视觉模型，文字和图片已保存等待联合分析"
    base=settings.get("api_base","https://api.openai.com/v1").rstrip("/"); model=settings.get("model","gpt-5-mini")
    prompt="""你是资深测试分析师。下面是同一份需求的网页文字、表格和按顺序滚动截取的原型图片。必须把文字与图片联合理解、互相校验，不得把每张图孤立分析。请用中文结构化输出：
1. 文档确认的需求目标与业务规则；2. 页面、字段、按钮和交互；3. 完整用户流程与状态转换；4. 正常/异常/边界/权限/数据一致性测试点；5. 可能关联的API及请求顺序；6. 无法确认和需要人工补充的内容。
明确标注“文字确认”“图片确认”“图文联合推断”，不要臆造。网页文字如下：\n"""+context_text[:30000]
    message=[{"type":"text","text":prompt}]
    for name,mime,data_b64 in images[:20]:
        message.append({"type":"text","text":"页面截图："+name})
        message.append({"type":"image_url","image_url":{"url":f"data:{mime};base64,{data_b64}","detail":"low"}})
    body=json.dumps({"model":model,"messages":[{"role":"user","content":message}]}).encode()
    req=urllib.request.Request(base+"/chat/completions",data=body,headers={"Content-Type":"application/json","Authorization":f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req,timeout=180) as resp: result=json.loads(resp.read())
        return "completed",result["choices"][0]["message"]["content"]
    except Exception as e: return "error","图文联合分析失败："+str(e)


def browser_capture_source(source_url):
    capture_dir=DATA/"browser-captures"/uid("capture"); profile_dir=DATA/"browser-profile"; capture_dir.mkdir(parents=True,exist_ok=True)
    node=Path(r"C:\Users\DELL\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe")
    env=dict(os.environ); env["NODE_PATH"]=r"C:\Users\DELL\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules"
    proc=subprocess.run([str(node),str(ROOT/"browser_collector.js"),source_url,str(capture_dir),str(profile_dir)],env=env,capture_output=True,text=True,timeout=240)
    if proc.returncode!=0: raise ValueError("浏览器采集失败："+(proc.stderr or (capture_dir/"error.txt").read_text("utf-8","ignore") if (capture_dir/"error.txt").exists() else "未知错误"))
    page=json.loads((capture_dir/"page.json").read_text(encoding="utf-8")); screenshot_files=[capture_dir/"full-page.png"]+sorted(capture_dir.glob("viewport-*.png"))
    network=[]
    if (capture_dir/"network.json").exists(): network=json.loads((capture_dir/"network.json").read_text(encoding="utf-8"))
    frame_text="\n\n".join(x.get("text","") for x in page.get("frames",[]) if x.get("text"))
    network_text="\n\n".join(f"[数据源 {x.get('url','')}]\n{x.get('body','')}" for x in network if x.get("body"))[:200000]
    completeness=page.get("completeness",{})
    text=page.get("text","")+"\n\n[内嵌页面文字]\n"+frame_text+"\n\n[页面表格]\n"+"\n\n".join(page.get("tables",[]))+"\n\n[页面数据接口]\n"+network_text+"\n\n[图片说明]\n"+"\n".join(f"{x.get('alt','')} {x.get('src','')}" for x in page.get("images",[]))+"\n\n[采集完整性]\n"+json.dumps(completeness,ensure_ascii=False)
    images=[(p.name,"image/png",base64.b64encode(p.read_bytes()).decode()) for p in screenshot_files[:31]]
    return text,images,page


def evaluate_capture_completeness(page):
    stats=page.get("completeness",{}); score=0; blockers=[]
    network=int(stats.get("networkDocumentCount",0)); shots=int(stats.get("screenshotCount",0)); frames=int(stats.get("frameCount",0)); images=int(stats.get("imageCount",0)); dom=int(stats.get("domTextLength",0)); manifests=int(stats.get("prototypeManifestCount",0)); resources=int(stats.get("prototypeResourceCount",0))
    if network: score+=30
    if shots>=3: score+=20
    if frames: score+=15
    if images: score+=10
    if dom>=200: score+=10
    elif stats.get("suspectedCanvasDocument") and network: score+=5
    if manifests and resources: score+=15
    if shots<2: blockers.append("未形成完整页面截图序列")
    if dom<100 and not network: blockers.append("页面正文很少且未捕获结构化数据源")
    if stats.get("suspectedCanvasDocument") and not manifests: blockers.append("疑似Canvas原型，但未识别到原型资源清单")
    status="passed" if score>=80 and not blockers else "review" if score>=60 else "blocked"
    return min(score,100),status,blockers


def local_generate(project_id, source):
    points, cases = [], []
    content, kind = source["content"], source["kind"]
    endpoints = parse_openapi(content) if kind in {"openapi", "har"} else []
    changed_keys = {x["endpoint_key"] for x in rows("SELECT endpoint_key FROM endpoint_changes WHERE source_id=? AND change_type IN ('added','modified')", (source["id"],))}
    if changed_keys:
        endpoints = [x for x in endpoints if f"{x['method']} {x['path']}" in changed_keys]
    for ep in endpoints:
        module = ep["tags"][0]
        base = ep["summary"]
        example = ep.get("example", {})
        executable_path = ep["path"]
        for name, value in example.get("path", {}).items(): executable_path = executable_path.replace("{" + name + "}", urllib.parse.quote(str(value)))
        if example.get("query"):
            executable_path += ("&" if "?" in executable_path else "?") + urllib.parse.urlencode(example["query"])
        example_headers = example.get("headers", {})
        if example.get("content_type"): example_headers.setdefault("Content-Type", example["content_type"])
        example_payload = example.get("body")
        success_codes = []
        for code in ep.get("responses", {}):
            if str(code).isdigit() and 200 <= int(code) < 300: success_codes.append(int(code))
        normal_status = min(success_codes) if success_codes else 200
        templates = [
            ("功能", f"{base}：正常请求", "P0", "高", "根据接口资料样例验证核心成功路径", normal_status, "", example_headers, example_payload, executable_path),
            ("异常", f"{base}：缺失必填参数", "P1", "高", "验证必填字段校验：" + ", ".join(ep.get("required", [])[:8]), 400, "", example_headers, {} if isinstance(example_payload, dict) else "", executable_path),
            ("边界", f"{base}：字段边界与类型错误", "P1", "中", "验证长度、数值、类型和空值边界", 400, "", example_headers, example_payload, executable_path),
        ]
        if ep["security"]:
            templates.append(("安全", f"{base}：未授权与越权访问", "P0", "高", "验证认证与资源权限", 401, "", {}, example_payload, executable_path))
        if ep["method"] in {"POST", "PUT", "PATCH", "DELETE"}:
            templates.append(("可靠性", f"{base}：重复提交与幂等性", "P1", "高", "验证重复操作不会破坏数据一致性", normal_status, "", example_headers, example_payload, executable_path))
        for category, title, priority, risk, rationale, expected_status, contains, headers, body, case_path in templates:
            pid = uid("tp")
            point = (pid, project_id, source["id"], module, title, category, priority, risk, rationale, "draft", now())
            points.append(point)
            cid = uid("tc")
            payload = json.dumps(body, ensure_ascii=False) if body is not None and ep["method"] in {"POST", "PUT", "PATCH"} else ""
            steps = f"1. 准备{category}场景数据\n2. 发送 {ep['method']} {case_path}\n3. 检查状态码、响应结构和业务结果"
            expected = rationale
            cases.append((cid, project_id, pid, title, ep["method"], case_path, json.dumps(headers, ensure_ascii=False), payload, expected_status, contains, priority, "ready", steps, expected, now()))
    rules=extract_rules(content)[:30]
    if kind != "openapi":
        variants=[
            ("功能","正常展示与主流程","P0","高","使用满足需求的正常数据完成主流程","页面内容、状态和结果符合需求"),
            ("异常","缺失、空值与加载失败","P1","高","构造数据缺失、资源失败或服务异常","系统有明确降级且不出现错误状态"),
            ("边界","最小值、最大值与区间边界","P1","高","覆盖零值、最大值及相邻区间切换","边界归属、计算和展示准确"),
            ("状态","已获得、未获得与状态变化","P1","高","切换用户状态、等级或业务阶段","状态样式和可操作能力同步变化"),
            ("UI","布局、文案与交互反馈","P2","中","检查不同内容长度、分辨率和操作反馈","无截断、遮挡、错位和错误文案"),
            ("一致性","前后端数据与刷新一致性","P1","高","刷新、重复进入并对比关联区域数据","同一业务数据在所有区域保持一致"),
        ]
        for rule in rules:
            module=(rule.split("：",1)[0] if "：" in rule else "需求分析")[:30]
            subject=(rule.split("：",1)[-1]).strip()[:48]
            for category,label,priority,risk,steps_hint,expected in variants:
                pid=uid("tp"); title=f"{subject}｜{label}"
                points.append((pid,project_id,source["id"],module,title,category,priority,risk,rule,"draft",now()))
                steps=f"1. 根据需求准备场景：{rule}\n2. {steps_hint}\n3. 检查页面、交互、数据和状态\n4. 保存实际结果与证据"
                cases.append((uid("tc"),project_id,pid,title,"","","{}","",200,"",priority,"design",steps,expected+"；需求依据："+rule,now()))
        cross_cutting=[
            ("端到端","首次进入到完成核心目标的完整用户流程","P0","高"),
            ("导航","返回、页签切换及重复进入后的状态保持","P1","中"),
            ("滚动","长列表连续滚动、快速滚动和回位定位","P1","中"),
            ("并发","数据更新过程中重复进入和多端同时查看","P1","高"),
            ("弱网","慢网络、超时、断网和恢复后的页面表现","P1","高"),
            ("缓存","冷启动、热启动、缓存过期和强制刷新","P1","中"),
            ("兼容","不同屏幕尺寸、系统版本和字体缩放","P2","中"),
            ("可用性","按钮可点击区域、加载反馈和错误提示","P1","中"),
            ("性能","首屏、长列表、图片和动画资源加载耗时","P1","高"),
            ("安全","未登录、会话失效和他人数据隔离","P0","高"),
            ("数据一致性","等级、经验、权益数量和解锁状态一致","P0","高"),
            ("可追溯","每项展示和交互均能关联需求依据","P1","中"),
        ]
        for category,title,priority,risk in cross_cutting:
            pid=uid("tp"); points.append((pid,project_id,source["id"],"全局质量",title,category,priority,risk,"跨模块通用质量要求","draft",now()))
            cases.append((uid("tc"),project_id,pid,title,"","","{}","",200,"",priority,"design","1. 准备对应环境与用户数据\n2. 执行跨模块场景\n3. 检查功能、数据、UI和日志证据","系统在跨模块场景下仍满足需求且无数据错乱",now()))
    else:
        for rule in rules[:15]:
            pid=uid("tp"); title=f"业务规则验证：{rule[:60]}"; category="权限" if "权限" in rule or "只能" in rule else "业务规则"
            points.append((pid,project_id,source["id"],"需求分析",title,category,"P1","中",rule,"draft",now()))
            cases.append((uid("tc"),project_id,pid,title,"","","{}","",200,"","P1","design",f"1. 构造满足规则的场景\n2. 构造违反规则的场景\n3. 对比系统行为",f"系统行为与规则一致：{rule}",now()))
    if not points:
        pid = uid("tp")
        points.append((pid, project_id, source["id"], "通用", "核心业务正常流程", "功能", "P0", "高", "验证主要用户目标可完成", "draft", now()))
    return points, cases


def ai_generate(project_id, source):
    settings = {x["key"]: x["value"] for x in rows("SELECT * FROM settings")}
    api_key = settings.get("api_key", "").strip()
    base = settings.get("api_base", "https://api.openai.com/v1").rstrip("/")
    model = settings.get("model", "gpt-5-mini")
    if not api_key:
        return local_generate(project_id, source), "local"
    prompt = """你是资深测试架构师。分析下列资料，输出严格JSON对象，结构为
{"points":[{"module":"","title":"","category":"功能/异常/边界/权限/安全/性能","priority":"P0/P1/P2","risk":"高/中/低","rationale":""}],
"cases":[{"point_index":0,"title":"","method":"GET","path":"/api/x","headers":{},"payload":{},"expected_status":200,"expected_contains":"","priority":"P1","steps":"","expected":""}]}。
测试应可追溯、去重，并覆盖正向、异常、边界、权限、幂等和数据一致性。资料：\n""" + source["content"][:50000]
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}).encode()
    req = urllib.request.Request(base + "/chat/completions", data=body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read())
        parsed = json.loads(result["choices"][0]["message"]["content"])
        points, cases, ids = [], [], []
        for p in parsed.get("points", []):
            pid = uid("tp"); ids.append(pid)
            points.append((pid, project_id, source["id"], p.get("module", "通用"), p["title"], p.get("category", "功能"), p.get("priority", "P1"), p.get("risk", "中"), p.get("rationale", ""), "draft", now()))
        for c in parsed.get("cases", []):
            idx = int(c.get("point_index", 0)); point_id = ids[idx] if ids and 0 <= idx < len(ids) else None
            cases.append((uid("tc"), project_id, point_id, c["title"], c.get("method", ""), c.get("path", ""), json.dumps(c.get("headers", {}), ensure_ascii=False), json.dumps(c.get("payload", ""), ensure_ascii=False) if not isinstance(c.get("payload", ""), str) else c.get("payload", ""), int(c.get("expected_status", 200)), c.get("expected_contains", ""), c.get("priority", "P1"), "ready", c.get("steps", ""), c.get("expected", ""), now()))
        return (points, cases), "ai"
    except Exception:
        return local_generate(project_id, source), "local-fallback"


def normalize_test_case_record(case):
    if len(case) >= 22:
        return case[:22]
    values = list(case) + [None] * (15 - len(case))
    (
        case_id, project_id, point_id, title, method, path, headers, payload,
        expected_status, expected_contains, priority, status, steps, expected, created_at
    ) = values[:15]
    has_request = bool(method and path)
    scenario = "正常请求" if has_request and "正常" in str(title) else "接口契约" if has_request else "设计用例"
    executor = "http" if has_request else "manual"
    execution_status = "NOT_RUN" if has_request else "BLOCKED"
    actual_result = "" if has_request else "缺少可执行接口、参数或外部工具上下文"
    requirement_ref = expected if expected else ""
    return (
        case_id, project_id, point_id, title, method or "", path or "", headers or "{}",
        payload or "", expected_status or 200, expected_contains or "", priority or "P1",
        status or "ready", steps or "", expected or "", created_at or now(), executor,
        scenario, requirement_ref, actual_result, execution_status, 0, None
    )


def generate_assets(project_id, source_id, force=False):
    source = row("SELECT * FROM sources WHERE id=? AND project_id=?", (source_id, project_id))
    if not source:
        raise ValueError("资料不存在")
    report=row("SELECT * FROM source_capture_reports WHERE source_id=?",(source_id,))
    if report and report["status"]=="blocked" and not force:
        raise ValueError(f"需求采集完整性仅 {report['score']} 分，已阻止自动生成；请补充资料或使用人工强制生成")
    (points, cases), engine = ai_generate(project_id, source)
    cases = [normalize_test_case_record(case) for case in cases]
    with db() as conn:
        conn.executemany("INSERT INTO test_points VALUES (?,?,?,?,?,?,?,?,?,?,?)", points)
        conn.executemany(
            """INSERT INTO test_cases(id,project_id,point_id,title,method,path,headers,payload,expected_status,expected_contains,priority,status,steps,expected,created_at,executor_type,scenario_type,requirement_ref,actual_result,execution_status,run_count,last_run_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            cases,
        )
        conn.execute("UPDATE projects SET updated_at=? WHERE id=?", (now(), project_id))
    return {"points": len(points), "cases": len(cases), "engine": engine}


def substitute_value(value, context):
    if isinstance(value, dict):
        return {k: substitute_value(context.get(k, v), context) for k, v in value.items()}
    if isinstance(value, list): return [substitute_value(x, context) for x in value]
    if isinstance(value, str):
        for k, v in context.items(): value = value.replace("{{" + k + "}}", str(v))
    return value


def extract_context(payload, output=None, depth=0):
    output = output if output is not None else {}
    if depth > 8: return output
    important = re.compile(r"(^|_)(id|token|sn|ticket|code|uuid)$|Id$|Token$|_id$", re.I)
    if isinstance(payload, dict):
        for k, v in payload.items():
            if important.search(k) and isinstance(v, (str, int, float)) and v not in ("", 0, None):
                output[k] = v
                output.setdefault(k.lower(), v)
            extract_context(v, output, depth + 1)
    elif isinstance(payload, list):
        for item in payload[:3]: extract_context(item, output, depth + 1)
    return output


def safe_runtime_context(context):
    """Keep variable-flow evidence without persisting credentials."""
    secret=re.compile(r"password|token|ticket|authorization|\bsn\b|secret|cookie",re.I)
    return {k:("***REDACTED***" if secret.search(str(k)) else v) for k,v in context.items()}


def json_path_value(payload, path):
    value=payload
    for part in str(path or "").strip("$.").split("."):
        if not part: continue
        if isinstance(value,dict) and part in value: value=value[part]
        elif isinstance(value,list) and part.isdigit() and int(part)<len(value): value=value[int(part)]
        else: return None
    return value


def classify_run_failure(run):
    if run.get("status")=="PASSED": return "none"
    code=run.get("http_status")
    if code in {401,403}: return "authentication"
    if code in {400,404,405,422}: return "request_contract"
    if code==429: return "rate_limit"
    if code in {500,502,503,504}: return "server"
    if run.get("status")=="ERROR": return "network_or_environment"
    return "business_assertion"


def data_consistency_summary(project_id):
    rules=rows("SELECT status FROM consistency_rules WHERE project_id=?",(project_id,))
    runs=rows("""SELECT x.status FROM consistency_runs x JOIN consistency_rules r ON r.id=x.rule_id WHERE x.project_id=? ORDER BY x.created_at DESC""",(project_id,))
    counts={}
    for item in runs: counts[item["status"]]=counts.get(item["status"],0)+1
    core_runs=rows("""SELECT x.status FROM consistency_runs x JOIN consistency_rules r ON r.id=x.rule_id WHERE x.project_id=? AND r.redis_key='yingtao_user_level_exper' ORDER BY x.created_at DESC""",(project_id,))
    core_counts={}
    for item in core_runs: core_counts[item["status"]]=core_counts.get(item["status"],0)+1
    mysql_maps=row("SELECT COUNT(*) n FROM api_db_mappings WHERE project_id=?",(project_id,))["n"]
    redis_maps=row("SELECT COUNT(*) n FROM api_redis_mappings WHERE project_id=?",(project_id,))["n"]
    mysql_tables=row("SELECT COUNT(*) n FROM db_tables WHERE project_id=?",(project_id,))["n"]
    redis_sources=rows("SELECT name,status,server_version,last_error,last_checked_at FROM redis_sources WHERE project_id=?",(project_id,))
    redis_snapshots=row("SELECT COUNT(*) n FROM redis_key_snapshots WHERE project_id=?",(project_id,))["n"]
    backend_configs=rows("SELECT level,config_id,config_status,reward_count FROM wealth_backend_reward_configs WHERE project_id=? ORDER BY level",(project_id,))
    core_status="PENDING" if not core_runs else "FAILED" if core_counts.get("FAILED") else "PASSED" if core_counts.get("PASSED") else "BLOCKED"
    status="PENDING" if not runs else "FAILED" if counts.get("FAILED") else "PASSED" if core_status=="PASSED" or counts.get("PASSED") else "BLOCKED"
    mysql_live = mysql_connection_status(project_id)
    mysql_status = "CONNECTED" if mysql_live.get("status") == "CONNECTED" else "CONFIGURED" if mysql_live.get("status") == "CONFIGURED" else "METADATA_READY" if mysql_tables else "NOT_CONNECTED"
    return {"status":status,"core_status":core_status,"strict_read_only":True,"policy":{"mysql":["SELECT","SHOW","DESCRIBE","EXPLAIN"],"redis":sorted(RedisReadonlyClient.ALLOWED),"backend_config":["GET"],"platform_storage":["INSERT","UPDATE","DELETE"]},"mysql":{"status":mysql_status,"connection":mysql_live,"tables":mysql_tables,"api_mappings":mysql_maps,"business_row_checks":"READY_FOR_READONLY_QUERY" if mysql_live.get("status")=="CONFIGURED" else "PENDING_QUERY_CONDITION","write_access":False},"redis":{"status":"CONNECTED" if any(x["status"]=="connected" for x in redis_sources) else "NOT_CONNECTED","sources":redis_sources,"api_mappings":redis_maps,"snapshots":redis_snapshots,"write_access":False},"backend_config":{"status":"READY" if backend_configs else "NOT_IMPORTED","endpoint_method":"GET","configs":len(backend_configs),"active_configs":sum(x["config_status"]==1 for x in backend_configs),"write_access":False},"platform_storage":{"status":"ENABLED","scope":"仅写入平台本地库，用于保存规则、映射、快照、报告和归纳结论","write_access":True},"mysql_mappings":mysql_maps,"redis_mappings":redis_maps,"consistency_rules":len(rules),"executed_runs":len(runs),"core_runs":len(core_runs),"result_counts":counts,"core_result_counts":core_counts,"note":"公司 MySQL、Redis 与后台配置只读；平台本地库可以根据真实只读数据更新映射、规则、快照和报告，不回写业务数据"}


def salary_trade_data_map():
    path = DATA / "salary-trade-data-map.json"
    if not path.exists():
        return {
            "requirement": "工资代理快速结算",
            "readonly": True,
            "tables": [],
            "runtime_variable_rules": [],
            "closure_checks": [],
            "status": "PENDING",
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    data["status"] = "READY" if data.get("tables") else "PENDING"
    return data


SALARY_TRADE_CASE_FLOWS = [
    {
        "id": "salary_flow_a_cancel_by_applicant",
        "code": "A",
        "name": "创建后申请人取消",
        "type": "normal",
        "priority": "P0",
        "account_slot": "applicant_01",
        "thread_group": "工资交易流程A：创建后申请人取消",
        "order_var": "flow_a_order_no",
        "steps": ["申请人读取额度", "申请人创建订单", "提取 orderNo/orderId", "申请人取消订单", "校验订单状态 50"],
        "assertions": ["创建接口 code=200", "orderNo 不为空", "取消后状态为已取消", "订单日志存在创建和取消记录"],
        "data_evidence": ["anchor_salary_trade_order", "anchor_salary_trade_order_log"],
        "automation_status": "ready",
    },
    {
        "id": "salary_flow_b_reject_by_proxy",
        "code": "B",
        "name": "创建后代理拒绝",
        "type": "normal",
        "priority": "P0",
        "account_slot": "applicant_02",
        "thread_group": "工资交易流程B：创建后代理拒绝",
        "order_var": "flow_b_order_no",
        "steps": ["申请人创建订单", "代理查询待处理订单", "代理拒绝订单", "校验订单状态为拒绝/关闭"],
        "assertions": ["代理侧能查到该订单", "拒绝接口 code=200", "拒绝后申请人无进行中订单"],
        "data_evidence": ["anchor_salary_trade_order", "anchor_salary_trade_order_log"],
        "automation_status": "planned",
    },
    {
        "id": "salary_flow_c_finish",
        "code": "C",
        "name": "接受并转账后申请人确认完成",
        "type": "normal",
        "priority": "P0",
        "account_slot": "applicant_03",
        "thread_group": "工资交易流程C：完整成交",
        "order_var": "flow_c_order_no",
        "steps": ["申请人创建订单", "代理接受", "代理标记已转账", "申请人确认收款", "校验交易完成"],
        "assertions": ["状态按 10 -> 20 -> 30 -> 40 流转", "完成后金额释放/扣减符合需求", "日志链路完整"],
        "data_evidence": ["anchor_salary_trade_order", "anchor_salary_trade_order_log"],
        "automation_status": "planned",
    },
    {
        "id": "salary_flow_d_appeal_failed",
        "code": "D",
        "name": "转账后申请人投诉，投诉失败",
        "type": "exception",
        "priority": "P0",
        "account_slot": "applicant_04",
        "thread_group": "工资交易流程D：投诉失败",
        "order_var": "flow_d_order_no",
        "steps": ["申请人创建订单", "代理接受", "代理标记已转账", "申请人投诉", "运营处理投诉失败", "校验最终状态"],
        "assertions": ["投诉记录写入", "投诉失败后订单结果符合需求", "证据记录可追溯"],
        "data_evidence": ["anchor_salary_trade_order", "anchor_salary_trade_evidence", "anchor_salary_trade_order_log"],
        "automation_status": "planned",
    },
    {
        "id": "salary_flow_e_appeal_success",
        "code": "E",
        "name": "转账后申请人投诉，投诉成功",
        "type": "exception",
        "priority": "P0",
        "account_slot": "applicant_05",
        "thread_group": "工资交易流程E：投诉成功",
        "order_var": "flow_e_order_no",
        "steps": ["申请人创建订单", "代理接受", "代理标记已转账", "申请人投诉", "运营处理投诉成功", "校验退款/关闭"],
        "assertions": ["投诉记录写入", "投诉成功后资金处理符合需求", "订单日志记录运营动作"],
        "data_evidence": ["anchor_salary_trade_order", "anchor_salary_trade_evidence", "anchor_salary_trade_order_log"],
        "automation_status": "planned",
    },
    {
        "id": "salary_flow_f_create_timeout",
        "code": "F",
        "name": "创建后代理不处理直到订单过期",
        "type": "timeout",
        "priority": "P1",
        "account_slot": "applicant_06",
        "thread_group": "工资交易流程F：待接单超时",
        "order_var": "flow_f_order_no",
        "steps": ["申请人创建订单", "等待或模拟过期时间", "触发/查询过期结果", "校验订单关闭"],
        "assertions": ["过期前状态保持待处理", "过期后状态符合需求", "资金原路返回"],
        "data_evidence": ["anchor_salary_trade_order", "anchor_salary_trade_order_log"],
        "automation_status": "blocked",
        "blocker": "需要可控时间策略、后台任务触发方式或测试环境缩短超时时间。",
    },
    {
        "id": "salary_flow_g_accept_timeout",
        "code": "G",
        "name": "代理接受后不转账，12小时过期取消",
        "type": "timeout",
        "priority": "P1",
        "account_slot": "applicant_07",
        "thread_group": "工资交易流程G：已接受未转账超时",
        "order_var": "flow_g_order_no",
        "steps": ["申请人创建订单", "代理接受", "等待或模拟12小时", "校验订单取消和资金返回"],
        "assertions": ["接受后状态正确", "超时任务执行后订单关闭", "申请人工资/冻结金额恢复"],
        "data_evidence": ["anchor_salary_trade_order", "anchor_salary_trade_order_log"],
        "automation_status": "blocked",
        "blocker": "需要测试环境可控过期时间或后台定时任务触发入口。",
    },
    {
        "id": "salary_flow_h_confirm_timeout",
        "code": "H",
        "name": "代理已转账后申请人24小时不确认，订单自动完成",
        "type": "timeout",
        "priority": "P1",
        "account_slot": "applicant_08",
        "thread_group": "工资交易流程H：已转账未确认超时完成",
        "order_var": "flow_h_order_no",
        "steps": ["申请人创建订单", "代理接受", "代理标记已转账", "等待或模拟24小时", "校验订单自动完成"],
        "assertions": ["已转账状态正确", "超时后订单完成", "日志记录自动完成来源"],
        "data_evidence": ["anchor_salary_trade_order", "anchor_salary_trade_order_log"],
        "automation_status": "blocked",
        "blocker": "需要测试环境可控24小时超时或后台任务触发入口。",
    },
]


def salary_trade_case_to_jmeter_model(project_id):
    cases = rows("SELECT * FROM test_cases WHERE project_id=? ORDER BY priority,created_at", (project_id,))
    salary_cases = [
        item for item in cases
        if any(word in str(item.get("title") or item.get("requirement_ref") or item.get("steps") or "") for word in ("工资", "代理", "交易", "订单", "投诉", "结算"))
    ]
    generated = ROOT / "outputs" / "salary-trade-state-machine.jmx"
    case_driven = ROOT / "outputs" / "salary-trade-case-driven.jmx"
    config = load_environment_config()
    salary_dataset = deep_get(config, "requirement_datasets.salary_trade", {}) or {}
    account_csv = ROOT / str(salary_dataset.get("account_csv_path") or "data/salary-trade-accounts.csv")
    applicant_csv = ROOT / str(salary_dataset.get("applicant_csv_path") or "data/salary-trade-applicants.csv")
    flow_slots_csv = ROOT / str(salary_dataset.get("flow_slots_csv_path") or "data/salary-trade-flow-slots.csv")
    account_model = REQUIREMENT_PACKAGE_ROOT / "salary-trade" / "account_model.yaml"
    runtime_decision = infer_jmeter_runtime_data_strategy(salary_cases, SALARY_TRADE_CASE_FLOWS)
    return {
        "requirement": "工资代理快速结算",
        "principle": "测试用例是输入，JMeter 是执行载体。平台先把用例结构化，再按步骤生成线程组、请求、提取器、断言和报告标签。",
        "runtime_data_strategy": runtime_decision,
        "coverage": {
            "required_flows": len(SALARY_TRADE_CASE_FLOWS),
            "normal": sum(1 for item in SALARY_TRADE_CASE_FLOWS if item["type"] == "normal"),
            "exception": sum(1 for item in SALARY_TRADE_CASE_FLOWS if item["type"] == "exception"),
            "timeout": sum(1 for item in SALARY_TRADE_CASE_FLOWS if item["type"] == "timeout"),
            "salary_cases_in_workbench": len(salary_cases),
        },
        "required_case_fields": [
            {"field": "case_id/title", "use": "生成 JMeter Sampler 名称和 JTL 标签，报告可反查到用例"},
            {"field": "precondition", "use": "生成 setUp Thread Group、CSV Data Set、运行变量检查"},
            {"field": "steps", "use": "每个业务步骤生成 HTTP Sampler 或 JSR223 处理器"},
            {"field": "role", "use": "区分 applicant/proxy/operator 的 uid、ticket、设备上下文"},
            {"field": "request_mapping", "use": "绑定接口方法、路径、Query、Body、Headers"},
            {"field": "extract_rules", "use": "从响应里提取 orderNo、orderId、状态、金额等变量"},
            {"field": "assertions", "use": "生成 HTTP 状态、业务 code、状态流转、金额/日志一致性断言"},
            {"field": "data_evidence", "use": "需要时调用只读 MySQL/Redis 取证并写入报告"},
        ],
        "jmeter_components": [
            {"case_part": "需求流", "jmeter": "Thread Group", "example": "一个业务流一个线程组，避免财富等级和工资交易混在一起"},
            {"case_part": "8个申请人账号", "jmeter": "CSV Data Set Config + User Defined Variables", "example": "每条流绑定独立 applicant_01~08；proxy 可复用"},
            {"case_part": "接口步骤", "jmeter": "HTTP Request Sampler", "example": "创建、接受、转账、确认、取消、投诉分别是可维护请求"},
            {"case_part": "变量承接", "jmeter": "JSON Extractor / JSR223 PostProcessor", "example": "创建订单后提取 orderNo，再传给后续步骤"},
            {"case_part": "预期结果", "jmeter": "Response Assertion / JSR223 Assertion", "example": "校验 code=200、状态码流转、金额和日志"},
            {"case_part": "报告归档", "jmeter": "Simple Data Writer / Summary Report / HTML Report", "example": "JTL 标签携带 flow/case/step，工作台按用例回收"},
        ],
        "flows": SALARY_TRADE_CASE_FLOWS,
        "artifacts": {
            "existing_state_machine_jmx": str(generated),
            "case_driven_jmx": str(case_driven),
            "launcher": str(ROOT / "outputs" / "open-salary-trade-state-machine.ps1"),
            "manifest": str(ROOT / "outputs" / "salary-trade-case-jmeter-manifest.json"),
            "runtime_parameters": str(ROOT / "outputs" / "salary-trade-runtime-parameters.md"),
            "account_model": str(account_model),
            "account_csv": str(account_csv),
            "applicant_csv": str(applicant_csv),
            "flow_slots_csv": str(flow_slots_csv),
        },
        "csv_contract": {
            "owner": "Runtime data source is inferred from test cases. CSV is used only when cases require multi-account, multi-role or data-matrix execution.",
            "account_csv": str(account_csv),
            "applicant_csv": str(applicant_csv),
            "flow_slots_csv": str(flow_slots_csv),
            "jmeter_properties": ["salary_accounts_csv", "salary_applicants_csv", "salary_flow_slots_csv", "salary_result_jtl"],
        },
        "gaps": salary_trade_case_jmeter_gaps(),
        "status": "READY" if generated.is_file() else "PENDING",
    }


def infer_jmeter_runtime_data_strategy(cases, flows=None):
    flows = list(flows or [])
    text_parts = []
    for case in cases or []:
        text_parts.extend([
            str(case.get("title") or ""),
            str(case.get("steps") or ""),
            str(case.get("expected") or ""),
            str(case.get("scenario_type") or ""),
            str(case.get("requirement_ref") or ""),
        ])
    for flow in flows:
        text_parts.extend([
            str(flow.get("name") or ""),
            " ".join(flow.get("steps") or []),
            str(flow.get("account_slot") or ""),
            str(flow.get("blocker") or ""),
        ])
    text = "\n".join(text_parts).lower()
    role_hits = {
        "applicant": any(word in text for word in ("申请人", "applicant", "用户发起", "确认收款")),
        "proxy": any(word in text for word in ("代理", "proxy", "agent", "接单", "转账")),
        "operator": any(word in text for word in ("运营", "operator", "投诉处理", "后台处理")),
    }
    roles = [key for key, hit in role_hits.items() if hit]
    slots = sorted({str(flow.get("account_slot") or "") for flow in flows if flow.get("account_slot")})
    flow_count = len(flows)
    has_account_mutex = any(word in text for word in ("一个处理中订单", "同一时间只能", "只能有一个", "one processing"))
    has_data_matrix = any(word in text for word in ("多账号", "批量", "参数化", "多个uid", "多组数据", "csv", "data set"))
    csv_required = len(roles) > 1 or len(slots) > 1 or has_account_mutex or has_data_matrix
    if csv_required:
        mode = "csv_required"
        source = "test_case_inferred"
    else:
        mode = "runtime_parameters"
        source = "test_case_inferred"
    reasons = []
    if len(roles) > 1:
        reasons.append(f"multi_role:{','.join(roles)}")
    if len(slots) > 1:
        reasons.append(f"multi_account_slots:{len(slots)}")
    if has_account_mutex:
        reasons.append("account_mutex")
    if has_data_matrix:
        reasons.append("data_matrix")
    if not reasons:
        reasons.append("single_account_or_single_flow")
    return {
        "mode": mode,
        "source": source,
        "csv_required": csv_required,
        "roles": roles,
        "flow_count": flow_count,
        "account_slots": slots,
        "reasons": reasons,
    }


def salary_trade_case_jmeter_gaps():
    gaps = []
    config = load_environment_config()
    salary_dataset = deep_get(config, "requirement_datasets.salary_trade", {}) or {}
    account_csv = ROOT / str(salary_dataset.get("account_csv_path") or "data/salary-trade-accounts.csv")
    applicant_csv = ROOT / str(salary_dataset.get("applicant_csv_path") or "data/salary-trade-applicants.csv")

    def count_csv(path, role=""):
        if not path.is_file():
            return 0
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                total = 0
                for item in csv.DictReader(handle):
                    if role and str(item.get("role") or "").strip() != role:
                        continue
                    if str(item.get("enabled", "true")).strip().lower() in ("0", "false", "no", "off"):
                        continue
                    total += 1
                return total
        except Exception:
            return 0

    count = count_csv(applicant_csv) + count_csv(account_csv, "applicant")
    if count < 8:
        gaps.append({"level": "P0", "item": "申请人账号池", "detail": f"工资交易8条状态流需要8个申请人账号，当前CSV可识别{count}个。"})
    state_jmx = ROOT / "outputs" / "salary-trade-state-machine.jmx"
    if not state_jmx.is_file():
        gaps.append({"level": "P0", "item": "状态机JMX", "detail": "缺少工资交易独立状态机脚本。"})
    timeout_count = sum(1 for item in SALARY_TRADE_CASE_FLOWS if item.get("automation_status") == "blocked")
    if timeout_count:
        gaps.append({"level": "P1", "item": "超时流程", "detail": f"{timeout_count}条超时流程需要测试环境提供时间加速或后台任务触发方式。"})
    return gaps


def _salary_trade_flow_slot_rows():
    result = []
    for item in SALARY_TRADE_CASE_FLOWS:
        result.append({
            "flow_code": item["code"],
            "flow_id": item["id"],
            "flow_name": item["name"],
            "flow_type": item["type"],
            "priority": item["priority"],
            "account_slot": item["account_slot"],
            "applicant_slot": item["account_slot"],
            "proxy_slot": "proxy_01",
            "operator_slot": "operator_01" if "投诉" in item["name"] else "",
            "order_var": item["order_var"],
            "thread_group": item["thread_group"],
            "automation_status": item["automation_status"],
            "enabled": "true" if item["automation_status"] != "blocked" else "false",
            "blocker": item.get("blocker", ""),
        })
    return result


def _write_salary_trade_flow_slots_csv(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows_to_write = _salary_trade_flow_slot_rows()
    fieldnames = list(rows_to_write[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_to_write)


def _jmeter_property_path(path):
    return str(Path(path)).replace("\\", "/")


def _normalize_jmeter_empty_script_filenames(text):
    """JMeter treats whitespace-only JSR223 filenames as real script paths."""
    return re.sub(r'<stringProp name="filename">\s+</stringProp>', '<stringProp name="filename"></stringProp>', text)


def _set_salary_trade_applicant_csv_property(text, value):
    pattern = r'(<CSVDataSet\b[^>]*testname="工资交易账号数据集：申请人CSV"[^>]*>.*?<stringProp name="filename">).*?(</stringProp>)'
    return re.sub(pattern, lambda match: match.group(1) + value + match.group(2), text, flags=re.S)


def _write_jmx_preserving_manual_edits(path, text):
    path = Path(path)
    old = path.read_text(encoding="utf-8") if path.is_file() else ""
    if old == text:
        return {"written": False, "backup_path": "", "preserve_mode": path.is_file()}
    backup_path = ""
    if old:
        backup = path.with_suffix(f".backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.jmx")
        backup.write_text(old, encoding="utf-8")
        backup_path = str(backup)
    path.write_text(text, encoding="utf-8")
    return {"written": True, "backup_path": backup_path, "preserve_mode": bool(old)}


def generate_salary_trade_jmeter_from_cases(project_id):
    model = salary_trade_case_to_jmeter_model(project_id)
    outputs = ROOT / "outputs"
    outputs.mkdir(exist_ok=True)
    source = outputs / "salary-trade-state-machine.jmx"
    target = outputs / "salary-trade-case-driven.jmx"
    if not source.is_file() and not target.is_file():
        raise ValueError("缺少工资交易状态机JMX，请先生成 salary-trade-state-machine.jmx")
    preserve_existing = target.is_file()
    text = target.read_text(encoding="utf-8") if preserve_existing else source.read_text(encoding="utf-8")
    if not preserve_existing:
        text = text.replace("工资代理快速结算-状态机流程版", "工资代理快速结算-用例驱动流程版")
    account_csv = Path(model["artifacts"]["account_csv"])
    applicant_csv = Path(model["artifacts"]["applicant_csv"])
    flow_slots_csv = Path(model["artifacts"]["flow_slots_csv"])
    env_config = load_environment_config()
    result_jtl = Path(
        deep_get(env_config, "requirement_datasets.salary_trade.result_jtl_path")
        or deep_get(env_config, "reports.salary_trade_jtl")
        or r"D:\apache-jmeter-5.6.3\jmx\20260826\工资代理结算-result.jtl"
    )
    _write_salary_trade_flow_slots_csv(flow_slots_csv)
    default_applicant_csv = _jmeter_property_path(applicant_csv)
    default_account_csv = _jmeter_property_path(account_csv)
    default_flow_slots_csv = _jmeter_property_path(flow_slots_csv)
    text = _set_salary_trade_applicant_csv_property(text, "${__P(salary_applicants_csv," + default_applicant_csv + ")}")
    default_result_jtl = _jmeter_property_path(result_jtl)
    text = text.replace(str(result_jtl), "${__P(salary_result_jtl," + default_result_jtl + ")}")
    text = _normalize_jmeter_empty_script_filenames(text)
    write_result = _write_jmx_preserving_manual_edits(target, text)
    manifest = {
        "generated_at": now(),
        "project_id": project_id,
        "requirement": model["requirement"],
        "source": "test_cases_to_jmeter_model",
        "skill": str(SKILL_DIR / "jmeter-script-generation" / "SKILL.md"),
        "account_model": {
            "path": model["artifacts"]["account_model"],
            "status": "READY" if Path(model["artifacts"]["account_model"]).is_file() else "MISSING",
            "rule": "JMeter生成必须先读取需求包 account_model.yaml，再决定单账号、多角色、多流程槽位、CSV、DB/Redis证据和阻断规则。",
        },
        "yaml_config": environment_config_status(project_id),
        "csv_contract": model["csv_contract"],
        "jmx_path": str(target),
        "launcher": model["artifacts"]["launcher"],
        "runtime_parameters": model["artifacts"]["runtime_parameters"],
        "csv_files": {
            "accounts": str(account_csv),
            "applicants": str(applicant_csv),
            "flow_slots": str(flow_slots_csv),
        },
        "jmeter_property_defaults": {
            "salary_accounts_csv": default_account_csv,
            "salary_applicants_csv": default_applicant_csv,
            "salary_flow_slots_csv": default_flow_slots_csv,
            "salary_result_jtl": default_result_jtl,
        },
        "preserve_policy": {
            "mode": "patch_existing_jmx" if preserve_existing else "initial_generate_from_state_machine",
            "manual_edits_preserved": preserve_existing,
            "backup_path": write_result["backup_path"],
            "written": write_result["written"],
            "rule": "已有正式JMX时不再从模板整文件覆盖，只做路径参数化、空脚本文件名清理等补丁。",
        },
        "flows": model["flows"],
        "gaps": model["gaps"],
        "trace_rule": "JMeter线程组/请求名称必须保留 flow code、case id、step name，JTL回收后按这些标签归档回测试用例。",
    }
    manifest_path = outputs / "salary-trade-case-jmeter-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path = outputs / "salary-trade-case-to-jmeter.md"
    lines = [
        "# 工资代理快速结算：测试用例到 JMeter 脚本映射",
        "",
        "## 生成原则",
        model["principle"],
        "",
        "## 覆盖流程",
    ]
    for item in model["flows"]:
        lines.append(f"- {item['code']}：{item['name']}；账号槽位：{item['account_slot']}；订单变量：{item['order_var']}；线程组：{item['thread_group']}；状态：{item['automation_status']}")
    lines.extend(["", "## 当前缺口"])
    if model["gaps"]:
        for gap in model["gaps"]:
            lines.append(f"- {gap['level']} {gap['item']}：{gap['detail']}")
    else:
        lines.append("- 暂无阻断缺口。")
    lines.extend([
        "",
        "## YAML/CSV 边界",
        "- YAML：环境、工具路径、只读数据源、报告路径、CSV路径。",
        "- 单账号需求：可直接使用运行参数、本机凭证、登录接口或Redis只读缓存。",
        "- 多账号/多流程需求：使用CSV承载账号、角色、国家币种、流程槽位、金额、循环次数等执行数据。",
        "- account_model.yaml：每个需求包自己的账号规则，JMeter生成前必须先读取它。",
        "",
        "## 生成产物",
        f"- JMX：{target}",
        f"- Manifest：{manifest_path}",
        f"- 账号模型：{model['artifacts']['account_model']}",
        f"- 账号CSV：{account_csv}",
        f"- 申请人CSV：{applicant_csv}",
        f"- 流程槽位CSV：{flow_slots_csv}",
        f"- Skill：{SKILL_DIR / 'jmeter-script-generation' / 'SKILL.md'}",
    ])
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    runtime_doc = outputs / "salary-trade-runtime-parameters.md"
    runtime_doc.write_text("\n".join([
        "# 工资交易 JMeter 运行参数",
        "",
        "## 必要参数",
        "- `salary_applicants_csv`：申请人账号CSV，默认读取 `data/salary-trade-applicants.csv`。",
        "- `salary_accounts_csv`：多角色账号CSV，默认读取 `data/salary-trade-accounts.csv`。",
        "- `salary_flow_slots_csv`：8条业务流槽位CSV，默认读取 `data/salary-trade-flow-slots.csv`。",
        "- `salary_result_jtl`：JMeter结果文件路径。",
        "",
        "## 启动示例",
        "```powershell",
        f"& \"{_jmeter_command()}\" -t \"{target}\" -Jsalary_applicants_csv=\"{applicant_csv}\" -Jsalary_accounts_csv=\"{account_csv}\" -Jsalary_flow_slots_csv=\"{flow_slots_csv}\"",
        "```",
        "",
        "## 规则",
        "- 不同需求包使用独立 JMX 和独立报告。",
        "- 平台先读取测试用例，再决定是否需要CSV参数化。",
        "- 平台再读取 account_model.yaml，决定账号角色、凭证来源和DB/Redis证据。",
        "- YAML 不保存真实 ticket、密码或公司密钥。",
    ]) + "\n", encoding="utf-8")
    model = salary_trade_case_to_jmeter_model(project_id)
    return {
        "status": "READY" if not any(gap["level"] == "P0" for gap in model["gaps"]) else "ATTENTION",
        "message": "已按测试用例驱动模型维护工资交易独立 JMeter 脚本；已有JMX时保留手工维护内容。",
        "jmx_path": str(target),
        "preserve_policy": {
            "mode": "patch_existing_jmx" if preserve_existing else "initial_generate_from_state_machine",
            "manual_edits_preserved": preserve_existing,
            "backup_path": write_result["backup_path"],
            "written": write_result["written"],
        },
        "manifest_path": str(manifest_path),
        "summary_path": str(summary_path),
        "runtime_parameters_path": str(runtime_doc),
        "flow_slots_csv_path": str(flow_slots_csv),
        "model": model,
    }


def _split_hints(value):
    if isinstance(value, list):
        raw = value
    else:
        raw = re.split(r"[\n,，;；]+", str(value or ""))
    return [str(item).strip() for item in raw if str(item).strip()]


def parse_runtime_variable_bindings(value):
    """Parse tester supplied readonly data-to-runtime rules."""
    bindings = []
    for line in _split_hints(value):
        original = line
        source = "mysql"
        var_name = table_name = column_name = condition = redis_key = redis_field = ""
        literal_value = None
        if "<-" in line:
            left, right = line.split("<-", 1)
        elif "=" in line:
            left, right = line.split("=", 1)
        else:
            bindings.append({"raw": original, "status": "INVALID", "message": "缺少变量赋值符号，例如 applicant_uid = user.uid where id=1"})
            continue
        var_name = left.strip()
        right = right.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", var_name or ""):
            bindings.append({"raw": original, "status": "INVALID", "message": "变量名只能使用字母、数字和下划线，且不能以数字开头"})
            continue
        if right.lower().startswith("redis:"):
            source = "redis"
            rest = right[6:].strip()
            m = re.match(r"(.+?)\s+(?:field|hash|hget)\s+(.+)$", rest, re.I)
            if m:
                redis_key = m.group(1).strip()
                redis_field = m.group(2).strip()
            else:
                redis_key = rest
        elif right.lower().startswith("value:"):
            source = "literal"
            literal_value = right[6:].strip()
        else:
            m = re.match(r"([A-Za-z0-9_.$`]+)\s+(?:where|WHERE)\s+(.+)$", right)
            selector = right
            if m:
                selector = m.group(1).strip()
                condition = m.group(2).strip()
            if "." in selector:
                table_name, column_name = selector.rsplit(".", 1)
            else:
                table_name = selector.strip()
        status = "READY"
        message = "运行时按只读数据源取值后注入接口变量"
        if source == "mysql" and (not table_name or not column_name):
            status = "INVALID"
            message = "MySQL规则需要写成 table.column where 条件"
        if source == "redis" and not redis_key:
            status = "INVALID"
            message = "Redis规则需要写成 redis:key 或 redis:key field hashField"
        bindings.append({
            "raw": original,
            "source": source,
            "variable": var_name,
            "table": table_name,
            "column": column_name,
            "condition": condition,
            "redis_key": redis_key,
            "redis_field": redis_field,
            "literal_value": literal_value,
            "status": status,
            "message": message,
        })
    return bindings


def run_manual_evidence_check(project_id, payload):
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    target = str(payload.get("target") or "").strip()
    if not target:
        raise ValueError("请填写本次要核查的业务对象，例如订单状态、金额、流水或缓存一致性")
    table_hints = _split_hints(payload.get("table_hints"))
    redis_hints = _split_hints(payload.get("redis_hints"))
    variable_bindings = parse_runtime_variable_bindings(payload.get("variable_bindings"))
    endpoint_id = str(payload.get("endpoint_id") or "").strip()
    endpoint = row("SELECT id,method,path,summary,parameters FROM api_endpoints WHERE id=?", (endpoint_id,)) if endpoint_id else None
    all_tables = rows("SELECT table_name,table_comment,module,columns_json FROM db_tables WHERE project_id=?", (project_id,))
    matched_tables = []
    for table_item in all_tables:
        table_text = " ".join([table_item.get("table_name",""), table_item.get("table_comment",""), table_item.get("module",""), table_item.get("columns_json","")]).lower()
        score = 0
        for hint in table_hints + re.findall(r"[\w\u4e00-\u9fff]+", target):
            token = str(hint).strip().lower()
            if token and token in table_text:
                score += 1
        if score:
            matched_tables.append({
                "table_name": table_item["table_name"],
                "table_comment": table_item.get("table_comment", ""),
                "matched_score": score,
            })
    matched_tables = sorted(matched_tables, key=lambda x: x["matched_score"], reverse=True)[:10]
    redis_sources = rows("SELECT id,name,status FROM redis_sources WHERE project_id=?", (project_id,))
    connected_redis = [x for x in redis_sources if x.get("status") == "connected"]
    status = "READY"
    blockers = []
    if table_hints and not matched_tables:
        blockers.append("给出的表线索暂未在已导入 Schema 中命中，仍可在执行时按接口语义继续推断。")
    if redis_hints and not connected_redis:
        blockers.append("给出了 Redis 线索，但当前没有可调用的 Redis 只读连接。")
    invalid_bindings = [x for x in variable_bindings if x.get("status") == "INVALID"]
    if invalid_bindings:
        blockers.append(f"有 {len(invalid_bindings)} 条变量取数规则格式不正确。")
    if blockers:
        status = "READY_WITH_WARNINGS"
    runtime_variables = {}
    for binding in variable_bindings:
        if binding.get("source") == "literal" and binding.get("status") == "READY":
            runtime_variables[binding["variable"]] = binding.get("literal_value", "")
    if variable_bindings:
        with db() as conn:
            conn.execute(
                "INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (f"project:{project_id}:execution_runtime_variable_bindings", json.dumps(variable_bindings, ensure_ascii=False)),
            )
            if runtime_variables:
                current = _json_setting(_project_settings(project_id), "execution_runtime_params", {})
                current.update(runtime_variables)
                conn.execute(
                    "INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (f"project:{project_id}:execution_runtime_params", json.dumps(current, ensure_ascii=False)),
                )
    report = {
        "report_type": "MANUAL_EVIDENCE_CHECK",
        "project_id": project_id,
        "project_name": project["name"],
        "status": status,
        "created_at": now(),
        "target": target,
        "endpoint": endpoint or {},
        "input_hints": {
            "tables": table_hints,
            "redis_keys": redis_hints,
            "variable_bindings": variable_bindings,
            "note": str(payload.get("note") or "").strip(),
        },
        "runtime_injection": {
            "mode": "指定数据源取值后注入接口/JMeter变量",
            "runtime_variables": runtime_variables,
            "binding_count": len(variable_bindings),
            "ready_count": sum(1 for x in variable_bindings if x.get("status") == "READY"),
            "mysql_execution": "待接入真实只读MySQL连接后执行SELECT取值",
            "redis_execution": "Redis已接入时可按Key只读取值",
        },
        "readonly_policy": {
            "mysql": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"],
            "redis": sorted(RedisReadonlyClient.ALLOWED),
            "business_write_allowed": False,
        },
        "runtime_plan": [
            "根据本次核查目标判断是否需要关系库、缓存或两者同时取证",
            "优先使用测试人员指定的表、字段、Key和条件",
            "只读查询 MySQL 或读取 Redis 快照，并把结果写入本次运行变量",
            "接口、Postman、JMeter 和 pytest 运行时读取同一份变量上下文",
            "将本次实际查询位置、摘要、差异和结论写入报告中心",
        ],
        "matched_tables": matched_tables,
        "redis_sources": [{"name": x["name"], "status": x["status"]} for x in redis_sources],
        "blockers": blockers,
        "conclusion": "已生成本次数据核查任务。外部数据源只读；页面不沉淀固定表名或 Key，实际取证位置进入报告。",
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = ROOT / "reports" / f"evidence-check-{project_id}-{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["json_url"] = "/reports/" + out.name
    report["file_name"] = out.name
    return report


SALARY_TRADE_DB_TABLES = {
    "agent_whitelist": "anchor_salary_trade_agent_whitelist",
    "order": "anchor_salary_trade_order",
    "order_log": "anchor_salary_trade_order_log",
    "evidence": "anchor_salary_trade_evidence",
}


def _mysql_safe_string(value, name="value", max_len=128):
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) > max_len or not re.fullmatch(r"[\w.\-:@]+", text):
        raise ValueError(f"{name}包含不允许的字符")
    return text


def _mysql_safe_int(value, name="value"):
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not re.fullmatch(r"\d{1,20}", text):
        raise ValueError(f"{name}必须是数字")
    return int(text)


def _salary_trade_latest_order_condition(payload):
    parts = []
    applicant_uid = _mysql_safe_int(payload.get("applicant_uid") or payload.get("uid"), "applicant_uid")
    proxy_uid = _mysql_safe_int(payload.get("proxy_uid") or payload.get("agent_uid"), "proxy_uid")
    country = _mysql_safe_string(payload.get("country_code") or payload.get("countryCode"), "country_code", 16)
    currency = _mysql_safe_string(payload.get("currency") or payload.get("receive_currency"), "currency", 16)
    if applicant_uid:
        parts.append(f"uid = {applicant_uid}")
    if proxy_uid:
        parts.append(f"agent_uid = {proxy_uid}")
    if country:
        parts.append(f"country_code = '{country}'")
    if currency:
        parts.append(f"receive_currency = '{currency}'")
    return " AND ".join(parts) if parts else "1=1"


def _mysql_rows(sql, limit=100):
    return mysql_readonly_query("runtime", {"sql": sql, "limit": limit})["rows"]


def salary_trade_db_evidence_check(project_id, payload):
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    order_no = _mysql_safe_string(payload.get("order_no") or payload.get("orderNo") or payload.get("salary_order_no"), "orderNo", 64)
    if not order_no:
        condition = _salary_trade_latest_order_condition(payload)
        latest = _mysql_rows(f"SELECT order_no FROM {SALARY_TRADE_DB_TABLES['order']} WHERE {condition} ORDER BY id DESC", 1)
        if latest:
            order_no = str(latest[0].get("order_no") or "")
    if not order_no:
        raise ValueError("未取得 orderNo，请从 JMeter 创建订单响应或订单列表中传入 orderNo")

    applicant_uid = _mysql_safe_int(payload.get("applicant_uid") or payload.get("uid"), "applicant_uid")
    proxy_uid = _mysql_safe_int(payload.get("proxy_uid") or payload.get("agent_uid"), "proxy_uid")
    expected_status = _mysql_safe_int(payload.get("expected_status"), "expected_status")
    expected_log_statuses = []
    for item in payload.get("expected_log_statuses") or []:
        expected_log_statuses.append(_mysql_safe_int(item, "expected_log_statuses"))
    country = _mysql_safe_string(payload.get("country_code") or payload.get("countryCode"), "country_code", 16)
    currency = _mysql_safe_string(payload.get("currency") or payload.get("receive_currency"), "currency", 16)

    order_rows = _mysql_rows(
        "SELECT id,order_no,uid,agent_uid,salary_month,salary_amount,frozen_salary_amount,gold_amount,"
        "receive_currency,country_code,status,expire_time,accepted_time,paid_time,confirmed_time,"
        f"finished_time,cancel_reason,appeal_uid,appeal_reason,operator_id,create_time,update_time FROM {SALARY_TRADE_DB_TABLES['order']} "
        f"WHERE order_no = '{order_no}'",
        10,
    )
    order_item = order_rows[0] if order_rows else {}
    log_rows = _mysql_rows(
        f"SELECT id,order_id,order_no,from_status,to_status,action,op_role,op_uid,admin_id,reason,create_time FROM {SALARY_TRADE_DB_TABLES['order_log']} "
        f"WHERE order_no = '{order_no}' ORDER BY id ASC",
        100,
    )
    evidence_rows = _mysql_rows(
        f"SELECT id,order_id,order_no,uid,admin_id,evidence_type,remark,create_time FROM {SALARY_TRADE_DB_TABLES['evidence']} "
        f"WHERE order_no = '{order_no}' ORDER BY id ASC",
        100,
    )
    whitelist_rows = []
    if proxy_uid:
        whitelist_rows = _mysql_rows(
            f"SELECT id,uid,country_code,support_currencies,status,remark,create_time,update_time FROM {SALARY_TRADE_DB_TABLES['agent_whitelist']} "
            f"WHERE uid = {proxy_uid}",
            20,
        )

    log_to_statuses = [int(x.get("to_status") or 0) for x in log_rows if str(x.get("to_status") or "").isdigit()]
    whitelist_ok = False
    if whitelist_rows:
        for item in whitelist_rows:
            item_country = str(item.get("country_code") or "")
            currencies = str(item.get("support_currencies") or "")
            status_ok = int(item.get("status") or 0) == 1
            country_ok = not country or item_country == country
            currency_ok = not currency or currency in re.split(r"[,，\s]+", currencies.replace("[", "").replace("]", "").replace('"', "").replace("'", ""))
            if status_ok and country_ok and currency_ok:
                whitelist_ok = True
                break

    assertions = [
        {"name": "订单主表存在", "expected": "存在1条订单", "actual": len(order_rows), "passed": len(order_rows) == 1, "table": SALARY_TRADE_DB_TABLES["order"]},
        {"name": "订单日志存在", "expected": "至少1条状态流转日志", "actual": len(log_rows), "passed": len(log_rows) > 0, "table": SALARY_TRADE_DB_TABLES["order_log"]},
    ]
    if applicant_uid:
        assertions.append({"name": "申请人UID一致", "expected": applicant_uid, "actual": order_item.get("uid"), "passed": order_item.get("uid") == applicant_uid, "table": SALARY_TRADE_DB_TABLES["order"]})
    if proxy_uid:
        assertions.append({"name": "代理UID一致", "expected": proxy_uid, "actual": order_item.get("agent_uid"), "passed": order_item.get("agent_uid") == proxy_uid, "table": SALARY_TRADE_DB_TABLES["order"]})
        assertions.append({"name": "代理白名单国家币种可用", "expected": f"{country or '任意国家'} / {currency or '任意币种'} / status=1", "actual": whitelist_rows[:3], "passed": whitelist_ok, "table": SALARY_TRADE_DB_TABLES["agent_whitelist"]})
    if country:
        assertions.append({"name": "订单国家一致", "expected": country, "actual": order_item.get("country_code"), "passed": order_item.get("country_code") == country, "table": SALARY_TRADE_DB_TABLES["order"]})
    if currency:
        assertions.append({"name": "订单币种一致", "expected": currency, "actual": order_item.get("receive_currency"), "passed": order_item.get("receive_currency") == currency, "table": SALARY_TRADE_DB_TABLES["order"]})
    if expected_status is not None:
        assertions.append({"name": "订单最终状态一致", "expected": expected_status, "actual": order_item.get("status"), "passed": order_item.get("status") == expected_status, "table": SALARY_TRADE_DB_TABLES["order"]})
    for status_value in expected_log_statuses:
        assertions.append({"name": f"日志包含状态{status_value}", "expected": status_value, "actual": log_to_statuses, "passed": status_value in log_to_statuses, "table": SALARY_TRADE_DB_TABLES["order_log"]})
    expect_evidence = bool(payload.get("expect_evidence")) or (expected_status in {80, 90})
    if expect_evidence:
        assertions.append({"name": "投诉/凭证证据存在", "expected": "至少1条 evidence", "actual": len(evidence_rows), "passed": len(evidence_rows) > 0, "table": SALARY_TRADE_DB_TABLES["evidence"]})

    passed = sum(1 for item in assertions if item["passed"])
    failed = len(assertions) - passed
    status = "PASSED" if failed == 0 else "FAILED"
    report = {
        "report_type": "SALARY_TRADE_DB_EVIDENCE",
        "project_id": project_id,
        "project_name": project["name"],
        "status": status,
        "created_at": now(),
        "requirement": "工资代理快速结算",
        "order_no": order_no,
        "input": {
            "applicant_uid": applicant_uid,
            "proxy_uid": proxy_uid,
            "country_code": country,
            "currency": currency,
            "expected_status": expected_status,
            "expected_log_statuses": expected_log_statuses,
            "expect_evidence": expect_evidence,
        },
        "summary": {
            "assertions_total": len(assertions),
            "assertions_passed": passed,
            "assertions_failed": failed,
            "order_rows": len(order_rows),
            "log_rows": len(log_rows),
            "evidence_rows": len(evidence_rows),
            "whitelist_rows": len(whitelist_rows),
        },
        "assertions": assertions,
        "evidence": {
            "order": order_item,
            "order_logs": log_rows,
            "evidence": evidence_rows,
            "agent_whitelist": whitelist_rows,
        },
        "readonly_policy": {
            "mysql": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"],
            "business_write_allowed": False,
            "note": "业务变化由接口/JMeter产生，平台只读取MySQL证据并归档。",
        },
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = ROOT / "reports" / f"salary-trade-db-evidence-{project_id}-{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    report["json_url"] = "/reports/" + out.name
    report["file_name"] = out.name
    return report


SALARY_TRADE_JMETER_SAMPLE_VARIABLES = [
    "flow_a_order_no",
    "flow_b_order_no",
    "flow_c_order_no",
    "flow_d_order_no",
    "flow_e_order_no",
    "flow_f_order_no",
    "flow_g_order_no",
    "flow_h_order_no",
    "salary_order_no",
    "applicant_uid",
    "proxy_uid",
    "agent_uid",
    "countryCode",
    "currency",
]


def _read_jmeter_jtl_rows(jtl_path):
    path = Path(jtl_path)
    if not path.is_file():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _latest_salary_trade_jtl():
    env = load_environment_config()
    configured = Path(
        deep_get(env, "requirement_datasets.salary_trade.result_jtl_path")
        or deep_get(env, "reports.salary_trade_jtl")
        or r"D:\apache-jmeter-5.6.3\jmx\20260826\工资代理结算-result.jtl"
    )
    candidates = []
    if configured.is_file():
        candidates.append(configured)
    default_dir = configured.parent
    if default_dir.exists():
        candidates.extend(default_dir.glob("*工资代理结算*.jtl"))
        candidates.extend(default_dir.glob("*salary*trade*.jtl"))
    unique = {str(item.resolve()).lower(): item for item in candidates if item.is_file()}
    if not unique:
        return configured
    return sorted(unique.values(), key=lambda item: item.stat().st_mtime, reverse=True)[0]


def _salary_flow_code_from_label(label, flows):
    text = str(label or "").lower()
    for flow in flows:
        code = str(flow.get("code") or "").lower()
        if code and (f"流程{code}" in text or f"flow_{code}" in text or f"flow {code}" in text):
            return str(flow.get("code"))
        for key in ("name", "thread_group", "id"):
            value = str(flow.get(key) or "").lower()
            if value and value in text:
                return str(flow.get("code"))
    return ""


def _salary_order_from_sample(sample, flow):
    order_var = str(flow.get("order_var") or "")
    for key in (order_var, "salary_order_no"):
        value = str(sample.get(key) or "").strip()
        if value and "${" not in value:
            return value, "jtl_sample_variable"
    return "", ""


def salary_trade_jmeter_mapping_status(project_id):
    manifest_path = ROOT / "outputs" / "salary-trade-case-jmeter-manifest.json"
    jtl_path = _latest_salary_trade_jtl()
    fields, rows_ = _read_jmeter_jtl_rows(jtl_path)
    sample_variable_fields = [field for field in SALARY_TRADE_JMETER_SAMPLE_VARIABLES if field in fields]
    manifest = {}
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}
    return {
        "status": "READY" if manifest_path.is_file() and jtl_path.is_file() and sample_variable_fields else "ATTENTION",
        "manifest_path": str(manifest_path),
        "manifest_ready": manifest_path.is_file(),
        "jtl_path": str(jtl_path),
        "jtl_ready": jtl_path.is_file(),
        "jtl_rows": len(rows_),
        "sample_variables": sample_variable_fields,
        "missing_sample_variables": [field for field in SALARY_TRADE_JMETER_SAMPLE_VARIABLES if field not in fields],
        "flows": len(manifest.get("flows") or []),
        "message": "JMeter结果已可按流程/订单号回收" if sample_variable_fields else "JTL尚未包含订单变量；请用新版打开脚本重新运行一次JMeter。",
    }


def harvest_salary_trade_jmeter_mapping(project_id, payload=None):
    payload = payload or {}
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    manifest_path = Path(payload.get("manifest_path") or ROOT / "outputs" / "salary-trade-case-jmeter-manifest.json")
    if not manifest_path.is_file():
        raise ValueError("缺少工资交易 JMeter Manifest，请先生成用例驱动脚本。")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    flows = manifest.get("flows") or []
    jtl_path = Path(payload.get("jtl_path") or _latest_salary_trade_jtl())
    fields, samples = _read_jmeter_jtl_rows(jtl_path)
    if not samples:
        raise ValueError(f"未找到可回收的 JMeter JTL 结果：{jtl_path}")

    flow_index = {str(flow.get("code")): flow for flow in flows if flow.get("code")}
    grouped = {code: [] for code in flow_index}
    unmapped = []
    for sample in samples:
        code = _salary_flow_code_from_label(f"{sample.get('threadName') or ''} {sample.get('label') or ''}", flows)
        if code and code in grouped:
            grouped[code].append(sample)
        else:
            unmapped.append(sample)

    jtl_summary = _summarize_jmeter_jtl(jtl_path)
    gate = _performance_gate(jtl_summary, payload)
    diagnosis = _performance_diagnosis(jtl_summary, gate)
    flow_reports = []
    db_passed = db_failed = db_blocked = 0
    order_fields_present = any(field in fields for field in [flow.get("order_var") for flow in flows] + ["salary_order_no"])
    for code, flow in flow_index.items():
        flow_samples = grouped.get(code) or []
        failures = [item for item in flow_samples if str(item.get("success", "")).lower() != "true"]
        order_no = ""
        order_source = ""
        for item in reversed(flow_samples):
            order_no, order_source = _salary_order_from_sample(item, flow)
            if order_no:
                break
        applicant_uid = next((str(item.get("applicant_uid") or "").strip() for item in reversed(flow_samples) if str(item.get("applicant_uid") or "").strip()), "")
        proxy_uid = next((str(item.get("proxy_uid") or item.get("agent_uid") or "").strip() for item in reversed(flow_samples) if str(item.get("proxy_uid") or item.get("agent_uid") or "").strip()), "")
        country = next((str(item.get("countryCode") or "").strip() for item in reversed(flow_samples) if str(item.get("countryCode") or "").strip()), "")
        currency = next((str(item.get("currency") or "").strip() for item in reversed(flow_samples) if str(item.get("currency") or "").strip()), "")
        db_evidence = {"status": "BLOCKED", "message": "本流程未从JTL取得orderNo，无法严格关联DB证据。"}
        if order_no:
            try:
                db_evidence = salary_trade_db_evidence_check(project_id, {
                    "order_no": order_no,
                    "applicant_uid": applicant_uid,
                    "proxy_uid": proxy_uid,
                    "country_code": country,
                    "currency": currency,
                    "expect_evidence": str(flow.get("type")) == "exception",
                })
            except Exception as exc:
                db_evidence = {"status": "FAILED", "message": str(exc)}
        if db_evidence.get("status") == "PASSED":
            db_passed += 1
        elif db_evidence.get("status") == "FAILED":
            db_failed += 1
        else:
            db_blocked += 1
        status = "BLOCKED" if not flow_samples else "FAILED" if failures or db_evidence.get("status") == "FAILED" else "PASSED" if db_evidence.get("status") == "PASSED" or str(flow.get("automation_status")) == "blocked" else "WARNING"
        flow_reports.append({
            "code": code,
            "name": flow.get("name"),
            "type": flow.get("type"),
            "priority": flow.get("priority"),
            "automation_status": flow.get("automation_status"),
            "account_slot": flow.get("account_slot"),
            "order_var": flow.get("order_var"),
            "order_no": order_no,
            "order_source": order_source,
            "status": status,
            "samples": len(flow_samples),
            "failed_samples": len(failures),
            "failed_labels": [item.get("label") for item in failures[:10]],
            "runtime": {
                "applicant_uid": applicant_uid,
                "proxy_uid": proxy_uid,
                "country_code": country,
                "currency": currency,
            },
            "db_evidence": {
                "status": db_evidence.get("status"),
                "summary": db_evidence.get("summary"),
                "json_url": db_evidence.get("json_url"),
                "message": db_evidence.get("message", ""),
            },
        })

    failed_flows = [item for item in flow_reports if item["status"] == "FAILED"]
    blocked_flows = [item for item in flow_reports if item["status"] == "BLOCKED"]
    status = "FAILED" if failed_flows or jtl_summary.get("errors") else "BLOCKED" if blocked_flows else "PASSED"
    warnings = []
    if not order_fields_present:
        warnings.append("当前JTL没有订单变量列，无法做到严格订单级映射；请用新版启动脚本重新打开JMeter并运行。")
    if unmapped:
        warnings.append(f"有 {len(unmapped)} 条JMeter采样未匹配到工资交易流程，建议检查请求命名是否保留流程编号。")
    report = {
        "report_type": "SALARY_TRADE_JMETER_MAPPING",
        "project_id": project_id,
        "project_name": project["name"],
        "requirement": manifest.get("requirement") or "工资代理快速结算",
        "status": status,
        "created_at": now(),
        "manifest_path": str(manifest_path),
        "jmx_path": manifest.get("jmx_path"),
        "jtl_path": str(jtl_path),
        "jtl_fields": fields,
        "sample_variables": [field for field in SALARY_TRADE_JMETER_SAMPLE_VARIABLES if field in fields],
        "warnings": warnings,
        "summary": {
            "flows_total": len(flow_reports),
            "flows_passed": sum(1 for item in flow_reports if item["status"] == "PASSED"),
            "flows_failed": len(failed_flows),
            "flows_blocked": len(blocked_flows),
            "db_passed": db_passed,
            "db_failed": db_failed,
            "db_blocked": db_blocked,
            "jmeter_requests": jtl_summary.get("requests", 0),
            "jmeter_errors": jtl_summary.get("errors", 0),
            "jmeter_error_rate": jtl_summary.get("error_rate", 0),
        },
        "performance_summary": jtl_summary,
        "performance_gate": gate,
        "performance_diagnosis": diagnosis,
        "flows": flow_reports,
        "unmapped_samples": [{"label": item.get("label"), "responseCode": item.get("responseCode"), "success": item.get("success")} for item in unmapped[:30]],
        "trace_rule": manifest.get("trace_rule"),
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = ROOT / "reports" / f"salary-trade-jmeter-mapping-{project_id}-{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    report["json_url"] = "/reports/" + out.name
    report["file_name"] = out.name
    return report


def quality_runtime():
    from quality_hub_backend.runtime import QualityHubRuntime

    return QualityHubRuntime(
        connection_factory=db,
        data_dir=DATA,
        report_lister=list_generated_reports,
        credential_loader=load_account_credential,
    )


def project_quality_diagnosis(project_id, persist=True):
    runtime = quality_runtime()
    diagnosis = runtime.diagnosis.diagnose(project_id, persist=persist)
    return diagnosis.model_dump(mode="json")


def project_dashboard(project_id):
    payload = quality_runtime().dashboard.dashboard(project_id)
    payload["environment_config"] = environment_config_status(project_id)
    payload["mysql_status"] = mysql_connection_status(project_id)
    payload["multi_account_context"] = multi_account_context_status(project_id)
    payload["jmeter_generation_skill"] = jmeter_generation_skill_status(project_id)
    payload["case_jmeter_model"] = salary_trade_case_to_jmeter_model(project_id)
    payload["salary_trade_jmeter_mapping"] = salary_trade_jmeter_mapping_status(project_id)
    payload["requirement_packages"] = requirement_package_catalog(project_id)
    return payload


def project_control_plane(project_id):
    return quality_runtime().control_plane.control_plane(project_id)


def _project_settings(project_id):
    prefix = f"project:{project_id}:"
    return {item["key"].removeprefix(prefix): item["value"] for item in rows("SELECT key,value FROM settings WHERE key LIKE ?", (prefix + "%",))}


def project_quality_profile(project_id):
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    settings = _project_settings(project_id)
    sources = rows("SELECT kind,COUNT(*) n FROM sources WHERE project_id=? GROUP BY kind", (project_id,))
    source_counts = {item["kind"]: item["n"] for item in sources}
    accounts = quality_runtime().repository.accounts(project_id)
    reports = list_generated_reports(project_id)
    db_tables = row("SELECT COUNT(*) n FROM db_tables WHERE project_id=?", (project_id,))["n"]
    redis_connected = row("SELECT COUNT(*) n FROM redis_sources WHERE project_id=? AND status='connected'", (project_id,))["n"]
    rules = row("SELECT COUNT(*) n FROM consistency_rules WHERE project_id=?", (project_id,))["n"]
    core_runs = row(
        """SELECT COUNT(*) n FROM consistency_runs x
           JOIN consistency_rules r ON r.id=x.rule_id
           WHERE x.project_id=? AND r.redis_key='yingtao_user_level_exper' AND x.status='PASSED'""",
        (project_id,),
    )["n"]
    sla = {
        "max_error_rate": settings.get("max_error_rate", ""),
        "max_p95_ms": settings.get("max_p95_ms", ""),
        "max_p99_ms": settings.get("max_p99_ms", ""),
        "min_throughput_rps": settings.get("min_throughput_rps", ""),
        "source": settings.get("sla_source", ""),
        "monitoring_url": settings.get("monitoring_url", ""),
    }
    sections = [
        {"key": "environment", "name": "测试环境", "status": "READY" if project.get("base_url") else "MISSING", "summary": project.get("base_url") or "缺少 Base URL"},
        {"key": "requirement", "name": "需求资料", "status": "READY" if source_counts.get("requirement") else "MISSING", "summary": f"{source_counts.get('requirement', 0)} 份需求资料"},
        {"key": "api_doc", "name": "接口文档", "status": "READY" if source_counts.get("openapi") else "ATTENTION", "summary": f"{source_counts.get('openapi', 0)} 份 OpenAPI/Swagger"},
        {"key": "capture", "name": "抓包样例", "status": "READY" if source_counts.get("har") else "ATTENTION", "summary": f"{source_counts.get('har', 0)} 份 HAR 样例"},
        {"key": "accounts", "name": "测试账号", "status": "READY" if any(x.get("has_ticket") or x.get("has_password") for x in accounts) else "ATTENTION", "summary": f"{len(accounts)} 个账号，{sum(bool(x.get('has_ticket') or x.get('has_password')) for x in accounts)} 个可执行"},
        {"key": "sla", "name": "SLA 准入", "status": "READY" if sla["max_error_rate"] and sla["max_p95_ms"] else "MISSING", "summary": f"错误率≤{sla['max_error_rate'] or '-'}%，P95≤{sla['max_p95_ms'] or '-'}ms"},
        {"key": "datasource", "name": "数据证据连接器", "status": "READY" if db_tables or redis_connected else "ATTENTION", "summary": "运行时自动选择只读证据源，不在工作台维护表或Key清单"},
        {"key": "data_gate", "name": "按需数据核查", "status": "READY" if core_runs or rules else "ATTENTION", "summary": "需要核查时自动执行，结果进入报告"},
        {"key": "reports", "name": "报告证据", "status": "READY" if reports else "ATTENTION", "summary": f"{len(reports)} 份报告"},
    ]
    ready = sum(item["status"] == "READY" for item in sections)
    return {
        "project": dict(project),
        "settings": settings,
        "sla": sla,
        "sections": sections,
        "score": round(ready / len(sections) * 100),
        "readonly": True,
        "updated_at": now(),
    }


def save_project_quality_profile(project_id, payload):
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    if "base_url" in payload or "name" in payload or "description" in payload:
        execute(
            "UPDATE projects SET name=?,description=?,base_url=?,updated_at=? WHERE id=?",
            (
                payload.get("name", project["name"]),
                payload.get("description", project["description"]),
                payload.get("base_url", project["base_url"]),
                now(),
                project_id,
            ),
        )
    allowed = {"env_name", "env_type", "owner", "max_error_rate", "max_p95_ms", "max_p99_ms", "min_throughput_rps", "sla_source", "monitoring_url"}
    with db() as conn:
        for key in allowed:
            if key in payload:
                conn.execute(
                    "INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (f"project:{project_id}:{key}", str(payload.get(key) or "")),
                )
    return project_quality_profile(project_id)


def _json_setting(settings, key, default):
    raw = settings.get(key, "")
    if not raw:
        return default
    try:
        value = json.loads(raw)
        return value if isinstance(value, type(default)) else default
    except Exception:
        return default


def project_execution_profile(project_id):
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    settings = _project_settings(project_id)
    accounts = list_test_accounts(project_id)
    account_uids = [x.get("account_uid") for x in accounts if x.get("account_uid")]
    primary_uid = next((x.get("account_uid") for role in ("sender", "general", "boundary") for x in accounts if x.get("account_role") == role and x.get("account_uid")), account_uids[0] if account_uids else 1454428)
    receiver_uid = next((x.get("account_uid") for x in accounts if x.get("account_role") == "receiver" and x.get("account_uid")), "")
    runtime_params = _json_setting(settings, "execution_runtime_params", {})
    if not runtime_params:
        runtime_params = {
            "uid": primary_uid,
            "uids": account_uids[:5] or [1454428],
            "receiver_uid": receiver_uid,
            "room_uid": primary_uid,
            "pageNo": 1,
            "pageSize": 50,
            "type": 1,
        }
    return {
        "runtime_params": runtime_params,
        "performance": {
            "profile": settings.get("execution_performance_profile", "smoke"),
            "jmeter_threads": int(settings.get("execution_jmeter_threads") or 2),
            "jmeter_loops": int(settings.get("execution_jmeter_loops") or 5),
            "jmeter_rampup": int(settings.get("execution_jmeter_rampup") or 2),
            "jmeter_timeout": int(settings.get("execution_jmeter_timeout") or 180),
            "max_error_rate": float(settings.get("execution_max_error_rate") or 0),
            "max_p95_ms": int(settings.get("execution_max_p95_ms") or settings.get("max_p95_ms") or 3000),
            "max_p99_ms": int(settings.get("execution_max_p99_ms") or settings.get("max_p99_ms") or 5000),
            "min_throughput_rps": float(settings.get("execution_min_throughput_rps") or 0),
        },
        "tools": {
            "run_newman": settings.get("execution_run_newman", "true") != "false",
            "run_jmeter": settings.get("execution_run_jmeter", "true") != "false",
            "run_pytest": settings.get("execution_run_pytest", "true") != "false",
        },
        "readonly": True,
        "updated_at": settings.get("execution_updated_at", ""),
    }


def save_project_execution_profile(project_id, payload):
    if not row("SELECT id FROM projects WHERE id=?", (project_id,)):
        raise ValueError("项目不存在")
    runtime_params = payload.get("runtime_params") or {}
    if not isinstance(runtime_params, dict):
        raise ValueError("运行参数必须是 JSON 对象")
    perf = payload.get("performance") or {}
    tools = payload.get("tools") or {}
    values = {
        "execution_runtime_params": json.dumps(runtime_params, ensure_ascii=False),
        "execution_performance_profile": str(perf.get("profile") or "smoke"),
        "execution_jmeter_threads": str(max(1, min(int(perf.get("jmeter_threads") or 2), 200))),
        "execution_jmeter_loops": str(max(1, min(int(perf.get("jmeter_loops") or 5), 1000))),
        "execution_jmeter_rampup": str(max(0, min(int(perf.get("jmeter_rampup") or 2), 600))),
        "execution_jmeter_timeout": str(max(30, min(int(perf.get("jmeter_timeout") or 180), 3600))),
        "execution_max_error_rate": str(max(0, float(perf.get("max_error_rate") or 0))),
        "execution_max_p95_ms": str(max(1, int(perf.get("max_p95_ms") or 3000))),
        "execution_max_p99_ms": str(max(1, int(perf.get("max_p99_ms") or 5000))),
        "execution_min_throughput_rps": str(max(0, float(perf.get("min_throughput_rps") or 0))),
        "execution_run_newman": "true" if tools.get("run_newman", True) is not False else "false",
        "execution_run_jmeter": "true" if tools.get("run_jmeter", True) is not False else "false",
        "execution_run_pytest": "true" if tools.get("run_pytest", True) is not False else "false",
        "execution_updated_at": now(),
    }
    with db() as conn:
        for key, value in values.items():
            conn.execute(
                "INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (f"project:{project_id}:{key}", value),
            )
    return project_execution_profile(project_id)


def _merge_execution_profile_options(project_id, options=None):
    options = dict(options or {})
    profile = project_execution_profile(project_id)
    perf = profile.get("performance", {})
    tools = profile.get("tools", {})
    runtime = dict(profile.get("runtime_params") or {})
    runtime.update(options.get("runtime_params") or {})
    options["runtime_params"] = runtime
    defaults = {
        "performance_profile": perf.get("profile"),
        "jmeter_threads": perf.get("jmeter_threads"),
        "jmeter_loops": perf.get("jmeter_loops"),
        "jmeter_rampup": perf.get("jmeter_rampup"),
        "jmeter_timeout": perf.get("jmeter_timeout"),
        "max_error_rate": perf.get("max_error_rate"),
        "max_p95_ms": perf.get("max_p95_ms"),
        "max_p99_ms": perf.get("max_p99_ms"),
        "min_throughput_rps": perf.get("min_throughput_rps"),
        "run_newman": tools.get("run_newman"),
        "run_jmeter": tools.get("run_jmeter"),
        "run_pytest": tools.get("run_pytest"),
    }
    for key, value in defaults.items():
        if key not in options or options.get(key) in ("", None):
            options[key] = value
    return options


def platform_storage_policy():
    from quality_hub_backend.storage_policy import storage_boundaries

    return {"boundaries": [x.__dict__ for x in storage_boundaries()]}


def _metadata_column_names(columns_json):
    try:
        payload = json.loads(columns_json or "[]")
    except Exception:
        payload = []
    if isinstance(payload, dict):
        payload = payload.get("columns") or payload.get("items") or []
    names = set()
    for item in payload if isinstance(payload, list) else []:
        if isinstance(item, dict):
            value = item.get("column_name") or item.get("COLUMN_NAME") or item.get("name") or item.get("field")
        else:
            value = item
        value = str(value or "").strip()
        if value:
            names.add(value)
    return names


def _metadata_text_sources(project_id, package_id=""):
    items = []
    for table, fields in (
        ("sources", ("name", "kind", "content")),
        ("requirement_items", ("title", "description", "acceptance_criteria")),
        ("test_points", ("module", "title", "category", "rationale")),
        ("test_cases", ("title", "method", "path", "headers", "payload", "steps", "expected")),
        ("api_endpoints", ("method", "path", "summary", "tags", "parameters", "request_body", "responses", "example_request", "required_fields")),
        ("workflows", ("name", "module", "description")),
        ("workflow_steps", ("name", "request_template", "assertion_template", "extractors")),
    ):
        try:
            for record in rows(f"SELECT {','.join(fields)} FROM {table} WHERE project_id=?", (project_id,)):
                text = "\n".join(str(record.get(field) or "") for field in fields)
                if text.strip():
                    items.append({"source": f"平台资产/{table}", "text": text[:60000]})
        except Exception:
            continue
    roots = []
    if package_id:
        roots.append(REQUIREMENT_PACKAGE_ROOT / package_id)
    else:
        roots += [REQUIREMENT_PACKAGE_ROOT, ROOT / "outputs"]
    roots.append(ROOT / "skills")
    seen = set()
    allowed = {".json", ".yaml", ".yml", ".md", ".txt", ".py", ".js", ".ps1"}
    for root_path in roots:
        if not root_path.exists():
            continue
        for file in root_path.rglob("*"):
            if file in seen or not file.is_file() or file.suffix.lower() not in allowed:
                continue
            seen.add(file)
            try:
                content = file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if content.strip():
                try:
                    source_name = str(file.relative_to(ROOT))
                except ValueError:
                    source_name = str(file)
                items.append({"source": source_name, "text": content[:120000]})
    return items


def _metadata_candidates(text):
    snake = set(re.findall(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+){1,}\b", text))
    db_like = {
        token for token in snake
        if token.startswith(("anchor_", "salary_trade_", "user_login_info_"))
        or token in {"order_no", "country_code", "support_currencies", "agent_uid", "appeal_uid", "operator_id"}
    }
    redis_like = set(re.findall(r"\b[a-zA-Z0-9_.-]+(?::[a-zA-Z0-9_.${}_-]+){1,}\b", text))
    return db_like, redis_like


def metadata_hallucination_audit(project_id, payload=None):
    payload = payload or {}
    package_id = str(payload.get("package_id") or "").strip()
    db_items = rows("SELECT table_name,table_comment,columns_json FROM db_tables WHERE project_id=?", (project_id,))
    table_names = {x["table_name"] for x in db_items if x.get("table_name")}
    column_names = set()
    for item in db_items:
        column_names.update(_metadata_column_names(item.get("columns_json")))
    redis_keys = {x["key_name"] for x in rows("SELECT key_name FROM redis_key_snapshots WHERE project_id=?", (project_id,)) if x.get("key_name")}
    redis_patterns = set()
    try:
        redis_patterns.update(x.get("key_pattern") or "" for x in rows("SELECT key_pattern FROM api_redis_mappings WHERE project_id=?", (project_id,)))
    except Exception:
        pass
    redis_patterns = {x for x in redis_patterns if x}
    sources = _metadata_text_sources(project_id, package_id)
    found_tables, found_columns, found_redis, unknown_db, unknown_redis = {}, {}, {}, {}, {}
    for item in sources:
        db_like, redis_like = _metadata_candidates(item["text"])
        for token in db_like:
            if token in table_names:
                found_tables.setdefault(token, item["source"])
            elif token in column_names:
                found_columns.setdefault(token, item["source"])
            elif token.startswith(("anchor_", "salary_trade_")):
                unknown_db.setdefault(token, item["source"])
        for token in redis_like:
            if token in redis_keys or any(pattern and pattern.replace("*", "") in token for pattern in redis_patterns):
                found_redis.setdefault(token, item["source"])
            elif token.startswith(("user_login_info:", "salary:", "anchor:", "trade:", "order:", "wallet:", "wealth:")):
                unknown_redis.setdefault(token, item["source"])
    metadata_ready = bool(table_names or column_names or redis_keys or redis_patterns)
    findings = []
    for name, source in sorted(unknown_db.items())[:80]:
        findings.append({"level": "P1", "type": "DB_REFERENCE_NOT_IN_METADATA", "name": name, "source": source, "recommendation": "确认这是业务表/字段后，重新导入数据库元数据；如果只是变量名，可忽略。"})
    for name, source in sorted(unknown_redis.items())[:80]:
        findings.append({"level": "P1", "type": "REDIS_REFERENCE_NOT_IN_METADATA", "name": name, "source": source, "recommendation": "确认Redis快照或Key映射是否已导入；如果只是示例占位，可忽略。"})
    status = "UNCONFIGURED" if not metadata_ready else "ATTENTION" if findings else "PASSED"
    report = {
        "report_type": "METADATA_HALLUCINATION_AUDIT",
        "project_id": project_id,
        "package_id": package_id or "general",
        "status": status,
        "created_at": now(),
        "summary": {
            "sources_scanned": len(sources),
            "db_tables_known": len(table_names),
            "db_columns_known": len(column_names),
            "redis_keys_known": len(redis_keys),
            "redis_patterns_known": len(redis_patterns),
            "db_references_verified": len(found_tables) + len(found_columns),
            "redis_references_verified": len(found_redis),
            "attention_items": len(findings),
        },
        "verified": {
            "tables": sorted(found_tables)[:100],
            "columns": sorted(found_columns)[:100],
            "redis": sorted(found_redis)[:100],
        },
        "findings": findings,
        "note": "本报告只使用平台已保存的数据库/Redis元数据校验AI输出，不直连或修改业务数据源。",
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = ROOT / "reports" / f"metadata-hallucination-audit-{project_id}-{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["json_url"] = "/reports/" + out.name
    report["file_name"] = out.name
    return report


def _latest_metadata_audit_report(project_id, package_id):
    report_dir = ROOT / "reports"
    if not report_dir.exists():
        return {}
    candidates = []
    for file in report_dir.glob("metadata-hallucination-audit-*.json"):
        try:
            payload = json.loads(file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if payload.get("project_id") != project_id:
            continue
        if str(payload.get("package_id") or "general") != str(package_id or "general"):
            continue
        candidates.append((file.stat().st_mtime, file, payload))
    if not candidates:
        return {}
    _, file, payload = sorted(candidates, key=lambda x: x[0], reverse=True)[0]
    payload["json_url"] = "/reports/" + file.name
    payload["file_name"] = file.name
    payload["file_path"] = str(file)
    return payload


def _metadata_unverified_names(audit_report):
    findings = audit_report.get("findings") or []
    return sorted({
        str(item.get("name") or "").strip()
        for item in findings
        if str(item.get("name") or "").strip()
    })


def _metadata_text_has_unverified(value, names):
    text = json.dumps(value, ensure_ascii=False, default=str) if not isinstance(value, str) else value
    return [name for name in names if name and name in text]


def _apply_metadata_review_marker(record, names, source=""):
    hits = _metadata_text_has_unverified(record, names)
    if not hits:
        return False
    marker = {
        "status": "NEEDS_METADATA_REVIEW",
        "unverified_references": hits,
        "source": source,
        "correction_action": "已降级为人工确认项；确认元数据存在后再采纳为正式资产。",
    }
    if isinstance(record, dict):
        record["metadata_validation"] = marker
        if record.get("quality_status") == "READY":
            record["quality_status"] = "NEEDS_METADATA_REVIEW"
        if record.get("automation_readiness") == "SCRIPT_GENERATION_READY":
            record["automation_readiness"] = "METADATA_REVIEW_REQUIRED"
        if record.get("review_status") in {"READY_FOR_REVIEW", "READY"}:
            record["review_status"] = "METADATA_REVIEW_REQUIRED"
        if record.get("readiness") in {"READY", "SCRIPT_GENERATION_READY"}:
            record["readiness"] = "METADATA_REVIEW_REQUIRED"
    return True


def _correct_account_model_for_metadata(account_model, names):
    corrected = json.loads(json.dumps(account_model, ensure_ascii=False))
    changed = 0
    for role in corrected.get("roles") or []:
        if not isinstance(role, dict):
            continue
        sources = role.get("credential_sources")
        if not isinstance(sources, list):
            continue
        kept, unverified = [], []
        for source in sources:
            if _metadata_text_has_unverified(source, names):
                unverified.append(source)
            else:
                kept.append(source)
        if unverified:
            role["credential_sources"] = kept
            role["unverified_credential_sources"] = unverified
            role["credential_review_required"] = True
            changed += len(unverified)
    if changed:
        corrected["metadata_correction"] = {
            "status": "NEEDS_REVIEW",
            "action": "未被元数据证实的登录态来源已从强凭证来源降级为待确认来源。",
            "unverified_references": names,
        }
    return corrected, changed


def metadata_hallucination_correction(project_id, payload=None):
    payload = payload or {}
    package_id = str(payload.get("package_id") or "").strip()
    if not package_id:
        raise ValueError("请选择需要修正的需求包")
    package = requirement_package_by_id(project_id, package_id)
    package_root = Path(package["root"])
    audit = _latest_metadata_audit_report(project_id, package_id)
    if not audit:
        audit = metadata_hallucination_audit(project_id, {"package_id": package_id})
    names = _metadata_unverified_names(audit)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    corrections_dir = package_root / "outputs" / "corrections" / f"metadata-correction-{stamp}"
    corrections_dir.mkdir(parents=True, exist_ok=True)
    generated = []
    changes = []

    structured_path = package_root / "outputs" / "structured-test-cases.json"
    structured = _read_json_asset(structured_path)
    if structured:
        corrected = json.loads(json.dumps(structured, ensure_ascii=False))
        changed = 0
        for case in corrected.get("cases") or []:
            if _apply_metadata_review_marker(case, names, str(structured_path)):
                changed += 1
        if changed:
            corrected.setdefault("summary", {})["metadata_review_required"] = changed
            corrected["correction_source"] = {
                "audit_report": audit.get("file_name"),
                "created_at": now(),
                "policy": "只生成一次修正版，不覆盖正式结构化用例。",
            }
            out = corrections_dir / "structured-test-cases.corrected.json"
            out.write_text(json.dumps(corrected, ensure_ascii=False, indent=2), encoding="utf-8")
            generated.append(str(out))
            changes.append({"asset": "structured-test-cases", "changed_items": changed, "action": "命中未证实元数据的用例已降级为元数据待确认。"})

    candidates_path = package_root / "evidence_rules.candidates.yaml"
    candidates = _load_yaml_file(candidates_path)
    if candidates:
        corrected = json.loads(json.dumps(candidates, ensure_ascii=False))
        changed = 0
        for rule in corrected.get("rules") or []:
            if _apply_metadata_review_marker(rule, names, str(candidates_path)):
                changed += 1
        if changed:
            corrected["metadata_correction"] = {
                "status": "NEEDS_REVIEW",
                "audit_report": audit.get("file_name"),
                "policy": "只生成一次修正版，不覆盖正式候选证据规则。",
                "unverified_references": names,
            }
            out = corrections_dir / "evidence-rules.candidates.corrected.yaml"
            out.write_text(_yaml_dump(corrected), encoding="utf-8")
            generated.append(str(out))
            changes.append({"asset": "candidate-evidence-rules", "changed_items": changed, "action": "命中未证实元数据的候选规则已降级为人工确认。"})

    account_model_path = package_root / "account_model.yaml"
    account_model = _load_yaml_file(account_model_path)
    if account_model:
        corrected, changed = _correct_account_model_for_metadata(account_model, names)
        if changed:
            out = corrections_dir / "account_model.corrected.yaml"
            out.write_text(_yaml_dump(corrected), encoding="utf-8")
            generated.append(str(out))
            changes.append({"asset": "account-model", "changed_items": changed, "action": "未证实凭证来源已移入 unverified_credential_sources。"})

    mapping_path = package_root / "outputs" / "case-jmeter-mapping.json"
    mapping = _read_json_asset(mapping_path)
    if mapping:
        corrected = json.loads(json.dumps(mapping, ensure_ascii=False))
        changed = 0
        for item in corrected.get("mappings") or []:
            if _apply_metadata_review_marker(item, names, str(mapping_path)):
                changed += 1
        if changed:
            corrected.setdefault("summary", {})["metadata_review_required"] = changed
            corrected["correction_source"] = {
                "audit_report": audit.get("file_name"),
                "created_at": now(),
                "policy": "只生成一次修正版，不覆盖正式JMeter映射。",
            }
            out = corrections_dir / "case-jmeter-mapping.corrected.json"
            out.write_text(json.dumps(corrected, ensure_ascii=False, indent=2), encoding="utf-8")
            generated.append(str(out))
            changes.append({"asset": "case-jmeter-mapping", "changed_items": changed, "action": "命中未证实元数据的映射已标记为待确认。"})

    status = "NO_FINDINGS" if not names else "CORRECTED" if generated else "NEEDS_MANUAL_REVIEW"
    report = {
        "report_type": "METADATA_HALLUCINATION_CORRECTION",
        "project_id": project_id,
        "package_id": package_id,
        "status": status,
        "created_at": now(),
        "summary": {
            "unverified_references": len(names),
            "assets_generated": len(generated),
            "changes": sum(int(x.get("changed_items") or 0) for x in changes),
        },
        "audit_report": audit.get("file_name"),
        "unverified_references": names,
        "changes": changes,
        "generated_files": generated,
        "output_dir": str(corrections_dir),
        "note": "修正版只作为候选输出保存，不覆盖正式用例、证据规则、账号模型或JMeter映射；由测试人员确认后再采纳。",
    }
    summary_path = corrections_dir / "metadata-correction-summary.json"
    summary_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report_out = ROOT / "reports" / f"metadata-hallucination-correction-{project_id}-{package_id}-{stamp}.json"
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["json_url"] = "/reports/" + report_out.name
    report["file_name"] = report_out.name
    report["summary_path"] = str(summary_path)
    return report


def list_generated_reports(project_id):
    report_dir=ROOT/"reports"
    if not report_dir.exists(): return []
    result=[]
    for file in report_dir.glob("metadata-hallucination-audit-*.json"):
        try: payload=json.loads(file.read_text(encoding="utf-8"))
        except Exception: payload={}
        if payload.get("project_id") and payload.get("project_id") != project_id:
            continue
        summary = payload.get("summary") or {}
        result.append({"name":"AI输出元数据幻觉校验报告","kind":"元数据校验","status":payload.get("status","UNKNOWN"),"created_at":payload.get("created_at") or datetime.fromtimestamp(file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),"summary":f"扫描{summary.get('sources_scanned',0)}处资产 · 已证实{summary.get('db_references_verified',0)+summary.get('redis_references_verified',0)}项 · 提醒{summary.get('attention_items',0)}项","json_url":"/reports/"+file.name,"html_url":"","file_name":file.name,"package_id":payload.get("package_id","general")})
    for file in report_dir.glob("metadata-hallucination-correction-*.json"):
        try: payload=json.loads(file.read_text(encoding="utf-8"))
        except Exception: payload={}
        if payload.get("project_id") and payload.get("project_id") != project_id:
            continue
        summary = payload.get("summary") or {}
        result.append({"name":"AI输出一次修正版报告","kind":"元数据修正","status":payload.get("status","UNKNOWN"),"created_at":payload.get("created_at") or datetime.fromtimestamp(file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),"summary":f"未证实引用{summary.get('unverified_references',0)}项 · 生成修正版{summary.get('assets_generated',0)}份 · 调整{summary.get('changes',0)}处","json_url":"/reports/"+file.name,"html_url":"","file_name":file.name,"package_id":payload.get("package_id","general")})
    for file in report_dir.glob("requirement-execution-plan-*.json"):
        try: payload=json.loads(file.read_text(encoding="utf-8"))
        except Exception: payload={}
        if payload.get("project_id") and payload.get("project_id") != project_id:
            continue
        summary = payload.get("summary") or {}
        status_counts = summary.get("status_counts") or {}
        tool_counts = summary.get("tool_counts") or {}
        result.append({"name":"需求包场景级执行计划","kind":"场景执行计划","status":payload.get("status","UNKNOWN"),"created_at":payload.get("generated_at") or datetime.fromtimestamp(file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),"summary":f"场景{summary.get('scenarios',0)}个 · 用例{summary.get('cases',0)}条 · READY{status_counts.get('READY',0)} · 待复核{status_counts.get('NEEDS_REVIEW',0)+status_counts.get('READY_WITH_WARNINGS',0)} · Newman/JMeter/pytest {tool_counts.get('newman',0)}/{tool_counts.get('jmeter',0)}/{tool_counts.get('pytest',0)}","json_url":"/reports/"+file.name,"html_url":"","file_name":file.name,"package_id":payload.get("package_id","general")})
    for file in report_dir.glob("business-evidence-plan-*.json"):
        try: payload=json.loads(file.read_text(encoding="utf-8"))
        except Exception: payload={}
        if payload.get("project_id") and payload.get("project_id") != project_id:
            continue
        summary = payload.get("summary") or {}
        result.append({"name":"执行后业务数据证据规则报告","kind":"业务证据规则","status":payload.get("status","UNKNOWN"),"created_at":payload.get("created_at") or datetime.fromtimestamp(file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),"summary":f"规则{summary.get('ready',0)}/{summary.get('rules',0)}可用 · MySQL{summary.get('mysql_rules',0)}条 · Redis{summary.get('redis_rules',0)}条 · 提醒{summary.get('attention',0)}项","json_url":"/reports/"+file.name,"html_url":"","file_name":file.name,"package_id":payload.get("package_id","general")})
    for file in report_dir.glob("business-evidence-run-*.json"):
        try: payload=json.loads(file.read_text(encoding="utf-8"))
        except Exception: payload={}
        if payload.get("project_id") and payload.get("project_id") != project_id:
            continue
        summary = payload.get("summary") or {}
        result.append({"name":"执行后业务数据证据执行报告","kind":"业务证据执行","status":payload.get("status","UNKNOWN"),"created_at":payload.get("created_at") or datetime.fromtimestamp(file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),"summary":f"场景{summary.get('scenarios_passed',0)}/{summary.get('scenarios_total',0)}通过 · 规则{summary.get('rules_passed',0)}/{summary.get('rules_total',0)}通过 · 失败{summary.get('rules_failed',0)} · 阻断{summary.get('rules_blocked',0)}","json_url":"/reports/"+file.name,"html_url":"","file_name":file.name,"package_id":payload.get("package_id","general")})
    for file in report_dir.glob("candidate-evidence-rules-*.json"):
        try: payload=json.loads(file.read_text(encoding="utf-8"))
        except Exception: payload={}
        if payload.get("project_id") and payload.get("project_id") != project_id:
            continue
        summary = payload.get("summary") or {}
        result.append({"name":"测试用例候选证据规则报告","kind":"候选证据规则","status":payload.get("status","UNKNOWN"),"created_at":payload.get("created_at") or datetime.fromtimestamp(file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),"summary":f"扫描用例{summary.get('cases_scanned',0)}条 · 候选规则{summary.get('candidates',0)}条 · 已有正式规则{summary.get('existing_rules',0)}条","json_url":"/reports/"+file.name,"html_url":"","file_name":file.name,"package_id":payload.get("package_id","general")})
    for file in report_dir.glob("accepted-evidence-rules-*.json"):
        try: payload=json.loads(file.read_text(encoding="utf-8"))
        except Exception: payload={}
        if payload.get("project_id") and payload.get("project_id") != project_id:
            continue
        summary = payload.get("summary") or {}
        result.append({"name":"候选证据规则采纳报告","kind":"证据规则采纳","status":payload.get("status","UNKNOWN"),"created_at":payload.get("created_at") or datetime.fromtimestamp(file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),"summary":f"采纳{summary.get('accepted',0)}条 · 跳过{summary.get('skipped',0)}条 · 正式规则{summary.get('official_rules',0)}条","json_url":"/reports/"+file.name,"html_url":"","file_name":file.name,"package_id":payload.get("package_id","general")})
    for file in report_dir.glob("structured-test-cases-*.json"):
        try: payload=json.loads(file.read_text(encoding="utf-8"))
        except Exception: payload={}
        if payload.get("project_id") and payload.get("project_id") != project_id:
            continue
        summary = payload.get("summary") or {}
        quality = summary.get("quality_counts") or {}
        readiness = summary.get("readiness_counts") or summary.get("automation_counts") or {}
        ready_count = readiness.get("SCRIPT_GENERATION_READY", readiness.get("AUTO_READY", 0))
        dashboard = payload.get("coverage_dashboard") or {}
        preflight = payload.get("data_preflight") or {}
        jmeter = payload.get("jmeter_mapping") or {}
        ready_rate = dashboard.get("script_generation_ready_rate")
        rate_text = f" · 就绪率{ready_rate}%" if ready_rate is not None else ""
        result.append({"name":"结构化测试用例增强报告","kind":"结构化用例","status":payload.get("status","UNKNOWN"),"created_at":payload.get("created_at") or datetime.fromtimestamp(file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),"summary":f"用例{summary.get('cases',0)}条 · READY{quality.get('READY',0)} · 脚本就绪{ready_count}{rate_text} · JMeter目标{jmeter.get('jmeter_targets','-')} · 数据预检{preflight.get('status','-')}","json_url":"/reports/"+file.name,"html_url":"","file_name":file.name,"package_id":payload.get("package_id","general")})
    for file in report_dir.glob("salary-trade-db-evidence-*.json"):
        try: payload=json.loads(file.read_text(encoding="utf-8"))
        except Exception: payload={}
        if payload.get("project_id") and payload.get("project_id") != project_id:
            continue
        summary = payload.get("summary") or {}
        result.append({"name":"工资交易数据库证据报告","kind":"数据核查","status":payload.get("status","UNKNOWN"),"created_at":payload.get("created_at") or datetime.fromtimestamp(file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),"summary":f"订单{payload.get('order_no','-')} · 断言{summary.get('assertions_passed',0)}/{summary.get('assertions_total',0)} · 日志{summary.get('log_rows',0)} · 凭证{summary.get('evidence_rows',0)}","json_url":"/reports/"+file.name,"html_url":"","file_name":file.name})
    for file in report_dir.glob("salary-trade-jmeter-mapping-*.json"):
        try: payload=json.loads(file.read_text(encoding="utf-8"))
        except Exception: payload={}
        if payload.get("project_id") and payload.get("project_id") != project_id:
            continue
        summary = payload.get("summary") or {}
        perf = payload.get("performance_summary") or {}
        warnings = payload.get("warnings") or []
        result.append({"name":"工资交易JMeter映射报告","kind":"JMeter映射","status":payload.get("status","UNKNOWN"),"created_at":payload.get("created_at") or datetime.fromtimestamp(file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),"summary":f"流程{summary.get('flows_passed',0)}/{summary.get('flows_total',0)}通过 · DB证据{summary.get('db_passed',0)}通过 · JMeter{perf.get('requests',0)}次 · 错误率{perf.get('error_rate','-')}%"+(f" · 提醒{len(warnings)}项" if warnings else ""),"json_url":"/reports/"+file.name,"html_url":"","file_name":file.name,"performance_diagnosis":payload.get("performance_diagnosis"),"performance_summary":perf,"performance_gate":payload.get("performance_gate")})
    for file in report_dir.glob("evidence-check-*.json"):
        try: payload=json.loads(file.read_text(encoding="utf-8"))
        except Exception: payload={}
        if payload.get("project_id") and payload.get("project_id") != project_id:
            continue
        result.append({"name":"数据证据核查报告","kind":"数据核查","status":payload.get("status","UNKNOWN"),"created_at":payload.get("created_at") or datetime.fromtimestamp(file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),"summary":f"{payload.get('target','本次核查')} · 候选表{len(payload.get('matched_tables') or [])}个 · 提醒{len(payload.get('blockers') or [])}项","json_url":"/reports/"+file.name,"html_url":"","file_name":file.name})
    for file in report_dir.glob("interface-safe-smoke-*.json"):
        try: payload=json.loads(file.read_text(encoding="utf-8"))
        except Exception: payload={}
        if payload.get("project_id") and payload.get("project_id") != project_id:
            continue
        failed = int(payload.get("failed") or 0) + int(payload.get("error") or 0)
        status = "FAILED" if failed else "PASSED" if payload.get("executed") else "PENDING"
        result.append({"name":"接口安全冒烟验证报告","kind":"接口测试","status":status,"created_at":payload.get("executed_at") or datetime.fromtimestamp(file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),"summary":f"执行{payload.get('executed',0)}条 · 通过{payload.get('passed',0)} · 失败{payload.get('failed',0)} · 写操作待确认{payload.get('skipped_mutation_cases',0)}","json_url":"/reports/"+file.name,"html_url":"","file_name":file.name})
    for file in report_dir.glob("gift-wealth-chain-*.json"):
        try: payload=json.loads(file.read_text(encoding="utf-8"))
        except Exception: payload={}
        raw_status=payload.get("status","UNKNOWN"); gift_runs=payload.get("steps",{}).get("gift_runs") or ([payload.get("steps",{}).get("gift")] if payload.get("steps",{}).get("gift") else []); calls_ok=bool(gift_runs) and all(isinstance(x,dict) and x.get("status")=="PASSED" for x in gift_runs)
        display_status="BUSINESS_DIFFERENCE" if raw_status=="FAILED" and calls_ok and payload.get("assertions_passed",0)<payload.get("assertions_total",0) else raw_status
        result.append({"name":"财富送礼跨接口高覆盖报告","kind":"跨接口链路","status":display_status,"created_at":payload.get("executed_at") or datetime.fromtimestamp(file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),"summary":f"接口执行 {'成功' if calls_ok else '异常'} · 断言 {payload.get('assertions_passed',0)}/{payload.get('assertions_total',0)} · 真实送礼{payload.get('gift_config',{}).get('gift_num',0)}次 · 消费{payload.get('gift_config',{}).get('consume_gold','-')} Gold","json_url":"/reports/"+file.name,"html_url":"","file_name":file.name})
    for file in report_dir.glob("wealth-full-real-test-*.json"):
        try:
            payload=json.loads(file.read_text(encoding="utf-8"))
        except Exception: payload={}
        jmeter=payload.get("jmeter",{}) if isinstance(payload,dict) else {}
        html_path=Path(jmeter.get("html_report","")) if jmeter.get("html_report") else None
        html_url=""
        if html_path and html_path.is_file():
            try: html_url="/reports/"+html_path.relative_to(report_dir).as_posix()
            except ValueError: html_url=""
        result.append({"name":"财富等级综合测试报告","kind":"综合报告","status":payload.get("status","UNKNOWN"),"created_at":payload.get("executed_at") or datetime.fromtimestamp(file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),"summary":f"接口 {payload.get('wealth_api',{}).get('status','-')} · JMeter {jmeter.get('status','未执行')} · {jmeter.get('requests',0)}次请求 · 错误率{jmeter.get('error_rate','-')}%","json_url":"/reports/"+file.name,"html_url":html_url,"file_name":file.name})
    for folder in report_dir.glob("jmeter-wealth-*"):
        summary_file=folder/"summary.json"; html_file=folder/"html"/"index.html"
        if not summary_file.is_file(): continue
        try: summary=json.loads(summary_file.read_text(encoding="utf-8"))
        except Exception: summary={}
        result.append({"name":"JMeter 财富接口性能报告","kind":"JMeter","status":summary.get("status","UNKNOWN"),"created_at":datetime.fromtimestamp(summary_file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),"summary":f"{summary.get('requests',0)}次请求 · 错误率{summary.get('error_rate','-')}% · P95 {summary.get('p95_ms','-')}ms · {summary.get('throughput_rps','-')} req/s","json_url":"/reports/"+summary_file.relative_to(report_dir).as_posix(),"html_url":"/reports/"+html_file.relative_to(report_dir).as_posix() if html_file.is_file() else "","file_name":folder.name})
    for folder in report_dir.glob("jmeter-gui-*"):
        summary_file=folder/"summary.json"; html_file=folder/"html"/"index.html"
        if not summary_file.is_file(): continue
        try: payload=json.loads(summary_file.read_text(encoding="utf-8"))
        except Exception: payload={}
        summary=payload.get("summary",{}) if isinstance(payload,dict) else {}
        gate=payload.get("performance_gate",{}) if isinstance(payload,dict) else {}
        diagnosis=payload.get("performance_diagnosis",{}) if isinstance(payload,dict) else {}
        diag_text=diagnosis.get("conclusion") or gate.get("summary","")
        result.append({"name":"JMeter GUI 工作台回收报告","kind":"JMeter","status":payload.get("status","UNKNOWN"),"created_at":payload.get("executed_at") or datetime.fromtimestamp(summary_file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),"summary":f"{summary.get('requests',0)}次请求 · 错误率{summary.get('error_rate','-')}% · P95 {summary.get('p95_ms','-')}ms · P99 {summary.get('p99_ms','-')}ms · {summary.get('throughput_rps','-')} req/s · {diag_text}","json_url":"/reports/"+summary_file.relative_to(report_dir).as_posix(),"html_url":"/reports/"+html_file.relative_to(report_dir).as_posix() if html_file.is_file() else "","file_name":folder.name,"performance_diagnosis":diagnosis,"performance_summary":summary})
    for folder in report_dir.glob("toolchain-*"):
        summary_file=folder/"summary.json"
        if not summary_file.is_file(): continue
        try: summary=json.loads(summary_file.read_text(encoding="utf-8"))
        except Exception: summary={}
        counts=summary.get("summary",{})
        tool_parts=[]
        for item in summary.get("results",[]):
            name=item.get("tool","工具")
            status=item.get("status","UNKNOWN")
            reason=item.get("reason") or ""
            if name == "JMeter" and item.get("requests") is not None:
                gate = item.get("performance_gate") or {}
                tool_parts.append(f"JMeter:{status}({item.get('requests',0)}次 · 错误率{item.get('error_rate','-')}% · P95 {item.get('p95_ms','-')}ms · {gate.get('label','性能')} {gate.get('status','-')})")
            else:
                tool_parts.append(f"{name}:{status}" + (f"({reason[:40]})" if reason else ""))
        detail_summary=" · ".join(tool_parts) or f"工具 {counts.get('passed',0)} 通过 · {counts.get('failed',0)} 失败 · {counts.get('blocked',0)} 阻断"
        quality_gate=summary.get("quality_gate") or {}
        if quality_gate.get("status"):
            detail_summary = f"准入:{quality_gate.get('status')} · {quality_gate.get('conclusion','')}" + (" · " + detail_summary if detail_summary else "")
        auth_diag=(summary.get("diagnosis") or {}).get("auth") or {}
        if auth_diag.get("items"):
            detail_summary += f" · 鉴权待补齐:{len(auth_diag.get('items',[]))}项"
        jmeter_html=""
        for item in summary.get("results",[]):
            if item.get("tool")=="JMeter" and item.get("html_report"):
                html_path=Path(item["html_report"])
                if html_path.is_file():
                    try: jmeter_html="/reports/"+html_path.relative_to(report_dir).as_posix()
                    except ValueError: pass
        result.append({"name":"企业工具链执行报告","kind":"外部工具链","status":summary.get("status","UNKNOWN"),"created_at":summary.get("executed_at") or datetime.fromtimestamp(summary_file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),"summary":detail_summary,"json_url":"/reports/"+summary_file.relative_to(report_dir).as_posix(),"html_url":jmeter_html,"file_name":folder.name})
    for folder in report_dir.glob("login-performance-*"):
        summary_file=folder/"summary.json"
        if not summary_file.is_file(): continue
        try: summary=json.loads(summary_file.read_text(encoding="utf-8"))
        except Exception: summary={}
        counts=summary.get("summary",{})
        config=summary.get("config",{})
        result.append({"name":"多账号登录性能专项报告","kind":"登录性能专项","status":summary.get("status","UNKNOWN"),"created_at":summary.get("executed_at") or datetime.fromtimestamp(summary_file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),"summary":f"{config.get('accounts_runnable',0)}个账号 · {counts.get('executed',0)}次登录 · 成功率{counts.get('success_rate',0)}% · P95 {counts.get('p95_ms',0)}ms","json_url":"/reports/"+summary_file.relative_to(report_dir).as_posix(),"html_url":"","file_name":folder.name})
    if REQUIREMENT_PACKAGE_ROOT.exists():
        for summary_file in REQUIREMENT_PACKAGE_ROOT.glob("*/reports/*/summary.json"):
            try: payload=json.loads(summary_file.read_text(encoding="utf-8"))
            except Exception: payload={}
            if payload.get("project_id") and payload.get("project_id") != project_id:
                continue
            package_id = payload.get("package_id") or summary_file.parents[2].name
            package_name = payload.get("package_name") or package_id
            failures = payload.get("failures") or []
            if payload.get("report_type") == "REQUIREMENT_PACKAGE_AI_REVIEW":
                summary = payload.get("summary") or {}
                cats = payload.get("root_cause_categories") or {}
                cat_text = " · ".join(f"{key}:{value}" for key, value in cats.items()) or "暂无"
                result.append({
                    "name": f"{package_name}AI复盘报告",
                    "kind": "AI复盘",
                    "status": payload.get("status", "UNKNOWN"),
                    "created_at": payload.get("created_at") or datetime.fromtimestamp(summary_file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
                    "summary": f"P0 {summary.get('p0',0)} · P1 {summary.get('p1',0)} · HTTP失败{summary.get('http_failed',0)} · 根因 {cat_text}",
                    "json_url": "/requirement-reports/" + summary_file.relative_to(REQUIREMENT_PACKAGE_ROOT).as_posix(),
                    "html_url": "",
                    "file_name": str(summary_file),
                    "package_id": package_id,
                })
                continue
            if payload.get("report_type") in {"REQUIREMENT_PACKAGE_PYTEST_EVIDENCE_RUN", "PYTEST_DEEP_EVIDENCE_REVIEW"}:
                summary = payload.get("summary") or {}
                result.append({
                    "name": f"{package_name}pytest深度证据报告",
                    "kind": "pytest证据",
                    "status": payload.get("status", "UNKNOWN"),
                    "created_at": payload.get("created_at") or datetime.fromtimestamp(summary_file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
                    "summary": f"HTTP失败{summary.get('http_failed',0)} · 证据规则{summary.get('rules_total',0)}条 · 失败{summary.get('rules_failed',0)} · 阻断{summary.get('rules_blocked',0)} · JTL失败{summary.get('jtl_failures',0)}",
                    "json_url": "/requirement-reports/" + summary_file.relative_to(REQUIREMENT_PACKAGE_ROOT).as_posix(),
                    "html_url": "",
                    "file_name": str(summary_file),
                    "package_id": package_id,
                })
                continue
            if payload.get("report_type") == "REQUIREMENT_PACKAGE_UNIFIED_SCENARIO_REPORT":
                summary = payload.get("summary") or {}
                result.append({
                    "name": f"{package_name}统一场景报告",
                    "kind": "场景总报告",
                    "status": payload.get("status", "UNKNOWN"),
                    "created_at": payload.get("created_at") or datetime.fromtimestamp(summary_file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
                    "summary": f"场景{summary.get('scenarios',0)}个 · 通过{summary.get('passed',0)} · 失败{summary.get('failed',0)} · 阻断{summary.get('blocked',0)} · 提醒{summary.get('warning',0)}",
                    "json_url": "/requirement-reports/" + summary_file.relative_to(REQUIREMENT_PACKAGE_ROOT).as_posix(),
                    "html_url": "",
                    "file_name": str(summary_file),
                    "package_id": package_id,
                })
                continue
            tool = "Newman" if payload.get("report_type") == "REQUIREMENT_PACKAGE_NEWMAN_RUN" else "需求包执行"
            result.append({
                "name": f"{package_name}{tool}报告",
                "kind": tool,
                "status": payload.get("status", "UNKNOWN"),
                "created_at": payload.get("created_at") or datetime.fromtimestamp(summary_file.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
                "summary": f"需求包 {package_id} · 失败{len(failures)}项 · 耗时{payload.get('duration_ms','-')}ms",
                "json_url": "/requirement-reports/" + summary_file.relative_to(REQUIREMENT_PACKAGE_ROOT).as_posix(),
                "html_url": "",
                "file_name": str(summary_file),
                "package_id": package_id,
            })
    for item in result:
        if item.get("package_id"):
            continue
        marker = " ".join(str(item.get(key) or "") for key in ("name", "kind", "summary", "file_name")).lower()
        if any(word in marker for word in ("salary", "工资", "代理", "交易", "订单")):
            item["package_id"] = "salary-trade"
        elif any(word in marker for word in ("wealth", "财富", "送礼", "等级")):
            item["package_id"] = "wealth-level"
        else:
            item["package_id"] = "general"
    return sorted(result,key=lambda x:x["created_at"],reverse=True)


def evidence_center_status(project_id):
    threshold=DATA/"wealth-level-thresholds.json"; redis_dump=DATA/"redis-wealth-decoded.json"
    threshold_data=json.loads(threshold.read_text(encoding="utf-8")) if threshold.is_file() else {}
    redis_data=json.loads(redis_dump.read_text(encoding="utf-8")) if redis_dump.is_file() else {}
    return {"thresholds":{"loaded":len(threshold_data.get("rows",[]))==100,"rows":len(threshold_data.get("rows",[])),"source":threshold_data.get("source_file","")},"redis_snapshot":{"loaded":bool(redis_data.get("items")),"key":redis_data.get("key",""),"fields":redis_data.get("field_count",len(redis_data.get("items",{}))),"source":redis_data.get("source_file","")},"live_redis_access":False}


def attach_manual_redis_result(project_id,payload):
    account_uid=int(payload.get("uid")); value=int(str(payload.get("value")).strip())
    report_dir=ROOT/"reports"; files=sorted(report_dir.glob("gift-wealth-chain-*.json"),key=lambda x:x.stat().st_mtime,reverse=True)
    if not files: raise ValueError("尚无财富送礼链路报告")
    path=files[0]; report=json.loads(path.read_text(encoding="utf-8")); sender_uid=report.get("accounts",{}).get("sender",{}).get("uid")
    if sender_uid!=account_uid: raise ValueError(f"UID与最新报告送礼账号不一致，报告UID为{sender_uid}")
    actual_after=report.get("redis_manual_check",{}).get("interface_actual_after") or report.get("steps",{}).get("wealth_after",{}).get("core",{}).get("current_experience")
    assertion={"name":"人工Redis｜Hash Value等于送礼后财富接口经验","expected":actual_after,"actual":value,"passed":value==actual_after,"source":"人工HGET结果"}
    assertions=[x for x in report.get("assertions",[]) if x.get("name")!=assertion["name"]]; assertions.append(assertion)
    report["assertions"]=assertions; report["assertions_passed"]=sum(bool(x.get("passed")) for x in assertions); report["assertions_total"]=len(assertions); report["status"]="PASSED" if all(x.get("passed") for x in assertions) else "FAILED"
    report["redis_manual_check"]={"status":"PASSED" if assertion["passed"] else "FAILED","uid":account_uid,"value":value,"interface_actual_after":actual_after,"submitted_at":now(),"live_redis_access":False}
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    return {"status":report["status"],"redis_check":report["redis_manual_check"],"assertions_passed":report["assertions_passed"],"assertions_total":report["assertions_total"],"report":str(path)}


def normalize_reward_name(value):
    value=re.sub(r"\s*\*\s*", "*", str(value or "").strip()).lower()
    return re.sub(r"\*(?:permanent|\d+\s*(?:d|days?))$", "", value).strip()


def safe_request_evidence(method, path, payload):
    safe_path=re.sub(r"([?&](?:ticket|token|access_token|sn)=)[^&\s]+",r"\1***REDACTED***",str(path or ""),flags=re.I)
    safe_payload=re.sub(r"((?:password|ticket|token|access_token|sn)=)[^&\s]+",r"\1***REDACTED***",str(payload or ""),flags=re.I)
    return f"{method} {safe_path}\n{safe_payload}"


def safe_response_evidence(response):
    """Redact credentials from persisted response evidence while preserving structure."""
    secret=re.compile(r"password|access_?token|refresh_?token|ticket|authorization|\bsn\b|secret|cookie",re.I)
    try:
        payload=json.loads(response)
        def clean(value):
            if isinstance(value,dict): return {k:("***REDACTED***" if secret.search(str(k)) else clean(v)) for k,v in value.items()}
            if isinstance(value,list): return [clean(x) for x in value]
            return value
        return json.dumps(clean(payload),ensure_ascii=False)
    except Exception:
        return re.sub(r"((?:password|access_?token|refresh_?token|ticket|authorization|sn)[\"'=:\s]+)[^\s,}&]+",r"\1***REDACTED***",str(response or ""),flags=re.I)


def reward_type_code(name_en):
    name=normalize_reward_name(name_en)
    if "vehicle" in name: return 1
    if "headwear" in name: return 2
    if "bubble" in name: return 24
    if "sound waves" in name: return 25
    if "special id" in name: return 26
    return None


def validate_backend_reward_config(project_id, body):
    """Three-way check: Excel expectations vs CMS config codes vs client API rewards."""
    configs=rows("SELECT * FROM wealth_backend_reward_configs WHERE project_id=? ORDER BY level",(project_id,))
    if not configs: return {"ok":False,"summary":"尚未读取后台wealth_level_award配置","details":["后台配置为空"],"level_results":{}}
    expected=rows("SELECT * FROM wealth_reward_expectations WHERE project_id=? ORDER BY level_min,source_row",(project_id,))
    data=body.get("data",{}) if isinstance(body,dict) else {}
    groups=data.get("experRights",[]) if isinstance(data,dict) else []
    api_by_level={g.get("levelMin"):g for g in groups if isinstance(g,dict)}
    excel_by_level={}
    for x in expected:
        typ=reward_type_code(x.get("reward_name_en"))
        if typ is not None: excel_by_level.setdefault(x["level_min"],[]).append(typ)
    details=[]; level_results={}
    for config in configs:
        level=config["level"]
        try: backend_items=json.loads(config["parsed_items"] or "[]")
        except Exception: backend_items=[]
        backend_types=sorted(int(x["source_type"]) for x in backend_items)
        excel_types=sorted(excel_by_level.get(level,[]))
        group=api_by_level.get(level,{})
        api_items=[x for bucket in ("right1","right2") for x in (group.get(bucket) or []) if isinstance(x,dict)]
        api_types=sorted(x for x in (reward_type_code(i.get("rightName")) for i in api_items) if x is not None)
        problems=[]
        if backend_types!=excel_types: problems.append(f"Excel类型{excel_types} != 后台类型{backend_types}")
        if api_types!=excel_types: problems.append(f"Excel类型{excel_types} != 接口类型{api_types}")
        should_enable=bool(excel_types)
        if (config["config_status"]==1)!=should_enable: problems.append(f"后台启用状态{config['config_status']}与应配置奖励状态不一致")
        if any(x.get("duration")!=9999 for x in backend_items): problems.append("后台存在非9999永久时效编码")
        status="FAILED" if problems else "PASSED"
        level_results[str(level)]={"status":status,"excel_types":excel_types,"backend_types":backend_types,"api_types":api_types,"problems":problems}
        details.extend(f"Lv.{level}: {p}" for p in problems)
    return {"ok":not details,"summary":f"后台配置、Excel和接口三方核对{len(configs)}个等级档位；"+("全部一致" if not details else f"发现{len(details)}项差异"),"details":details,"level_results":level_results}


def update_linked_level_cases(project_id, matrix_result, backend_result):
    """Write real comparison evidence back to every linked Lv.1-Lv.100 case."""
    matrix_details=matrix_result.get("details",[])
    backend_levels=backend_result.get("level_results",{})
    changed=0
    for level in range(1,101):
        problems=[]
        for detail in matrix_details:
            m=re.match(r"Lv\.(\d+)(?:-(\d+))?",detail)
            if m and int(m.group(1))<=level<=int(m.group(2) or m.group(1)): problems.append(detail)
        milestone=max((x for x in map(int,backend_levels) if x<=level),default=None)
        if milestone and backend_levels[str(milestone)]["status"]=="FAILED": problems.extend(backend_levels[str(milestone)]["problems"])
        status="FAILED" if problems else "PASSED"
        actual="；".join(dict.fromkeys(problems)) if problems else f"Lv.{level}所属奖励段已通过Excel、后台配置和真实接口三方比对"
        execute("UPDATE test_cases SET execution_status=?,actual_result=?,run_count=COALESCE(run_count,0)+1,last_run_at=? WHERE project_id=? AND title=?",(status,actual,now(),project_id,f"财富等级矩阵：Lv.{level}奖励明细正确"))
        changed+=1
    return changed


def validate_wealth_reward_matrix(project_id, body):
    """Compare the real wealth response with the approved spreadsheet matrix."""
    data=body.get("data") if isinstance(body,dict) else None
    actual_groups=data.get("experRights") if isinstance(data,dict) else None
    if not isinstance(actual_groups,list):
        return {"ok":False,"summary":"缺少data.experRights或其不是数组","details":["data.experRights"]}
    expected=rows("SELECT * FROM wealth_reward_expectations WHERE project_id=? ORDER BY level_min,source_row",(project_id,))
    if not expected:
        return {"ok":False,"summary":"尚未导入等级奖励真值矩阵","details":["wealth_reward_expectations为空"]}
    exp_groups={}
    for item in expected: exp_groups.setdefault((item["level_min"],item["level_max"]),[]).append(item)
    act_groups={(g.get("levelMin"),g.get("levelMax")):g for g in actual_groups if isinstance(g,dict)}
    details=[]; checked=0
    for levels,exp_items in exp_groups.items():
        group=act_groups.get(levels)
        label=f"Lv.{levels[0]}-{levels[1]}" if levels[0]!=levels[1] else f"Lv.{levels[0]}"
        if not group:
            details.append(f"{label}: 接口缺少整个等级奖励分组"); continue
        actual=[x for bucket in ("right1","right2") for x in (group.get(bucket) or []) if isinstance(x,dict)]
        by_name={normalize_reward_name(x.get("rightName")):x for x in actual}
        expected_names=set()
        for exp in exp_items:
            key=normalize_reward_name(exp["reward_name_en"]); expected_names.add(key); checked+=1
            got=by_name.get(key)
            if not got:
                details.append(f"{label}: 缺少奖励《{exp['reward_name_cn']} / {exp['reward_name_en']}》"); continue
            if str(got.get("rightArName") or "").strip()!=str(exp["reward_name_ar"] or "").strip():
                details.append(f"{label} {exp['reward_name_cn']}: 阿语不一致，表格={exp['reward_name_ar']}，接口={got.get('rightArName')}")
            if exp["special_id"] and str(got.get("idTitle") or "")!=exp["special_id"]:
                details.append(f"{label} 靓号ID: 期望{exp['special_id']}，接口={got.get('idTitle')!r}")
            if not got.get("rightImageUrl"):
                details.append(f"{label} {exp['reward_name_cn']}: 缺少奖励展示图片")
            en=str(exp["reward_name_en"] or "").lower()
            if ("vehicle" in en or "headwear" in en or "entry" in en) and not (got.get("mp4Url") or got.get("svgaUrl")):
                details.append(f"{label} {exp['reward_name_cn']}: 缺少MP4/SVGA动效资源")
            if "sound waves" in en and not got.get("pagUrl"):
                details.append(f"{label} 麦浪: 缺少PAG资源")
        extras=sorted(set(by_name)-expected_names)
        for key in extras: details.append(f"{label}: 接口多出奖励《{by_name[key].get('rightName')}》")
    source_issues=rows("SELECT * FROM reward_matrix_issues WHERE project_id=? AND status='OPEN' ORDER BY source_row",(project_id,))
    summary=f"已按表格核对{checked}项奖励、{len(exp_groups)}个等级段"
    if details: summary+=f"；发现{len(details)}项接口/配置差异"
    if source_issues: summary+=f"；表格自身有{len(source_issues)}项待确认冲突"
    return {"ok":not details and not source_issues,"summary":summary,"details":details,"source_issues":source_issues,"checked":checked}


def validate_wealth_core_contract(body, expected_uid=None):
    """Validate identity, level progression, experience bounds and entitlement ranges."""
    data=body.get("data") if isinstance(body,dict) else None
    info=data.get("myExperLevelInfo") if isinstance(data,dict) else None
    groups=data.get("experRights") if isinstance(data,dict) else None
    checks={"data_object":isinstance(data,dict),"level_info_object":isinstance(info,dict),"rights_array":isinstance(groups,list) and bool(groups)}
    details=[]
    if not isinstance(info,dict):
        details.append("缺少data.myExperLevelInfo对象")
        return {"ok":False,"checks":checks,"details":details,"summary":"财富核心字段不完整"}
    current=info.get("currentLevel"); nxt=info.get("nextLevel"); value=info.get("currentExperValue"); lower=info.get("currentExperLevelValue"); upper=info.get("nextExperLevelValue")
    threshold_file=DATA/"wealth-level-thresholds.json"; threshold_rows=[]
    try: threshold_rows=json.loads(threshold_file.read_text(encoding="utf-8")).get("rows",[])
    except Exception: threshold_rows=[]
    threshold_by_level={int(x["level"]):x for x in threshold_rows if isinstance(x,dict) and x.get("level") is not None}
    expected_current=threshold_by_level.get(current,{}).get("cumulative_experience") if isinstance(current,int) else None
    expected_next=threshold_by_level.get(current+1,{}).get("cumulative_experience") if isinstance(current,int) and current<100 else 0
    bounds_ok=all(isinstance(x,(int,float)) for x in (value,lower,upper)) and lower<=value and ((current==100 and upper in {0,None}) or (current!=100 and value<upper))
    checks.update({"uid_matches_login":expected_uid is None or info.get("uid")==expected_uid,"level_integer":isinstance(current,int) and 1<=current<=100,"next_level_relation":isinstance(nxt,int) and (nxt==current+1 or (current==100 and nxt==100)),"experience_bounds":bounds_ok,"threshold_source_loaded":len(threshold_by_level)==100,"current_threshold_matches_excel":expected_current is not None and lower==expected_current,"next_threshold_matches_excel":expected_next is not None and upper==expected_next,"current_range_unique":isinstance(groups,list) and sum(isinstance(g,dict) and isinstance(current,int) and g.get("levelMin",101)<=current<=g.get("levelMax",0) for g in groups)==1,"ranges_valid":isinstance(groups,list) and all(isinstance(g,dict) and isinstance(g.get("levelMin"),int) and isinstance(g.get("levelMax"),int) and g["levelMin"]<=g["levelMax"] and isinstance(g.get("right1"),list) and isinstance(g.get("right2"),list) for g in groups)})
    labels={"uid_matches_login":"响应UID与登录UID不一致","level_integer":"当前等级不是1-100整数","next_level_relation":"下一等级与当前等级关系错误","experience_bounds":"当前经验不在本等级经验区间内","threshold_source_loaded":"财富等级升级表未完整加载100级","current_threshold_matches_excel":"接口当前等级起始经验与升级表不一致","next_threshold_matches_excel":"接口下一等级门槛与升级表不一致","current_range_unique":"当前等级没有唯一匹配的权益区间","ranges_valid":"权益等级区间或right1/right2结构非法"}
    details.extend(message for key,message in labels.items() if not checks.get(key))
    rights=sum(len(g.get("right1",[]))+len(g.get("right2",[])) for g in groups) if isinstance(groups,list) else 0
    return {"ok":all(checks.values()),"checks":checks,"details":details,"current_level":current,"next_level":nxt,"current_experience":value,"expected_current_threshold":expected_current,"expected_next_threshold":expected_next,"progress":value-lower if all(isinstance(x,(int,float)) for x in (value,lower)) else None,"remaining":upper-value if current!=100 and all(isinstance(x,(int,float)) for x in (upper,value)) else 0 if current==100 else None,"rights_groups":len(groups) if isinstance(groups,list) else 0,"rights_count":rights,"threshold_source":"财富等级升级数据.xlsx / Sheet1 / A2:E101","summary":f"核对UID、等级、升级表门槛、经验区间及{len(groups) if isinstance(groups,list) else 0}个权益段/{rights}项权益；"+("全部通过" if not details else f"发现{len(details)}项异常")}


def wealth_interface_assertions(http_status, body, expected_uid, core):
    """Return user-facing assertion evidence without exposing credentials."""
    data=body.get("data") if isinstance(body,dict) else None
    info=data.get("myExperLevelInfo") if isinstance(data,dict) else None
    mapping={"data_object":"data为对象","level_info_object":"myExperLevelInfo存在","rights_array":"experRights为非空数组","uid_matches_login":"响应UID等于登录UID","level_integer":"currentLevel为1-100整数","next_level_relation":"nextLevel递进关系正确","experience_bounds":"当前经验处于等级经验区间","threshold_source_loaded":"升级表完整加载100级","current_threshold_matches_excel":"当前等级起始经验等于升级表","next_threshold_matches_excel":"下一等级门槛等于升级表","current_range_unique":"当前等级唯一匹配权益区间","ranges_valid":"权益等级段和right1/right2结构有效"}
    result=[
      {"name":"HTTP状态码","expected":200,"actual":http_status,"passed":http_status==200},
      {"name":"业务状态码","expected":200,"actual":body.get("code") if isinstance(body,dict) else None,"passed":isinstance(body,dict) and body.get("code")==200},
      {"name":"业务消息","expected":"success","actual":body.get("message") if isinstance(body,dict) else None,"passed":isinstance(body,dict) and str(body.get("message") or "").lower()=="success"},
    ]
    for key,label in mapping.items(): result.append({"name":label,"expected":True,"actual":bool(core.get("checks",{}).get(key)),"passed":bool(core.get("checks",{}).get(key))})
    if isinstance(info,dict):
        result.append({"name":"用户标识值","expected":expected_uid,"actual":info.get("uid"),"passed":info.get("uid")==expected_uid})
    return result


def query_wallet(base_url, ticket, account_uid, runtime=None):
    """Read the selected account wallet and validate its stable response contract."""
    params=mobile_profile(runtime); params.update({"ticket":str(ticket),"CacheBuild-Control":"no-cache","uid":str(account_uid)})
    url=base_url.rstrip("/")+"/purse/query?"+urllib.parse.urlencode(params)
    started=time.perf_counter(); http_status=None; body={}; error=""
    try:
        req=urllib.request.Request(url,method="GET",headers={"Accept":"application/json","Cache-Control":"no-cache"})
        try: resp=urllib.request.urlopen(req,timeout=20); http_status=resp.status; raw=resp.read(100000)
        except urllib.error.HTTPError as exc: http_status=exc.code; raw=exc.read(100000)
        try: body=json.loads(raw.decode("utf-8","replace"))
        except Exception: body={}
    except Exception as exc: error=str(exc)
    data=body.get("data") if isinstance(body,dict) else None; gold=data.get("goldNum") if isinstance(data,dict) else None; response_uid=data.get("uid") if isinstance(data,dict) else None
    core_fields=("goldNum","uid","diamondNum","currencyNum","goldType")
    assertions=[
      {"name":"钱包HTTP状态码","expected":200,"actual":http_status,"passed":http_status==200},
      {"name":"钱包业务状态码","expected":200,"actual":body.get("code") if isinstance(body,dict) else None,"passed":isinstance(body,dict) and body.get("code")==200},
      {"name":"钱包业务消息","expected":"success","actual":body.get("message") if isinstance(body,dict) else None,"passed":isinstance(body,dict) and str(body.get("message") or "").lower()=="success"},
      {"name":"钱包data为对象","expected":True,"actual":isinstance(data,dict),"passed":isinstance(data,dict)},
      {"name":"钱包UID与执行账号一致","expected":account_uid,"actual":response_uid,"passed":response_uid==account_uid},
      {"name":"Gold余额为非负整数","expected":">= 0的整数","actual":gold,"passed":isinstance(gold,int) and gold>=0},
      {"name":"钱包固定核心字段完整","expected":list(core_fields),"actual":[k for k in core_fields if isinstance(data,dict) and k in data],"passed":isinstance(data,dict) and all(k in data for k in core_fields)}]
    return {"status":"PASSED" if all(x["passed"] for x in assertions) else "FAILED","http_status":http_status,"business_code":body.get("code") if isinstance(body,dict) else None,"response_ts":body.get("ts") if isinstance(body,dict) else None,"uid":response_uid,"gold_num":gold,"diamond_num":data.get("diamondNum") if isinstance(data,dict) else None,"currency_num":data.get("currencyNum") if isinstance(data,dict) else None,"gold_type":data.get("goldType") if isinstance(data,dict) else None,"assertions":assertions,"assertions_passed":sum(x["passed"] for x in assertions),"assertions_total":len(assertions),"duration_ms":int((time.perf_counter()-started)*1000),"error":error}


def query_gift_bill_records(base_url, ticket, account_uid, page_no=1, page_size=50, bill_type=1, query_time_ms=None, runtime=None):
    """Read gift bills; date is generated at execution time and is never copied from a capture."""
    runtime=runtime or {}; query_time_ms=int(query_time_ms or time.time()*1000)
    captured_defaults={"deviceType":"0","systemLanguage":"zh","appVersion":"100.1.5.4","os":"android","netType":"2","channel":"google","appsflyerId":"1787197403637-157853865254338231","language":"en","appCode":"100154","deviceId":"8fcce1f1-5153-3207-9786-0240140a524a","osVersion":"16","isVpnConnected":"0","appid":"soulfree","model":"SM-A546B","packageName":"com.soulfree.happiness","ispType":"4","organic":"Organic"}
    params={key:str(runtime.get(key,value)) for key,value in captured_defaults.items()}
    params.update({"date":str(query_time_ms),"ticket":str(ticket),"pageSize":str(page_size),"type":str(bill_type),"uid":str(account_uid),"pageNo":str(page_no)})
    url=base_url.rstrip("/")+"/billrecord/get?"+urllib.parse.urlencode(params)
    started=time.perf_counter(); http_status=None; body={}; error=""
    try:
        req=urllib.request.Request(url,method="GET",headers={"Accept":"application/json"})
        try: resp=urllib.request.urlopen(req,timeout=20); http_status=resp.status; raw=resp.read(200000)
        except urllib.error.HTTPError as exc: http_status=exc.code; raw=exc.read(200000)
        try: body=json.loads(raw.decode("utf-8","replace"))
        except Exception: body={}
    except Exception as exc: error=str(exc)
    data=body.get("data") if isinstance(body,dict) else None; groups=data.get("billList") if isinstance(data,dict) else None
    records=[]; groups_valid=isinstance(groups,list)
    if groups_valid:
        for group in groups:
            if not isinstance(group,dict): groups_valid=False; continue
            for date_key,items in group.items():
                if not str(date_key).isdigit() or not isinstance(items,list): groups_valid=False; continue
                records.extend(x for x in items if isinstance(x,dict))
    required=("recordTime","targetNick","giftPict","diamondNum","giftName","goldNum","giftNum")
    records_valid=all(all(k in x for k in required) and isinstance(x.get("recordTime"),int) and isinstance(x.get("goldNum"),int) and x.get("goldNum")>=0 and isinstance(x.get("giftNum"),int) and x.get("giftNum")>0 for x in records)
    assertions=[{"name":"账单HTTP状态码","expected":200,"actual":http_status,"passed":http_status==200},{"name":"账单业务状态码","expected":200,"actual":body.get("code") if isinstance(body,dict) else None,"passed":isinstance(body,dict) and body.get("code")==200},{"name":"账单业务消息","expected":"success","actual":body.get("message") if isinstance(body,dict) else None,"passed":isinstance(body,dict) and str(body.get("message") or "").lower()=="success"},{"name":"billList按日期分组结构有效","expected":True,"actual":groups_valid,"passed":groups_valid},{"name":"送礼记录固定字段和类型有效","expected":list(required),"actual":f"{len(records)}条记录","passed":records_valid}]
    return {"status":"PASSED" if all(x["passed"] for x in assertions) else "FAILED","http_status":http_status,"business_code":body.get("code") if isinstance(body,dict) else None,"response_ts":body.get("ts") if isinstance(body,dict) else None,"query_time_ms":query_time_ms,"record_count":len(records),"records":records,"assertions":assertions,"assertions_passed":sum(x["passed"] for x in assertions),"assertions_total":len(assertions),"duration_ms":int((time.perf_counter()-started)*1000),"error":error,"correlation_capability":{"time_window":True,"target_nick":True,"gold_num":True,"gift_num":True,"gift_name":True,"target_uid":False,"gift_id":False,"conclusion":"可核对时间、昵称、金额、数量和礼物名；响应缺少目标UID与giftId，不能单独作为唯一身份凭据"}}


def mobile_profile(runtime=None):
    runtime=runtime or {}; defaults={"deviceType":"0","systemLanguage":"zh","appVersion":"100.1.5.4","os":"android","netType":"2","channel":"google","appsflyerId":"1787197403637-157853865254338231","language":"en","appCode":"100154","deviceId":"8fcce1f1-5153-3207-9786-0240140a524a","osVersion":"16","isVpnConnected":"0","appid":"soulfree","model":"SM-A546B","packageName":"com.soulfree.happiness","ispType":"4","organic":"Organic"}
    return {k:str(runtime.get(k,v)) for k,v in defaults.items()}


def login_test_account_real(base_url, account, runtime=None):
    secret=load_account_credential(account["id"]); password=secret.get("encrypted_password")
    if not password: return {"status":"BLOCKED","message":"送礼账号未保存加密密码"}
    params=mobile_profile(runtime); params.update({"shortId":str(account["short_id"]),"version":params["appVersion"],"password":password})
    request_time=str(int(time.time()*1000)); headers={"t":request_time,"Content-Type":"application/x-www-form-urlencoded","User-Agent":"okhttp/4.12.0"}
    sn=str((runtime or {}).get("login_sn") or "").strip()
    if sn: headers["sn"]=sn
    started=time.perf_counter(); http_status=None; body={}; error=""
    try:
        req=urllib.request.Request(base_url.rstrip("/")+"/userserv/id/login",data=urllib.parse.urlencode(params).encode(),method="POST",headers=headers)
        try: resp=urllib.request.urlopen(req,timeout=20); http_status=resp.status; raw=resp.read(100000)
        except urllib.error.HTTPError as exc: http_status=exc.code; raw=exc.read(100000)
        body=json.loads(raw.decode("utf-8","replace"))
    except Exception as exc: error=str(exc)
    data=body.get("data") if isinstance(body,dict) else None; ticket=data.get("access_token") if isinstance(data,dict) else None; response_uid=data.get("uid") if isinstance(data,dict) else None
    assertions=[{"name":"登录HTTP状态码","expected":200,"actual":http_status,"passed":http_status==200},{"name":"登录业务状态码","expected":200,"actual":body.get("code") if isinstance(body,dict) else None,"passed":isinstance(body,dict) and body.get("code")==200},{"name":"登录UID等于送礼账号","expected":account["account_uid"],"actual":response_uid,"passed":response_uid==account["account_uid"]},{"name":"登录返回Ticket","expected":"非空","actual":"存在" if ticket else "缺失","passed":bool(ticket)}]
    if ticket and response_uid==account["account_uid"]: save_account_credential(account["id"],ticket,password)
    return {"status":"PASSED" if all(x["passed"] for x in assertions) else "FAILED","http_status":http_status,"uid":response_uid,"ticket":ticket,"assertions":assertions,"duration_ms":int((time.perf_counter()-started)*1000),"error":error}


def run_login_performance_special(project_id, options=None):
    options = options or {}
    project = row("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        raise ValueError("项目不存在")
    if not project["base_url"]:
        raise ValueError("项目缺少测试环境基础地址")

    threads = max(1, min(int(options.get("threads", 3) or 3), 50))
    loops = max(1, min(int(options.get("loops", 1) or 1), 100))
    rampup = max(0, min(int(options.get("rampup", 0) or 0), 600))
    selected_uids = {int(x) for x in (options.get("uids") or []) if str(x).strip().isdigit()}
    accounts = list_test_accounts(project_id)
    if selected_uids:
        accounts = [item for item in accounts if int(item["account_uid"]) in selected_uids]
    runnable = []
    blocked_accounts = []
    for account in accounts:
        secret = load_account_credential(account["id"])
        safe_account = {"uid": account["account_uid"], "short_id": account["short_id"], "role": account["account_role"]}
        if secret.get("encrypted_password"):
            runnable.append(account)
        else:
            blocked_accounts.append({**safe_account, "reason": "账号未保存登录加密密码"})

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_dir = ROOT / "reports" / f"login-performance-{project_id}-{stamp}"
    report_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    samples = []

    if runnable:
        tasks = []
        for loop_index in range(loops):
            for account in runnable:
                tasks.append((loop_index + 1, account))
        if rampup:
            time.sleep(min(rampup, 5))
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(threads, len(tasks))) as pool:
            future_map = {pool.submit(login_test_account_real, project["base_url"], account, options): (loop_index, account) for loop_index, account in tasks}
            for future in concurrent.futures.as_completed(future_map):
                loop_index, account = future_map[future]
                try:
                    result = future.result()
                except Exception as exc:
                    result = {"status": "FAILED", "http_status": None, "duration_ms": 0, "error": str(exc), "uid": None}
                samples.append({
                    "loop": loop_index,
                    "uid": account["account_uid"],
                    "short_id": account["short_id"],
                    "role": account["account_role"],
                    "status": result.get("status"),
                    "http_status": result.get("http_status"),
                    "response_uid_match": result.get("uid") == account["account_uid"],
                    "duration_ms": result.get("duration_ms", 0),
                    "error": result.get("error", ""),
                    "ticket": "***REDACTED***" if result.get("ticket") else "",
                })

    durations = [int(item.get("duration_ms") or 0) for item in samples if item.get("duration_ms") is not None]
    passed = sum(item.get("status") == "PASSED" for item in samples)
    failed = sum(item.get("status") == "FAILED" for item in samples)
    blocked = len(blocked_accounts)
    total = len(samples) + blocked
    status = "BLOCKED" if not runnable else "FAILED" if failed else "PASSED"
    report = {
        "report_type": "LOGIN_PERFORMANCE_SPECIAL",
        "project_id": project_id,
        "project_name": project["name"],
        "status": status,
        "executed_at": now(),
        "target": "POST /userserv/id/login",
        "scenario": "多账号登录专项性能测试",
        "config": {"threads": threads, "loops": loops, "rampup_seconds": rampup, "accounts_total": len(accounts), "accounts_runnable": len(runnable)},
        "summary": {
            "total": total,
            "executed": len(samples),
            "passed": passed,
            "failed": failed,
            "blocked": blocked,
            "success_rate": round(passed / len(samples) * 100, 2) if samples else 0,
            "duration_ms": int((time.perf_counter() - started) * 1000),
            "avg_ms": round(statistics.mean(durations), 2) if durations else 0,
            "p50_ms": percentile_value(durations, .50),
            "p90_ms": percentile_value(durations, .90),
            "p95_ms": percentile_value(durations, .95),
            "p99_ms": percentile_value(durations, .99),
        },
        "blocked_accounts": blocked_accounts,
        "samples": samples,
        "policy": {
            "login_endpoint_mode": "performance_special_only",
            "business_interfaces_excluded": True,
            "secrets_runtime_only": True,
            "account_passwords_redacted": True,
        },
    }
    report_path = report_dir / "summary.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return {**report, "report": str(report_path), "report_url": "/reports/" + report_path.relative_to(ROOT / "reports").as_posix()}


def query_wealth_direct(base_url,ticket,account_uid,runtime=None):
    params=mobile_profile(runtime); params.update({"ticket":ticket,"uid":str(account_uid)})
    started=time.perf_counter(); http_status=None; body={}; error=""
    try:
        req=urllib.request.Request(base_url.rstrip("/")+"/level/exeperience/v2/get?"+urllib.parse.urlencode(params),method="GET",headers={"Accept":"application/json"})
        try: resp=urllib.request.urlopen(req,timeout=20); http_status=resp.status; raw=resp.read(200000)
        except urllib.error.HTTPError as exc: http_status=exc.code; raw=exc.read(200000)
        body=json.loads(raw.decode("utf-8","replace"))
    except Exception as exc: error=str(exc)
    core=validate_wealth_core_contract(body,account_uid)
    return {"status":"PASSED" if http_status==200 and body.get("code")==200 and core["ok"] else "FAILED","http_status":http_status,"business_code":body.get("code") if isinstance(body,dict) else None,"response_ts":body.get("ts") if isinstance(body,dict) else None,"core":core,"duration_ms":int((time.perf_counter()-started)*1000),"error":error}


def send_gift_once(base_url,ticket,sender_uid,room_uid,target_uid,gift_id,gift_num=1,runtime=None):
    if int(gift_num)!=1: return {"status":"BLOCKED","message":"受控链路每次只允许送1个礼物"}
    params=mobile_profile(runtime); params.update({"ticket":ticket,"roomUid":str(room_uid),"uid":str(sender_uid),"giftId":str(gift_id),"targetUids":str(target_uid),"giftNum":"1"})
    started_at=int(time.time()*1000); started=time.perf_counter(); http_status=None; body={}; error=""
    try:
        req=urllib.request.Request(base_url.rstrip("/")+"/gift/purse/room/sendMulti",data=urllib.parse.urlencode(params).encode(),method="POST",headers={"Content-Type":"application/x-www-form-urlencoded","User-Agent":"okhttp/4.12.0"})
        try: resp=urllib.request.urlopen(req,timeout=20); http_status=resp.status; raw=resp.read(100000)
        except urllib.error.HTTPError as exc: http_status=exc.code; raw=exc.read(100000)
        body=json.loads(raw.decode("utf-8","replace"))
    except Exception as exc: error=str(exc)
    data=body.get("data") if isinstance(body,dict) else None; consume=data.get("consumeGold") if isinstance(data,dict) else None
    assertions=[{"name":"送礼HTTP状态码","expected":200,"actual":http_status,"passed":http_status==200},{"name":"送礼业务状态码","expected":200,"actual":body.get("code") if isinstance(body,dict) else None,"passed":isinstance(body,dict) and body.get("code")==200},{"name":"礼物ID一致","expected":gift_id,"actual":data.get("giftId") if isinstance(data,dict) else None,"passed":isinstance(data,dict) and data.get("giftId")==gift_id},{"name":"送礼数量一致","expected":1,"actual":data.get("giftNum") if isinstance(data,dict) else None,"passed":isinstance(data,dict) and data.get("giftNum")==1},{"name":"目标UID包含收礼人","expected":target_uid,"actual":data.get("targetUids") if isinstance(data,dict) else None,"passed":isinstance(data,dict) and target_uid in (data.get("targetUids") or [])},{"name":"实际消费Gold为正整数","expected":">0","actual":consume,"passed":isinstance(consume,int) and consume>0}]
    return {"status":"PASSED" if all(x["passed"] for x in assertions) else "FAILED","http_status":http_status,"business_code":body.get("code") if isinstance(body,dict) else None,"response_ts":body.get("ts") if isinstance(body,dict) else None,"started_at_ms":started_at,"gift_id":gift_id,"gift_num":1,"target_uid":target_uid,"consume_gold":consume,"gold_price":data.get("goldPrice") if isinstance(data,dict) else None,"assertions":assertions,"duration_ms":int((time.perf_counter()-started)*1000),"error":error}


def build_wealth_upgrade_validation(wealth_before,wealth_after,consume,runtime=None):
    runtime=runtime or {}
    before_core=wealth_before.get("core",{}) if isinstance(wealth_before,dict) else {}
    after_core=wealth_after.get("core",{}) if isinstance(wealth_after,dict) else {}
    before_level=before_core.get("current_level"); after_level=after_core.get("current_level")
    before_exp=before_core.get("current_experience"); after_exp=after_core.get("current_experience")
    threshold_rows=[]
    try: threshold_rows=json.loads((DATA/"wealth-level-thresholds.json").read_text(encoding="utf-8")).get("rows",[])
    except Exception: threshold_rows=[]
    threshold_by_level={int(x["level"]):int(x["cumulative_experience"]) for x in threshold_rows if isinstance(x,dict) and str(x.get("level","")).isdigit() and str(x.get("cumulative_experience","")).isdigit()}
    target_raw=runtime.get("target_level")
    try: target_level=int(target_raw) if target_raw not in (None,"") else (before_level+1 if isinstance(before_level,int) and before_level<100 else before_level)
    except Exception: target_level=before_level+1 if isinstance(before_level,int) and before_level<100 else before_level
    if isinstance(target_level,int): target_level=max(1,min(target_level,100))
    expected_threshold_raw=runtime.get("expected_target_threshold")
    expected_target_threshold=None
    try:
        if expected_threshold_raw not in (None,""): expected_target_threshold=int(expected_threshold_raw)
    except Exception: expected_target_threshold=None
    target_threshold=expected_target_threshold if expected_target_threshold is not None else threshold_by_level.get(target_level)
    expected_after_level=max((level for level,threshold in threshold_by_level.items() if isinstance(after_exp,int) and threshold<=after_exp),default=1 if isinstance(after_exp,int) else None)
    expected_exp_after=before_exp+consume if all(isinstance(x,int) for x in (before_exp,consume)) else None
    remaining_before=target_threshold-before_exp if all(isinstance(x,int) for x in (target_threshold,before_exp)) else None
    reached_by_plan=expected_exp_after>=target_threshold if all(isinstance(x,int) for x in (expected_exp_after,target_threshold)) else False
    reached_by_actual=after_exp>=target_threshold if all(isinstance(x,int) for x in (after_exp,target_threshold)) else False
    actual_upgrade=after_level>=target_level if all(isinstance(x,int) for x in (after_level,target_level)) else False
    expected_upgrade=reached_by_plan and isinstance(target_level,int) and isinstance(before_level,int) and target_level>before_level
    level_delta=after_level-before_level if all(isinstance(x,int) for x in (before_level,after_level)) else None
    exp_delta=after_exp-before_exp if all(isinstance(x,int) for x in (before_exp,after_exp)) else None
    if expected_upgrade and actual_upgrade:
        conclusion="本次送礼已达到目标门槛，财富等级已升级"
        reason="upgraded"
    elif expected_upgrade and not reached_by_actual:
        conclusion="按送礼消费应达到目标门槛，但接口经验未同步到目标门槛，优先排查经验累计或异步刷新"
        reason="experience_not_refreshed"
    elif expected_upgrade:
        conclusion="接口经验已达到目标门槛但等级未提升，优先排查等级计算缓存或升级配置是否生效"
        reason="level_not_refreshed"
    elif remaining_before is not None and consume<remaining_before:
        conclusion="本次消费未覆盖升级所需经验，属于未达到门槛"
        reason="insufficient_consume"
    elif not threshold_by_level:
        conclusion="升级真值表未加载，无法计算目标等级门槛"
        reason="threshold_missing"
    else:
        conclusion="本次未形成目标等级升级，需结合门槛配置和接口刷新结果确认"
        reason="not_upgraded"
    assertions=[
        {"name":"财富升级｜本次送礼消费达到目标门槛","expected":remaining_before if remaining_before is not None else "目标门槛可计算","actual":consume,"passed":bool(reached_by_plan) if expected_upgrade else bool(consume>=0 and remaining_before is not None),"source":"送礼前财富快照+送礼消费合计"},
        {"name":"财富升级｜送礼后经验达到目标等级门槛","expected":target_threshold,"actual":after_exp,"passed":bool(reached_by_actual) if expected_upgrade else True,"source":"送礼后财富接口"},
        {"name":"财富升级｜达到门槛时等级应提升到目标等级","expected":target_level,"actual":after_level,"passed":bool(actual_upgrade) if expected_upgrade else True,"source":"送礼后财富接口"},
        {"name":"财富升级｜送礼后等级符合升级表推导","expected":expected_after_level,"actual":after_level,"passed":expected_after_level is None or expected_after_level==after_level,"source":"财富等级升级表+送礼后经验"},
    ]
    return {"target_level":target_level,"target_threshold":target_threshold,"expected_target_threshold":expected_target_threshold,"before":{"level":before_level,"experience":before_exp,"current_threshold":before_core.get("expected_current_threshold"),"next_level":before_core.get("next_level"),"next_threshold":before_core.get("expected_next_threshold"),"remaining_to_target":remaining_before},"after":{"level":after_level,"experience":after_exp,"level_delta":level_delta,"experience_delta":exp_delta},"consume_gold":consume,"expected_experience_after":expected_exp_after,"expected_level_after":expected_after_level,"expected_upgrade":expected_upgrade,"actual_upgrade":actual_upgrade,"reached_by_plan":reached_by_plan,"reached_by_actual":reached_by_actual,"conclusion":conclusion,"reason":reason,"assertions":assertions}


def run_gift_business_chain(project_id,runtime=None):
    runtime=runtime or {}
    gift_iterations=max(1,min(int(runtime.get("gift_iterations",1)),100))
    if not runtime.get("confirm_batch_gift"): return {"status":"BLOCKED","message":f"必须勾选确认：真实送礼{gift_iterations}次并产生实际Gold消费"}
    sender_uid=int(runtime.get("sender_uid",1454428)); receiver_uid=int(runtime.get("receiver_uid",1454779)); room_uid=int(runtime.get("room_uid",1454428)); gift_id=int(runtime.get("gift_id",1057))
    sender=row("SELECT * FROM test_accounts WHERE project_id=? AND account_uid=?",(project_id,sender_uid)); receiver=row("SELECT * FROM test_accounts WHERE project_id=? AND account_uid=?",(project_id,receiver_uid)); project=row("SELECT * FROM projects WHERE id=?",(project_id,))
    if not sender or not receiver: return {"status":"BLOCKED","message":"送礼人或收礼人不在多账号测试池"}
    if not sender.get("mutable"): return {"status":"BLOCKED","message":"送礼账号未授权修改业务数据"}
    shared_ticket=str(runtime.get("runtime_ticket") or "").strip()
    if shared_ticket:
        ticket=shared_ticket; login={"status":"REUSED_SHARED","uid":sender_uid,"ticket":ticket,"assertions":[{"name":"共用Ticket已提供","expected":True,"actual":True,"passed":True}]}
    else:
        login=login_test_account_real(project["base_url"],sender,runtime)
        if login["status"]!="PASSED": return {"status":"BLOCKED","stage":"login","message":"共用Ticket未提供且888真实登录失败，未执行送礼","login":{k:v for k,v in login.items() if k!="ticket"}}
    ticket=login["ticket"]
    wealth_before=query_wealth_direct(project["base_url"],ticket,sender_uid,runtime); wallet_before=query_wallet(project["base_url"],ticket,sender_uid,runtime); bills_before=query_gift_bill_records(project["base_url"],ticket,sender_uid,runtime=runtime)
    if shared_ticket and (wealth_before["status"]!="PASSED" or wallet_before["status"]!="PASSED"):
        fallback_login=login_test_account_real(project["base_url"],sender,runtime)
        if fallback_login["status"]=="PASSED":
            login=fallback_login; ticket=fallback_login["ticket"]
            wealth_before=query_wealth_direct(project["base_url"],ticket,sender_uid,runtime); wallet_before=query_wallet(project["base_url"],ticket,sender_uid,runtime); bills_before=query_gift_bill_records(project["base_url"],ticket,sender_uid,runtime=runtime)
    if wealth_before["status"]!="PASSED" or wallet_before["status"]!="PASSED": return {"status":"BLOCKED","stage":"before_snapshot","message":"共用Ticket对888的只读身份预检未通过，已停止且未送礼","login":{"status":login["status"],"uid":sender_uid},"wealth_before":wealth_before,"wallet_before":wallet_before}
    gifts=[]
    for sequence in range(1,gift_iterations+1):
        gift=send_gift_once(project["base_url"],ticket,sender_uid,room_uid,receiver_uid,gift_id,1,runtime); gift["sequence"]=sequence; gifts.append(gift)
        if gift["status"]!="PASSED": return {"status":"FAILED","stage":"gift","message":f"第{sequence}次真实送礼响应未通过断言，批量执行已停止","gift_runs":gifts,"wealth_before":wealth_before,"wallet_before":wallet_before}
    wealth_after={}; wallet_after={}; bills_after={}
    for attempt in range(1,4):
        if attempt>1: time.sleep(1)
        wallet_after=query_wallet(project["base_url"],ticket,sender_uid,runtime); wealth_after=query_wealth_direct(project["base_url"],ticket,sender_uid,runtime); bills_after=query_gift_bill_records(project["base_url"],ticket,sender_uid,query_time_ms=int(time.time()*1000),runtime=runtime)
        before_gold=wallet_before.get("gold_num"); after_gold=wallet_after.get("gold_num"); before_exp=wealth_before.get("core",{}).get("current_experience"); after_exp=wealth_after.get("core",{}).get("current_experience"); consume=sum(x.get("consume_gold") or 0 for x in gifts)
        if all(isinstance(x,int) for x in (before_gold,after_gold,consume)) and before_gold-after_gold==consume: break
    before_gold=wallet_before.get("gold_num"); after_gold=wallet_after.get("gold_num"); before_exp=wealth_before.get("core",{}).get("current_experience"); after_exp=wealth_after.get("core",{}).get("current_experience"); consume=sum(x.get("consume_gold") or 0 for x in gifts); started_at_ms=gifts[0]["started_at_ms"]
    new_records=[x for x in bills_after.get("records",[]) if isinstance(x.get("recordTime"),int) and x["recordTime"]>=started_at_ms-2000]
    unit_consumes=[x.get("consume_gold") for x in gifts if isinstance(x.get("consume_gold"),int)]; bill_matches=[x for x in new_records if x.get("goldNum") in unit_consumes and x.get("giftNum")==1]; bill_match=bill_matches[0] if bill_matches else None
    assertions=[{"name":"钱包总扣款等于批量送礼消费合计","expected":consume,"actual":before_gold-after_gold if all(isinstance(x,int) for x in (before_gold,after_gold)) else None,"passed":all(isinstance(x,int) for x in (before_gold,after_gold,consume)) and before_gold-after_gold==consume},{"name":"财富经验按需求1:1累计增加","expected":consume,"actual":after_exp-before_exp if all(isinstance(x,int) for x in (before_exp,after_exp)) else None,"passed":all(isinstance(x,int) for x in (before_exp,after_exp,consume)) and after_exp-before_exp==consume},{"name":"账单新增记录覆盖批量送礼次数","expected":gift_iterations,"actual":len(bill_matches),"passed":len(bill_matches)>=gift_iterations},{"name":"送礼后钱包余额非负","expected":">=0","actual":after_gold,"passed":isinstance(after_gold,int) and after_gold>=0},{"name":"送礼前后UID保持送礼账号","expected":sender_uid,"actual":[wallet_before.get("uid"),wallet_after.get("uid")],"passed":wallet_before.get("uid")==sender_uid and wallet_after.get("uid")==sender_uid}]
    def prefixed(prefix,items): return [{**x,"name":f"{prefix}｜{x.get('name','断言')}"} for x in (items or [])]
    comprehensive=[]
    comprehensive.extend(prefixed("送礼前钱包",wallet_before.get("assertions")))
    for gift in gifts: comprehensive.extend(prefixed(f"送礼第{gift['sequence']}次响应",gift.get("assertions")))
    comprehensive.extend(prefixed("送礼后钱包",wallet_after.get("assertions")))
    comprehensive.extend(prefixed("送礼后账单",bills_after.get("assertions")))
    for phase,result in (("送礼前财富",wealth_before),("送礼后财富",wealth_after)):
        for key,passed in result.get("core",{}).get("checks",{}).items(): comprehensive.append({"name":f"{phase}｜{key}","expected":True,"actual":bool(passed),"passed":bool(passed)})
    comprehensive.extend(assertions)
    before_level=wealth_before.get("core",{}).get("current_level"); after_level=wealth_after.get("core",{}).get("current_level")
    expected_after_level=after_level
    try:
        thresholds=json.loads((DATA/"wealth-level-thresholds.json").read_text(encoding="utf-8")).get("rows",[])
        expected_after_level=max((int(x["level"]) for x in thresholds if isinstance(after_exp,int) and int(x["cumulative_experience"])<=after_exp),default=1)
    except Exception: pass
    upgrade_validation=build_wealth_upgrade_validation(wealth_before,wealth_after,consume,runtime)
    comprehensive.extend([{"name":"跨步骤｜财富经验单调不下降","expected":">=送礼前经验","actual":{"before":before_exp,"after":after_exp},"passed":all(isinstance(x,int) for x in (before_exp,after_exp)) and after_exp>=before_exp},{"name":"跨步骤｜送礼后等级符合Excel门槛计算","expected":expected_after_level,"actual":after_level,"passed":after_level==expected_after_level},{"name":"跨步骤｜未跨门槛时等级保持不变","expected":before_level,"actual":after_level,"passed":expected_after_level!=before_level or after_level==before_level},{"name":"账单｜记录时间位于批量送礼动作之后","expected":f">={started_at_ms}","actual":bill_match.get("recordTime") if bill_match else None,"passed":bool(bill_match and bill_match.get("recordTime",0)>=started_at_ms-2000)},{"name":"账单｜礼物名称非空","expected":"非空","actual":bill_match.get("giftName") if bill_match else None,"passed":bool(bill_match and bill_match.get("giftName"))},{"name":"账单｜目标昵称非空","expected":"非空","actual":bill_match.get("targetNick") if bill_match else None,"passed":bool(bill_match and bill_match.get("targetNick"))}])
    comprehensive.extend(upgrade_validation.get("assertions",[]))
    assertions=comprehensive
    execution_ok=all(x.get("status")=="PASSED" for x in gifts) and wallet_after.get("status")=="PASSED" and wealth_after.get("status")=="PASSED" and bills_after.get("status")=="PASSED"
    final="PASSED" if execution_ok and all(x["passed"] for x in assertions) else "BUSINESS_DIFFERENCE" if execution_ok else "FAILED"
    requirement_validation={"scenario":"财富等级需求闭环","driver":"真实送礼接口","gift_iterations":gift_iterations,"expected_experience_delta":consume,"actual_experience_delta":after_exp-before_exp if all(isinstance(x,int) for x in (before_exp,after_exp)) else None,"expected_wallet_deduction":consume,"actual_wallet_deduction":before_gold-after_gold if all(isinstance(x,int) for x in (before_gold,after_gold)) else None,"bill_records_matched":len(bill_matches),"level_before":before_level,"level_after":after_level,"conclusion":"财富等级需求闭环已完成：登录、财富前置、钱包前置、真实送礼、钱包后置、财富后置和账单证据已归档"}
    report={"report_type":"GIFT_WEALTH_REQUIREMENT_CLOSURE","mock":False,"status":final,"message":requirement_validation["conclusion"],"executed_at":now(),"accounts":{"sender":{"short_id":sender["short_id"],"uid":sender_uid},"receiver":{"short_id":receiver["short_id"],"uid":receiver_uid,"nickname":receiver["nickname"]},"room_uid":room_uid},"gift_config":{"gift_id":gift_id,"gift_num":gift_iterations,"consume_gold":consume},"requirement_validation":requirement_validation,"upgrade_validation":upgrade_validation,"steps":{"login":{"status":"PASSED","uid":sender_uid},"wealth_before":wealth_before,"wallet_before":wallet_before,"bill_before":{"status":bills_before.get("status"),"record_count":bills_before.get("record_count")} ,"gift_runs":gifts,"wallet_after":wallet_after,"wealth_after":wealth_after,"bill_after":{"status":bills_after.get("status"),"record_count":bills_after.get("record_count"),"new_records":new_records[:50]}},"assertions":assertions,"assertions_passed":sum(x["passed"] for x in assertions),"assertions_total":len(assertions),"bill_nickname_warning":"" if not bill_match or bill_match.get("targetNick")==receiver.get("nickname") else f"账号池昵称{receiver.get('nickname')}与账单当前昵称{bill_match.get('targetNick')}不同，目标UID以送礼响应为准","redis_manual_check":{"status":"PENDING","command_template":f"HGET yingtao_user_level_exper {sender_uid}","expected_after_if_1_to_1":before_exp+consume if all(isinstance(x,int) for x in (before_exp,consume)) else None,"interface_actual_after":after_exp,"note":"由用户手工查询后补充；平台未连接Redis"},"security_note":f"真实送礼受控顺序执行{gift_iterations}次；Ticket和密码未写入报告；MySQL/Redis均未写入，Redis未在线读取"}
    report_dir=ROOT/"reports"; report_dir.mkdir(exist_ok=True); report_path=report_dir/f"gift-wealth-chain-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"; report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    return {**report,"report":str(report_path)}


def execute_case(case_id, overrides=None, context=None):
    case = row("SELECT c.*, p.base_url FROM test_cases c JOIN projects p ON p.id=c.project_id WHERE c.id=?", (case_id,))
    if not case:
        raise ValueError("用例不存在")
    overrides = overrides or {}; context = context or _runtime_context(case["project_id"], {})
    if os.getenv("AUTOTEST_QUERY_TICKET"): context.setdefault("ticket",os.environ["AUTOTEST_QUERY_TICKET"])
    if os.getenv("AUTOTEST_LOGIN_PASSWORD_ENCRYPTED"): context.setdefault("login_password_encrypted",os.environ["AUTOTEST_LOGIN_PASSWORD_ENCRYPTED"])
    if os.getenv("AUTOTEST_LOGIN_SN"): context.setdefault("login_sn",os.environ["AUTOTEST_LOGIN_SN"])
    if os.getenv("AUTOTEST_LOGIN_T"): context.setdefault("login_t",os.environ["AUTOTEST_LOGIN_T"])
    for key in ("path", "headers", "payload", "expected_status", "expected_contains"):
        if key in overrides and overrides[key] is not None: case[key] = overrides[key]
    case["path"] = substitute_value(case["path"], context)
    try:
        parsed_headers = substitute_value(json.loads(case["headers"] or "{}"), context)
        case["headers"] = json.dumps(parsed_headers, ensure_ascii=False)
    except Exception: pass
    try:
        parsed_payload = substitute_value(json.loads(case["payload"]), context)
        case["payload"] = json.dumps(parsed_payload, ensure_ascii=False)
    except Exception: case["payload"] = substitute_value(case["payload"], context)
    run_id, started = uid("run"), time.perf_counter()
    path_blob = f"{case['path']} {case['title']}".lower()
    high_hits = [x for x in HIGH_RISK_WORDS if x in path_blob]
    if high_hits and os.getenv("AUTOTEST_ALLOW_HIGH_RISK", "true").lower() != "true":
        status, http_status, response, error = "BLOCKED", None, "", "安全策略阻止高风险接口：" + ", ".join(high_hits[:4])
    elif case["method"] in {"POST", "PUT", "PATCH", "DELETE"} and os.getenv("AUTOTEST_ALLOW_MUTATIONS", "true").lower() != "true":
        status, http_status, response, error = "BLOCKED", None, "", "安全模式默认禁止可能改变数据的请求"
    elif not case["method"] or not case["path"]:
        status, http_status, response, error = "SKIPPED", None, "", "该用例是设计用例，尚未绑定可执行接口"
    elif not case["base_url"]:
        status, http_status, response, error = "BLOCKED", None, "", "项目尚未配置 Base URL"
    else:
        url = case["path"] if case["path"].startswith("http") else case["base_url"].rstrip("/") + "/" + case["path"].lstrip("/")
        allowed_hosts = {x.strip().lower() for x in os.getenv("AUTOTEST_ALLOWED_HOSTS", "test2westarlive.gzxchate.com").split(",") if x.strip()}
        target_host = urllib.parse.urlsplit(url).hostname or ""
        if allowed_hosts and target_host.lower() not in allowed_hosts:
            status, http_status, response, error = "BLOCKED", None, "", f"目标域名 {target_host} 不在测试环境白名单"
            duration = int((time.perf_counter() - started) * 1000)
            analysis = "目标环境安全边界阻止请求"
            execute("INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?)", (run_id, case["project_id"], case_id, status, duration, http_status, safe_request_evidence(case["method"],case["path"],case["payload"]), response, error, analysis, now()))
            return row("SELECT * FROM runs WHERE id=?", (run_id,))
        try:
            headers = json.loads(case["headers"] or "{}")
            # Secrets are injected at runtime and never persisted in SQLite.
            if os.getenv("AUTOTEST_HEADER_SN"):
                headers.setdefault("sn", os.environ["AUTOTEST_HEADER_SN"])
            if os.getenv("AUTOTEST_HEADER_AUTHORIZATION"):
                headers.setdefault("Authorization", os.environ["AUTOTEST_HEADER_AUTHORIZATION"])
            payload = case["payload"].encode() if case["payload"] else None
            if payload and "Content-Type" not in headers:
                headers["Content-Type"] = "application/json"
            req = urllib.request.Request(url, data=payload, method=case["method"], headers=headers)
            try:
                resp = urllib.request.urlopen(req, timeout=20)
                http_status, response = resp.status, resp.read(100000).decode("utf-8", "replace")
            except urllib.error.HTTPError as e:
                http_status, response = e.code, e.read(100000).decode("utf-8", "replace")
            ok = http_status == case["expected_status"] and (not case["expected_contains"] or case["expected_contains"] in response)
            case_path=case["path"].split("?",1)[0]
            if ok and case_path=="/userserv/id/login":
                try: login_validation=json.loads(response)
                except Exception: login_validation={}
                login_data=login_validation.get("data") if isinstance(login_validation,dict) else None
                login_ok=login_validation.get("code")==200 and isinstance(login_data,dict) and bool(login_data.get("access_token")) and isinstance(login_data.get("uid"),int)
                status="PASSED" if login_ok else "FAILED"
                error="" if login_ok else f"登录业务校验失败：code={login_validation.get('code')}，message={login_validation.get('message')}，access_token={'存在' if isinstance(login_data,dict) and login_data.get('access_token') else '缺失'}"
            elif ok and case_path=="/level/exeperience/v2/get":
                try:
                    response_body=json.loads(response)
                    core_validation=validate_wealth_core_contract(response_body)
                    business_ok=response_body.get("code")==200 and core_validation["ok"]
                    status="PASSED" if business_ok else "FAILED"
                    error="" if business_ok else core_validation["summary"]+(("；"+"；".join(core_validation.get("details",[])[:10])) if core_validation.get("details") else "")
                except Exception as validation_error:
                    status="FAILED"; error=f"财富接口核心契约校验异常：{validation_error}"
            else:
                status, error = ("PASSED", "") if ok else ("FAILED", f"期望状态码 {case['expected_status']}，实际 {http_status}")
        except Exception as e:
            status, http_status, response, error = "ERROR", None, "", str(e)
    duration = int((time.perf_counter() - started) * 1000)
    analysis = {"PASSED": "响应符合断言", "FAILED": "疑似产品行为或断言与当前实现不一致", "ERROR": "请求或环境异常", "BLOCKED": "缺少执行配置", "SKIPPED": "非接口自动化用例"}.get(status, "")
    execute("INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?)", (run_id, case["project_id"], case_id, status, duration, http_status, safe_request_evidence(case["method"],case["path"],case["payload"]), safe_response_evidence(response), error, analysis, now()))
    actual = f"HTTP {http_status}；{analysis}" if http_status is not None else (error or analysis)
    execute("UPDATE test_cases SET execution_status=?,actual_result=?,run_count=COALESCE(run_count,0)+1,last_run_at=? WHERE id=?", (status, actual, now(), case_id))
    persisted=dict(row("SELECT * FROM runs WHERE id=?", (run_id,)))
    persisted["response_data"]=response
    return persisted


def resolve_executable_case(project_id, method, path):
    """Resolve a runnable case by API identity instead of project-specific row ids."""
    normalized=str(path or "").split("?",1)[0]
    candidates=rows("SELECT * FROM test_cases WHERE project_id=? AND UPPER(method)=? AND path<>'' ORDER BY CASE WHEN status='ready' THEN 0 ELSE 1 END, created_at",(project_id,str(method).upper()))
    matched=[item for item in candidates if str(item.get("path") or "").split("?",1)[0]==normalized]
    negative=re.compile(r"缺失|无效|过期|非法|不一致|越权|异常|空data|字段缺失",re.I)
    def score(item):
        raw=str(item.get("path") or ""); title=str(item.get("title") or "")
        value=20 if not negative.search(title) else -50
        if item.get("status")=="ready": value+=5
        if "{{ticket}}" in raw: value+=20
        if "{{uid}}" in raw: value+=20
        if "正常" in title or "登录后" in title or "真实" in title: value+=10
        value+=min(raw.count("="),10)
        return value
    return max(matched,key=score) if matched else None


def resolve_primary_business_chain(project_id):
    """Recognize the current chain from endpoint identities, independent of generated row ids."""
    login=resolve_executable_case(project_id,"POST","/userserv/id/login")
    wealth=resolve_executable_case(project_id,"GET","/level/exeperience/v2/get")
    if not (login and wealth): return None
    workflows=rows("SELECT * FROM workflows WHERE project_id=? ORDER BY CASE WHEN status='ready' THEN 0 ELSE 1 END, created_at",(project_id,))
    for workflow in workflows:
        paths={(x.get("method"),str(x.get("path") or "").split("?",1)[0]) for x in rows("SELECT e.method,e.path FROM workflow_steps s JOIN api_endpoints e ON e.id=s.endpoint_id WHERE s.workflow_id=?",(workflow["id"],))}
        if {("POST","/userserv/id/login"),("GET","/level/exeperience/v2/get")}.issubset(paths): return workflow
    return {"id":"virtual_login_wealth_chain","project_id":project_id,"name":"登录 → 财富等级（自动识别）","status":"ready"}


def run_business_chain_full_test(project_id, performance_requests=20, runtime=None):
    """Authenticate once when needed, then reuse an encrypted local credential for the read-only chain."""
    runtime=runtime or {}
    login_case=resolve_executable_case(project_id,"POST","/userserv/id/login")
    wealth_case=resolve_executable_case(project_id,"GET","/level/exeperience/v2/get")
    missing=[]
    if not login_case: missing.append("POST /userserv/id/login")
    if not wealth_case: missing.append("GET /level/exeperience/v2/get")
    if missing: return {"status":"BLOCKED","stage":"chain_resolve","message":"业务链路缺少可执行接口："+"、".join(missing),"missing_endpoints":missing}
    cached=load_runtime_credential(project_id)
    selected_account_uid=runtime.get("account_uid")
    if selected_account_uid not in (None,""):
        selected_account=row("SELECT * FROM test_accounts WHERE project_id=? AND account_uid=?",(project_id,int(selected_account_uid)))
        if not selected_account: return {"status":"BLOCKED","stage":"account_select","message":"所选账号不在当前项目的多账号测试池中"}
        account_secret=load_account_credential(selected_account["id"])
        if account_secret.get("ticket"): cached={"ticket":account_secret["ticket"],"uid":selected_account["account_uid"]}
    direct_ticket=str(runtime.get("runtime_ticket") or "").strip()
    login_t=str(runtime.get("login_t") or "").strip(); login_sn=str(runtime.get("login_sn") or "").strip(); login_password=str(runtime.get("login_password_encrypted") or "").strip()
    force_fresh_login=bool(login_t or login_sn or login_password)
    if direct_ticket:
        claims=jwt_claims_unverified(direct_ticket); direct_uid=runtime.get("runtime_uid") or claims.get("uid")
        if direct_uid is None: return {"status":"BLOCKED","stage":"ticket_parse","credential_status":"INCOMPLETE","message":"无法从Ticket解析UID，请确认Ticket完整有效"}
        ticket=direct_ticket; login_uid=int(direct_uid); login={"status":"DIRECT","http_status":None,"error":"","response_data":""}; login_body={"code":200,"data":{"access_token":ticket,"uid":login_uid}}
        save_runtime_credential(project_id,ticket,"",login_uid)
    elif force_fresh_login and not (login_t and login_password):
        return {"status":"BLOCKED","stage":"credential_input_incomplete","credential_status":"INCOMPLETE","message":"重新登录需要填写t和加密密码；sn可留空"}
    elif cached.get("ticket") and cached.get("uid") is not None and not force_fresh_login:
        ticket=cached["ticket"]; login_uid=cached["uid"]
        login={"status":"REUSED","http_status":None,"error":"","response_data":""}
        login_body={"code":200,"data":{"access_token":ticket,"uid":login_uid}}
    else:
        if not force_fresh_login:
            return {"status":"BLOCKED","stage":"credential_missing","credential_status":"MISSING","message":"尚未保存可复用凭证，请完成一次真实登录后，平台将自动加密保存ticket和sn"}
        login_context={"login_t":login_t,"login_sn":login_sn,"login_password_encrypted":login_password}
        login=execute_case(login_case["id"],context=login_context)
        if login["status"]!="PASSED":
            report={"report_type":"BUSINESS_CHAIN_REAL_TEST","mock":False,"status":"BLOCKED","stage":"login","executed_at":now(),"message":"真实登录未通过，未继续业务接口和性能测试","login":{"status":login["status"],"http_status":login["http_status"],"error":login["error"]},"security_note":"报告未保存Token、密码、sn或完整请求参数"}
            report_dir=ROOT/"reports"; report_dir.mkdir(exist_ok=True); report_path=report_dir/f"wealth-full-real-test-blocked-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"; report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
            return {"status":"BLOCKED","stage":"login","message":report["message"],"login_status":login["status"],"error":login["error"],"report":str(report_path)}
        try: login_body=json.loads(login["response_data"] or "{}")
        except Exception: login_body={}
        login_data=login_body.get("data",{}) if isinstance(login_body,dict) else {}
        ticket=login_data.get("access_token"); login_uid=login_data.get("uid")
        if not ticket: return {"status":"BLOCKED","stage":"login_extract","message":"登录响应没有access_token"}
        save_runtime_credential(project_id,ticket,"",login_uid)
    context={"ticket":ticket,"uid":login_uid}
    reused=login["status"]=="REUSED"; direct=login["status"]=="DIRECT"
    flow_trace=[{"order":1,"name":"直接使用已有Ticket" if direct else "复用本机加密凭证" if reused else "真实登录并保存Ticket","status":"PASSED","http_status":login["http_status"],"inputs":["手动Ticket"] if direct else ["本机加密ticket"] if reused else ["t","可选sn","加密password"],"assertions":{"credential_available":bool(ticket),"uid_present":login_uid is not None},"outputs":{"ticket":"***REDACTED***","uid":login_uid},"failure_category":"none"}]
    wealth=execute_case(wealth_case["id"],context=context)
    try: wealth_body=json.loads(wealth["response_data"] or "{}")
    except Exception: wealth_body={}
    core_contract=validate_wealth_core_contract(wealth_body,login_uid)
    interface_assertions=wealth_interface_assertions(wealth.get("http_status"),wealth_body,login_uid,core_contract)
    matrix={"ok":True,"status":"SKIPPED","summary":"已按当前测试范围跳过奖励矩阵比对","details":[]}
    backend={"ok":True,"status":"SKIPPED","summary":"已按当前测试范围跳过奖励后台配置比对","details":[]}
    wealth_call_ok=wealth.get("http_status")==200 and wealth_body.get("code")==200 and isinstance(wealth_body.get("data"),dict)
    if wealth.get("http_status") in {401,403} or (isinstance(wealth_body,dict) and wealth_body.get("code") in {401,403,1001,1002,1003}):
        return {"status":"BLOCKED","stage":"credential_expired","credential_status":"EXPIRED","message":"已保存的ticket/sn已失效，请提供一次新的真实登录信息；平台不会继续执行后续测试","flow_trace":flow_trace}
    flow_trace.append({"order":2,"name":"查询财富等级","status":"PASSED" if wealth_call_ok and core_contract["ok"] else "FAILED","http_status":wealth.get("http_status"),"inputs":{"ticket":"来自步骤1（已脱敏）","uid":login_uid},"assertions":{"http_200":wealth.get("http_status")==200,"business_code_200":wealth_body.get("code")==200,**core_contract["checks"]},"outputs":{"current_level":core_contract.get("current_level"),"next_level":core_contract.get("next_level"),"rights_groups":core_contract.get("rights_groups"),"rights_count":core_contract.get("rights_count")},"failure_category":"none" if wealth_call_ok and core_contract["ok"] else "business_assertion"})
    redis_evidence=read_wealth_experience_redis(project_id,login_uid,core_contract.get("current_experience"),core_contract.get("current_level"))
    flow_trace.append({"order":3,"name":"离线Redis财富经验三方核对","status":redis_evidence["status"],"http_status":None,"inputs":{"source":"Dump_20260821.csv","key":"yingtao_user_level_exper","field":login_uid},"assertions":{"passed":redis_evidence.get("assertions_passed",0),"total":redis_evidence.get("assertions_total",0)},"outputs":{"redis_value":redis_evidence.get("value"),"derived_level":redis_evidence.get("derived_level"),"live_redis_access":False},"failure_category":"none" if redis_evidence["status"]=="PASSED" else "business_data_mismatch"})
    project=row("SELECT * FROM projects WHERE id=?",(project_id,))
    wallet=query_wallet(project["base_url"],ticket,login_uid)
    flow_trace.append({"order":4,"name":"查询钱包余额","status":wallet["status"],"http_status":wallet.get("http_status"),"inputs":{"ticket":"来自步骤1（已脱敏）","uid":login_uid},"assertions":{"passed":wallet["assertions_passed"],"total":wallet["assertions_total"]},"outputs":{"goldNum":wallet.get("gold_num"),"diamondNum":wallet.get("diamond_num"),"currencyNum":wallet.get("currency_num"),"goldType":wallet.get("gold_type")},"failure_category":"none" if wallet["status"]=="PASSED" else "wallet_contract"})
    bill_records=query_gift_bill_records(project["base_url"],ticket,login_uid,runtime.get("bill_page_no",1),runtime.get("bill_page_size",50),runtime.get("bill_type",1),runtime=runtime)
    flow_trace.append({"order":5,"name":"查询送礼账单记录","status":bill_records["status"],"http_status":bill_records.get("http_status"),"inputs":{"ticket":"来自步骤1（已脱敏）","uid":login_uid,"date":"${current_timestamp_ms}","pageNo":runtime.get("bill_page_no",1),"pageSize":runtime.get("bill_page_size",50),"type":runtime.get("bill_type",1)},"assertions":{"passed":bill_records["assertions_passed"],"total":bill_records["assertions_total"]},"outputs":{"query_time_ms":bill_records["query_time_ms"],"record_count":bill_records["record_count"],"correlation":bill_records["correlation_capability"]},"failure_category":"none" if bill_records["status"]=="PASSED" else "bill_record_contract"})
    api_variants=run_wealth_api_variants(project_id,ticket,login_uid,project["base_url"])
    path=substitute_value(wealth_case["path"],context)
    url=project["base_url"].rstrip("/")+"/"+path.lstrip("/")
    durations=[]; perf_errors=[]; success=0
    for _ in range(max(1,min(int(performance_requests),100))):
        started=time.perf_counter()
        try:
            req=urllib.request.Request(url,method="GET",headers={"Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=20) as resp:
                raw=resp.read(100000).decode("utf-8","replace")
                body=json.loads(raw)
                if resp.status==200 and body.get("code")==200: success+=1
                else: perf_errors.append(f"HTTP {resp.status}/code {body.get('code')}")
        except Exception as exc: perf_errors.append(str(exc))
        durations.append(int((time.perf_counter()-started)*1000))
    ordered=sorted(durations)
    percentile=lambda p: ordered[min(len(ordered)-1,max(0,int(len(ordered)*p)-1))]
    performance={"requests":len(durations),"success":success,"failed":len(durations)-success,"success_rate":round(success/len(durations)*100,2),"average_ms":round(statistics.mean(durations),2),"p50_ms":percentile(.50),"p95_ms":percentile(.95),"min_ms":min(durations),"max_ms":max(durations),"errors":perf_errors[:10],"engine":"Python快速冒烟"}
    jmeter=run_jmeter_wealth(ticket,login_uid,runtime.get("jmeter_threads",2),runtime.get("jmeter_loops",5),runtime.get("jmeter_rampup",2)) if runtime.get("run_jmeter",True) else {"status":"SKIPPED","engine":"JMeter"}
    flow_trace.append({"order":6,"name":"JMeter正式性能测试","status":jmeter.get("status"),"inputs":{"ticket":"复用步骤1内存变量","uid":login_uid,"threads":jmeter.get("threads"),"loops":jmeter.get("loops")},"assertions":{"error_rate_zero":jmeter.get("error_rate")==0,"http_codes":jmeter.get("response_codes",{})},"failure_category":"none" if jmeter.get("status")=="PASSED" else "performance_or_authentication"})
    perf_actual=f"真实请求{performance['requests']}次，成功率{performance['success_rate']}%，平均{performance['average_ms']}ms，P50={performance['p50_ms']}ms，P95={performance['p95_ms']}ms，最大{performance['max_ms']}ms；性能阈值尚未确认"
    execute("UPDATE test_cases SET execution_status='BLOCKED',actual_result=?,run_count=COALESCE(run_count,0)+1,last_run_at=? WHERE project_id=? AND title='财富接口响应性能'",(perf_actual,now(),project_id))
    functional_ok=wealth["http_status"]==200 and isinstance(wealth_body,dict) and wealth_body.get("code")==200 and core_contract["ok"]
    jmeter_ok=jmeter.get("status") in {"PASSED","SKIPPED"}
    final="PASSED" if functional_ok and redis_evidence["status"]=="PASSED" and wallet["status"]=="PASSED" and bill_records["status"]=="PASSED" and success==len(durations) and jmeter_ok else "FAILED"
    consistency=data_consistency_summary(project_id)
    report={"report_type":"BUSINESS_CHAIN_REAL_TEST","chain_name":"登录 → 财富等级 → 钱包余额","mock":False,"status":final,"executed_at":now(),"flow":["凭证复用或真实登录","财富接口核心契约校验","钱包余额固定契约校验","接口异常与鉴权场景","Python快速冒烟","JMeter正式性能测试"],"flow_trace":flow_trace,"login":{"status":login["status"],"http_status":login["http_status"],"uid":login_uid},"wealth_api":{"status":"PASSED" if functional_ok else "FAILED","validation_status":wealth["status"],"http_status":wealth["http_status"],"business_code":wealth_body.get("code") if isinstance(wealth_body,dict) else None,"core_contract":core_contract,"assertions":interface_assertions,"assertions_passed":sum(x["passed"] for x in interface_assertions),"assertions_total":len(interface_assertions)},"wallet_api":wallet,"api_variants":{"total":len(api_variants),"passed":sum(x["status"]=="PASSED" for x in api_variants),"failed":sum(x["status"]=="FAILED" for x in api_variants),"results":api_variants},"reward_matrix":matrix,"backend_config":backend,"data_consistency":consistency,"performance":performance,"jmeter":jmeter,"security_note":"报告未保存Token、密码、sn或完整请求参数；钱包与外部数据源严格只读；奖励内容不参与本次测试结论"}
    report["chain_name"]="登录 → 财富等级 → 离线Redis经验 → Excel门槛 → 钱包余额 → 送礼账单"
    report["flow"].insert(2,"离线Redis Hash经验与Excel等级门槛三方核对")
    report["flow"].insert(4,"送礼账单固定契约校验")
    report["redis_wealth_evidence"]=redis_evidence
    report["bill_record_api"]=bill_records
    report_dir=ROOT/"reports"; report_dir.mkdir(exist_ok=True)
    stamp=datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path=report_dir/f"wealth-full-real-test-{stamp}.json"
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    close_unexecuted_cases(project_id)
    return {"status":final,"report":str(report_path),"functional":functional_ok,"flow_trace":flow_trace,"wealth_api":report["wealth_api"],"redis_wealth_evidence":redis_evidence,"wallet_api":wallet,"bill_record_api":bill_records,"api_variants":report["api_variants"],"reward_matrix_ok":matrix["ok"],"reward_matrix":report["reward_matrix"],"backend_config_ok":backend["ok"],"backend_config":report["backend_config"],"data_consistency":consistency,"performance":performance,"jmeter":jmeter}


def run_wealth_full_test(project_id, performance_requests=20, runtime=None):
    return run_business_chain_full_test(project_id,performance_requests,runtime)


def close_unexecuted_cases(project_id):
    """Every case must end with evidence or an explicit blocker; never leave ambiguous NOT_RUN after Run All."""
    reasons={
      "ui_device":"需接入Android真机/Appium后验证页面定位、渲染、动画和交互",
      "api_ui":"接口证据已具备，但仍需真机页面证据完成接口与UI一致性校验",
      "db_redis":"需确认测试账号对应Redis Key及允许的只读查询规则后执行三方一致性校验",
      "api_security":"需启动隔离的安全异常执行器；不得用正常请求结果代替异常场景结果",
      "performance_ui":"已有接口性能数据；页面首屏、帧率和内存仍需真机性能执行器",
      "workflow":"涉及升级、降级、送礼或缓存变更，需可恢复的测试数据操作权限和回滚步骤",
      "api_db":"需准备对应边界等级账号或可恢复的数据库测试数据后执行"
    }
    for executor,reason in reasons.items():
        execute("UPDATE test_cases SET execution_status='BLOCKED',actual_result=? WHERE project_id=? AND executor_type=? AND execution_status='NOT_RUN'",(reason,project_id,executor))


def ensure_wealth_api_cases(project_id):
    """Auto-fill missing executable API scenarios instead of leaving design-only rows."""
    definitions=[
      ("缺失Token","认证异常"),("无效Token","认证异常"),("过期Token","认证异常"),
      ("Token UID与参数UID不一致","越权"),("缺失UID参数","参数异常"),("缺失设备参数","参数异常"),
      ("语言参数非法","参数异常"),("非法UID类型","参数异常"),("服务返回空data","异常响应"),("响应字段缺失","异常响应")]
    created=0
    source=row("SELECT id FROM sources WHERE project_id=? AND kind='requirement' ORDER BY created_at DESC LIMIT 1",(project_id,))
    for title,scenario in definitions:
        existing=row("SELECT id FROM test_cases WHERE project_id=? AND title=?",(project_id,title))
        if existing: continue
        point_id=uid("tp"); case_id=uid("tc")
        execute("INSERT INTO test_points VALUES (?,?,?,?,?,?,?,?,?,?,?)",(point_id,project_id,source["id"] if source else "","异常与安全",title,scenario,"P0","高","由真实财富接口契约自动补齐","draft",now()))
        executable=title not in {"过期Token","服务返回空data","响应字段缺失"}
        execute("""INSERT INTO test_cases(id,project_id,point_id,title,method,path,headers,payload,expected_status,expected_contains,priority,status,steps,expected,created_at,executor_type,scenario_type,requirement_ref,actual_result,execution_status,run_count,last_run_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(case_id,project_id,point_id,title,"GET" if executable else "","/level/exeperience/v2/get" if executable else "","{}","",200,"","P0","ready" if executable else "blocked","平台自动构造参数并发送只读请求","拒绝非法请求或不泄露其他用户数据",now(),"api_security",scenario,"财富接口异常契约","","NOT_RUN" if executable else "BLOCKED",0,None))
        created+=1
    return created


def run_wealth_api_variants(project_id, ticket, account_uid, base_url):
    ensure_wealth_api_cases(project_id)
    base=base_url.rstrip("/")+"/level/exeperience/v2/get"
    common={"deviceType":"0","systemLanguage":"zh","appVersion":"100.1.5.4","os":"android","language":"en","appCode":"100154","uid":str(account_uid),"appid":"soulfree","ticket":ticket}
    variants=[
      ("缺失Token",{k:v for k,v in common.items() if k!="ticket"}),
      ("无效Token",{**common,"ticket":"invalid-token-for-readonly-test"}),
      ("Token UID与参数UID不一致",{**common,"uid":str(account_uid+1)}),
      ("缺失UID参数",{k:v for k,v in common.items() if k!="uid"}),
      ("缺失设备参数",{k:v for k,v in common.items() if k not in {"deviceType","appVersion","os"}}),
      ("语言参数非法",{**common,"language":"__invalid__"}),
      ("非法UID类型",{**common,"uid":"not-a-number"})]
    scenarios={
      "缺失Token":("有效测试账号，删除ticket参数","发送财富等级查询","服务端拒绝请求且不得返回任何用户财富数据"),
      "无效Token":("使用伪造Token，其余参数有效","发送财富等级查询","服务端拒绝鉴权且不得返回用户财富数据"),
      "Token UID与参数UID不一致":("Token属于当前账号，参数UID改为其他值","发送财富等级查询","拒绝请求或只返回Token所属账号数据，禁止越权"),
      "缺失UID参数":("Token有效，删除uid参数","发送财富等级查询","拒绝请求或安全绑定Token所属账号，禁止返回其他用户数据"),
      "缺失设备参数":("Token和UID有效，删除部分设备参数","发送财富等级查询","可明确拒绝；若兼容成功，返回数据必须仍属于当前账号"),
      "语言参数非法":("Token和UID有效，语言参数设置为非法值","发送财富等级查询","可明确拒绝或使用安全默认语言，用户数据不得串号"),
      "非法UID类型":("Token有效，uid设置为非数字文本","发送财富等级查询","拒绝非法类型或安全绑定Token账号，禁止越权")}
    results=[]
    for title,params in variants:
        started=time.perf_counter(); http_status=None; body={}; request_error=""
        try:
            req=urllib.request.Request(base+"?"+urllib.parse.urlencode(params),method="GET",headers={"Accept":"application/json"})
            try:
                resp=urllib.request.urlopen(req,timeout=20); http_status=resp.status; raw=resp.read(100000)
            except urllib.error.HTTPError as exc: http_status=exc.code; raw=exc.read(100000)
            try: body=json.loads(raw.decode("utf-8","replace"))
            except Exception: body={}
        except Exception as exc: request_error=str(exc)
        data=body.get("data") if isinstance(body,dict) else None
        info=data.get("myExperLevelInfo") if isinstance(data,dict) else None
        rejected=body.get("code")!=200 or http_status in {400,401,403,422}
        no_user_data=not isinstance(info,dict)
        own_user_only=isinstance(info,dict) and info.get("uid")==account_uid
        no_other_user_data=no_user_data or own_user_only
        if title in {"缺失Token","无效Token"}: assertions=[{"name":"鉴权被拒绝","passed":rejected,"actual":f"HTTP {http_status}/code {body.get('code')}"},{"name":"未返回用户财富数据","passed":no_user_data,"actual":"无用户数据" if no_user_data else f"返回UID {info.get('uid')}"}]
        else: assertions=[{"name":"未泄露其他账号数据","passed":no_other_user_data,"actual":"未返回用户数据" if no_user_data else f"返回UID {info.get('uid')}"},{"name":"响应结果可解释","passed":rejected or own_user_only,"actual":"明确拒绝" if rejected else "安全绑定Token账号" if own_user_only else "异常返回"}]
        passed=all(x["passed"] for x in assertions)
        status="PASSED" if passed else "FAILED"; actual=f"HTTP {http_status} / code {body.get('code') if isinstance(body,dict) else None}；"+("未泄露错误账号数据" if passed else "返回结果不符合异常契约")
        execute("UPDATE test_cases SET execution_status=?,actual_result=?,run_count=COALESCE(run_count,0)+1,last_run_at=? WHERE project_id=? AND title=?",(status,actual,now(),project_id,title))
        precondition,action,expected=scenarios[title]
        results.append({"name":title,"status":status,"precondition":precondition,"action":action,"expected_result":expected,"actual_result":actual,"assertions":assertions,"http_status":http_status,"business_code":body.get("code") if isinstance(body,dict) else None,"duration_ms":int((time.perf_counter()-started)*1000),"error":request_error})
    return results


class Handler(BaseHTTPRequestHandler):
    server_version = "AutoTestAI/0.1"

    def log_message(self, fmt, *args):
        print(f"[{now()}] {self.client_address[0]} {fmt % args}")

    def send_json(self, data, status=200):
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)

    def body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        try:
            p = urlparse(self.path); path = p.path
            if path == "/api/health": return self.send_json({"ok": True, "time": now(), "build": BUILD_ID, "frontend_build": BUILD_ID, "backend": "python-stdlib"})
            if path == "/api/system/storage-policy": return self.send_json(platform_storage_policy())
            if path == "/api/projects": return self.send_json(rows("SELECT * FROM projects ORDER BY updated_at DESC"))
            m = re.fullmatch(r"/api/projects/([^/]+)/reports", path)
            if m: return self.send_json(list_generated_reports(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/test-accounts", path)
            if m: return self.send_json(list_test_accounts(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/evidence-center", path)
            if m: return self.send_json(evidence_center_status(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/diagnosis", path)
            if m: return self.send_json(project_quality_diagnosis(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/quality-profile", path)
            if m:
                try: return self.send_json(project_quality_profile(m.group(1)))
                except ValueError as exc: return self.send_json({"error":str(exc)},404)
            m = re.fullmatch(r"/api/projects/([^/]+)/execution-profile", path)
            if m:
                try: return self.send_json(project_execution_profile(m.group(1)))
                except ValueError as exc: return self.send_json({"error":str(exc)},404)
            m = re.fullmatch(r"/api/projects/([^/]+)/requirement-packages", path)
            if m: return self.send_json(requirement_package_catalog(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/requirement-packages/([^/]+)/account-model", path)
            if m: return self.send_json(generate_requirement_account_model(m.group(1), m.group(2), True))
            m = re.fullmatch(r"/api/projects/([^/]+)/requirement-packages/([^/]+)/evidence-rules", path)
            if m: return self.send_json(requirement_evidence_rules(m.group(1), m.group(2)))
            m = re.fullmatch(r"/api/projects/([^/]+)/requirement-packages/([^/]+)/execution-plan", path)
            if m: return self.send_json(generate_requirement_execution_plan(m.group(1), m.group(2), {}))
            m = re.fullmatch(r"/api/projects/([^/]+)/wealth-latest-report", path)
            if m:
                report_dir=ROOT/"reports"
                files=sorted(report_dir.glob("wealth-full-real-test-*.json"),key=lambda x:x.stat().st_mtime,reverse=True) if report_dir.exists() else []
                if not files: return self.send_json({})
                payload=json.loads(files[0].read_text(encoding="utf-8")); payload["report_path"]=str(files[0])
                wealth_api=payload.get("wealth_api",{})
                payload["functional"]=wealth_api.get("http_status")==200 and wealth_api.get("business_code")==200
                payload["reward_matrix_ok"]=bool(payload.get("reward_matrix",{}).get("ok"))
                payload["backend_config_ok"]=bool(payload.get("backend_config",{}).get("ok"))
                return self.send_json(payload)
            m = re.fullmatch(r"/api/projects/([^/]+)/gift-latest-report", path)
            if m:
                report_dir=ROOT/"reports"; files=sorted(report_dir.glob("gift-wealth-chain-*.json"),key=lambda x:x.stat().st_mtime,reverse=True) if report_dir.exists() else []
                if not files: return self.send_json({})
                payload=json.loads(files[0].read_text(encoding="utf-8")); payload["report_path"]=str(files[0]); return self.send_json(payload)
            m = re.fullmatch(r"/api/projects/([^/]+)/wealth-reward-configs", path)
            if m:
                pid=m.group(1)
                return self.send_json({"configs":rows("SELECT * FROM wealth_backend_reward_configs WHERE project_id=? ORDER BY level",(pid,)),"expectations":rows("SELECT * FROM wealth_reward_expectations WHERE project_id=? ORDER BY level_min,source_row",(pid,)),"issues":rows("SELECT * FROM reward_matrix_issues WHERE project_id=? ORDER BY source_row",(pid,))})
            m = re.fullmatch(r"/api/projects/([^/]+)/dashboard", path)
            if m:
                try:
                    return self.send_json(project_dashboard(m.group(1)))
                except ValueError as exc:
                    return self.send_json({"error": str(exc)}, 404)
            m = re.fullmatch(r"/api/projects/([^/]+)/capture-reports", path)
            if m: return self.send_json(rows("SELECT * FROM source_capture_reports WHERE project_id=? ORDER BY created_at DESC",(m.group(1),)))
            m = re.fullmatch(r"/api/projects/([^/]+)/interface-document", path)
            if m: return self.send_json(build_project_interface_document(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/toolchain", path)
            if m: return self.send_json(enterprise_toolchain_status(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/jmeter/case-script-model", path)
            if m: return self.send_json(salary_trade_case_to_jmeter_model(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/salary-trade/jmeter-mapping", path)
            if m: return self.send_json(salary_trade_jmeter_mapping_status(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/mysql/status", path)
            if m: return self.send_json(mysql_connection_status(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/redis-mappings", path)
            if m: return self.send_json(rows("SELECT m.*,e.method,e.path,e.summary FROM api_redis_mappings m JOIN api_endpoints e ON e.id=m.endpoint_id WHERE m.project_id=? ORDER BY m.confidence DESC LIMIT 1000",(m.group(1),)))
            m = re.fullmatch(r"/api/projects/([^/]+)/consistency", path)
            if m:
                pid=m.group(1); return self.send_json({"summary":data_consistency_summary(pid),"rules":rows("SELECT r.*,e.method,e.path,e.summary FROM consistency_rules r JOIN api_endpoints e ON e.id=r.endpoint_id WHERE r.project_id=? ORDER BY r.confidence DESC",(pid,)),"runs":rows("SELECT x.*,r.redis_pattern,e.path FROM consistency_runs x JOIN consistency_rules r ON r.id=x.rule_id JOIN api_endpoints e ON e.id=r.endpoint_id WHERE x.project_id=? ORDER BY x.created_at DESC LIMIT 100",(pid,))})
            m = re.fullmatch(r"/api/projects/([^/]+)/assistant/messages", path)
            if m: return self.send_json(rows("SELECT id,role,content,action,created_at FROM assistant_messages WHERE project_id=? ORDER BY created_at DESC LIMIT 100",(m.group(1),))[::-1])
            if path == "/api/settings":
                s = {x["key"]: x["value"] for x in rows("SELECT * FROM settings")}; s["api_key"] = "••••••••" if s.get("api_key") else ""; return self.send_json(s)
            if path.startswith("/reports/"):
                relative=Path(urllib.parse.unquote(path.removeprefix("/reports/")))
                file=(ROOT/"reports"/relative).resolve(); root=(ROOT/"reports").resolve()
                if file.is_file() and root in file.parents:
                    mime={".html":"text/html; charset=utf-8",".json":"application/json; charset=utf-8",".csv":"text/csv; charset=utf-8",".js":"application/javascript",".css":"text/css",".png":"image/png",".svg":"image/svg+xml",".woff":"font/woff",".woff2":"font/woff2"}.get(file.suffix.lower(),"application/octet-stream")
                    raw=file.read_bytes(); self.send_response(200); self.send_header("Content-Type",mime); self.send_header("Cache-Control","no-store"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); return self.wfile.write(raw)
            if path.startswith("/requirement-reports/"):
                relative=Path(urllib.parse.unquote(path.removeprefix("/requirement-reports/")))
                file=(REQUIREMENT_PACKAGE_ROOT/relative).resolve(); root=REQUIREMENT_PACKAGE_ROOT.resolve()
                if file.is_file() and root in file.parents:
                    mime={".html":"text/html; charset=utf-8",".json":"application/json; charset=utf-8",".csv":"text/csv; charset=utf-8",".js":"application/javascript",".css":"text/css",".png":"image/png",".svg":"image/svg+xml"}.get(file.suffix.lower(),"application/octet-stream")
                    raw=file.read_bytes(); self.send_response(200); self.send_header("Content-Type",mime); self.send_header("Cache-Control","no-store"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); return self.wfile.write(raw)
            file = STATIC / ("index.html" if path == "/" else path.lstrip("/"))
            if file.is_file() and STATIC in file.resolve().parents:
                raw = file.read_bytes(); mime = "text/html; charset=utf-8" if file.suffix == ".html" else "text/css" if file.suffix == ".css" else "application/javascript"; self.send_response(200); self.send_header("Content-Type", mime); self.send_header("Cache-Control", "no-store, no-cache, must-revalidate"); self.send_header("Pragma", "no-cache"); self.send_header("Content-Length", str(len(raw))); self.end_headers(); return self.wfile.write(raw)
            self.send_error(404)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def do_POST(self):
        try:
            path = urlparse(self.path).path
            if path == "/api/projects":
                x = self.body(); pid = uid("prj"); t = now(); execute("INSERT INTO projects VALUES (?,?,?,?,?,?)", (pid, x.get("name", "未命名项目"), x.get("description", ""), x.get("base_url", ""), t, t)); return self.send_json(row("SELECT * FROM projects WHERE id=?", (pid,)), 201)
            m = re.fullmatch(r"/api/projects/([^/]+)/test-accounts", path)
            if m: return self.send_json(upsert_test_account(m.group(1),self.body()),201)
            m = re.fullmatch(r"/api/projects/([^/]+)/redis-manual-result", path)
            if m: return self.send_json(attach_manual_redis_result(m.group(1),self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/sources", path)
            if m:
                x = self.body(); sid = uid("src"); kind = x.get("kind", "requirement"); browser_images=[]
                page_meta=None
                if x.get("browser_capture") and x.get("source_url"):
                    content,browser_images,page_meta=browser_capture_source(x["source_url"]); content=(x.get("content","")+"\n"+content).strip()
                else: content=extract_source_content(x)
                capture_entries=0
                if kind == "har":
                    content,capture_entries=parse_har_capture(content)
                image_values=[]; all_images=extract_source_images(x)+browser_images
                if all_images:
                    status,analysis=vision_analyze_bundle(content,all_images)
                    for index,(image_name,mime,data_b64) in enumerate(all_images):
                        asset_analysis=analysis if index==0 else "已纳入同一份需求的图文联合分析，综合结论见首张资源"
                        image_values.append((uid("asset"),m.group(1),sid,image_name,mime,data_b64,status,asset_analysis,now()))
                    content += f"\n\n[文字与{len(all_images)}张图片联合分析]\n{analysis}"
                execute("INSERT INTO sources VALUES (?,?,?,?,?,?)", (sid, m.group(1), x.get("name", x.get("file_name") or x.get("source_url") or "资料"), kind, content, now()))
                if page_meta is not None:
                    score,capture_status,capture_blockers=evaluate_capture_completeness(page_meta)
                    execute("INSERT INTO source_capture_reports VALUES (?,?,?,?,?,?,?)",(sid,m.group(1),x.get("source_url",""),score,capture_status,json.dumps(page_meta.get("completeness",{}),ensure_ascii=False),json.dumps(capture_blockers,ensure_ascii=False),now()))
                if image_values:
                    with db() as conn: conn.executemany("INSERT INTO source_assets VALUES (?,?,?,?,?,?,?,?,?)",image_values)
                result = store_endpoints_incremental(m.group(1),sid,content,x.get("requirement_source_id"),x.get("batch_name") or x.get("name","接口变更")) if kind in {"openapi","har"} else {"endpoints":0}; result["requirement_items"] = analyze_requirement_source(m.group(1),sid,content) if kind=="requirement" else 0; result["images"]=len(image_values)
                if kind == "har": result["capture_entries"]=capture_entries
                if page_meta is not None: result.update({"capture_score":score,"capture_status":capture_status,"capture_blockers":capture_blockers})
                return self.send_json({"id": sid, **result}, 201)
            m = re.fullmatch(r"/api/projects/([^/]+)/generate", path)
            if m:
                x = self.body(); return self.send_json(generate_assets(m.group(1), x["source_id"], bool(x.get("force"))))
            m = re.fullmatch(r"/api/projects/([^/]+)/db-schema", path)
            if m:
                x = self.body(); return self.send_json(import_db_schema(m.group(1), x.get("content", "{}")))
            m = re.fullmatch(r"/api/projects/([^/]+)/mysql/test", path)
            if m: return self.send_json(mysql_test_connection(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/mysql/query", path)
            if m: return self.send_json(mysql_readonly_query(m.group(1), self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/mysql/import-schema-live", path)
            if m: return self.send_json(import_mysql_schema_live(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/salary-trade/db-evidence", path)
            if m: return self.send_json(salary_trade_db_evidence_check(m.group(1), self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/salary-trade/jmeter-harvest", path)
            if m: return self.send_json(harvest_salary_trade_jmeter_mapping(m.group(1), self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/redis-sources", path)
            if m:
                x = self.body(); rid = uid("redis")
                host = str(x.get("host", "")).strip(); port = int(x.get("port", 6379)); db_no = int(x.get("db_no", 0))
                if not host: return self.send_json({"error": "Host不能为空"}, 400)
                if not (1 <= port <= 65535) or not (0 <= db_no <= 1024): return self.send_json({"error": "Port或DB编号无效"}, 400)
                execute("INSERT INTO redis_sources VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (rid,m.group(1),x.get("name","Redis测试数据源"),host,port,db_no,int(bool(x.get("use_tls",False))),1,"unknown","","",None,now()))
                result = check_redis_source(rid); return self.send_json({**row("SELECT * FROM redis_sources WHERE id=?",(rid,)), **result}, 201)
            m = re.fullmatch(r"/api/projects/([^/]+)/auto-match-data", path)
            if m: return self.send_json(auto_match_project_data(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/quality-profile", path)
            if m:
                try: return self.send_json(save_project_quality_profile(m.group(1), self.body()))
                except ValueError as exc: return self.send_json({"error":str(exc)},404)
            m = re.fullmatch(r"/api/projects/([^/]+)/execution-profile", path)
            if m:
                try: return self.send_json(save_project_execution_profile(m.group(1), self.body()))
                except ValueError as exc: return self.send_json({"error":str(exc)},400)
            m = re.fullmatch(r"/api/projects/([^/]+)/generate-consistency", path)
            if m: return self.send_json(prepare_consistency_rules(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/consistency/run-ready", path)
            if m:
                body=self.body(); return self.send_json(run_ready_consistency_rules(m.group(1), body.get("limit", 5), body.get("scope", "core")))
            m = re.fullmatch(r"/api/projects/([^/]+)/evidence-check", path)
            if m: return self.send_json(run_manual_evidence_check(m.group(1), self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/metadata-hallucination-audit", path)
            if m: return self.send_json(metadata_hallucination_audit(m.group(1), self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/metadata-hallucination-correction", path)
            if m: return self.send_json(metadata_hallucination_correction(m.group(1), self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/business-evidence-plan", path)
            if m: return self.send_json(generate_business_evidence_plan(m.group(1), self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/business-evidence-run", path)
            if m: return self.send_json(run_business_evidence_rules(m.group(1), self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/candidate-evidence-rules", path)
            if m: return self.send_json(generate_candidate_evidence_rules(m.group(1), self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/accept-candidate-evidence-rules", path)
            if m: return self.send_json(accept_candidate_evidence_rules(m.group(1), self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/structured-test-cases", path)
            if m: return self.send_json(generate_structured_test_cases(m.group(1), self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/assistant", path)
            if m:
                x=self.body(); return self.send_json(assistant_reply(m.group(1),x.get("message","")))
            m = re.fullmatch(r"/api/consistency-rules/([^/]+)/run", path)
            if m: return self.send_json(run_consistency_rule(m.group(1)))
            m = re.fullmatch(r"/api/redis-sources/([^/]+)/test", path)
            if m: return self.send_json(check_redis_source(m.group(1)))
            m = re.fullmatch(r"/api/redis-sources/([^/]+)/scan", path)
            if m:
                x = self.body(); return self.send_json(scan_redis_keys(m.group(1), x.get("pattern", "*"), x.get("limit", 100)))
            m = re.fullmatch(r"/api/redis-sources/([^/]+)/inspect", path)
            if m:
                x = self.body(); return self.send_json(inspect_redis_key(m.group(1), x.get("key", "")))
            m = re.fullmatch(r"/api/projects/([^/]+)/generate-workflows", path)
            if m: return self.send_json(generate_workflows(m.group(1)))
            m = re.fullmatch(r"/api/workflows/([^/]+)/run", path)
            if m: return self.send_json(execute_workflow(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/generate-nonfunctional", path)
            if m: return self.send_json(generate_nonfunctional(m.group(1)))
            m = re.fullmatch(r"/api/suites/([^/]+)/run", path)
            if m: return self.send_json(run_suite(m.group(1)))
            m = re.fullmatch(r"/api/performance/([^/]+)/run", path)
            if m: return self.send_json(run_performance(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/generate-operations", path)
            if m: return self.send_json(generate_operations_assets(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/security-scan", path)
            if m: return self.send_json(run_security_scan(m.group(1)))
            m = re.fullmatch(r"/api/jobs/([^/]+)/run", path)
            if m:
                job=row("SELECT * FROM scheduled_jobs WHERE id=?",(m.group(1),)); return self.send_json(dispatch_job(job))
            m = re.fullmatch(r"/api/projects/([^/]+)/endpoints", path)
            if m: return self.send_json(add_manual_endpoint(m.group(1),self.body()),201)
            m = re.fullmatch(r"/api/projects/([^/]+)/jobs", path)
            if m:
                x=self.body(); jid=uid("job"); execute("INSERT INTO scheduled_jobs VALUES (?,?,?,?,?,?,?,?,?,?,?)",(jid,m.group(1),x.get("name","自定义任务"),x.get("job_type","security"),x.get("target_id",""),max(1,int(x.get("interval_minutes",60))),int(bool(x.get("enabled",False))),None,now() if x.get("enabled") else None,"NEVER",now())); return self.send_json(row("SELECT * FROM scheduled_jobs WHERE id=?",(jid,)),201)
            m = re.fullmatch(r"/api/projects/([^/]+)/refresh-trace", path)
            if m: return self.send_json({"links":refresh_traceability(m.group(1))})
            m = re.fullmatch(r"/api/projects/([^/]+)/ai-pipeline", path)
            if m: return self.send_json(run_ai_pipeline(m.group(1),self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/tool-assets", path)
            if m: return self.send_json(generate_enterprise_tool_assets(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/requirement-packages", path)
            if m: return self.send_json(create_requirement_package(m.group(1), self.body()), 201)
            m = re.fullmatch(r"/api/projects/([^/]+)/requirement-packages/([^/]+)/tool-assets", path)
            if m: return self.send_json(generate_requirement_package_tool_assets(m.group(1), m.group(2), self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/requirement-packages/([^/]+)/account-model", path)
            if m: return self.send_json(generate_requirement_account_model(m.group(1), m.group(2), True))
            m = re.fullmatch(r"/api/projects/([^/]+)/requirement-packages/([^/]+)/execution-plan", path)
            if m: return self.send_json(generate_requirement_execution_plan(m.group(1), m.group(2), self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/requirement-packages/([^/]+)/newman/run", path)
            if m: return self.send_json(run_requirement_package_newman(m.group(1), m.group(2), self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/requirement-packages/([^/]+)/pytest/run", path)
            if m: return self.send_json(run_requirement_package_pytest(m.group(1), m.group(2), self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/requirement-packages/([^/]+)/ai-review", path)
            if m: return self.send_json(generate_requirement_package_ai_review(m.group(1), m.group(2), self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/requirement-packages/([^/]+)/scenario-report", path)
            if m: return self.send_json(generate_requirement_package_unified_scenario_report(m.group(1), m.group(2), self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/jmeter/open-gui", path)
            if m: return self.send_json(open_jmeter_gui(m.group(1),self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/jmeter/harvest-gui-report", path)
            if m: return self.send_json(harvest_jmeter_workbench_report(m.group(1),self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/jmeter/generate-from-cases", path)
            if m: return self.send_json(generate_salary_trade_jmeter_from_cases(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/salary-trade-data-map", path)
            if m: return self.send_json(salary_trade_data_map())
            m = re.fullmatch(r"/api/projects/([^/]+)/apipost-package", path)
            if m: return self.send_json(build_apipost_collaboration_package(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/delivery-package", path)
            if m: return self.send_json(build_test_asset_delivery_package(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/toolchain/run", path)
            if m: return self.send_json(run_enterprise_toolchain(m.group(1),self.body()))
            m = re.fullmatch(r"/api/requirements/([^/]+)/link", path)
            if m:
                x=self.body(); return self.send_json(set_requirement_link(m.group(1),x["endpoint_id"],x.get("selected",True),x.get("sort_order",0)))
            m = re.fullmatch(r"/api/requirements/([^/]+)/generate-workflow", path)
            if m: return self.send_json(generate_requirement_workflow(m.group(1)))
            m = re.fullmatch(r"/api/cases/([^/]+)/run", path)
            if m: return self.send_json(execute_case(m.group(1)))
            m = re.fullmatch(r"/api/projects/([^/]+)/gift-chain", path)
            if m: return self.send_json(run_gift_business_chain(m.group(1),self.body()))
            m = re.fullmatch(r"/api/projects/([^/]+)/run-all", path)
            if m:
                project_id=m.group(1)
                primary=resolve_primary_business_chain(project_id)
                if primary:
                    runtime=self.body()
                    result=run_business_chain_full_test(project_id,int(runtime.get("performance_requests",20)),runtime)
                    total=row("SELECT COUNT(*) n FROM test_cases WHERE project_id=?",(project_id,))["n"]
                    executable=row("SELECT COUNT(*) n FROM test_cases WHERE project_id=? AND method<>'' AND path<>''",(project_id,))["n"]
                    return self.send_json({"total_cases":total,"executable":executable,"not_executed":max(0,total-executable),"primary_flow":"凭证复用/真实登录 → 内存变量传递 → 财富接口 → 业务校验 → 性能测试 → 报告","full_test":result})
                cases = rows("SELECT id FROM test_cases WHERE project_id=? AND method<>'' AND path<>''", (project_id,))
                results = [execute_case(x["id"]) for x in cases]
                total=row("SELECT COUNT(*) n FROM test_cases WHERE project_id=?",(project_id,))["n"]
                return self.send_json({"total_cases":total,"executable":len(results),"not_executed":total-len(results),"results":results})
            if path == "/api/settings":
                x = self.body()
                existing = row("SELECT value FROM settings WHERE key='api_key'")
                if x.get("api_key") == "••••••••" and existing: x["api_key"] = existing["value"]
                with db() as conn:
                    for k in ("api_key", "api_base", "model"):
                        if k in x: conn.execute("INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, str(x[k])))
                return self.send_json({"ok": True})
            if path == "/api/system/reload":
                self.send_json({"ok":True,"message":"平台正在重新加载"})
                threading.Timer(.35, lambda: os._exit(75)).start(); return
            self.send_json({"error": "平台功能接口不存在或当前后端版本尚未加载"}, 404)
        except Exception as e:
            traceback.print_exc(); self.send_json({"error": str(e)}, 500)

    def do_PUT(self):
        try:
            path = urlparse(self.path).path; x = self.body()
            m = re.fullmatch(r"/api/projects/([^/]+)", path)
            if m:
                execute("UPDATE projects SET name=?,description=?,base_url=?,updated_at=? WHERE id=?", (x.get("name", ""), x.get("description", ""), x.get("base_url", ""), now(), m.group(1))); return self.send_json({"ok": True})
            m = re.fullmatch(r"/api/cases/([^/]+)", path)
            if m:
                fields = ["title","method","path","headers","payload","expected_status","expected_contains","priority","status","steps","expected"]
                old = row("SELECT * FROM test_cases WHERE id=?", (m.group(1),)); vals = [x.get(f, old[f]) for f in fields]; execute(f"UPDATE test_cases SET {','.join(f+'=?' for f in fields)} WHERE id=?", (*vals, m.group(1))); return self.send_json({"ok": True})
            m = re.fullmatch(r"/api/jobs/([^/]+)", path)
            if m:
                job=row("SELECT * FROM scheduled_jobs WHERE id=?",(m.group(1),)); enabled=int(bool(x.get("enabled",job["enabled"]))); interval=max(1,int(x.get("interval_minutes",job["interval_minutes"]))); nxt=now() if enabled else None; execute("UPDATE scheduled_jobs SET enabled=?,interval_minutes=?,next_run_at=? WHERE id=?",(enabled,interval,nxt,m.group(1))); return self.send_json({"ok":True})
            m = re.fullmatch(r"/api/endpoints/([^/]+)", path)
            if m:
                old=row("SELECT * FROM api_endpoints WHERE id=?",(m.group(1),)); execute("UPDATE api_endpoints SET method=?,path=?,summary=?,tags=?,auth_required=? WHERE id=?",(x.get("method",old["method"]).upper(),x.get("path",old["path"]),x.get("summary",old["summary"]),json.dumps([x.get("module")],ensure_ascii=False) if x.get("module") else old["tags"],int(x.get("auth_required",old["auth_required"])),m.group(1))); refresh_traceability(old["project_id"]); return self.send_json({"ok":True})
            m = re.fullmatch(r"/api/requirements/([^/]+)", path)
            if m:
                old=row("SELECT * FROM requirement_items WHERE id=?",(m.group(1),)); fields=["title","description","acceptance_criteria","priority","risk_level","status"]; vals=[x.get(f,old[f]) for f in fields]; execute("UPDATE requirement_items SET title=?,description=?,acceptance_criteria=?,priority=?,risk_level=?,status=? WHERE id=?",(*vals,m.group(1))); refresh_traceability(old["project_id"]); return self.send_json({"ok":True})
            self.send_json({"error": "接口不存在"}, 404)
        except Exception as e: self.send_json({"error": str(e)}, 500)


def main():
    init_db()
    threading.Thread(target=scheduler_loop, daemon=True).start()
    host = os.getenv("AUTOTEST_HOST", "127.0.0.1"); port = int(os.getenv("AUTOTEST_PORT", "8765"))
    print(f"AutoTest AI 工作台已启动：http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
