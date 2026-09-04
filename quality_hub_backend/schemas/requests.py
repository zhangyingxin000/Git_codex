from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class BackgroundTaskCreateRequest(BaseModel):
    task_type: str = Field(min_length=1, max_length=64)
    project_id: str = Field(default="", max_length=128)
    package_id: str = Field(default="", max_length=128)
    options: dict[str, Any] = Field(default_factory=dict)


class ProjectCreateRequest(BaseModel):
    name: str = Field(default="未命名项目", description="项目名称")
    description: str = Field(default="", description="项目说明")
    base_url: str = Field(default="", description="测试环境 Base URL")


class SourceCreateRequest(BaseModel):
    name: str = Field(default="资料", description="资料或迭代名称")
    kind: Literal["requirement", "openapi", "har", "rules"] = Field(default="requirement", description="资料类型")
    content: str = Field(default="", description="粘贴的需求、规则、OpenAPI 或 HAR 内容")
    source_url: str = Field(default="", description="需求文档或接口文档链接")
    browser_capture: bool = Field(default=False, description="是否启用网页登录采集")
    file_name: str = Field(default="", description="上传文件名")
    file_base64: str = Field(default="", description="上传文件内容，Base64")
    requirement_source_id: str = Field(default="", description="关联需求资料 ID")
    batch_name: str = Field(default="", description="接口变更批次名称")


class TestAccountSaveRequest(BaseModel):
    nickname: str = Field(default="", description="账号昵称")
    short_id: str = Field(description="短 ID")
    uid: int = Field(description="账号 UID")
    wealth_level: int | None = Field(default=None, description="财富等级")
    role: Literal["general", "sender", "receiver", "boundary"] = Field(default="general", description="账号用途")
    mutable: bool = Field(default=False, description="是否允许执行会改变业务数据的场景")
    ticket: str = Field(default="", description="可复用 Ticket，保存时本机加密")
    encrypted_password: str = Field(default="", description="加密密码，保存时本机加密")


class RedisSourceCreateRequest(BaseModel):
    name: str = Field(default="Redis测试数据源", description="连接名称")
    host: str = Field(description="Redis Host")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis Port")
    db_no: int = Field(default=0, ge=0, le=1024, description="Redis DB 编号")
    use_tls: bool = Field(default=False, description="是否使用 TLS")


class RedisScanRequest(BaseModel):
    pattern: str = Field(default="*", description="Key 匹配模式")
    limit: int = Field(default=100, ge=1, le=500, description="最多返回 Key 数")


class RedisInspectRequest(BaseModel):
    key: str = Field(description="要查看的 Redis Key")


class GenerateFromSourceRequest(BaseModel):
    source_id: str = Field(description="资料 ID")
    force: bool = Field(default=False, description="是否强制生成")


class ProjectRuntimeRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    performance_requests: int = Field(default=20, ge=1, le=100, description="快速性能冒烟请求次数")
    run_jmeter: bool = Field(default=True, description="是否调用 JMeter")
    extra: dict[str, Any] = Field(default_factory=dict, description="预留运行参数")
