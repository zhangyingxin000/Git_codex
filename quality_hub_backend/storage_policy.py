from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StorageBoundary:
    name: str
    write_allowed: bool
    purpose: str
    migration_scope: str


PLATFORM_STORAGE = StorageBoundary(
    name="platform_local_storage",
    write_allowed=True,
    purpose="保存项目、需求、接口资产、规则、映射、执行证据、报告索引和诊断结果",
    migration_scope="后续可迁移到 MySQL/PostgreSQL",
)

COMPANY_MYSQL = StorageBoundary(
    name="company_mysql",
    write_allowed=False,
    purpose="只读查询真实业务数据，用于核对接口结果和沉淀验证证据",
    migration_scope="不迁移、不回写，只保存脱敏证据和映射配置",
)

COMPANY_REDIS = StorageBoundary(
    name="company_redis",
    write_allowed=False,
    purpose="只读读取缓存 Key、TTL 和快照，用于数据一致性验证",
    migration_scope="不迁移、不回写，只保存只读快照摘要",
)


def storage_boundaries() -> list[StorageBoundary]:
    return [PLATFORM_STORAGE, COMPANY_MYSQL, COMPANY_REDIS]
