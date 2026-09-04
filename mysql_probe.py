"""Minimal read-only MySQL metadata probe. Credentials come only from env vars."""

import hashlib
import os
import socket
import struct

HOST = os.environ["AUTOTEST_DB_HOST"]
PORT = int(os.getenv("AUTOTEST_DB_PORT", "3306"))
USER = os.environ["AUTOTEST_DB_USER"]
PASSWORD = os.environ["AUTOTEST_DB_PASSWORD"].encode()
DATABASE = os.environ["AUTOTEST_DB_NAME"]


def packet(sock):
    h = sock.recv(4)
    if len(h) < 4:
        raise RuntimeError("MySQL connection closed")
    n = h[0] | h[1] << 8 | h[2] << 16
    b = b""
    while len(b) < n:
        b += sock.recv(n - len(b))
    return b


def send(sock, b, seq=0):
    sock.sendall(struct.pack("<I", len(b))[:3] + bytes([seq]) + b)


def nul(b, p):
    q = b.index(0, p)
    return b[p:q], q + 1


def native(password, salt):
    a = hashlib.sha1(password).digest()
    b = hashlib.sha1(a).digest()
    c = hashlib.sha1(salt + a and salt + a).digest()
    return bytes(x ^ y for x, y in zip(a, c))


def caching(password, salt):
    a = hashlib.sha256(password).digest()
    b = hashlib.sha256(a).digest()
    c = hashlib.sha256(b + salt).digest()
    return bytes(x ^ y for x, y in zip(a, c))


def lenc(b, p):
    x = b[p]
    if x < 0xFB:
        return x, p + 1
    if x == 0xFC:
        return struct.unpack_from("<H", b, p + 1)[0], p + 3
    if x == 0xFD:
        return int.from_bytes(b[p + 1 : p + 4], "little"), p + 4
    if x == 0xFE:
        return struct.unpack_from("<Q", b, p + 1)[0], p + 9
    return 0, p + 1


def query(sock, sql):
    normalized = " ".join(str(sql).strip().split())
    first = (normalized.split(" ", 1)[0] if normalized else "").upper()
    if first not in {"SELECT", "SHOW", "DESCRIBE", "DESC", "EXPLAIN"}:
        raise RuntimeError("只读策略禁止MySQL命令: " + first)
    if ";" in normalized.rstrip(";") or any(
        token in (" " + normalized.upper() + " ")
        for token in (
            " FOR UPDATE ",
            " INTO OUTFILE ",
            " INTO DUMPFILE ",
            " LOCK IN SHARE MODE ",
        )
    ):
        raise RuntimeError("只读策略禁止多语句、锁定或文件输出查询")
    send(sock, b"\x03" + sql.encode(), 0)
    first = packet(sock)
    if first[0] == 0xFF:
        raise RuntimeError(first[3:].decode("utf8", "replace"))
    count, _ = lenc(first, 0)
    for _ in range(count):
        packet(sock)
    packet(sock)
    out = []
    while True:
        r = packet(sock)
        if r[0] in (0xFE, 0x00) and len(r) < 9:
            break
        vals = []
        p = 0
        for _ in range(count):
            n, p = lenc(r, p)
            vals.append(r[p : p + n].decode("utf8", "replace"))
            p += n
        out.append(vals)
    return out


s = socket.create_connection((HOST, PORT), 8)
s.settimeout(10)
h = packet(s)
p = 1
server, p = nul(h, p)
p += 4
salt1 = h[p : p + 8]
p += 9
cap_low = struct.unpack_from("<H", h, p)[0]
p += 2
charset = h[p]
p += 1 + 2
cap_high = struct.unpack_from("<H", h, p)[0]
caps = cap_low | (cap_high << 16)
p += 2
auth_len = h[p]
p += 1 + 10
salt2 = h[p : p + max(13, auth_len - 8)]
p += max(13, auth_len - 8)
salt = (salt1 + salt2).rstrip(b"\0")
plugin = (h[p:].split(b"\0")[0] if p < len(h) else b"mysql_native_password").decode()
CLIENT_PROTOCOL_41 = 0x200
CLIENT_SECURE_CONNECTION = 0x8000
CLIENT_PLUGIN_AUTH = 0x80000
CLIENT_CONNECT_WITH_DB = 0x8
flags = (
    CLIENT_PROTOCOL_41
    | CLIENT_SECURE_CONNECTION
    | CLIENT_PLUGIN_AUTH
    | CLIENT_CONNECT_WITH_DB
)
auth = (
    caching(PASSWORD, salt)
    if plugin == "caching_sha2_password"
    else native(PASSWORD, salt)
)
resp = (
    struct.pack("<IIB23s", flags, 16 * 1024 * 1024, charset, b"")
    + USER.encode()
    + b"\0"
    + bytes([len(auth)])
    + auth
    + DATABASE.encode()
    + b"\0"
    + plugin.encode()
    + b"\0"
)
send(s, resp, 1)
r = packet(s)
if r[0] == 0xFF:
    raise RuntimeError(r[3:].decode("utf8", "replace"))
if r[0] == 1 and len(r) > 1 and r[1] == 4:
    raise RuntimeError("服务器要求 caching_sha2 完整认证；需要正式 MySQL 驱动或 SSL")
if r[0] == 1 and len(r) > 1 and r[1] == 3:
    r = packet(s)
if r[0] not in (0,):
    raise RuntimeError("不支持的认证响应: " + r.hex())
dbq = DATABASE.replace("'", "''")
tables = query(
    s,
    "SELECT TABLE_NAME, TABLE_TYPE, COALESCE(TABLE_COMMENT,''), COALESCE(TABLE_ROWS,0) FROM information_schema.TABLES WHERE TABLE_SCHEMA='"
    + dbq
    + "' ORDER BY TABLE_NAME",
)
columns = query(
    s,
    "SELECT TABLE_NAME,COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_KEY,COALESCE(COLUMN_DEFAULT,''),EXTRA,COALESCE(COLUMN_COMMENT,'') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='"
    + dbq
    + "' ORDER BY TABLE_NAME,ORDINAL_POSITION",
)
indexes = query(
    s,
    "SELECT TABLE_NAME,INDEX_NAME,NON_UNIQUE,SEQ_IN_INDEX,COLUMN_NAME FROM information_schema.STATISTICS WHERE TABLE_SCHEMA='"
    + dbq
    + "' ORDER BY TABLE_NAME,INDEX_NAME,SEQ_IN_INDEX",
)
relations = query(
    s,
    "SELECT TABLE_NAME,COLUMN_NAME,REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME,CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA='"
    + dbq
    + "' AND REFERENCED_TABLE_NAME IS NOT NULL ORDER BY TABLE_NAME,COLUMN_NAME",
)
result = {
    "connected": True,
    "server": server.decode(),
    "database": DATABASE,
    "table_count": len(tables),
    "column_count": len(columns),
    "index_count": len(indexes),
    "relation_count": len(relations),
    "tables": tables,
    "columns": columns,
    "indexes": indexes,
    "relations": relations,
}
import json

out = os.getenv("AUTOTEST_SCHEMA_OUTPUT")
if out:
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
print(
    json.dumps(
        {
            k: result[k]
            for k in (
                "connected",
                "server",
                "database",
                "table_count",
                "column_count",
                "index_count",
                "relation_count",
            )
        },
        ensure_ascii=False,
    )
)
s.close()
