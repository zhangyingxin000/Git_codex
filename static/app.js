let projects=[], current=null, data=null, pendingFile=null, wealthLastResult=null, activeResourceManifest=null;const PAGE_BUILD=document.documentElement.dataset.build||'';
const {request:api,select:$,selectAll:$$,escapeHtml:esc}=window.QualityHub.services.api;
const requirementPackagesApi=window.QualityHub.services.requirementPackages;
let toast=window.QualityHub.components.notifications.toast;
document.addEventListener('change',e=>{if(e.target&&e.target.id==='toolPerfProfile')applyPerformanceProfile()});
async function loadProjects(){projects=await api("/api/projects");$("#projects").innerHTML=projects.map(p=>`<button class="project ${current===p.id?'active':''}" onclick="openProject('${p.id}')">◫　${esc(p.name)}</button>`).join("")}
async function openProject(id){current=id;await loadProjects();data=await api(`/api/projects/${id}/dashboard`);data.capture_reports=[];data.redis_mappings=[];data.toolchain={tools:[],artifacts:[],blockers:[],loading:true};data.case_jmeter_model=null;$("#welcome").classList.add("hidden");$("#workspace").classList.remove("hidden");$("#pageTitle").textContent=data.project.name;$("#subtitle").textContent=data.project.description||"AI 自主测试控制中心";render();Promise.all([api(`/api/projects/${id}/capture-reports`).catch(()=>[]),api(`/api/projects/${id}/redis-mappings`).catch(()=>[]),api(`/api/projects/${id}/toolchain`).catch(()=>({tools:[],artifacts:[],blockers:[]})),api(`/api/projects/${id}/jmeter/case-script-model`).catch(()=>null)]).then(extras=>{if(current!==id)return;data.capture_reports=extras[0];data.redis_mappings=extras[1];data.toolchain=extras[2];data.case_jmeter_model=extras[3];render()})}
function render(){let pass=data.runs.filter(x=>x.status==='PASSED').length,fail=data.runs.filter(x=>['FAILED','ERROR'].includes(x.status)).length,rate=data.runs.length?Math.round(pass/data.runs.length*100):0;$("#metrics").innerHTML=[["接口资产",data.endpoints?.length||0],["测试点",data.points.length],["测试用例",data.cases.length],["最近通过率",rate+'%']].map(x=>`<div class="metric"><span>${x[0]}</span><b>${x[1]}</b></div>`).join('');
  $("#overview").innerHTML=`<div class="grid2"><div class="card"><h3>测试资产概况</h3><p>已归纳 <b>${data.points.length}</b> 个测试点，生成 <b>${data.cases.length}</b> 条用例。</p><div class="bar"><i style="width:${Math.min(100,data.cases.length*4)}%"></i></div><p style="color:var(--muted);font-size:12px">继续导入需求或接口定义可扩大覆盖范围。</p></div><div class="card"><h3>执行健康度</h3><p><b>${pass}</b> 通过 · <b>${fail}</b> 异常 · <b>${data.runs.length}</b> 次执行</p><div class="bar"><i style="width:${rate}%"></i></div><p style="color:var(--muted);font-size:12px">项目 Base URL：<code>${esc(data.project.base_url||'尚未配置')}</code></p><button class="small" onclick="editProject()">配置项目</button></div></div><div class="card"><h3>AI 下一步建议</h3>${suggestions()}</div>`;
  $("#sources").innerHTML=`<div class="grid2"><div class="card"><h3>添加迭代资料</h3><label>资料名称 / 迭代名称</label><input id="srcName" placeholder="例如：V2.3 房间PK需求"><label>资料类型</label><select id="srcKind"><option value="requirement">需求文档</option><option value="openapi">OpenAPI / Swagger</option><option value="har">HAR 抓包文件</option><option value="rules">测试规则与约束</option></select><label>关联需求（接口文档可选）</label><select id="requirementSource"><option value="">不关联</option>${data.sources.filter(s=>s.kind==='requirement').map(s=>`<option value="${s.id}">${esc(s.name)}</option>`).join('')}</select><label>粘贴文本、JSON、YAML 或 HAR</label><textarea id="srcContent" placeholder="在此粘贴需求、OpenAPI 或 HAR 内容…"></textarea><label>或读取本地文件</label><input type="file" id="srcFile" accept=".txt,.md,.json,.yaml,.yml,.har"><button class="primary" onclick="addSource()">保存并分析变更</button></div><div class="card"><h3>已导入资料</h3>${data.sources.length?data.sources.map(s=>`<div style="padding:12px 0;border-bottom:1px solid var(--line)"><b>${esc(s.name)}</b><span class="tag" style="float:right">${esc(s.kind)}</span><p style="font-size:11px;color:var(--muted)">${s.created_at}</p><button class="small" onclick="generate('${s.id}')">✦ AI 增量生成</button></div>`).join(''):'<div class="empty">尚未导入资料</div>'}</div></div>`;
  decorateSources();$("#srcContent")?.insertAdjacentHTML('beforebegin','<label>需求/文档链接（可选）</label><input id="srcUrl" placeholder="https://docs.example.com/requirement"><label><input id="browserCapture" type="checkbox" style="width:auto"> 使用网页登录采集器（支持登录、动态长页面、图文）</label>');if($("#srcFile"))$("#srcFile").accept='.txt,.md,.json,.yaml,.yml,.har,.docx,.pdf,.png,.jpg,.jpeg,.webp,.zip';$("#manual").innerHTML=tableManualV2();$("#changes").innerHTML=tableChanges();$("#apis").innerHTML=tableApis();$("#flows").innerHTML=tableFlows();$("#automation").innerHTML=tableAutomation();$("#operations").innerHTML=tableOperations();$("#points").innerHTML=tablePoints();$("#cases").innerHTML=tableCases();enhanceCaseLifecycleTable();$("#database").innerHTML=tableDatabase();$("#redis").innerHTML=tableRedis();$("#runs").innerHTML=tableRuns();bindFile()}
function decorateSources(){for(const r of data.capture_reports||[]){const button=$$('#sources button').find(b=>b.getAttribute('onclick')===`generate('${r.source_id}')`);if(!button)continue;let blockers=[];try{blockers=JSON.parse(r.blockers||'[]')}catch{};const color=r.status==='passed'?'PASSED':r.status==='review'?'P1':'P0';button.insertAdjacentHTML('beforebegin',`<p><span class="tag ${color}">采集完整性 ${r.score}% · ${r.status}</span></p>${blockers.length?`<small style="color:var(--danger)">${esc(blockers.join('；'))}</small><br>`:''}`);if(r.status==='blocked'){button.disabled=true;button.insertAdjacentHTML('afterend',` <button class="small" onclick="generate('${r.source_id}',true)">人工强制生成</button>`)}}}
function suggestions(){let s=[];if(!data.sources.length)s.push('先导入需求文档、OpenAPI 或 HAR 抓包记录。');if(!data.project.base_url)s.push('配置测试环境 Base URL 后即可执行接口用例。');if(data.sources.length&&!data.points.length)s.push('选择已导入资料，运行 AI 测试资产生成。');if(data.runs.some(x=>x.status==='FAILED'))s.push('存在失败用例，应核对响应证据并确认是产品缺陷还是断言偏差。');if(!s.length)s.push('当前闭环已经建立，可以继续补充资料或执行回归。');return `<ul>${s.map(x=>`<li>${x}</li>`).join('')}</ul>`}
function tableManual(){let reqs=data.requirement_items||[],links=data.trace_links||[],jobs=data.scheduled_jobs||[];return `<div class="grid2"><div class="card"><h3>手工新增接口</h3><div class="formrow"><select id="manualMethod"><option>GET</option><option>POST</option><option>PUT</option><option>PATCH</option><option>DELETE</option></select><input id="manualModule" placeholder="业务模块"></div><label>接口路径</label><input id="manualPath" placeholder="/users/{id}"><label>接口名称</label><input id="manualSummary" placeholder="查询用户详情"><label><input id="manualAuth" type="checkbox" style="width:auto"> 需要认证</label><button class="primary" onclick="addManualApi()">新增接口</button></div><div class="card"><h3>自定义定时任务</h3><label>任务名称</label><input id="jobName" placeholder="每日核心回归"><div class="formrow"><select id="jobType"><option value="security">安全扫描</option><option value="suite">接口套件</option><option value="workflow">业务流程</option><option value="performance">性能计划</option></select><input id="jobTarget" placeholder="目标ID（安全扫描可空）"></div><label>执行间隔（分钟）</label><input id="jobInterval" type="number" value="1440" min="1"><label><input id="jobEnabled" type="checkbox" style="width:auto"> 创建后立即启用</label><button class="primary" onclick="addCustomJob()">创建任务</button></div></div><div class="card"><h3>需求结构化与完整追踪</h3><p style="font-size:12px;color:var(--muted)">需求条目 ${reqs.length} 个，已建立 ${links.length} 条需求→接口/用例/流程/数据库追踪关系。</p><button class="small" onclick="refreshTrace()">重新计算追踪链</button>${reqs.length?`<table><thead><tr><th>优先级</th><th>需求/规则</th><th>类型</th><th>风险</th><th>关联资产</th><th></th></tr></thead><tbody>${reqs.map((r,i)=>`<tr><td><span class="tag ${r.priority}">${r.priority}</span></td><td><b>${esc(r.title)}</b><br><small>${esc(r.acceptance_criteria)}</small></td><td>${esc(r.item_type)}</td><td>${esc(r.risk_level)}</td><td>${links.filter(x=>x.requirement_id===r.id).length}</td><td><button class="small" onclick="editRequirement(${i})">编辑</button></td></tr>`).join('')}</tbody></table>`:'<div class="empty">在“资料与生成”中上传需求文档或填写需求描述</div>'}</div>`}
function tableManualV2(){let reqs=data.requirement_items||[],links=data.trace_links||[];return `<div class="card" style="background:#153c2c;color:white"><span style="color:var(--lime);font-size:11px">ONE-CLICK AI PIPELINE</span><h2>需求 + 注意事项 + 接口文档，一键生成完整测试流水线</h2><p style="color:#c2d3ca">自动完成需求拆解、候选接口筛选、测试点、用例、接口自动化、业务流程、性能、异常、安全、UI脚本、调度和报告。</p><button class="primary" onclick="runPipeline()">✦ AI一条龙运行</button></div><div class="grid2"><div class="card"><h3>手工新增接口</h3><div class="formrow"><select id="manualMethod"><option>GET</option><option>POST</option><option>PUT</option><option>PATCH</option><option>DELETE</option></select><input id="manualModule" placeholder="业务模块"></div><label>接口路径</label><input id="manualPath" placeholder="/users/{id}"><label>接口名称</label><input id="manualSummary" placeholder="查询用户详情"><label><input id="manualAuth" type="checkbox" style="width:auto"> 需要认证</label><button class="primary" onclick="addManualApi()">新增接口</button></div><div class="card"><h3>自定义定时任务</h3><label>任务名称</label><input id="jobName" placeholder="每日核心回归"><div class="formrow"><select id="jobType"><option value="security">安全扫描</option><option value="suite">接口套件</option><option value="workflow">业务流程</option><option value="performance">性能计划</option></select><input id="jobTarget" placeholder="目标ID（安全扫描可空）"></div><label>间隔（分钟）</label><input id="jobInterval" type="number" value="1440"><label><input id="jobEnabled" type="checkbox" style="width:auto"> 立即启用</label><button class="primary" onclick="addCustomJob()">创建任务</button></div></div><div class="card"><h3>需求驱动的多接口筛选</h3><p style="font-size:12px;color:var(--muted)">AI为每条需求从全部接口中推荐最多50个候选，你拥有最终选择权。</p><button class="small" onclick="refreshTrace()">重新筛选候选接口</button>${reqs.length?`<table><thead><tr><th>需求</th><th>候选</th><th>已选择</th><th>完整流程</th></tr></thead><tbody>${reqs.map((r,i)=>{let xs=links.filter(x=>x.requirement_id===r.id&&x.target_type==='endpoint');return `<tr><td><b>${esc(r.title)}</b><br><small>${esc(r.acceptance_criteria)}</small></td><td>${xs.length}</td><td>${xs.filter(x=>x.selected).length}</td><td><button class="small" onclick="showCandidates(${i})">筛选接口</button> <button class="small" onclick="generateRequirementFlow('${r.id}')">生成需求流程</button> <button class="small" onclick="editRequirement(${i})">编辑需求</button></td></tr>`}).join('')}</tbody></table>`:'<div class="empty">先在“资料与生成”上传需求文档和需求注意事项</div>'}</div>`}
function tableChanges(){let bs=data.batches||[],cs=data.changes||[];if(!bs.length)return '<div class="empty"><b>暂无接口版本</b>导入OpenAPI或HAR后自动记录新增、修改、删除和未变化接口</div>';return `<div class="card"><h3>增量迭代历史</h3><p style="font-size:12px;color:var(--muted)">接口资料自动与当前资产对比，只为新增和修改接口生成增量测试。</p></div>${bs.map(b=>`<div class="card"><span class="tag">V${b.version_no}</span><h3 style="display:inline;margin-left:10px">${esc(b.name)}</h3><p><span class="tag PASSED">新增 ${b.added_count}</span>　<span class="tag P1">修改 ${b.modified_count}</span>　<span class="tag P0">删除 ${b.removed_count}</span>　<span class="tag">未变 ${b.unchanged_count}</span></p><small>${b.created_at}</small>${(()=>{let xs=cs.filter(c=>c.batch_id===b.id);return xs.length?`<table style="margin-top:12px"><tbody>${xs.slice(0,30).map(c=>`<tr><td><span class="tag ${c.change_type==='added'?'PASSED':c.change_type==='removed'?'P0':'P1'}">${c.change_type}</span></td><td><code>${esc(c.endpoint_key)}</code></td><td>${esc(c.summary)}</td><td>${esc(c.impact)}</td></tr>`).join('')}</tbody></table>`:''})()}</div>`).join('')}`}
function tablePoints(){if(!data.points.length)return '<div class="empty"><b>暂无测试点</b>从项目资料中生成测试分析</div>';return `<table><thead><tr><th>优先级</th><th>模块</th><th>测试点</th><th>类型</th><th>风险</th><th>依据</th></tr></thead><tbody>${data.points.map(x=>`<tr><td><span class="tag ${x.priority}">${x.priority}</span></td><td>${esc(x.module)}</td><td><b>${esc(x.title)}</b></td><td>${esc(x.category)}</td><td>${esc(x.risk)}</td><td>${esc(x.rationale)}</td></tr>`).join('')}</tbody></table>`}
function tableFlows(){let fs=data.workflows||[];if(!fs.length)return `<div class="card empty"><b>尚未生成业务流程</b><p>AI会根据接口标签、路径、方法和风险自动组织跨步骤场景。</p><button class="primary" onclick="generateFlows()">✦ 生成业务流程</button></div>`;return `<div class="card"><h3>AI业务流程</h3><p style="font-size:12px;color:var(--muted)">共 ${fs.length} 条流程、${(data.workflow_steps||[]).length} 个步骤。流程按 setup → action → verify 串行执行。</p><button class="small" onclick="generateFlows()">重新归纳流程</button></div><div class="grid2">${fs.map((x,i)=>{let steps=(data.workflow_steps||[]).filter(s=>s.workflow_id===x.id);return `<div class="card"><span class="tag ${x.risk_level==='high'?'P0':x.risk_level==='medium'?'P1':'PASSED'}">${x.risk_level}</span><h3 style="margin-top:12px">${esc(x.name)}</h3><p style="font-size:12px;color:var(--muted)">${esc(x.description)}</p><div>${steps.slice(0,5).map(s=>`<div style="padding:7px 0;border-bottom:1px solid var(--line)"><small>${s.step_order}. ${esc(s.name)} · ${s.phase}</small></div>`).join('')}${steps.length>5?`<small>还有 ${steps.length-5} 个步骤</small>`:''}</div><button class="small" onclick="showFlow(${i})">查看流程</button> <button class="small" onclick="runFlow('${x.id}')">▶ 执行</button></div>`}).join('')}</div>`}
function tableAutomation(){let suites=data.automation_suites||[],plans=data.performance_plans||[],faults=data.fault_scenarios||[];if(!suites.length&&!plans.length&&!faults.length)return `<div class="card empty"><b>尚未生成非功能测试资产</b><p>将自动建立接口套件、性能基准和异常注入场景。</p><button class="primary" onclick="generateNonfunctional()">✦ 生成自动化/性能/异常测试</button></div>`;return `<div class="metrics"><div class="metric"><span>自动化套件</span><b>${suites.length}</b></div><div class="metric"><span>性能计划</span><b>${plans.length}</b></div><div class="metric"><span>异常场景</span><b>${faults.length}</b></div><div class="metric"><span>极高危险</span><b>${faults.filter(x=>x.danger_score>=80).length}</b></div></div><div class="card"><button class="small" onclick="generateNonfunctional()">重新生成</button><h3>接口自动化套件</h3>${suites.slice(0,20).map(x=>`<div style="padding:9px;border-bottom:1px solid var(--line)"><b>${esc(x.name)}</b> · ${JSON.parse(x.case_ids||'[]').length}条用例 <button class="small" style="float:right" onclick="runSuite('${x.id}')">执行套件</button></div>`).join('')}</div><div class="grid2"><div class="card"><h3>性能基准计划</h3>${plans.slice(0,20).map(x=>`<div style="padding:9px;border-bottom:1px solid var(--line)"><b>${esc(x.name)}</b><br><small>并发 ${x.concurrency} · 请求 ${x.total_requests} · P95警戒 ${x.warning_p95_ms}ms · 危险系数 ${x.danger_score}</small><button class="small" style="float:right" onclick="runPerformance('${x.id}')">压测</button></div>`).join('')}</div><div class="card"><h3>异常与故障场景</h3>${faults.slice(0,30).map(x=>`<div style="padding:9px;border-bottom:1px solid var(--line)"><span class="tag ${x.danger_score>=80?'P0':x.danger_score>=60?'P1':''}">${x.danger_score}</span> <b>${esc(x.name)}</b><br><small>${esc(x.fault_type)} · ${esc(x.warning)}</small></div>`).join('')}</div></div>`}
function tableOperations(){let scans=data.security_scans||[],findings=data.security_findings||[],uis=data.ui_test_plans||[],jobs=data.scheduled_jobs||[];if(!uis.length&&!jobs.length)return `<div class="card empty"><b>尚未生成安全、UI和调度资产</b><p>生成被动安全检查、Playwright脚本及每日自动任务。</p><button class="primary" onclick="generateOperations()">✦ 生成运维自动化资产</button></div>`;let latest=scans[0];return `<div class="metrics"><div class="metric"><span>安全评分</span><b>${latest?latest.score:'-'}</b></div><div class="metric"><span>安全发现</span><b>${findings.length}</b></div><div class="metric"><span>UI计划</span><b>${uis.length}</b></div><div class="metric"><span>定时任务</span><b>${jobs.length}</b></div></div><div class="grid2"><div class="card"><h3>被动安全扫描</h3><button class="small" onclick="runSecurity()">立即扫描</button>${findings.slice(0,20).map(x=>`<div style="padding:9px;border-bottom:1px solid var(--line)"><span class="tag ${x.severity==='high'?'P0':x.severity==='medium'?'P1':''}">${x.severity}</span> <b>${esc(x.title)}</b><br><small>${esc(x.target)} · ${esc(x.evidence)}</small></div>`).join('')}</div><div class="card"><h3>Web UI自动化计划</h3>${uis.map((x,i)=>`<div style="padding:9px;border-bottom:1px solid var(--line)"><b>${esc(x.name)}</b><br><small>${esc(x.page_url)}</small><button class="small" style="float:right" onclick="showUiPlan(${i})">脚本</button></div>`).join('')}</div></div><div class="card"><h3>定时任务</h3>${jobs.map(x=>`<div style="padding:10px;border-bottom:1px solid var(--line)"><span class="tag ${x.enabled?'PASSED':''}">${x.enabled?'已启用':'已停用'}</span> <b>${esc(x.name)}</b> · 每${x.interval_minutes}分钟 · 最近 ${esc(x.last_status)}<span style="float:right"><button class="small" onclick="runJob('${x.id}')">立即运行</button> <button class="small" onclick="toggleJob('${x.id}',${x.enabled?0:1},${x.interval_minutes})">${x.enabled?'停用':'启用'}</button></span></div>`).join('')}</div>`}
function tableApis(){let eps=data.endpoints||[];if(!eps.length)return '<div class="empty"><b>暂无接口资产</b>导入OpenAPI或HAR后自动建立接口目录</div>';let counts={low:0,medium:0,high:0};eps.forEach(x=>counts[x.risk_level]++);return `<div class="card"><h3>风险分布</h3><span class="tag PASSED">低风险 ${counts.low}</span>　<span class="tag P1">中风险 ${counts.medium}</span>　<span class="tag P0">高风险 ${counts.high}</span><p style="font-size:12px;color:var(--muted)">测试环境已允许全部HTTP方法；风险等级用于排序、审查和报告，目标域名仍受白名单限制。</p><div class="formrow"><input id="apiSearch" placeholder="搜索路径、摘要或标签" oninput="filterRows('apiRows',this.value,$('#apiRisk').value)"><select id="apiRisk" onchange="filterRows('apiRows',$('#apiSearch')?.value||'',this.value)"><option value="">全部风险</option><option value="low">低风险</option><option value="medium">中风险</option><option value="high">高风险</option></select></div></div><table><thead><tr><th>风险</th><th>方法</th><th>接口</th><th>摘要</th><th>标签</th><th></th></tr></thead><tbody id="apiRows">${eps.map((x,i)=>`<tr data-risk="${x.risk_level}" data-search="${esc((x.method+' '+x.path+' '+x.summary+' '+x.tags).toLowerCase())}"><td><span class="tag ${x.risk_level==='high'?'P0':x.risk_level==='medium'?'P1':'PASSED'}">${x.risk_level}</span></td><td><code>${x.method}</code></td><td><code>${esc(x.path)}</code></td><td>${esc(x.summary)}<br><small>${esc(x.risk_reason)}</small></td><td>${esc(JSON.parse(x.tags||'[]').join(' / '))}</td><td><button class="small" onclick="showApi(${i})">详情</button></td></tr>`).join('')}</tbody></table>`}
function tableCases(){if(!data.cases.length)return '<div class="empty"><b>暂无测试用例</b>AI 生成后将在此处管理</div>';let labels={NOT_RUN:'未执行',PASSED:'通过',FAILED:'失败',BLOCKED:'阻塞',ERROR:'环境异常',ASSERTION_PASSED:'原子断言通过'},counts={},lifeCounts={};data.cases.forEach(x=>{counts[x.execution_status||'NOT_RUN']=(counts[x.execution_status||'NOT_RUN']||0)+1;let life=(x.lifecycle_status||'ACTIVE').toUpperCase();lifeCounts[life]=(lifeCounts[life]||0)+1});return `<div class="card"><h3>需求驱动用例集</h3><p style="font-size:12px;color:var(--muted)">生命周期控制用例是否可进入回归和执行；执行状态只记录最近一次运行结果。</p><p>${['DRAFT','ACTIVE','DEPRECATED'].map(k=>`<span class="tag ${k==='ACTIVE'?'PASSED':k==='DRAFT'?'P1':''}">${k} ${lifeCounts[k]||0}</span>`).join(' ')}　${Object.entries(counts).map(([k,v])=>`<span class="tag ${k}">${labels[k]||k} ${v}</span>`).join(' ')}</p><div class="formrow"><input id="caseSearch" placeholder="搜索标题、场景、需求依据或执行器" oninput="filterCaseRows()"><select id="caseExecutorFilter" onchange="filterCaseRows()"><option value="">全部执行器</option><option value="http">真实HTTP</option><option value="workflow">关联流程</option><option value="api_db">接口+数据库</option><option value="db_redis">数据库+Redis</option><option value="ui_device">UI真机</option><option value="api_ui">接口+UI</option><option value="performance_ui">性能+UI</option><option value="api_security">安全接口</option></select><select id="caseLifecycleFilter" onchange="filterCaseRows()"><option value="">全部生命周期</option><option value="DRAFT">DRAFT</option><option value="ACTIVE">ACTIVE</option><option value="DEPRECATED">DEPRECATED</option></select></div></div><table><thead><tr><th>优先级</th><th>用例 / 需求依据</th><th>场景 / 执行器</th><th>预期结果</th><th>生命周期</th><th>执行状态</th><th></th></tr></thead><tbody id="caseRows">${data.cases.map(x=>{let st=x.execution_status||'NOT_RUN',life=(x.lifecycle_status||'ACTIVE').toUpperCase(),canRun=life==='ACTIVE';return `<tr data-risk="${esc(x.executor_type||'manual')}" data-lifecycle="${esc(life)}" data-search="${esc((x.title+' '+x.scenario_type+' '+x.executor_type+' '+x.requirement_ref).toLowerCase())}"><td><span class="tag ${x.priority}">${x.priority}</span></td><td><b>${esc(x.title)}</b><br><small>${esc(x.requirement_ref||'未标注')}</small></td><td><span class="tag">${esc(x.scenario_type||'-')}</span><br><small>${esc(x.executor_type||'manual')}</small></td><td>${esc(x.expected||'未填写')}</td><td><select onchange="updateCaseLifecycle('${x.id}',this.value)" title="用例生命周期"><option value="DRAFT" ${life==='DRAFT'?'selected':''}>DRAFT</option><option value="ACTIVE" ${life==='ACTIVE'?'selected':''}>ACTIVE</option><option value="DEPRECATED" ${life==='DEPRECATED'?'selected':''}>DEPRECATED</option></select>${x.lifecycle_note?`<small>${esc(x.lifecycle_note)}</small>`:''}</td><td><span class="tag ${st}">${labels[st]||st}</span></td><td>${x.method?`<button class="small" ${canRun?'':'disabled title="只有ACTIVE用例可以执行"'} onclick="runCase('${x.id}')">执行真实请求</button>`:st==='BLOCKED'?'等待条件':'待对应执行器'}</td></tr>`}).join('')}</tbody></table>`}

function filterCaseRows(){let text=($('#caseSearch')?.value||'').toLowerCase(),executor=$('#caseExecutorFilter')?.value||'',life=$('#caseLifecycleFilter')?.value||'';$$('#caseRows tr').forEach(r=>r.classList.toggle('hidden',!((!text||r.dataset.search.includes(text))&&(!executor||r.dataset.risk===executor)&&(!life||r.dataset.lifecycle===life))))}

async function updateCaseLifecycle(caseId,lifecycleStatus){try{let note=lifecycleStatus==='DEPRECATED'?'由工作台标记为废弃':lifecycleStatus==='DRAFT'?'返回草稿继续维护':'已评审并激活';await QualityHub.services.caseLifecycle.update(caseId,lifecycleStatus,note);toast(`用例状态已更新为 ${lifecycleStatus}`,'success');await openProject(current);switchTab('cases')}catch(e){toast(e.message,'error');await openProject(current);switchTab('cases')}}
function selectedLifecycleCaseIds(){return [...document.querySelectorAll('.case-life-select:checked')].map(x=>x.value)}
function toggleAllLifecycleCases(checked){document.querySelectorAll('.case-life-select').forEach(x=>{if(!x.closest('tr')?.hidden)x.checked=checked})}
async function bulkUpdateCaseLifecycle(lifecycleStatus){let caseIds=selectedLifecycleCaseIds();if(!caseIds.length)return toast('请先勾选测试用例','error');let labels={ACTIVE:'批量评审通过',DRAFT:'批量退回草稿',DEPRECATED:'批量标记废弃'};try{let result=await QualityHub.services.caseLifecycle.bulkUpdate(current,caseIds,lifecycleStatus,labels[lifecycleStatus]||'批量维护');toast(`已更新 ${result.updated} 条用例`,'success');await openProject(current);switchTab('cases')}catch(e){toast(e.message,'error')}}
async function showCaseLifecycleHistory(caseId){try{let result=await QualityHub.services.caseLifecycle.history(caseId),items=result.history||[];$('#modalBody').innerHTML=`<h2>用例生命周期历史</h2>${items.length?`<table><thead><tr><th>时间</th><th>状态变化</th><th>备注</th><th>操作者</th></tr></thead><tbody>${items.map(x=>`<tr><td>${esc((x.created_at||'').replace('T',' '))}</td><td>${esc(x.previous_status)} → ${esc(x.lifecycle_status)}</td><td>${esc(x.note||'-')}</td><td>${esc(x.actor||'-')}</td></tr>`).join('')}</tbody></table>`:'<div class="empty"><b>暂无状态变更记录</b></div>'}`;$('#modal').classList.remove('hidden')}catch(e){toast(e.message,'error')}}
function enhanceCaseLifecycleTable(){let root=$('#cases'),table=root?.querySelector('table'),card=root?.querySelector('.card');if(!table||!card)return;card.insertAdjacentHTML('beforeend',`<div class="hub-action-row"><button class="small" onclick="bulkUpdateCaseLifecycle('ACTIVE')">批量激活</button><button class="small" onclick="bulkUpdateCaseLifecycle('DRAFT')">批量退回草稿</button><button class="small" onclick="bulkUpdateCaseLifecycle('DEPRECATED')">批量废弃</button></div>`);let head=table.querySelector('thead tr');head?.insertAdjacentHTML('afterbegin','<th><input type="checkbox" style="width:auto" title="选择当前可见用例" onchange="toggleAllLifecycleCases(this.checked)"></th>');[...table.querySelectorAll('tbody tr')].forEach((row,index)=>{let item=(data.cases||[])[index];if(!item)return;row.insertAdjacentHTML('afterbegin',`<td><input class="case-life-select" type="checkbox" style="width:auto" value="${esc(item.id)}"></td>`);row.lastElementChild?.insertAdjacentHTML('beforeend',` <button class="small" onclick="showCaseLifecycleHistory('${esc(item.id)}')">历史</button>`)})}
function tableRuns(){if(!data.runs.length)return '<div class="empty"><b>暂无执行记录</b>执行接口用例后会保留请求、响应和归因</div>';return `<table><thead><tr><th>状态</th><th>用例</th><th>耗时</th><th>HTTP</th><th>自动归因</th><th>错误</th></tr></thead><tbody>${data.runs.map(x=>`<tr><td><span class="tag ${x.status}">${x.status}</span></td><td>${esc(x.case_title)}</td><td>${x.duration_ms} ms</td><td>${x.http_status??'-'}</td><td>${esc(x.analysis)}</td><td title="${esc(x.response_data)}">${esc(x.error||'').slice(0,100)}</td></tr>`).join('')}</tbody></table>`}
function tableDatabase(){let tabs=data.db_tables||[],maps=data.mappings||[];if(!tabs.length)return `<div class="card"><h3>导入数据库结构</h3><p style="color:var(--muted);font-size:12px">上传平台导出的数据库Schema JSON，将自动建立接口与数据表的候选关系。不会上传或读取业务行数据。</p><input type="file" id="dbSchemaFile" accept=".json"><button class="primary" onclick="importDbSchema()">导入并映射</button></div>`;let modules={};tabs.forEach(x=>modules[x.module]=(modules[x.module]||0)+1);return `<div class="metrics"><div class="metric"><span>数据表</span><b>${tabs.length}</b></div><div class="metric"><span>候选映射</span><b>${maps.length}</b></div><div class="metric"><span>业务前缀</span><b>${Object.keys(modules).length}</b></div><div class="metric"><span>模式</span><b style="font-size:18px">只读</b></div></div><table><thead><tr><th>表名</th><th>模块</th><th>注释</th><th>估算行数</th></tr></thead><tbody>${tabs.slice(0,500).map(x=>`<tr><td><code>${esc(x.table_name)}</code></td><td>${esc(x.module)}</td><td>${esc(x.table_comment)}</td><td>${x.approx_rows}</td></tr>`).join('')}</tbody></table>`}
function tableRedis(){let sources=data.redis_sources||[],snaps=data.redis_snapshots||[];return `<div class="grid2"><div class="card"><h3>接入 Redis</h3><p style="font-size:12px;color:var(--muted)">支持仅 Host/Port 的测试环境。平台只开放读取命令，写入和危险命令均未实现。</p><label>名称</label><input id="redisName" value="测试环境 Redis"><div class="formrow"><input id="redisHost" placeholder="Redis Host"><input id="redisPort" type="number" value="6379"></div><div class="formrow"><input id="redisDb" type="number" value="0" min="0" placeholder="DB"><label><input id="redisTls" type="checkbox" style="width:auto"> TLS</label></div><button class="primary" onclick="addRedisSource()">连接并保存</button></div><div class="card"><h3>安全边界</h3><p><span class="tag PASSED">默认只读</span></p><ul><li>使用 SCAN，禁止 KEYS 全库阻塞查询</li><li>单次最多返回 500 个 Key</li><li>允许 GET/HGETALL/LRANGE/SMEMBERS/ZRANGE</li><li>未提供 SET、DEL、FLUSH、CONFIG、SHUTDOWN 执行入口</li><li>每次查看 Key 都保存摘要快照，便于前后对比</li></ul></div></div>${sources.length?sources.map(s=>`<div class="card"><span class="tag ${s.status==='connected'?'PASSED':'P0'}">${esc(s.status)}</span><h3 style="display:inline;margin-left:10px">${esc(s.name)}</h3><p><code>${esc(s.host)}:${s.port}</code> · DB ${s.db_no} · Redis ${esc(s.server_version||'-')} · 只读</p><div class="formrow"><input id="redisPattern_${s.id}" value="*" placeholder="Key pattern，例如 user:*"><input id="redisLimit_${s.id}" type="number" value="100" min="1" max="500"></div><button class="small" onclick="testRedis('${s.id}')">测试连接</button> <button class="primary" onclick="scanRedis('${s.id}')">扫描 Key</button><div id="redisKeys_${s.id}"></div></div>`).join(''):'<div class="empty"><b>尚未接入 Redis</b>填写 Host 和 Port 后连接</div>'}${snaps.length?`<div class="card"><h3>最近读取快照</h3><table><thead><tr><th>Key</th><th>类型</th><th>TTL</th><th>时间</th></tr></thead><tbody>${snaps.slice(0,30).map(x=>`<tr><td><code>${esc(x.key_name)}</code></td><td>${esc(x.key_type)}</td><td>${x.ttl}</td><td>${esc(x.captured_at)}</td></tr>`).join('')}</tbody></table></div>`:''}`}
function sourceStatus(message,type=''){let box=$("#sourceImportStatus");if(box)box.innerHTML=`<span class="tag ${type}">${esc(message)}</span>`}
function setSourceSaving(active,message=''){let btn=$("#sourceSaveButton");if(btn){btn.disabled=active;btn.textContent=active?'保存中…':'保存并分析'}if(message)sourceStatus(message,active?'P1':'PASSED')}
function guessSourceKind(fileName){if(/\.har$/i.test(fileName))return 'har';if(/\.(json|ya?ml)$/i.test(fileName))return 'openapi';return null}
function bindFile(){const f=$("#srcFile");if(f)f.onchange=async()=>{const file=f.files[0];if(!file)return;pendingFile=null;sourceStatus(`正在读取文件：${file.name}`,'P1');try{if(!$("#srcName").value)$("#srcName").value=file.name;let guessed=guessSourceKind(file.name);if(guessed)$("#srcKind").value=guessed;if(/\.(txt|md|json|ya?ml|har)$/i.test(file.name)){$("#srcContent").value=await file.text();sourceStatus(`文件已就绪：${file.name}`,'PASSED')}else{let bytes=new Uint8Array(await file.arrayBuffer()),binary='';for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode(...bytes.subarray(i,i+32768));pendingFile={name:file.name,base64:btoa(binary),size:file.size};$("#srcContent").value=`已选择二进制文档：${file.name}，将由平台解析文字和图片`;sourceStatus(`文件已就绪：${file.name}，保存后开始解析`,'PASSED')}}catch(e){pendingFile=null;sourceStatus(`文件读取失败：${e.message}`,'P0');toast(e.message)}}}
async function addSource(){let btn=$("#sourceSaveButton");if(btn?.disabled)return;try{let name=$("#srcName").value.trim(),content=$("#srcContent").value.trim(),kind=$("#srcKind").value,source_url=$("#srcUrl")?.value.trim()||'',browser_capture=$("#browserCapture")?.checked||false;if(!name||(!content&&!source_url&&!pendingFile))return toast('请填写名称并提供文字、链接或文件');setSourceSaving(true,pendingFile?'正在上传并解析文件，图文资料可能需要几十秒':'正在保存并分析资料');if(browser_capture)toast('正在打开网页登录采集器，请在可见窗口中完成登录并等待自动采集');let x=await api(`/api/projects/${current}/sources`,{method:'POST',body:JSON.stringify({name,content:pendingFile?'':content,kind,source_url,browser_capture,file_name:pendingFile?.name||'',file_base64:pendingFile?.base64||'',requirement_source_id:$("#requirementSource")?.value||'',batch_name:name})});let msg=kind==='openapi'||kind==='har'?`V${x.version}：新增${x.added}、修改${x.modified}、删除${x.removed}、未变${x.unchanged}${kind==='har'?`，抓包${x.capture_entries||0}条`:''}`:`资料已保存，生成${x.requirement_items||0}条需求，发现${x.images||0}张图片`;sourceStatus(msg,'PASSED');toast(msg);pendingFile=null;await openProject(current);if(kind==='openapi'||kind==='har')switchTab('changes')}catch(e){sourceStatus(`保存失败：${e.message}`,'P0');toast(e.message)}finally{setSourceSaving(false)}}
async function generate(id,force=false){try{toast('AI 正在归纳资料并设计测试…');let x=await api(`/api/projects/${current}/generate`,{method:'POST',body:JSON.stringify({source_id:id,force})});toast(`已生成 ${x.points} 个测试点、${x.cases} 条用例（${x.engine}）`);await openProject(current)}catch(e){toast(e.message)}}
async function runCase(id){try{toast('正在执行用例…');let x=await api(`/api/cases/${id}/run`,{method:'POST',body:'{}'});toast(`执行完成：${x.status}`);await openProject(current);switchTab('runs')}catch(e){toast(e.message)}}
async function runAll(){if(!current)return;try{toast('正在执行当前已具备真实执行条件的用例…');let x=await api(`/api/projects/${current}/run-all`,{method:'POST',body:'{}'});toast(`本次可执行 ${x.executable} 条，其余 ${x.not_executed} 条保持未执行/阻塞`);await openProject(current);switchTab('cases')}catch(e){toast(e.message)}}
async function importDbSchema(){let f=$('#dbSchemaFile').files[0];if(!f)return toast('请选择Schema JSON');try{toast('正在建立接口与数据库映射…');let x=await api(`/api/projects/${current}/db-schema`,{method:'POST',body:JSON.stringify({content:await f.text()})});toast(`已导入 ${x.tables} 张表，建立 ${x.mappings} 个候选映射`);await openProject(current);switchTab('database')}catch(e){toast(e.message)}}
async function addRedisSource(){try{toast('正在连接 Redis…');let x=await api(`/api/projects/${current}/redis-sources`,{method:'POST',body:JSON.stringify({name:$('#redisName').value,host:$('#redisHost').value,port:+$('#redisPort').value,db_no:+$('#redisDb').value,use_tls:$('#redisTls').checked})});toast(`Redis 已连接：${x.dbsize} 个 Key`);await openProject(current);switchTab('redis')}catch(e){toast(e.message)}}
async function testRedis(id){try{let x=await api(`/api/redis-sources/${id}/test`,{method:'POST',body:'{}'});toast(`连接正常，DBSIZE ${x.dbsize}`);await openProject(current);switchTab('redis')}catch(e){toast(e.message)}}
async function scanRedis(id){try{let pattern=$(`#redisPattern_${id}`).value||'*',limit=+$(`#redisLimit_${id}`).value||100;toast('正在以 SCAN 方式读取 Key…');let x=await api(`/api/redis-sources/${id}/scan`,{method:'POST',body:JSON.stringify({pattern,limit})}),box=$(`#redisKeys_${id}`);box.innerHTML=x.keys.length?`<p style="font-size:12px;color:var(--muted)">找到 ${x.count} 个，${x.cursor_complete?'已扫描完成':'达到数量上限'}</p><div style="max-height:420px;overflow:auto">${x.keys.map(k=>`<div style="padding:7px;border-bottom:1px solid var(--line)"><code>${esc(k)}</code><button class="small" style="float:right" onclick="inspectRedis(${esc(JSON.stringify(id))},${esc(JSON.stringify(k))})">查看</button></div>`).join('')}</div>`:'<div class="empty">未匹配到 Key</div>'}catch(e){toast(e.message)}}
async function inspectRedis(id,key){try{toast('正在只读查看 Key…');let x=await api(`/api/redis-sources/${id}/inspect`,{method:'POST',body:JSON.stringify({key})});$('#modalBody').innerHTML=`<h2>Redis Key</h2><p><code>${esc(x.key)}</code></p><p><span class="tag">${esc(x.type)}</span> TTL ${x.ttl} ${x.truncated?'· 内容已截断':''}</p><textarea readonly style="min-height:420px">${esc(typeof x.value==='string'?x.value:JSON.stringify(x.value,null,2))}</textarea>`;$('#modal').classList.remove('hidden');await openProject(current);switchTab('redis')}catch(e){toast(e.message)}}
async function generateFlows(){try{toast('AI正在归纳接口依赖与业务流程…');let x=await api(`/api/projects/${current}/generate-workflows`,{method:'POST',body:'{}'});toast(`已生成 ${x.workflows} 条流程、${x.steps} 个步骤`);await openProject(current);switchTab('flows')}catch(e){toast(e.message)}}
function showFlow(i){let w=data.workflows[i],steps=(data.workflow_steps||[]).filter(s=>s.workflow_id===w.id),run=(data.workflow_runs||[]).find(r=>r.workflow_id===w.id),runHtml='';if(run){let details=[];try{details=JSON.parse(run.details||'[]')}catch{};let ctx=details.find(x=>x.runtime_context)?.runtime_context||{},flows=details.flatMap(x=>x.variable_flow||[]);runHtml=`<label>最近执行</label><p><span class="tag ${run.status==='PASSED'?'PASSED':run.status==='PARTIAL'?'P1':'P0'}">${run.status}</span> 通过 ${run.passed_steps}/${run.total_steps}</p><label>变量提取与传递证据</label>${flows.length?`<table><thead><tr><th>变量</th><th>来源步骤</th><th>是否持久化原值</th></tr></thead><tbody>${flows.map(x=>`<tr><td>${esc(x.name)}</td><td>${esc(x.source_step)}</td><td>${x.persisted?'是':'否，仅内存'}</td></tr>`).join('')}</tbody></table>`:'<p>本次执行没有提取到可传递变量。</p>'}<label>脱敏后的运行上下文</label><textarea readonly>${esc(JSON.stringify(ctx,null,2))}</textarea>`}$('#modalBody').innerHTML=`<h2>${esc(w.name)}</h2><p>${esc(w.description)}</p><label>流程步骤</label>${steps.map(s=>`<div style="padding:12px;border-left:3px solid var(--green);margin:9px 0;background:#f7faf8"><b>${s.step_order}. ${esc(s.name)}</b><br><small>阶段：${s.phase}　前置：${esc(s.precondition)}　提取规则：${esc(s.extract_rules||'自动')}</small></div>`).join('')}${runHtml}`;$('#modal').classList.remove('hidden')}
async function runFlow(id){try{toast('正在按顺序执行流程…');let x=await api(`/api/workflows/${id}/run`,{method:'POST',body:'{}'});toast(`流程执行完成：${x.status}，通过 ${x.passed_steps}/${x.total_steps}`);await openProject(current);switchTab('flows')}catch(e){toast(e.message)}}
async function generateNonfunctional(){try{toast('AI正在生成自动化、性能和异常测试资产…');let x=await api(`/api/projects/${current}/generate-nonfunctional`,{method:'POST',body:'{}'});toast(`已生成 ${x.suites} 个套件、${x.performance_plans} 个性能计划、${x.fault_scenarios} 个异常场景`);await openProject(current);switchTab('automation')}catch(e){toast(e.message)}}
async function generateToolAssets(){try{toast('正在生成 Postman、JMeter、pytest 标准资产…');let x=await api(`/api/projects/${current}/tool-assets`,{method:'POST',body:'{}'});toast(`已生成 ${x.generated} 个企业工具资产`);await openProject(current);switchTab('automation')}catch(e){toast(e.message)}}
function applyPerformanceProfile(){let p=$('#toolPerfProfile')?.value||'smoke',m={smoke:{threads:2,loops:5,rampup:2,timeout:180,error:0,p95:3000,p99:5000,tps:0},baseline:{threads:1,loops:100,rampup:5,timeout:300,error:1,p95:1500,p99:2500,tps:1},load:{threads:30,loops:30,rampup:60,timeout:900,error:1,p95:2000,p99:3500,tps:5},concurrency:{threads:50,loops:10,rampup:1,timeout:600,error:1,p95:2000,p99:3500,tps:0},spike:{threads:100,loops:5,rampup:1,timeout:600,error:2,p95:3000,p99:5000,tps:0},stress:{threads:100,loops:50,rampup:120,timeout:1800,error:5,p95:5000,p99:8000,tps:0},soak:{threads:20,loops:1000,rampup:60,timeout:86400,error:.5,p95:2000,p99:4000,tps:2},stability:{threads:20,loops:1000,rampup:60,timeout:86400,error:.5,p95:2000,p99:4000,tps:2}}[p]||{};[['#toolJmeterThreads','threads'],['#toolJmeterLoops','loops'],['#toolJmeterRampup','rampup'],['#toolJmeterTimeout','timeout'],['#toolMaxErrorRate','error'],['#toolMaxP95','p95'],['#toolMaxP99','p99'],['#toolMinThroughput','tps']].forEach(([id,key])=>{let el=$(id);if(el&&m[key]!==undefined)el.value=m[key]})}
async function runEnterpriseToolchain(){let button=$('#toolchainRunButton'),box=$('#toolchainRunStatus');try{let login_strategy=$('#toolLoginStrategy')?.value||'auto',login_t=$('#toolLoginT')?.value.trim()||'',login_sn=$('#toolLoginSn')?.value.trim()||'',login_password_encrypted=$('#toolLoginPassword')?.value.trim()||'',runtimeText=$('#toolRuntimeParams')?.value.trim()||'{}',runtime_params={};if(login_t&&login_t.split('.').length===3)return toast('请求头 t 看起来像 token/ticket，请不要填到 t；留空由平台自动生成时间戳','warning');if(login_strategy==='force'&&!login_password_encrypted)return toast('强制重新登录需要填写加密密码；t 可留空自动生成','warning');if(login_strategy==='auto'&&(login_t||login_sn||login_password_encrypted)&&!login_password_encrypted)return toast('已填写登录上下文时，需要提供加密密码；t 可留空自动生成，sn 可空','warning');try{runtime_params=runtimeText?JSON.parse(runtimeText):{}}catch{return toast('运行参数必须是合法 JSON','warning')}let payload={login_strategy,login_t,login_sn,login_password_encrypted,runtime_params,jmeter_threads:+$('#toolJmeterThreads')?.value||1,jmeter_loops:+$('#toolJmeterLoops')?.value||1,jmeter_rampup:+$('#toolJmeterRampup')?.value||1,jmeter_timeout:+$('#toolJmeterTimeout')?.value||180,performance_profile:$('#toolPerfProfile')?.value||'smoke',max_error_rate:+$('#toolMaxErrorRate')?.value||0,max_p95_ms:+$('#toolMaxP95')?.value||3000,max_p99_ms:+$('#toolMaxP99')?.value||5000,min_throughput_rps:+$('#toolMinThroughput')?.value||0,run_newman:$('#toolRunNewman')?.checked!==false,run_jmeter:$('#toolRunJmeter')?.checked!==false,run_pytest:$('#toolRunPytest')?.checked!==false};if(button){button.disabled=true;button.textContent='执行中…'}if(box)box.innerHTML='<p>正在前置登录、同步运行上下文，并调用 Newman / JMeter / pytest。执行完成后自动进入报告中心。</p>';toast('工具链已开始执行…');let x=await api(`/api/projects/${current}/toolchain/run`,{method:'POST',body:JSON.stringify(payload)});let msg=`工具链完成：${x.status}，通过${x.summary?.passed||0}，失败${x.summary?.failed||0}，阻断${x.summary?.blocked||0}`;let warnings=(x.runtime?.warnings||[]).map(esc).join('；');if(box)box.innerHTML=`<div class="summary-panel"><b>${esc(x.status)}</b><p>${esc(msg)} · 运行来源 ${esc(x.runtime?.source||'-')}${warnings?' · '+warnings:''}</p></div>`;toast(msg,x.status==='PASSED'?'success':x.status==='BLOCKED'?'warning':'error');if($('#toolLoginPassword'))$('#toolLoginPassword').value='';await openProject(current);switchTab('reports')}catch(e){if(box)box.innerHTML=`<p>${esc(e.message)}</p>`;toast(e.message,'error')}finally{let b=$('#toolchainRunButton');if(b){b.disabled=false;b.textContent='执行工具链'}}}
async function runSuite(id){try{toast('正在批量执行自动化套件…');let x=await api(`/api/suites/${id}/run`,{method:'POST',body:'{}'});toast(`套件完成：通过${x.passed}，失败${x.failed}，总计${x.total}`);await openProject(current);switchTab('runs')}catch(e){toast(e.message)}}
async function runPerformance(id){try{toast('正在执行并发性能基准…');let x=await api(`/api/performance/${id}/run`,{method:'POST',body:'{}'});toast(`性能结果 ${x.status}：RPS ${x.rps}，P95 ${x.p95_ms}ms`);await openProject(current);switchTab('automation')}catch(e){toast(e.message)}}
async function generateOperations(){try{let x=await api(`/api/projects/${current}/generate-operations`,{method:'POST',body:'{}'});toast(`已生成 ${x.ui_plans} 个UI计划和 ${x.scheduled_jobs} 个定时任务`);await openProject(current);switchTab('operations')}catch(e){toast(e.message)}}
async function runSecurity(){try{toast('正在执行被动安全扫描…');let x=await api(`/api/projects/${current}/security-scan`,{method:'POST',body:'{}'});toast(`安全扫描完成：评分 ${x.score}，发现 ${x.findings_count}`);await openProject(current);switchTab('operations')}catch(e){toast(e.message)}}
function showUiPlan(i){let x=data.ui_test_plans[i];$('#modalBody').innerHTML=`<h2>${esc(x.name)}</h2><p><code>${esc(x.page_url)}</code></p><label>Playwright脚本</label><textarea readonly style="min-height:420px">${esc(x.playwright_script)}</textarea>`;$('#modal').classList.remove('hidden')}
async function runJob(id){try{toast('正在运行调度任务…');let x=await api(`/api/jobs/${id}/run`,{method:'POST',body:'{}'});toast(`任务完成：${x.status||'COMPLETED'}`);await openProject(current);switchTab('operations')}catch(e){toast(e.message)}}
async function toggleJob(id,enabled,minutes){try{await api(`/api/jobs/${id}`,{method:'PUT',body:JSON.stringify({enabled:!!enabled,interval_minutes:minutes})});toast(enabled?'任务已启用':'任务已停用');await openProject(current);switchTab('operations')}catch(e){toast(e.message)}}
async function addManualApi(){try{let x=await api(`/api/projects/${current}/endpoints`,{method:'POST',body:JSON.stringify({method:$('#manualMethod').value,path:$('#manualPath').value,summary:$('#manualSummary').value,module:$('#manualModule').value,auth_required:$('#manualAuth').checked})});toast(`接口已新增：${x.method} ${x.path}`);await openProject(current);switchTab('apis')}catch(e){toast(e.message)}}
async function addCustomJob(){try{let x=await api(`/api/projects/${current}/jobs`,{method:'POST',body:JSON.stringify({name:$('#jobName').value,job_type:$('#jobType').value,target_id:$('#jobTarget').value,interval_minutes:+$('#jobInterval').value,enabled:$('#jobEnabled').checked})});toast(`定时任务已创建：${x.name}`);await openProject(current);switchTab('operations')}catch(e){toast(e.message)}}
async function refreshTrace(){try{let x=await api(`/api/projects/${current}/refresh-trace`,{method:'POST',body:'{}'});toast(`已建立 ${x.links} 条追踪关系`);await openProject(current);switchTab('manual')}catch(e){toast(e.message)}}
function editRequirement(i){let r=data.requirement_items[i];$('#modalBody').innerHTML=`<h2>编辑需求条目</h2><label>标题</label><input id="reqTitle" value="${esc(r.title)}"><label>需求描述</label><textarea id="reqDesc">${esc(r.description)}</textarea><label>验收标准</label><textarea id="reqAcceptance">${esc(r.acceptance_criteria)}</textarea><div class="formrow"><select id="reqPriority"><option ${r.priority==='P0'?'selected':''}>P0</option><option ${r.priority==='P1'?'selected':''}>P1</option><option ${r.priority==='P2'?'selected':''}>P2</option></select><select id="reqRisk"><option value="high" ${r.risk_level==='high'?'selected':''}>高风险</option><option value="medium" ${r.risk_level==='medium'?'selected':''}>中风险</option><option value="low" ${r.risk_level==='low'?'selected':''}>低风险</option></select></div><button class="primary" onclick="saveRequirement('${r.id}')">保存并更新追踪链</button>`;$('#modal').classList.remove('hidden')}
async function saveRequirement(id){try{await api(`/api/requirements/${id}`,{method:'PUT',body:JSON.stringify({title:$('#reqTitle').value,description:$('#reqDesc').value,acceptance_criteria:$('#reqAcceptance').value,priority:$('#reqPriority').value,risk_level:$('#reqRisk').value})});closeModal();toast('需求已更新');await openProject(current);switchTab('manual')}catch(e){toast(e.message)}}
async function runPipeline(){try{toast('AI正在执行完整测试流水线，这可能需要几十秒…');let x=await api(`/api/projects/${current}/ai-pipeline`,{method:'POST',body:'{}'});let blockers=[];try{blockers=JSON.parse(x.blockers||'[]')}catch{};toast(`流水线完成：${x.status}，卡点 ${blockers.length} 个`);await openProject(current);switchTab('overview');if(blockers.length){$('#modalBody').innerHTML=`<h2>AI流水线已完成</h2><p><span class="tag P1">${esc(x.status)}</span></p><label>当前卡点</label><ul>${blockers.map(b=>`<li>${esc(b)}</li>`).join('')}</ul>`;$('#modal').classList.remove('hidden')}}catch(e){toast(e.message)}}
function showCandidates(i){let r=data.requirement_items[i],links=(data.trace_links||[]).filter(x=>x.requirement_id===r.id&&x.target_type==='endpoint'),epMap=Object.fromEntries((data.endpoints||[]).map(x=>[x.id,x]));$('#modalBody').innerHTML=`<h2>候选接口：${esc(r.title)}</h2><p>已从 ${(data.endpoints||[]).length} 个接口中筛出 ${links.length} 个候选。</p><input id="candidateSearch" placeholder="搜索接口" oninput="filterRows('candidateRows',this.value,'')"><div id="candidateRows">${links.map((l,n)=>{let e=epMap[l.target_id];if(!e)return'';return `<div data-search="${esc((e.method+' '+e.path+' '+e.summary+' '+e.tags).toLowerCase())}" style="padding:10px;border-bottom:1px solid var(--line)"><input type="checkbox" style="width:auto" ${l.selected?'checked':''} onchange="toggleCandidate('${r.id}','${e.id}',this.checked,${n+1})"> <span class="tag">${Math.round(l.confidence*100)}%</span> <b>${e.method} ${esc(e.path)}</b><br><small>${esc(e.summary)} · ${esc(l.reason)}</small></div>`}).join('')}</div><button class="primary" onclick="closeModal();generateRequirementFlow('${r.id}')">使用已选接口生成完整流程</button>`;$('#modal').classList.remove('hidden')}
async function toggleCandidate(reqId,endpointId,selected,order){try{await api(`/api/requirements/${reqId}/link`,{method:'POST',body:JSON.stringify({endpoint_id:endpointId,selected,sort_order:order})});let link=(data.trace_links||[]).find(x=>x.requirement_id===reqId&&x.target_type==='endpoint'&&x.target_id===endpointId);if(link)link.selected=selected?1:0;toast(selected?'已关联接口':'已取消关联')}catch(e){toast(e.message)}}
async function generateRequirementFlow(reqId){try{let x=await api(`/api/requirements/${reqId}/generate-workflow`,{method:'POST',body:'{}'});toast(`需求流程已生成，共 ${x.steps} 个接口步骤`);closeModal();await openProject(current);switchTab('flows')}catch(e){toast(e.message)}}
function filterRows(id,text,kind){text=(text||'').toLowerCase();$$(`#${id} tr`).forEach(r=>r.classList.toggle('hidden',!((!text||r.dataset.search.includes(text))&&(!kind||r.dataset.risk===kind))))}
function showApi(i){let x=data.endpoints[i],ex={};try{ex=JSON.parse(x.example_request||'{}')}catch{};let req=[];try{req=JSON.parse(x.required_fields||'[]')}catch{};let maps=(data.mappings||[]).filter(m=>m.endpoint_id===x.id).slice(0,8);$('#modalBody').innerHTML=`<h2>${esc(x.summary)}</h2><p><span class="tag">${x.method}</span> <code>${esc(x.path)}</code></p><label>风险判断</label><p>${esc(x.risk_reason)}</p><label>已确认的请求参数</label><textarea readonly>${esc(JSON.stringify(ex,null,2))}</textarea><p><small>这里只展示接口文档明确example、真实抓包或你手动填写的值；平台不再根据字段类型自动猜参数。</small></p><label>必填但可能待填写的字段</label><p>${req.length?req.map(esc).join('、'):'文档未声明'}</p><label>候选数据表</label><p>${maps.length?maps.map(m=>`<code>${esc(m.table_name)}</code> (${Math.round(m.confidence*100)}%)`).join('　'):'尚未建立映射'}</p>`;$('#modal').classList.remove('hidden')}
function downloadExport(){let payload={exported_at:new Date().toISOString(),project:data.project,summary:{sources:data.sources.length,endpoints:(data.endpoints||[]).length,workflows:(data.workflows||[]).length,test_points:data.points.length,test_cases:data.cases.length,db_tables:(data.db_tables||[]).length,runs:data.runs.length},endpoints:data.endpoints,workflows:data.workflows,workflow_steps:data.workflow_steps,test_points:data.points,test_cases:data.cases,db_mappings:data.mappings,runs:data.runs};let blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`${data.project.name}-测试资产.json`;a.click();URL.revokeObjectURL(a.href);toast('测试资产已导出')}
async function downloadInterfaceDocument(){try{let doc=await api(`/api/projects/${current}/interface-document`);let blob=new Blob([JSON.stringify(doc,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`${data.project.name}-接口文档基线.openapi.json`;a.click();URL.revokeObjectURL(a.href);toast('接口文档基线已导出')}catch(e){toast(e.message)}}
function showNewProject(){$("#modalBody").innerHTML=`<h2>创建测试项目</h2><label>项目名称</label><input id="newName" placeholder="例如：交易平台"><label>项目说明</label><textarea id="newDesc" style="min-height:80px" placeholder="本项目的业务目标与重点风险"></textarea><label>测试环境 Base URL（可稍后配置）</label><input id="newUrl" placeholder="https://test-api.example.com"><button class="primary" onclick="createProject()">创建并进入</button>`;$("#modal").classList.remove('hidden')}
async function createProject(){try{let p=await api('/api/projects',{method:'POST',body:JSON.stringify({name:$("#newName").value||'未命名项目',description:$("#newDesc").value,base_url:$("#newUrl").value})});closeModal();await openProject(p.id)}catch(e){toast(e.message)}}
function editProject(){$("#modalBody").innerHTML=`<h2>项目配置</h2><label>名称</label><input id="editName" value="${esc(data.project.name)}"><label>说明</label><textarea id="editDesc" style="min-height:80px">${esc(data.project.description)}</textarea><label>测试环境 Base URL</label><input id="editUrl" value="${esc(data.project.base_url)}"><button class="primary" onclick="saveProject()">保存</button>`;$("#modal").classList.remove('hidden')}
async function saveProject(){await api(`/api/projects/${current}`,{method:'PUT',body:JSON.stringify({name:$("#editName").value,description:$("#editDesc").value,base_url:$("#editUrl").value})});closeModal();toast('项目配置已保存');await openProject(current)}
async function showSettings(){let s=await api('/api/settings');$("#modalBody").innerHTML=`<h2>AI 模型设置</h2><p style="color:var(--muted);font-size:12px">不配置密钥时使用内置规则引擎；配置 OpenAI 兼容接口后使用大模型深度分析。</p><label>API Base</label><input id="apiBase" value="${esc(s.api_base||'https://api.openai.com/v1')}"><label>API Key</label><input id="apiKey" type="password" value="${esc(s.api_key||'')}"><label>模型</label><input id="model" value="${esc(s.model||'gpt-5-mini')}"><button class="primary" onclick="saveSettings()">保存设置</button>`;$("#modal").classList.remove('hidden')}
async function saveSettings(){await api('/api/settings',{method:'POST',body:JSON.stringify({api_base:$("#apiBase").value,api_key:$("#apiKey").value,model:$("#model").value})});closeModal();toast('模型设置已保存')}
function closeModal(){$("#modal").classList.add('hidden')}function switchTab(id){return window.QualityHub.routers.workspace.switchTab(id,{$,$$,current,data})}
function tableRedisV2(){let maps=data.redis_mappings||[];let auto=`<div class="card" style="background:#153c2c;color:white"><span style="color:var(--lime);font-size:11px">MYSQL + REDIS AUTO MATCH</span><h2>自动匹配数据库与 Redis</h2><p style="color:#c2d3ca">根据接口路径、请求字段、MySQL 表字段和 Redis Key 名称建立关联链。自动扫描阶段不读取缓存值。</p><button class="primary" onclick="autoMatchData()">✦ 开始自动匹配</button></div>`;let result=maps.length?`<div class="card"><h3>接口 → MySQL → Redis 自动映射</h3><p style="font-size:12px;color:var(--muted)">共 ${maps.length} 条候选关联，动态数字和 UUID 已归纳为 Key Pattern。</p><table><thead><tr><th>置信度</th><th>接口</th><th>数据库表</th><th>Redis Key / Pattern</th><th>依据</th></tr></thead><tbody>${maps.slice(0,300).map(x=>`<tr><td><span class="tag ${x.confidence>=.75?'PASSED':x.confidence>=.5?'P1':''}">${Math.round(x.confidence*100)}%</span></td><td><code>${esc(x.method+' '+x.path)}</code><br><small>${esc(x.summary)}</small></td><td><code>${esc(x.matched_table||'待确认')}</code></td><td><code>${esc(x.key_pattern)}</code><br><small>${esc(x.key_type)}</small></td><td>${esc(x.reason)}</td></tr>`).join('')}</tbody></table></div>`:'';return auto+result+tableRedis()}
async function autoMatchData(){try{toast('正在自动匹配接口、数据库与 Redis Key…');let x=await api(`/api/projects/${current}/auto-match-data`,{method:'POST',body:'{}'});toast(`匹配完成：扫描 ${x.keys_scanned} 个 Key，生成 ${x.redis_mappings} 条关联`);await openProject(current);switchTab('redis')}catch(e){toast(e.message)}}
function polishInterfaceCopy(){let labels={manual:'智能工作台',sources:'资料中心',changes:'版本变更',apis:'接口资产',flows:'业务流程',automation:'自动化中心',operations:'安全 · UI · 调度',points:'测试点',cases:'测试用例',database:'数据映射',redis:'Redis 中心',runs:'执行记录'};$$('.tabs button').forEach(b=>{if(labels[b.dataset.tab])b.textContent=labels[b.dataset.tab]});let runAllBtn=$('.toolbar .primary');if(runAllBtn)runAllBtn.textContent='▶ 运行全部用例';let redis=$('#redis');if(!redis)return;redis.querySelectorAll('.card').forEach(card=>{let h=card.querySelector('h3');if(!h)return;if(h.textContent.trim()==='接入 Redis'){h.textContent='Redis 数据源';let p=card.querySelector('p');if(p)p.textContent='连接测试环境 Redis，用于缓存验证与数据一致性分析。接入后默认以只读模式运行。';let labels=card.querySelectorAll('label');if(labels[0])labels[0].textContent='连接名称';let inputs=card.querySelectorAll('input');if(inputs[1])inputs[1].placeholder='服务器地址（Host）';let btn=card.querySelector('button.primary');if(btn)btn.textContent='验证并接入'}if(h.textContent.trim()==='安全边界'){h.textContent='只读安全策略';let items=card.querySelectorAll('li');let copy=['使用渐进式 SCAN，避免阻塞 Redis 服务','单次最多展示 500 个 Key，防止页面负载过高','支持读取 String、Hash、List、Set 与 ZSet','写入、删除、清库及配置类命令均不可执行','查看 Key 时保留摘要快照，便于测试前后对比'];items.forEach((x,i)=>{if(copy[i])x.textContent=copy[i]})}});redis.querySelectorAll('.tag').forEach(x=>{if(x.textContent.trim()==='connected')x.textContent='已连接'});redis.querySelectorAll('.empty').forEach(x=>{if(x.textContent.includes('尚未接入 Redis'))x.innerHTML='<b>等待接入 Redis</b>填写服务器地址和端口，验证成功后即可开始分析'})}
function tableConsistency(){let pack=data.consistency||{},rules=pack.rules||[],runs=pack.runs||[],summary=pack.summary||data.wealth_latest?.data_consistency||{},coreRules=rules.filter(x=>x.redis_key==='yingtao_user_level_exper'),extended=rules.filter(x=>x.redis_key&&x.redis_key!=='yingtao_user_level_exper'),ready=rules.filter(x=>x.case_id&&x.redis_source_id&&x.redis_key),pendingMysql=rules.filter(x=>x.mysql_table&&!x.mysql_condition),latest=runs[0];return `<div class="card"><div style="display:flex;justify-content:space-between;gap:16px;align-items:flex-start;flex-wrap:wrap"><div><span class="tag ${summary.status==='PASSED'?'PASSED':summary.status==='FAILED'?'FAILED':'P1'}">DATA GATE ${esc(summary.status||'PENDING')}</span><h2 style="margin:12px 0 6px">接口 · MySQL · Redis 数据验证闭环</h2><p style="color:var(--muted);margin:0">平台自动生成规则、补齐可推导条件，并优先运行核心业务 Key。扩展候选用于扩大覆盖，不再影响核心准入。</p></div><div class="formrow" style="min-width:360px"><button class="primary" onclick="generateAndRunConsistency()">生成并运行核心验证</button><button class="small" onclick="runReadyConsistency('extended')">运行扩展候选</button></div></div>${rules.length?`<div class="metrics" style="margin-top:20px"><div class="metric"><span>核心状态</span><b style="font-size:20px">${esc(summary.core_status||summary.status||'PENDING')}</b></div><div class="metric"><span>可执行规则</span><b>${ready.length}/${rules.length}</b></div><div class="metric"><span>扩展候选</span><b>${extended.length}</b></div><div class="metric"><span>MySQL待补</span><b>${pendingMysql.length}</b></div></div><div id="consistencyRunStatus">${latest?`<div class="summary-panel"><b>最近验证：${esc(latest.status)}</b><p>${esc(latest.path||'')} · Redis ${latest.changed?'发生变化':'保持不变'} · ${esc(latest.created_at||'')}</p></div>`:''}</div><table><thead><tr><th>范围</th><th>接口</th><th>Redis Pattern</th><th>MySQL 条件</th><th>验证预期</th><th>操作</th></tr></thead><tbody>${rules.slice(0,100).map(x=>`<tr><td><span class="tag ${x.redis_key==='yingtao_user_level_exper'?'PASSED':'P1'}">${x.redis_key==='yingtao_user_level_exper'?'核心':'扩展'}</span></td><td><code>${esc(x.method+' '+x.path)}</code><br><small>${esc(x.summary||'')}</small></td><td><code>${esc(x.redis_pattern||x.redis_key||'待映射')}</code></td><td>${x.mysql_table?`<code>${esc(x.mysql_table)}</code><br><small>${esc(x.mysql_condition||'待自动补齐或人工确认')}</small>`:'待匹配'}</td><td>${x.expectation==='unchanged'?'只读接口应保持不变':'记录变更证据'}</td><td><button class="small" ${x.case_id?'':'disabled title="尚未关联可执行用例"'} onclick="runConsistency('${x.id}')">执行</button></td></tr>`).join('')}</tbody></table>`:'<div class="empty"><b>尚未生成数据验证规则</b>点击“生成并运行核心验证”，平台会自动匹配可执行用例、Redis Key 和 MySQL 条件。</div>'}</div>${runs.length?`<div class="card"><h3>数据验证记录</h3><table><thead><tr><th>状态</th><th>接口</th><th>Redis Pattern</th><th>是否变化</th><th>时间</th></tr></thead><tbody>${runs.slice(0,30).map(x=>`<tr><td><span class="tag ${x.status}">${esc(x.status)}</span></td><td><code>${esc(x.path)}</code></td><td><code>${esc(x.redis_pattern)}</code></td><td>${x.changed?'已变化':'未变化'}</td><td>${esc(x.created_at)}</td></tr>`).join('')}</tbody></table></div>`:''}`}
function realChainRun(){return (data.workflow_runs||[]).find(x=>x.workflow_id==='wf_e63d06e1ff')||(data.workflow_runs||[]).find(x=>String(x.workflow_name||'').includes('登录')&&String(x.workflow_name||'').includes('财富'))}
function realChainDetails(){let run=realChainRun(),details=[];try{details=JSON.parse(run?.details||'[]')}catch{}return {run,details,steps:details.filter(x=>x.step)}}
function tableRealChainResult(){let {run,steps}=realChainDetails();if(!run)return'';let passed=run.status==='PASSED';return `<div class="card real-result-card"><div class="real-result-head"><div><span class="tag ${passed?'PASSED':'P0'}">${passed?'真实链路已通过':'真实链路异常'}</span><h2>登录 → 财富等级端到端测试</h2><p>基于客户端真实登录请求、真实 Token 和测试环境真实响应，全程未使用 Mock。</p></div><div class="real-score"><b>${run.passed_steps}/${run.total_steps}</b><span>流程步骤通过</span></div></div><div class="real-timeline">${steps.map((s,i)=>`<div class="real-step ${s.status==='PASSED'?'done':''}"><i>${s.status==='PASSED'?'✓':i+1}</i><div><b>${esc(s.name)}</b><span>${s.duration_ms??'-'} ms${s.assertions?` · ${Object.values(s.assertions).filter(Boolean).length}/${Object.keys(s.assertions).length} 断言通过`:''}</span></div></div>`).join('')}</div><div class="real-result-actions"><span>执行时间：${esc(run.created_at)}</span><button class="primary" onclick="showRealChainReport()">查看真实执行证据</button></div></div>`}
function tableFlowsV2(){return tableRealChainResult()+tableFlows()}
function showRealChainReport(){let {run,steps}=realChainDetails(),recent=(data.runs||[]).filter(x=>['测试账号ID登录','登录后查询财富等级'].includes(x.case_title)).slice(0,2);$('#modalBody').innerHTML=`<h2>真实端到端执行报告</h2><p><span class="tag ${run.status}">${run.status}</span> ${run.passed_steps}/${run.total_steps} 步骤通过 · 未使用 Mock</p><label>执行链路</label>${steps.map(s=>`<div style="padding:13px;margin:8px 0;border:1px solid var(--line);border-radius:12px"><b>${esc(s.name)}</b><span class="tag ${s.status}" style="float:right">${s.status}</span><br><small>耗时 ${s.duration_ms??'-'} ms</small></div>`).join('')}<label>接口执行证据</label>${recent.map(x=>`<div style="padding:13px;margin:8px 0;background:#f7faf8;border-radius:12px"><b>${esc(x.case_title)}</b><br><small>HTTP ${x.http_status} · ${x.duration_ms} ms · ${esc(x.analysis)}</small></div>`).join('')}<label>敏感信息处理</label><p>Token、登录加密参数和签名仅在运行时使用，工作台证据中已脱敏。</p>`;$('#modal').classList.remove('hidden')}
async function refreshConsistency(){data.consistency=await api(`/api/projects/${current}/consistency`);render();switchTab('dataquality')}
async function generateConsistency(){try{toast('正在生成并补齐数据验证规则…');let x=await api(`/api/projects/${current}/generate-consistency`,{method:'POST',body:'{}'}),g=x.generated||x;toast(`已生成 ${g.rules||0} 条规则，可执行 ${g.executable||0} 条，MySQL条件补齐 ${x.autofill?.mysql_conditions||0} 条`);await refreshConsistency()}catch(e){toast(e.message,'error')}}
async function runReadyConsistency(scope='core'){let box=$('#consistencyRunStatus');try{if(box)box.innerHTML='<p>正在调用真实接口，并以只读方式核对 Redis 前后指纹…</p>';let limit=scope==='core'?5:10,x=await api(`/api/projects/${current}/consistency/run-ready`,{method:'POST',body:JSON.stringify({scope,limit})});let msg=`${scope==='core'?'核心':'扩展'}验证：${x.status}，通过${x.passed||0}，阻断${x.blocked||0}，失败${x.failed||0}`;if(box)box.innerHTML=`<div class="summary-panel"><b>${esc(msg)}</b><p>${esc(x.warning||'外部 MySQL/Redis 只读，平台仅保存本地规则、快照和报告。')}</p></div>`;toast(msg,x.status==='PASSED'?'success':x.status==='BLOCKED'?'warning':'error');await refreshConsistency()}catch(e){if(box)box.innerHTML=`<p>${esc(e.message)}</p>`;toast(e.message,'error')}}
async function generateAndRunConsistency(){await generateConsistency();await runReadyConsistency('core')}
async function runConsistency(id){try{toast('正在执行接口并核对 Redis 前后状态…');let x=await api(`/api/consistency-rules/${id}/run`,{method:'POST',body:'{}'});toast(`验证完成：${x.status}，Redis ${x.redis_changed?'发生变化':'保持不变'}`);await refreshConsistency()}catch(e){toast(e.message,'error')}}
function coreSection(title,description,html){return `<section class="core-section"><div class="card" style="margin-bottom:14px"><button class="small" style="float:right" onclick="switchTab('overview')">← 返回任务工作台</button><h2 style="margin:0 0 6px">${title}</h2><p style="margin:0;color:var(--muted)">${description}</p></div>${html}</section>`}
function tableTaskCommandCenter(){let req=(data.requirement_items||[]).length,eps=(data.endpoints||[]).length,cases=(data.cases||[]).length,flows=(data.workflows||[]).length,latest=wealthLastResult||data.wealth_latest||{},hasReport=latest&&Object.keys(latest).length;return `<div class="card" style="background:linear-gradient(135deg,#123d2b,#24704e);color:white"><span style="color:var(--lime);font-size:11px">AI TEST ORCHESTRATION</span><h2 style="font-size:28px;margin:10px 0 6px">从需求到报告，只在这里操作</h2><p style="color:#c9ded3">按顺序完成资料接入、AI生成、业务链路确认、真实执行和报告输出。</p><div class="grid2" style="margin-top:20px"><button class="card" style="text-align:left;cursor:pointer" onclick="switchTab('sources')"><b>① 导入需求与接口</b><br><small>${req}条需求 · ${eps}个接口<br>上传需求文档、图文链接和OpenAPI</small></button><button class="card" style="text-align:left;cursor:pointer" onclick="switchTab('points')"><b>② 查看AI测试资产</b><br><small>${cases}条用例<br>检查测试点、预期结果和覆盖缺口</small></button><button class="card" style="text-align:left;cursor:pointer" onclick="switchTab('flows')"><b>③ 确认跨接口链路</b><br><small>${flows}条业务链路<br>核对登录、变量提取和下游接口</small></button><button class="card" style="text-align:left;cursor:pointer" onclick="switchTab('automation')"><b>④ 执行接口与性能测试</b><br><small>填写本次登录参数，一次生成完整报告</small></button></div><div style="margin-top:16px"><button class="primary" onclick="switchTab('sources')">开始一个测试任务 →</button> <button class="small" onclick="switchTab('database')">配置MySQL / Redis / 后台数据</button> ${hasReport?`<button class="small" onclick="switchTab('automation')">查看最近报告</button>`:''}</div></div>`}
function traceCoverageHtml(){let reqs=data.requirement_items||[],links=(data.trace_links||[]).filter(x=>x.target_type==='endpoint'),eps=Object.fromEntries((data.endpoints||[]).map(x=>[x.id,x])),isUi=r=>/左右切换|轮播|指示点|关闭|勾选|颜色|样式|布局|展示状态|按钮交互/.test((r.title||'')+' '+(r.description||''));if(!reqs.length)return `<div class="card empty"><b>尚无可分析需求</b><p>导入需求文档后，平台会为每条需求筛选多个候选接口并显示关联原因。</p></div>`;let rows=reqs.map((r,i)=>{let all=links.filter(x=>x.requirement_id===r.id).sort((a,b)=>b.confidence-a.confidence),selected=all.filter(x=>+x.selected===1),top=all.slice(0,5),uiOnly=isUi(r);return `<tr><td><b>${esc(r.title)}</b><br><small>${esc(r.acceptance_criteria||'未填写验收标准')}</small><br>${uiOnly?'<span class="tag P1">需要UI执行器</span>':`<button class="small" onclick="showCandidates(${i})">管理候选接口</button> <button class="small" onclick="generateRequirementFlow('${r.id}')" ${selected.length?'':'disabled'}>生成业务链路</button>`}</td><td><span class="tag ${selected.length?'PASSED':uiOnly?'P1':'P0'}">${selected.length?selected.length+'个已关联':uiOnly?'UI需求':'接口未覆盖'}</span><br><small>${all.length}个候选</small></td><td>${top.length?top.map(x=>{let e=eps[x.target_id]||{};return `<div><span class="tag ${+x.selected===1?'PASSED':''}">${Math.round((x.confidence||0)*100)}%</span> ${esc((e.method||'')+' '+(e.path||x.target_id))}<br><small>${esc(x.reason||'AI语义匹配')}</small></div>`}).join(''):uiOnly?'<span>该需求应由Playwright/Appium验证，不强制关联接口。</span>':'<span style="color:#a63131">OpenAPI中暂未找到候选接口</span>'}</td></tr>`}).join('');let covered=reqs.filter(r=>links.some(x=>x.requirement_id===r.id&&+x.selected===1)).length,uiCount=reqs.filter(isUi).length,apiScope=reqs.length-uiCount;return `<div class="card"><h2>需求 → 多接口关联覆盖</h2><p>接口范围已覆盖 <b>${covered}/${apiScope}</b> 条，另有 <b>${uiCount}</b> 条识别为UI需求。AI结合中文业务词、英文接口名、路径和验收标准计算候选，你可以人工增删后再生成链路。</p><table><thead><tr><th>需求与操作</th><th>覆盖状态</th><th>候选接口与关联原因</th></tr></thead><tbody>${rows}</tbody></table></div>`}
function composeCoreWorkspace(){let sources=$('#sources'),apis=$('#apis'),points=$('#points'),cases=$('#cases'),database=$('#database'),redis=$('#redis'),automation=$('#automation'),runs=$('#runs');let sourceHtml=sources.innerHTML,apiHtml=apis.innerHTML,pointHtml=points.innerHTML,caseHtml=cases.innerHTML,databaseHtml=database.innerHTML,redisHtml=redis.innerHTML,automationHtml=automation.innerHTML,runHtml=runs.innerHTML;sources.innerHTML=coreSection('需求资料与接口资产','导入需求、图文文档和OpenAPI，自动筛选需求关联接口。',sourceHtml+traceCoverageHtml()+`<div class="card"><h2>关联接口资产</h2></div>`+apiHtml);points.innerHTML=coreSection('测试点','按需求查看正常、异常、边界、状态和关联测试分析。',pointHtml);cases.innerHTML=coreSection('测试用例','独立查看前置条件、执行步骤、预期结果、实际结果和执行状态。',caseHtml);database.innerHTML=coreSection('MySQL数据库核对','查看数据库结构、接口候选表和字段映射，作为业务数据真值来源。',databaseHtml);redis.innerHTML=coreSection('Redis与后台配置核对','管理Redis连接、Key映射、缓存一致性和财富奖励后台配置。',redisHtml);automation.innerHTML=coreSection('执行与标准报告','执行跨接口链路、接口专项和性能测试，并查看真实证据。',automationHtml+`<div class="card"><h2>最近执行记录</h2></div>`+runHtml);for(const id of ['manual','changes','operations','apis','runs']){let el=$('#'+id);if(el)el.innerHTML=''}}
function wealthResultHtml(r){if(!r||!Object.keys(r).length)return'';let p=r.performance||{},api=r.api_variants||{},apiRows=api.results||[],assertions=r.wealth_api?.assertions||[],card='style="color:#173d2f;background:#fff"';return `<div class="metrics"><div class="metric" ${card}><span>接口测试状态</span><b style="font-size:18px;color:#173d2f">${esc(r.status||'-')}</b></div><div class="metric" ${card}><span>断言通过</span><b style="color:#173d2f">${r.wealth_api?.assertions_passed??'-'}/${r.wealth_api?.assertions_total??'-'}</b></div><div class="metric" ${card}><span>平均耗时</span><b style="color:#173d2f">${p.average_ms??'-'}ms</b></div><div class="metric" ${card}><span>P95</span><b style="color:#173d2f">${p.p95_ms??'-'}ms</b></div></div>${assertions.length?`<div class="card" style="color:#173d2f;background:#fff;margin-top:14px"><h3>正常业务接口断言</h3><table><thead><tr><th>断言</th><th>期望</th><th>实际</th><th>结果</th></tr></thead><tbody>${assertions.map(x=>`<tr><td>${esc(x.name)}</td><td>${esc(typeof x.expected==='object'?JSON.stringify(x.expected):x.expected)}</td><td>${esc(typeof x.actual==='object'?JSON.stringify(x.actual):x.actual)}</td><td><span class="tag ${x.passed?'PASSED':'FAILED'}">${x.passed?'通过':'失败'}</span></td></tr>`).join('')}</tbody></table></div>`:''}<div class="card" style="color:#173d2f;background:#fff;margin-top:14px"><h3>真实异常与安全场景断言</h3><p>正常财富接口：<span class="tag ${r.functional?'PASSED':'P0'}">${r.functional?'通过':'失败'}</span>　场景：${api.passed??0}通过 / ${api.failed??0}失败 / ${api.total??apiRows.length}总计</p>${apiRows.map((x,i)=>`<div style="border:1px solid var(--line);border-radius:12px;padding:14px;margin:10px 0"><b>${i+1}. ${esc(x.name)}</b><span class="tag ${x.status}" style="float:right">${esc(x.status)}</span><div class="grid2" style="margin-top:10px"><p><small>前置条件</small><br>${esc(x.precondition||'-')}</p><p><small>执行动作</small><br>${esc(x.action||'-')}</p><p><small>预期结果</small><br>${esc(x.expected_result||'-')}</p><p><small>实际结果</small><br>${esc(x.actual_result||'-')}</p></div>${(x.assertions||[]).map(a=>`<div><span class="tag ${a.passed?'PASSED':'FAILED'}">${a.passed?'通过':'失败'}</span> ${esc(a.name)}：${esc(a.actual)}</div>`).join('')}<small>HTTP ${x.http_status??'-'} · 业务码 ${x.business_code??'-'} · ${x.duration_ms??'-'}ms</small></div>`).join('')}</div><div class="card" style="color:#173d2f;background:#fff;margin-top:14px"><h3>性能明细</h3><table><tbody><tr><td>请求数</td><td>${p.requests??'-'}</td><td>失败数</td><td>${p.failed??'-'}</td></tr><tr><td>最小耗时</td><td>${p.min_ms??'-'} ms</td><td>最大耗时</td><td>${p.max_ms??'-'} ms</td></tr><tr><td>P50</td><td>${p.p50_ms??'-'} ms</td><td>P95</td><td>${p.p95_ms??'-'} ms</td></tr></tbody></table></div><p style="color:#d8ebe1">报告：${esc(r.report||r.report_path||'未生成')}</p>`}
function jmeterResultHtml(j){if(!j||!Object.keys(j).length)return'';return `<div class="card" style="color:#173d2f;background:#fff;margin-top:14px"><h3>JMeter 正式性能报告</h3><p><span class="tag ${j.status==='PASSED'?'PASSED':'P0'}">${esc(j.status||'未执行')}</span> ${esc(j.message||j.failure_reason||'')}</p><table><tbody><tr><td>线程 × 循环</td><td>${j.threads??'-'} × ${j.loops??'-'}</td><td>Ramp-up</td><td>${j.rampup_seconds??'-'} 秒</td></tr><tr><td>请求 / 错误</td><td>${j.requests??'-'} / ${j.errors??'-'}</td><td>错误率</td><td>${j.error_rate??'-'}%</td></tr><tr><td>吞吐量</td><td>${j.throughput_rps??'-'} req/s</td><td>平均耗时</td><td>${j.average_ms??'-'} ms</td></tr><tr><td>P50 / P90</td><td>${j.p50_ms??'-'} / ${j.p90_ms??'-'} ms</td><td>P95 / P99</td><td>${j.p95_ms??'-'} / ${j.p99_ms??'-'} ms</td></tr><tr><td>响应码分布</td><td colspan="3">${esc(JSON.stringify(j.response_codes||{}))}</td></tr></tbody></table>${j.html_report?`<p>原生HTML报告：${esc(j.html_report)}</p>`:''}</div>`}
function consistencyResultHtml(c){if(!c||!Object.keys(c).length)return'';let m=c.mysql||{},r=c.redis||{},b=c.backend_config||{};return `<div class="card" style="color:#173d2f;background:#fff;margin-top:14px"><h3>MySQL / Redis / 后台配置只读证据</h3><p><span class="tag ${c.strict_read_only?'PASSED':'P0'}">${c.strict_read_only?'严格只读':'策略异常'}</span> ${esc(c.note||'')}</p><table><thead><tr><th>数据源</th><th>状态</th><th>已获取证据</th><th>允许操作</th><th>写权限</th></tr></thead><tbody><tr><td>公司MySQL</td><td>${esc(m.status||'PENDING')}</td><td>${m.tables??0}张表 · ${m.api_mappings??0}条接口映射<br><small>业务行核对：${esc(m.business_row_checks||'PENDING')}</small></td><td>${esc((c.policy?.mysql||[]).join(', '))}</td><td><span class="tag PASSED">禁止</span></td></tr><tr><td>公司Redis</td><td>${esc(r.status||'PENDING')}</td><td>${r.api_mappings??0}条映射 · ${r.snapshots??0}个只读快照</td><td>${esc((c.policy?.redis||[]).join(', '))}</td><td><span class="tag PASSED">禁止</span></td></tr><tr><td>后台配置</td><td>${esc(b.status||'PENDING')}</td><td>${b.configs??0}项配置 · ${b.active_configs??0}项启用</td><td>GET</td><td><span class="tag PASSED">禁止</span></td></tr></tbody></table><p>一致性规则 ${c.consistency_rules??0} 条，真实执行 ${c.executed_runs??0} 次；结果：${esc(JSON.stringify(c.result_counts||{}))}</p></div>`}
function flowTraceHtml(xs){if(!xs?.length)return'';let labels={none:'无',authentication:'鉴权失败',request_contract:'请求契约',rate_limit:'限流',server:'服务端异常',network_or_environment:'网络/环境',business_assertion:'业务断言',business_data_mismatch:'业务数据不一致',performance_or_authentication:'性能或鉴权'};return `<div class="card" style="color:#173d2f;background:#fff;margin-top:14px"><h3>跨接口变量与逐步断言</h3><table><thead><tr><th>步骤</th><th>状态</th><th>输入来源</th><th>断言结果</th><th>输出</th><th>失败定位</th></tr></thead><tbody>${xs.map(x=>`<tr><td><b>${x.order}. ${esc(x.name)}</b><br><small>HTTP ${x.http_status??'-'}</small></td><td><span class="tag ${x.status==='PASSED'?'PASSED':'FAILED'}">${esc(x.status)}</span></td><td><small>${esc(JSON.stringify(x.inputs||{}))}</small></td><td>${Object.entries(x.assertions||{}).map(([k,v])=>`<div><span class="tag ${v===true?'PASSED':v===false?'FAILED':''}">${esc(k)}</span> ${esc(typeof v==='object'?JSON.stringify(v):v)}</div>`).join('')}</td><td><small>${esc(JSON.stringify(x.outputs||{}))}</small></td><td>${esc(labels[x.failure_category]||x.failure_category||'无')}</td></tr>`).join('')}</tbody></table><p style="font-size:12px">Token只在本次运行内存中传递，页面和报告仅显示脱敏占位符。</p></div>`}
function tableReports(){let xs=data?.generated_reports||[];if(!xs.length)return `<div class="card empty"><b>尚未生成测试报告</b><p>执行接口专项或JMeter性能测试后，报告会自动出现在这里。</p></div>`;return `<div class="card"><span class="tag PASSED">REPORT CENTER</span><h2>测试报告中心</h2><p>统一查看平台综合报告、JMeter原生HTML和历史执行证据，共 ${xs.length} 份。</p></div><div class="card"><table><thead><tr><th>生成时间</th><th>报告</th><th>状态</th><th>摘要</th><th>操作</th></tr></thead><tbody>${xs.map(x=>`<tr><td>${esc((x.created_at||'').replace('T',' '))}</td><td><b>${esc(x.name)}</b><br><small>${esc(x.kind)} · ${esc(x.file_name)}</small></td><td><span class="tag ${x.status==='PASSED'?'PASSED':x.status==='FAILED'?'FAILED':'P1'}">${esc(x.status)}</span></td><td>${esc(x.summary)}</td><td>${x.html_url?`<button class="small" onclick="openReport('${esc(x.html_url)}')">查看HTML</button> `:''}${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">查看JSON</button>`:''}</td></tr>`).join('')}</tbody></table></div>`}
function openReport(url){window.open(url,'_blank','noopener')}
function showReportsPage(){if(!current)return toast('请先选择项目','warning');switchTab('reports');$('#reportMenu')?.classList.add('active');$('#pageTitle').textContent='测试报告中心';$('#subtitle').textContent='综合报告、JMeter性能报告与历史执行证据'}
function tableWealthApiWorkbench(){return `<div class="card" id="wealthApiWorkbench" style="background:linear-gradient(135deg,#123d2b,#1c5840);color:white"><span class="tag PASSED">GENERIC API CHAIN + JMETER</span><h2 style="margin:12px 0 6px">通用接口链路调试台</h2><p style="color:#c8ddd2">财富与魅力查询接口已验证无需sn。请选择使用已有Ticket，或在Ticket失效时重新登录获取。</p><div class="formrow"><select id="credentialMode" onchange="toggleCredentialEditor()"><option value="ticket">使用已有Ticket</option><option value="login">重新登录获取Ticket</option></select></div><div id="ticketEditor"><input id="runtimeTicket" placeholder="粘贴Ticket；留空则复用本机已保存Ticket" autocomplete="off" data-lpignore="true"></div><div id="credentialEditor" class="hidden"><div class="formrow"><input id="wealthLoginT" placeholder="登录请求头 t（必填）" autocomplete="off" data-lpignore="true"><input id="wealthLoginSn" placeholder="登录请求头 sn（可留空）" autocomplete="off" data-lpignore="true"></div><input id="wealthLoginPassword" type="password" placeholder="请求体加密密码（必填）" autocomplete="new-password" data-lpignore="true"></div><div class="formrow" style="margin-top:12px"><input id="wealthPerfCount" type="number" min="1" max="100" value="5" placeholder="接口快速冒烟次数"><input id="jmeterThreads" type="number" min="1" max="50" value="2" placeholder="JMeter线程数"></div><div class="formrow"><input id="jmeterLoops" type="number" min="1" max="100" value="5" placeholder="每线程循环数"><input id="jmeterRampup" type="number" min="0" max="300" value="2" placeholder="Ramp-up秒"></div><button id="wealthRunButton" class="primary" onclick="runWealthApiWorkbench()">▶ 执行完整业务链路</button><div id="wealthApiResult" style="margin-top:14px">${wealthResultHtml(wealthLastResult)}${flowTraceHtml(wealthLastResult?.flow_trace)}${consistencyResultHtml(wealthLastResult?.data_consistency)}${jmeterResultHtml(wealthLastResult?.jmeter)}</div></div>`}
function toggleCredentialEditor(){let login=$('#credentialMode')?.value==='login';$('#credentialEditor')?.classList.toggle('hidden',!login);$('#ticketEditor')?.classList.toggle('hidden',login)}
function tableAccountPool(){let xs=data.test_accounts||[];return `<div class="card"><span class="tag PASSED">MULTI ACCOUNT</span><h2>多账号测试池</h2><p>账号资料用于登录、送礼、财富和魅力链路。Ticket与加密密码只在本机加密保存，页面不回显。</p><div class="formrow"><input id="acctNickname" placeholder="昵称"><input id="acctShortId" placeholder="短ID，例如888"><input id="acctUid" placeholder="UID"></div><div class="formrow"><input id="acctLevel" type="number" placeholder="财富等级"><select id="acctRole"><option value="general">通用账号</option><option value="sender">送礼人</option><option value="receiver">收礼人</option><option value="boundary">边界账号</option></select><label style="display:flex;align-items:center;gap:7px"><input id="acctMutable" type="checkbox" style="width:auto">允许修改</label></div><div class="formrow"><input id="acctTicket" placeholder="Ticket（可稍后补充）" autocomplete="off" data-lpignore="true"><input id="acctPassword" type="password" placeholder="加密密码（可稍后补充）" autocomplete="new-password" data-lpignore="true"></div><button class="primary" onclick="saveTestAccount()">保存测试账号</button></div>${xs.length?`<div class="card"><table><thead><tr><th>账号</th><th>UID</th><th>等级</th><th>用途</th><th>权限</th><th>凭证</th></tr></thead><tbody>${xs.map(x=>`<tr><td><b>${esc(x.nickname||'-')}</b><br><small>ID ${esc(x.short_id)}</small></td><td>${x.account_uid}</td><td>${x.wealth_level??'-'}</td><td>${esc({sender:'送礼人',receiver:'收礼人',boundary:'边界账号',general:'通用账号'}[x.account_role]||x.account_role)}</td><td><span class="tag ${x.mutable?'P1':'PASSED'}">${x.mutable?'允许修改':'只读'}</span></td><td>Ticket ${x.has_ticket?'✓':'—'}　密码 ${x.has_password?'✓':'—'}</td></tr>`).join('')}</tbody></table></div>`:''}`}
async function saveTestAccount(){let payload={nickname:$('#acctNickname').value.trim(),short_id:$('#acctShortId').value.trim(),uid:$('#acctUid').value.trim(),wealth_level:$('#acctLevel').value?+$('#acctLevel').value:null,role:$('#acctRole').value,mutable:$('#acctMutable').checked,ticket:$('#acctTicket').value.trim(),encrypted_password:$('#acctPassword').value.trim()};if(!payload.short_id||!payload.uid)return toast('请填写短ID和UID','warning');try{await api(`/api/projects/${current}/test-accounts`,{method:'POST',body:JSON.stringify(payload)});toast('测试账号已安全保存','success');await openProject(current);switchTab('automation')}catch(e){toast(e.message,'error')}}
function tableLoginPerformanceSpecial(){let xs=data.test_accounts||[],ready=xs.filter(x=>x.has_password);return `<div class="card"><span class="tag P1">LOGIN PERFORMANCE</span><h2>多账号登录性能专项</h2><p>仅用于认证服务容量验证；普通业务压测不会纳入登录接口。</p><div class="formrow"><input id="loginPerfThreads" type="number" min="1" max="50" value="3" placeholder="并发线程"><input id="loginPerfLoops" type="number" min="1" max="100" value="1" placeholder="每账号循环"><input id="loginPerfRampup" type="number" min="0" max="600" value="0" placeholder="Ramp-up秒"></div><label>账号范围</label><select id="loginPerfScope"><option value="ready">全部已保存密码账号（${ready.length}）</option><option value="all">全部账号（${xs.length}，无密码会阻断）</option></select><button id="loginPerfButton" class="primary" onclick="runLoginPerformanceSpecial()">执行登录专项</button><div id="loginPerfResult" style="margin-top:12px"></div></div>`}
async function runLoginPerformanceSpecial(){let button=$('#loginPerfButton'),box=$('#loginPerfResult'),scope=$('#loginPerfScope')?.value||'ready',accounts=data.test_accounts||[],selected=scope==='ready'?accounts.filter(x=>x.has_password):accounts,payload={threads:+$('#loginPerfThreads')?.value||3,loops:+$('#loginPerfLoops')?.value||1,rampup:+$('#loginPerfRampup')?.value||0,uids:selected.map(x=>x.account_uid)};if(!selected.length)return toast('当前没有可用于登录专项的账号','warning');button.disabled=true;button.textContent='正在执行登录专项…';box.innerHTML='<p>正在按账号池并发调用登录接口，凭证仅在本机运行时使用。</p>';try{let r=await api(`/api/projects/${current}/login-performance`,{method:'POST',body:JSON.stringify(payload)}),s=r.summary||{};box.innerHTML=`<div class="summary-panel"><b>${esc(r.status)}</b><p>${s.executed||0}次登录 · 成功率${s.success_rate||0}% · P95 ${s.p95_ms||0}ms · 阻断${s.blocked||0}</p></div>`;toast(`登录专项完成：${r.status}，成功率${s.success_rate||0}%`,r.status==='PASSED'?'success':r.status==='BLOCKED'?'warning':'error');await openProject(current);switchTab('reports')}catch(e){box.innerHTML=`<p>${esc(e.message)}</p>`;toast(e.message,'error')}finally{let b=$('#loginPerfButton');if(b){b.disabled=false;b.textContent='执行登录专项'}}}
async function runWealthApiWorkbench(){let mode=$('#credentialMode')?.value||'ticket',ticket=mode==='ticket'?($('#runtimeTicket')?.value.trim()||''):'',t=mode==='login'?($('#wealthLoginT')?.value.trim()||''):'',sn=mode==='login'?($('#wealthLoginSn')?.value.trim()||''):'',password=mode==='login'?($('#wealthLoginPassword')?.value.trim()||''):'',count=+$('#wealthPerfCount').value||5,threads=+$('#jmeterThreads').value||2,loops=+$('#jmeterLoops').value||5,rampup=+$('#jmeterRampup').value||0,box=$('#wealthApiResult'),button=$('#wealthRunButton');if(mode==='login'&&(!t||!password))return toast('重新登录时需要填写t和加密密码，sn可以留空','warning');button.disabled=true;button.textContent='正在执行完整业务链路…';box.innerHTML='<p>正在准备Ticket、传递身份变量、校验财富接口并启动JMeter…</p>';try{let x=await api(`/api/projects/${current}/run-all`,{method:'POST',body:JSON.stringify({runtime_ticket:ticket,login_t:t,login_sn:sn,login_password_encrypted:password,performance_requests:count,run_jmeter:true,jmeter_threads:threads,jmeter_loops:loops,jmeter_rampup:rampup})}),r=x.full_test||{};wealthLastResult=r;if(['MISSING','EXPIRED','INCOMPLETE'].includes(r.credential_status)){box.innerHTML=`<div class="card" style="color:#7a321c"><h3>需要更新凭证</h3><p>${esc(r.message)}</p></div>`;toast(r.message,'warning');return}box.innerHTML=wealthResultHtml(r)+flowTraceHtml(r.flow_trace)+consistencyResultHtml(r.data_consistency)+jmeterResultHtml(r.jmeter);if($('#wealthLoginPassword'))$('#wealthLoginPassword').value='';if($('#runtimeTicket'))$('#runtimeTicket').value='';toast(`链路完成：接口 ${r.functional?'通过':'失败'}，JMeter ${r.jmeter?.status||'未执行'}`,r.jmeter?.status==='PASSED'?'success':'warning');await openProject(current);switchTab('automation')}catch(e){box.innerHTML=`<p style="color:#ffd4d4">${esc(e.message)}</p>`;toast(e.message,'error')}finally{let b=$('#wealthRunButton');if(b){b.disabled=false;b.textContent='▶ 执行完整业务链路'}}}
const renderBase=render;render=function(){renderBase();$("#redis").innerHTML=tableRedisV2()+tableConsistency();$("#flows").innerHTML=tableFlowsV2();$("#reports").innerHTML=enterpriseReportCenter();let genericAutomation=$("#automation").innerHTML;$("#automation").innerHTML=`<div class="card"><div class="formrow"><button id="wealthCenterTab" class="primary" onclick="switchAutomationCenter('wealth')">财富等级专项</button><button id="genericCenterTab" class="small" onclick="switchAutomationCenter('generic')">通用接口与性能</button></div></div><div id="wealthSpecialCenter">${tableAccountPool()+tableLoginPerformanceSpecial()+tableEvidenceCenter()+tableGiftChainWorkbench()+tableWealthApiWorkbench()}</div><div id="genericAutomationCenter" class="hidden">${genericAutomation}</div>`;if($("#giftChainResult")&&data.gift_latest)$("#giftChainResult").innerHTML=giftChainResultHtml(data.gift_latest);labelSpecialCenters();let result=tableRealChainResult();if(result)$("#overview").insertAdjacentHTML('beforeend',result);$("#overview").insertAdjacentHTML('afterbegin',tableTaskCommandCenter());polishInterfaceCopy();composeCoreWorkspace()};
const openProjectBase=openProject;
openProject=async function(id){
  await openProjectBase(id);
  const requests=[
    api(`/api/projects/${id}/consistency`).catch(()=>({rules:[],runs:[]})),
    api(`/api/projects/${id}/wealth-latest-report`).catch(()=>({})),
    api(`/api/projects/${id}/gift-latest-report`).catch(()=>({})),
    api(`/api/projects/${id}/evidence-center`).catch(()=>({})),
    api(`/api/projects/${id}/reports`).catch(()=>([])),
    api(`/api/projects/${id}/test-accounts`).catch(()=>([])),
    api(`/api/projects/${id}/quality-profile`).catch(()=>({sections:[],score:0})),
    api(`/api/projects/${id}/diagnosis`).catch(()=>({items:[],summary:{}})),
  ];
  const [consistency,wealthLatest,giftLatest,evidenceCenter,reports,accounts,qualityProfile,diagnosis]=await Promise.all(requests);
  if(current!==id)return;
  data.consistency=consistency;
  data.wealth_latest=wealthLatest;
  if(!wealthLastResult||!Object.keys(wealthLastResult).length)wealthLastResult=wealthLatest;
  data.gift_latest=giftLatest;
  data.evidence_center=evidenceCenter;
  data.generated_reports=reports;
  data.test_accounts=accounts;
  data.quality_profile=qualityProfile;
  data.diagnosis=diagnosis;
  render()
};
toast=function(message,type){let text=String(message||'操作完成');if(!type){type=/失败|错误|异常|不存在|不能为空|请选择/.test(text)?'error':/警告|风险|阻止|卡点|未完成/.test(text)?'warning':/完成|成功|已连接|已保存|已生成|正常/.test(text)?'success':'info'}let d=document.createElement('div');d.className=`toast ${type}`;d.textContent=text;d.setAttribute('role','status');$("#toast").append(d);setTimeout(()=>{d.style.opacity='0';d.style.transform='translateY(8px)';setTimeout(()=>d.remove(),220)},3200)};
async function checkPlatformVersion(){try{let h=await fetch('/api/health?ts='+Date.now(),{cache:'no-store'}).then(r=>r.json()),server=h.frontend_build||h.build,banner=$('#demoModeBanner');window.platformHealth=h;document.body.classList.toggle('demo-mode',!!h.demo_mode);banner?.classList.toggle('hidden',!h.demo_mode);if(server&&PAGE_BUILD&&server!==PAGE_BUILD){let key=`autotest-reload-${server}`;if(!sessionStorage.getItem(key)){sessionStorage.setItem(key,'1');location.replace(location.pathname+'?build='+encodeURIComponent(server));return}let b=$('#versionWarning')||document.createElement('div');b.id='versionWarning';b.innerHTML=`<b>平台资源未能自动同步</b><span>页面：${esc(PAGE_BUILD)}　服务：${esc(server)}</span><span>请按 Ctrl+F5 强制刷新；无需重复重启服务。</span>`;if(!b.parentNode)document.body.append(b)}else{$('#versionWarning')?.remove()}}catch{}}
function mountAssistant(){if($('#aiAssistant'))return;let root=document.createElement('div');root.id='aiAssistant';root.innerHTML=`<button id="aiAssistantOrb" onclick="toggleAssistant()" aria-label="打开 AI 测试助手"><span class="ai-face"><i></i><i></i></span><b>AI</b><em></em></button><div id="aiAssistantHint">我是 AI 测试助手，可以帮你操作当前工作台</div><section id="aiAssistantPanel" class="hidden"><header><div class="ai-avatar"><span class="ai-face"><i></i><i></i></span></div><div><h3>AI 测试助手</h3><p><span></span> 已就绪 · 可导航、填写和生成测试资产</p></div><button onclick="toggleAssistant()">×</button></header><div id="aiChat"><div class="ai-message assistant"><div>你好，我可以直接操作当前工作台，例如：</div><ul><li>打开完整执行证据</li><li>打开性能报告</li><li>准备1057礼物循环20次</li><li>打开测试用例</li><li>生成跨接口流程</li></ul><div>真实送礼仍需要你亲自确认。</div></div></div><div class="ai-chips"><button onclick="assistantQuick('打开完整执行证据')">完整证据</button><button onclick="assistantQuick('打开性能报告')">性能报告</button><button onclick="assistantQuick('准备1057礼物循环20次')">准备送礼</button></div><div class="ai-compose"><textarea id="aiInput" rows="1" placeholder="输入指令，例如：打开风险报告" onkeydown="assistantKey(event)"></textarea><button onclick="sendAssistant()">发送</button></div></section>`;document.body.append(root);setTimeout(()=>$('#aiAssistantHint')?.classList.add('show'),500);setTimeout(()=>$('#aiAssistantHint')?.classList.remove('show'),5500)}
function toggleAssistant(){let panel=$('#aiAssistantPanel');panel.classList.toggle('hidden');$('#aiAssistantHint')?.classList.remove('show');if(!panel.classList.contains('hidden')){loadAssistantHistory();setTimeout(()=>$('#aiInput')?.focus(),100)}}
function assistantQuick(text){$('#aiInput').value=text;sendAssistant()}
function assistantKey(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendAssistant()}}
function appendAssistant(role,text){let chat=$('#aiChat'),d=document.createElement('div');d.className=`ai-message ${role}`;d.textContent=text;chat.append(d);chat.scrollTop=chat.scrollHeight;return d}
async function loadAssistantHistory(){if(!current)return;try{let xs=await api(`/api/projects/${current}/assistant/messages`);if(!xs.length)return;let chat=$('#aiChat');chat.innerHTML='';xs.forEach(x=>appendAssistant(x.role,x.content))}catch{}}
async function applyAssistantAction(x){let result=x.result||{};if(result.refresh||['auto_match_data','generate_consistency','generate_workflows','generate_nonfunctional'].includes(x.action))await openProject(current);if(x.action==='navigate'||x.action==='analyze_report'){switchTab(result.tab||'overview');if(result.report_kind)setTimeout(()=>switchEnterpriseReport(result.report_kind),0)}else if(x.action==='prepare_gift'){switchTab('automation');switchAutomationCenter('wealth');setTimeout(()=>{if($('#giftIterations'))$('#giftIterations').value=result.iterations||20;if($('#giftId'))$('#giftId').value=result.gift_id||1057;if($('#giftConfirm'))$('#giftConfirm').checked=false;if($('#giftChainButton'))$('#giftChainButton').textContent=`▶ 执行${result.iterations||20}次财富送礼链路`;toast('参数已填写，请核对并亲自勾选真实送礼确认','warning')},0)}else if(['auto_match_data','generate_consistency'].includes(x.action))switchTab('redis');else if(result.tab)switchTab(result.tab)}
async function sendAssistant(){let input=$('#aiInput'),message=input.value.trim();if(!message)return;if(!current){appendAssistant('assistant','请先从左侧选择一个项目，我才能操作对应的测试资产。');return}input.value='';appendAssistant('user',message);let waiting=appendAssistant('assistant','正在理解指令并操作工作台…');waiting.classList.add('thinking');try{let x=await api(`/api/projects/${current}/assistant`,{method:'POST',body:JSON.stringify({message})});waiting.remove();appendAssistant('assistant',x.message);await applyAssistantAction(x)}catch(e){waiting.remove();appendAssistant('assistant',e.message)}}
function walletResultHtml(w){if(!w||!Object.keys(w).length)return'';return `<div class="card" style="color:#173d2f;background:#fff;margin-top:14px"><h3>钱包余额断言</h3><p><span class="tag ${w.status==='PASSED'?'PASSED':'FAILED'}">${esc(w.status||'-')}</span> Gold余额：<b>${w.gold_num??'-'}</b> · UID：${w.uid??'-'} · ${w.assertions_passed??0}/${w.assertions_total??0}条通过</p><table><thead><tr><th>断言</th><th>期望</th><th>实际</th><th>结果</th></tr></thead><tbody>${(w.assertions||[]).map(x=>`<tr><td>${esc(x.name)}</td><td>${esc(typeof x.expected==='object'?JSON.stringify(x.expected):x.expected)}</td><td>${esc(typeof x.actual==='object'?JSON.stringify(x.actual):x.actual)}</td><td><span class="tag ${x.passed?'PASSED':'FAILED'}">${x.passed?'通过':'失败'}</span></td></tr>`).join('')}</tbody></table></div>`}
function tableGiftChainWorkbench(){let xs=data.test_accounts||[],sender=xs.find(x=>x.account_role==='sender')||{},receiver=xs.find(x=>x.account_role==='receiver')||{},latest=data.gift_latest?.upgrade_validation||{};return `<div class="card" style="border:1px solid #d9b55f;background:#fffaf0"><span class="tag P1">CONTROLLED REAL GIFT</span><h2>财富升级闭环验证</h2><p>平台先读取财富、钱包和账单快照，再调用真实送礼接口制造可控经验变化，最后回收接口、账单和升级门槛证据。</p><div class="formrow"><select id="giftSender" onchange="syncGiftControls()">${xs.map(x=>`<option value="${x.account_uid}" ${x.account_uid===sender.account_uid?'selected':''}>送礼人：${esc(x.short_id)} / ${x.account_uid}</option>`).join('')}</select><select id="giftReceiver" onchange="syncGiftControls()">${xs.map(x=>`<option value="${x.account_uid}" ${x.account_uid===receiver.account_uid?'selected':''}>收礼人：${esc(x.short_id)} / ${x.account_uid}</option>`).join('')}</select></div><div class="formrow"><input id="giftRoomUid" value="${sender.account_uid||1454428}" placeholder="房间UID" oninput="syncGiftControls()"><input id="giftId" value="1057" placeholder="礼物ID" oninput="syncGiftControls()"></div><div class="formrow"><input id="giftIterations" type="number" min="1" max="100" value="20" placeholder="执行次数（1-100）" oninput="syncGiftControls()"><input id="giftTargetLevel" type="number" min="1" max="100" value="${latest.target_level||2}" placeholder="目标等级，例如2" oninput="syncGiftControls()"></div><div class="formrow"><input id="giftTargetThreshold" type="number" min="0" value="${latest.target_threshold||''}" placeholder="目标累计经验门槛，可留空"><input id="giftSharedTicket" type="password" placeholder="Ticket可留空；失效时使用账号凭证重新登录" autocomplete="off" data-lpignore="true"></div><label style="display:flex;align-items:center;gap:8px;margin:12px 0"><input id="giftConfirm" type="checkbox" style="width:auto"><span id="giftConfirmText">确认按当前配置执行真实送礼并产生Gold消费</span></label><p id="giftExecutionSummary" style="font-size:12px;color:var(--muted)"></p><button id="giftChainButton" class="primary" onclick="runGiftChain()">▶ 执行财富升级验证</button><div id="giftChainResult" style="margin-top:14px"></div></div>`}
function syncGiftControls(){let count=Math.max(1,Math.min(100,+$('#giftIterations')?.value||1)),giftId=+$('#giftId')?.value||0,target=+$('#giftTargetLevel')?.value||2,threshold=$('#giftTargetThreshold')?.value||'自动读取升级表',sender=$('#giftSender')?.selectedOptions?.[0]?.textContent||'所选账号',receiver=$('#giftReceiver')?.selectedOptions?.[0]?.textContent||'所选账号';if($('#giftIterations'))$('#giftIterations').value=count;if($('#giftConfirmText'))$('#giftConfirmText').textContent=`确认由${sender}向${receiver}真实赠送礼物 ${giftId||'未填写'}，共 ${count} 次，并验证财富是否达到 Lv.${target}`;if($('#giftExecutionSummary'))$('#giftExecutionSummary').textContent=`当前目标：Lv.${target} · 门槛 ${threshold} · 礼物ID ${giftId||'-'} · 顺序执行 ${count} 次 · 任一次失败立即停止`;if($('#giftChainButton'))$('#giftChainButton').textContent=`▶ 执行 ${count} 次财富升级验证`;if($('#giftConfirm'))$('#giftConfirm').checked=false}
function giftUpgradeSummaryHtml(u){if(!u||!Object.keys(u).length)return'';let cls=u.actual_upgrade?'PASSED':u.expected_upgrade?'FAILED':'P1';return `<div class="metrics"><div class="metric"><span>送礼前</span><b>Lv.${u.before?.level??'-'}</b><small>经验 ${u.before?.experience??'-'}</small></div><div class="metric"><span>送礼后</span><b>Lv.${u.after?.level??'-'}</b><small>经验 ${u.after?.experience??'-'}</small></div><div class="metric"><span>目标门槛</span><b>${u.target_threshold??'-'}</b><small>Lv.${u.target_level??'-'}</small></div><div class="metric"><span>本次消费</span><b>${u.consume_gold??'-'}</b><small>差值 ${u.after?.experience_delta??'-'}</small></div></div><div class="card"><h3>升级结论 <span class="tag ${cls}">${u.actual_upgrade?'已升级':u.expected_upgrade?'应升未升':'未达到门槛'}</span></h3><p>${esc(u.conclusion||'')}</p><p>升级前距离目标还差：${u.before?.remaining_to_target??'-'} · 理论送礼后经验：${u.expected_experience_after??'-'} · 升级表推导等级：Lv.${u.expected_level_after??'-'}</p></div>`}
function giftChainResultHtml(r){if(!r||!Object.keys(r).length)return'';let a=r.assertions||[],runs=r.steps?.gift_runs||[],callsOk=runs.length&&runs.every(x=>x.status==='PASSED'),hasDifference=a.some(x=>!x.passed),status=r.status==='BUSINESS_DIFFERENCE'||(r.status==='FAILED'&&callsOk&&hasDifference)?'BUSINESS_DIFFERENCE':r.status,label=status==='BUSINESS_DIFFERENCE'?'存在业务差异':status,statusClass=status==='PASSED'?'PASSED':status==='BLOCKED'||status==='BUSINESS_DIFFERENCE'?'P1':'FAILED';return `<div class="card"><h3>财富升级验证结果 <span class="tag ${statusClass}">${esc(label)}</span></h3><p>${esc(r.message||'真实链路已完成')}</p>${giftUpgradeSummaryHtml(r.upgrade_validation)}${a.length?`<table><thead><tr><th>断言</th><th>期望</th><th>实际</th><th>结果</th></tr></thead><tbody>${a.map(x=>`<tr><td>${esc(x.name)}</td><td>${esc(typeof x.expected==='object'?JSON.stringify(x.expected):x.expected)}</td><td>${esc(typeof x.actual==='object'?JSON.stringify(x.actual):x.actual)}</td><td><span class="tag ${x.passed?'PASSED':'FAILED'}">${x.passed?'通过':'失败'}</span></td></tr>`).join('')}</tbody></table>`:''}<p>报告：${esc(r.report||'-')}</p>${r.redis_manual_check?`<p><b>Redis人工补充：</b><code>${esc(r.redis_manual_check.command_template)}</code></p>`:''}</div>`}
async function runGiftChain(){let button=$('#giftChainButton'),box=$('#giftChainResult'),confirmed=$('#giftConfirm')?.checked,iterations=Math.max(1,Math.min(100,+$('#giftIterations').value||1)),giftId=+$('#giftId').value,targetLevel=+$('#giftTargetLevel')?.value||2,targetThreshold=$('#giftTargetThreshold')?.value.trim();if(!giftId)return toast('请填写有效的礼物ID','warning');if(!confirmed)return toast(`请先核对配置并确认真实赠送礼物${giftId}，共${iterations}次`,'warning');let payload={sender_uid:+$('#giftSender').value,receiver_uid:+$('#giftReceiver').value,room_uid:+$('#giftRoomUid').value,gift_id:giftId,gift_iterations:iterations,target_level:targetLevel,expected_target_threshold:targetThreshold,runtime_ticket:$('#giftSharedTicket').value.trim(),confirm_batch_gift:true};button.disabled=true;button.textContent=`正在顺序执行 ${iterations} 次…`;box.innerHTML=`<p>正在进行登录、财富、钱包和账单预检；通过后顺序送礼并回收升级证据。</p>`;try{let r=await api(`/api/projects/${current}/gift-chain`,{method:'POST',body:JSON.stringify(payload)});box.innerHTML=giftChainResultHtml(r);$('#giftSharedTicket').value='';let ok=r.status==='PASSED',difference=r.status==='BUSINESS_DIFFERENCE';toast(ok?`财富升级验证通过`:difference?'接口执行成功，但升级/数据断言存在差异':r.message||`链路结果：${r.status}`,ok?'success':'warning');await openProject(current);switchTab('automation')}catch(e){box.innerHTML=`<p>${esc(e.message)}</p>`;toast(e.message,'error')}finally{let b=$('#giftChainButton');if(b){b.disabled=false;syncGiftControls()}}}
function tableEvidenceCenter(){let e=data.evidence_center||{},t=e.thresholds||{},r=e.redis_snapshot||{},latest=data.gift_latest||{},sender=latest.accounts?.sender?.uid||1454428;return `<div class="card"><span class="tag PASSED">DATA EVIDENCE</span><h2>财富专项数据证据</h2><div class="metrics"><div class="metric"><span>升级表</span><b>${t.loaded?t.rows+'级':'未导入'}</b></div><div class="metric"><span>Redis离线Hash</span><b>${r.loaded?r.fields+'个UID':'未导入'}</b></div><div class="metric"><span>在线Redis访问</span><b>${e.live_redis_access?'开启':'关闭'}</b></div></div><p>升级表：${esc(t.source||'-')}　Redis快照：${esc(r.source||'-')}　Key：${esc(r.key||'-')}</p><h3>补录本次人工HGET结果</h3><div class="formrow"><input id="manualRedisUid" value="${sender}" placeholder="UID"><input id="manualRedisValue" placeholder="输入HGET返回的累计经验值"></div><button class="small" onclick="submitManualRedisResult()">保存并重新计算报告断言</button><p><small>该操作只更新工作台报告，不连接或修改Redis。</small></p></div>`}
async function submitManualRedisResult(){let uid=+$('#manualRedisUid').value,value=$('#manualRedisValue').value.trim();if(!uid||!/^\d+$/.test(value))return toast('请填写正确的UID和Redis累计经验值','warning');try{let r=await api(`/api/projects/${current}/redis-manual-result`,{method:'POST',body:JSON.stringify({uid,value})});toast(`Redis证据已写入报告：${r.assertions_passed}/${r.assertions_total}`,'success');await openProject(current);switchTab('automation')}catch(e){toast(e.message,'error')}}
function switchAutomationCenter(kind){let wealth=kind==='wealth';$('#wealthSpecialCenter')?.classList.toggle('hidden',!wealth);$('#genericAutomationCenter')?.classList.toggle('hidden',wealth);if($('#wealthCenterTab'))$('#wealthCenterTab').className=wealth?'primary':'small';if($('#genericCenterTab'))$('#genericCenterTab').className=wealth?'small':'primary'}
function labelSpecialCenters(){let card=$('#wealthApiWorkbench');if(card){let tag=card.querySelector('.tag'),h=card.querySelector('h2'),p=card.querySelector('p');if(tag)tag.textContent='WEALTH API BASELINE + JMETER';if(h)h.textContent='财富接口基础专项';if(p)p.textContent='财富接口自身的基础契约用于执行预检；最终结论以报告中心按业务分类、自动去重后的断言为准。'}let reportCopy=$('#enterprise-functional p');if(reportCopy)reportCopy.textContent='展示本次财富送礼链路中的单接口契约断言；送礼前后重复规则合并为一条，并保留两个阶段的实际证据。'}
function assertionSummaryHtml(){let report=data.gift_latest||{},xs=report.assertions||[];if(!xs.length)return `<div class="card empty"><b>暂无可归纳断言</b><p>执行接口链路后，断言会按业务步骤自动汇总到这里。</p></div>`;let groups={};xs.forEach(x=>{let name=x.name||'未分类',group=name.includes('｜')?name.split('｜')[0]:'跨步骤';(groups[group]||(groups[group]=[])).push(x)});let passed=xs.filter(x=>x.passed).length,failed=xs.filter(x=>!x.passed).length;return `<div class="metrics"><div class="metric"><span>断言总数</span><b>${xs.length}</b></div><div class="metric"><span>通过</span><b>${passed}</b></div><div class="metric"><span>失败</span><b>${failed}</b></div><div class="metric"><span>覆盖分组</span><b>${Object.keys(groups).length}</b></div></div><div class="card"><h2>断言覆盖归纳</h2><p>来源：${esc(report.report_type||'跨接口报告')} · ${esc(report.executed_at||'')}</p><div class="grid2">${Object.entries(groups).map(([name,items])=>`<div class="card"><h3>${esc(name)}</h3><p><span class="tag PASSED">通过 ${items.filter(x=>x.passed).length}</span> <span class="tag ${items.some(x=>!x.passed)?'FAILED':''}">失败 ${items.filter(x=>!x.passed).length}</span></p></div>`).join('')}</div></div><div class="card"><h3>全部断言明细</h3><table><thead><tr><th>分组/断言</th><th>期望</th><th>实际</th><th>结论</th></tr></thead><tbody>${xs.map(x=>`<tr><td><b>${esc(x.name)}</b>${x.source?`<br><small>证据：${esc(x.source)}</small>`:''}</td><td>${esc(typeof x.expected==='object'?JSON.stringify(x.expected):x.expected)}</td><td>${esc(typeof x.actual==='object'?JSON.stringify(x.actual):x.actual)}</td><td><span class="tag ${x.passed?'PASSED':'FAILED'}">${x.passed?'通过':'失败'}</span></td></tr>`).join('')}</tbody></table></div>`}
function tableReportWorkspace(){return `<div class="card"><div class="formrow"><button id="reportListTab" class="primary" onclick="switchReportView('list')">报告列表</button><button id="assertionSummaryTab" class="small" onclick="switchReportView('assertions')">断言归纳</button></div></div><div id="reportListView">${tableReports()}</div><div id="assertionSummaryView" class="hidden">${assertionSummaryHtml()}</div>`}
function switchReportView(kind){let list=kind==='list';$('#reportListView')?.classList.toggle('hidden',!list);$('#assertionSummaryView')?.classList.toggle('hidden',list);if($('#reportListTab'))$('#reportListTab').className=list?'primary':'small';if($('#assertionSummaryTab'))$('#assertionSummaryTab').className=list?'small':'primary'}
function allReportAssertions(){let gift=data.gift_latest||{},groups={};(gift.assertions||[]).forEach(x=>{let original=x.name||'未命名断言',phase='',name=original,m=original.match(/^(送礼前|送礼后)(钱包|财富)｜(.+)$/);if(m){phase=m[1];name=`${m[2]}｜${m[3]}`}let item=groups[name]||(groups[name]={...x,name,report_source:'财富送礼跨接口',executed_at:gift.executed_at||'',evidence:[]});item.evidence.push({phase:phase||'本次执行',actual:x.actual,passed:!!x.passed});item.passed=item.evidence.every(e=>e.passed);item.actual=item.evidence.length===1?item.evidence[0].actual:item.evidence});return Object.values(groups)}
function assertionTable(xs,empty='暂无断言'){if(!xs.length)return `<div class="card empty"><b>${empty}</b></div>`;return `<div class="card"><table><thead><tr><th>断言与来源</th><th>期望</th><th>实际</th><th>结论</th></tr></thead><tbody>${xs.map(x=>`<tr><td><b>${esc(x.name)}</b><br><small>${esc(x.report_source||'-')} · ${esc((x.executed_at||'').replace('T',' '))}</small></td><td>${esc(typeof x.expected==='object'?JSON.stringify(x.expected):x.expected)}</td><td>${esc(typeof x.actual==='object'?JSON.stringify(x.actual):x.actual)}</td><td><span class="tag ${x.passed?'PASSED':'FAILED'}">${x.passed?'通过':'失败'}</span></td></tr>`).join('')}</tbody></table></div>`}
function enterpriseReportCenter(){let all=allReportAssertions(),gift=data.gift_latest||{},wealth=data.wealth_latest||{},reports=data.generated_reports||[];let dataRules=all.filter(x=>/redis|threshold|门槛|excel|起始经验|下一等级/i.test(x.name||'')),e2e=all.filter(x=>/^(跨步骤|账单)/.test(x.name||'')),functional=all.filter(x=>!dataRules.includes(x)&&!e2e.includes(x)),failed=all.filter(x=>!x.passed),passed=all.length-failed.length,coverage={};all.forEach(x=>{let k=x.report_source||'其他';coverage[k]=(coverage[k]||0)+1});let perf=reports.filter(x=>x.kind==='JMeter');return `<div class="card"><span class="tag PASSED">ENTERPRISE REPORT CENTER</span><h2>报告中心</h2><p>统一归档接口、端到端链路、性能、数据一致性、风险与需求覆盖证据。</p><div class="formrow report-menu">${[['overview','测试总览'],['functional','功能与接口'],['e2e','端到端链路'],['performance','性能测试'],['data','数据一致性'],['risk','缺陷与风险'],['coverage','覆盖与追踪']].map((x,i)=>`<button id="report-${x[0]}" class="${i?'small':'primary'}" onclick="switchEnterpriseReport('${x[0]}')">${x[1]}</button>`).join('')}</div></div><section id="enterprise-overview" class="enterprise-report-view"><div class="metrics"><div class="metric"><span>断言总数</span><b>${all.length}</b></div><div class="metric"><span>通过</span><b>${passed}</b></div><div class="metric"><span>失败</span><b>${failed.length}</b></div><div class="metric"><span>报告数量</span><b>${reports.length}</b></div></div>${tableReports()}</section><section id="enterprise-functional" class="enterprise-report-view hidden"><div class="card"><h2>功能与接口</h2><p>财富基础13条与送礼链路中的单接口契约断言，按真实执行证据展示。</p></div>${assertionTable(functional)}</section><section id="enterprise-e2e" class="enterprise-report-view hidden"><div class="card"><h2>端到端业务链路</h2><p>登录、钱包、送礼、账单和财富变化之间的跨步骤断言。</p></div>${assertionTable(e2e)}</section><section id="enterprise-performance" class="enterprise-report-view hidden"><div class="card"><h2>性能测试</h2><p>只读接口进入JMeter；送礼写接口严格禁止循环。</p></div>${perf.length?`<div class="card">${perf.map(x=>`<p><b>${esc(x.name)}</b>　<span class="tag ${x.status==='PASSED'?'PASSED':'FAILED'}">${esc(x.status)}</span><br>${esc(x.summary)} ${x.html_url?`<button class="small" onclick="openReport('${esc(x.html_url)}')">查看JMeter HTML</button>`:''}</p>`).join('')}</div>`:'<div class="card empty"><b>暂无JMeter性能报告</b></div>'}</section><section id="enterprise-data" class="enterprise-report-view hidden"><div class="card"><h2>数据一致性</h2><p>接口、Excel升级表、Redis离线Hash、钱包及账单数据核对。</p></div>${assertionTable(dataRules)}</section><section id="enterprise-risk" class="enterprise-report-view hidden"><div class="card"><h2>缺陷与风险</h2><p>只展示失败断言和需要人工确认的真实差异。</p></div>${assertionTable(failed,'当前没有失败断言')}</section><section id="enterprise-coverage" class="enterprise-report-view hidden"><div class="card"><h2>覆盖与追踪</h2><p>需求 → 接口 → 链路 → 断言 → 报告。</p><table><thead><tr><th>证据来源</th><th>断言数</th><th>通过</th><th>失败</th></tr></thead><tbody>${Object.entries(coverage).map(([k,n])=>{let xs=all.filter(x=>x.report_source===k);return `<tr><td>${esc(k)}</td><td>${n}</td><td>${xs.filter(x=>x.passed).length}</td><td>${xs.filter(x=>!x.passed).length}</td></tr>`}).join('')}</tbody></table></div></section>`}
function switchEnterpriseReport(kind){$$('.enterprise-report-view').forEach(x=>x.classList.add('hidden'));$(`#enterprise-${kind}`)?.classList.remove('hidden');$$('.report-nav-item').forEach(x=>x.classList.remove('active'));$(`#report-${kind}`)?.classList.add('active')}
function decorateEnterpriseReports(){let root=$('#reports'),heading=root?.firstElementChild,menu=heading?.querySelector('.report-menu');if(!root||!heading||!menu)return;heading.classList.add('report-heading');let layout=document.createElement('div'),content=document.createElement('div');layout.className='report-layout';menu.className='report-sidebar';[...menu.querySelectorAll('button')].forEach((button,index)=>{button.className=`report-nav-item${index===0?' active':''}`});content.className='report-content';root.insertBefore(layout,heading.nextSibling);layout.append(menu,content);[...root.querySelectorAll(':scope > .enterprise-report-view')].forEach(section=>content.append(section));let evidence=(data.gift_latest?.assertions||[]),metrics=$('#enterprise-overview .metrics'),unique=allReportAssertions().length;if(metrics)metrics.innerHTML=`<div class="metric"><span>执行证据</span><b>${evidence.length}</b></div><div class="metric"><span>唯一断言规则</span><b>${unique}</b></div><div class="metric"><span>通过证据</span><b>${evidence.filter(x=>x.passed).length}</b></div><div class="metric"><span>失败证据</span><b>${evidence.filter(x=>!x.passed).length}</b></div>`}
const renderWithReportSidebar=render;render=function(){renderWithReportSidebar();decorateEnterpriseReports()};
function fullEvidenceAuditHtml(){let xs=data.gift_latest?.assertions||[];if(!xs.length)return `<section id="enterprise-evidence" class="enterprise-report-view hidden"><div class="card empty"><b>暂无执行证据</b><p>完成真实接口链路后，逐条断言证据会自动归档到这里。</p></div></section>`;let groups={};xs.forEach((x,index)=>{let name=x.name||'未命名断言',group=name.includes('｜')?name.split('｜')[0]:'跨步骤',item={...x,index:index+1};(groups[group]||(groups[group]=[])).push(item)});return `<section id="enterprise-evidence" class="enterprise-report-view hidden"><div class="card"><span class="tag PASSED">AUDIT EVIDENCE</span><h2>完整执行证据</h2><p>保留本次真实链路产生的全部 ${xs.length} 条证据，不合并送礼前后重复执行项。敏感凭证不会展示。</p></div>${Object.entries(groups).map(([group,items])=>`<div class="card evidence-group"><h3>${esc(group)} <span class="tag">${items.length}条</span></h3><table><thead><tr><th>#</th><th>断言</th><th>期望</th><th>实际</th><th>结论</th></tr></thead><tbody>${items.map(x=>`<tr><td>${x.index}</td><td><b>${esc(x.name)}</b></td><td>${esc(typeof x.expected==='object'?JSON.stringify(x.expected):x.expected)}</td><td>${esc(typeof x.actual==='object'?JSON.stringify(x.actual):x.actual)}</td><td><span class="tag ${x.passed?'PASSED':'FAILED'}">${x.passed?'通过':'失败'}</span></td></tr>`).join('')}</tbody></table></div>`).join('')}</section>`}
function enhanceEvidenceAudit(){let sidebar=$('#reports .report-sidebar'),content=$('#reports .report-content');if(!sidebar||!content||$('#report-evidence'))return;let button=document.createElement('button');button.id='report-evidence';button.className='report-nav-item';button.textContent='完整执行证据';button.onclick=()=>switchEnterpriseReport('evidence');sidebar.insertBefore(button,$('#report-coverage'));content.insertAdjacentHTML('beforeend',fullEvidenceAuditHtml())}
const renderWithEvidenceAudit=render;render=function(){renderWithEvidenceAudit();enhanceEvidenceAudit()};
function polishBusinessDifferenceStatus(){$$('#reports .tag,#giftChainResult .tag').forEach(x=>{if(x.textContent.trim()==='BUSINESS_DIFFERENCE'){x.textContent='存在业务差异';x.className='tag P1'}})}
const renderWithStatusCopy=render;render=function(){renderWithStatusCopy();polishBusinessDifferenceStatus();syncGiftControls()};
function hubStatus(done){return done?'<span class="tag PASSED">已就绪</span>':'<span class="tag P1">待补齐</span>'}
function professionalLabels(){let labels={overview:'质量总览',sources:'需求资产',dataquality:'数据验证',automation:'执行中心',reports:'报告中心'};$$('.tabs button,.side-tab').forEach(b=>{if(labels[b.dataset.tab])b.textContent=labels[b.dataset.tab]});let runAllBtn=$('.toolbar .primary');if(runAllBtn)runAllBtn.textContent='启动生成流程'}
function qualityHubMaturity(){let checks=[(data.sources||[]).length,(data.requirement_items||[]).length,(data.points||[]).length,(data.cases||[]).length,(data.endpoints||[]).length,(data.workflows||[]).length,(data.db_tables||[]).length,(data.redis_sources||[]).some(x=>x.status==='connected'),(data.generated_reports||[]).length];return Math.round(checks.filter(Boolean).length/checks.length*100)}
function platformGaps(){let backend=data?.diagnosis?.items;if(Array.isArray(backend)&&backend.length)return backend.map(x=>({level:x.severity||x.level,title:x.title,desc:x.description||x.desc,tab:x.action_target||x.tab,action:x.action_label||'处理',details:x.details||[],module:x.module}));let gaps=[],endpoints=data.endpoints||[],cases=data.cases||[],rules=(data.consistency||{}).rules||[],reports=data.generated_reports||[],redisConnected=(data.redis_sources||[]).some(x=>x.status==='connected'),dbTables=data.db_tables||[],accounts=data.test_accounts||[],maps=data.mappings||[],redisMaps=data.redis_mappings||[];let add=(level,title,desc,tab)=>gaps.push({level,title,desc,tab,action:'处理',details:[]});if(!(data.sources||[]).length)add('P0','补齐需求或接口资料','请接入需求文档、链接、图片、描述或 OpenAPI，平台才能生成测试资产。','sources');if(!endpoints.length)add('P0','补齐接口定义','当前没有可用于接口自动化和数据验证的接口定义。','sources');if(endpoints.length&&!cases.some(x=>x.method&&x.path))add('P0','补齐可执行用例','已有接口但缺少可执行用例，无法触发接口测试和数据验证。','sources');if(!accounts.length)add('P1','补齐测试账号池','真实链路、登录态和需要鉴权的接口需要测试账号与凭证。','automation');if(!dbTables.length)add('P1','补齐 MySQL Schema','无法建立接口到数据表的候选映射，也无法形成业务数据核对。','dataquality');if(!redisConnected)add('P1','补齐 Redis 只读连接','无法做缓存 Key 映射、快照和前后状态比对。','dataquality');let uncovered=endpoints.filter(ep=>!rules.some(r=>r.endpoint_id===ep.id));if(uncovered.length)add('P1','补齐验证规则',`${uncovered.length} 个接口还没有验证规则，需要生成或补齐映射。`,'dataquality');let missingDb=endpoints.filter(ep=>!maps.some(m=>m.endpoint_id===ep.id));if(missingDb.length)add('P1','补齐 MySQL 映射',`${missingDb.length} 个接口还没有候选数据表，需要导入 Schema 或补充映射。`,'dataquality');let missingRedis=endpoints.filter(ep=>!redisMaps.some(m=>m.endpoint_id===ep.id));if(missingRedis.length)add('P1','补齐 Redis 映射',`${missingRedis.length} 个接口还没有缓存 Key 映射；没有缓存依赖的接口可标记为不适用。`,'dataquality');let pendingMysql=rules.filter(x=>x.mysql_table&&!x.mysql_condition);if(pendingMysql.length)add('P1','补齐 MySQL 查询条件',`${pendingMysql.length} 条规则已有候选表，但还缺少业务行查询条件。`,'dataquality');if(!reports.length)add('P1','补齐报告证据','尚未形成可归档的接口、性能、数据验证或完整证据报告。','reports');if(!gaps.length)add('PASSED','当前闭环材料已齐','当前项目资产、执行、数据验证和报告证据均已具备基础闭环条件。','reports');return gaps}
function gapDiagnosisPanel(limit=8){let gaps=platformGaps().slice(0,limit),summary=data?.diagnosis?.summary||{},stamp=data?.diagnosis?.generated_at||'';return `<div class="card diagnosis-card"><div class="diagnosis-head"><div><h2>平台待补齐清单</h2><p>平台根据当前资料、接口、账号、数据源、执行记录和报告证据自动判断下一步。</p></div><div class="diagnosis-score"><b>${summary.p0||0}</b><span>P0阻断</span><b>${summary.p1||0}</b><span>P1待补</span></div></div><p class="policy-note">外部 MySQL 与 Redis 均按只读策略使用；诊断、规则、快照和报告只写入平台本地库。</p><div class="gap-list">${gaps.map((g,i)=>`<div class="gap-item ${g.level}"><span class="tag ${g.level}">${esc(g.level)}</span><div><b>${esc(g.title)}</b><p>${esc(g.desc)}</p>${g.details?.length?`<small>${g.details.length} 项明细</small>`:''}</div><div class="gap-actions">${g.details?.length?`<button class="small" onclick="showDiagnosisDetails(${i})">明细</button>`:''}<button class="small" onclick="switchTab('${g.tab||'overview'}')">${esc(g.action||'处理')}</button></div></div>`).join('')}</div>${stamp?`<small class="diagnosis-time">最近诊断：${esc(stamp.replace('T',' '))}</small>`:''}</div>`}
function showDiagnosisDetails(index){let item=platformGaps()[index]||{},details=item.details||[];let html=details.length?`<table><thead><tr><th>对象</th><th>名称</th><th>需要补齐</th></tr></thead><tbody>${details.map(x=>`<tr><td><code>${esc(x.endpoint||x.title||x.status||'-')}</code></td><td>${esc(x.name||x.case_title||x.http_status||'')}</td><td>${esc(Array.isArray(x.missing)?x.missing.join('、'):x.error||x.detail||JSON.stringify(x))}</td></tr>`).join('')}</tbody></table>`:'<div class="empty"><b>暂无明细</b></div>';$('#modalBody').innerHTML=`<h2>${esc(item.title||'诊断明细')}</h2><p style="color:var(--muted);font-size:12px">${esc(item.desc||'')}</p>${html}<button class="primary" onclick="closeModal();switchTab('${item.tab||'overview'}')">${esc(item.action||'处理')}</button>`;$('#modal').classList.remove('hidden')}
function aiControlPlanePanel(){let cp=data.control_plane||{},stages=cp.stages||[],next=cp.next_action||{};return `<div class="card control-plane"><div class="diagnosis-head"><div><h2>自动化控制链路</h2><p>从资料输入到证据归档，平台负责自动判断、生成、编排和归纳；实际执行交给标准测试工具和只读数据源。</p></div><span class="tag ${cp.status==='BLOCKED'?'P0':cp.status==='ATTENTION'?'P1':'PASSED'}">${esc(cp.status||'PENDING')}</span></div><div class="control-track">${stages.map((s,i)=>`<button class="control-stage ${s.status==='READY'?'ready':'pending'}" onclick="switchTab('${s.target}')"><span>${i+1}</span><b>${esc(s.name)}</b><small>${esc(s.description)}</small></button>`).join('')}</div><div class="next-action"><b>${esc(next.title||'等待诊断')}</b><p>${esc(next.description||'平台会在资料、接口、数据源和报告变化后重新计算下一步。')}</p><button class="small" onclick="switchTab('${next.target||'overview'}')">处理</button></div></div>`}
function qualityProfilePanel(){let p=data.quality_profile||{},sections=p.sections||[],score=p.score??0,missing=sections.filter(x=>x.status!=='READY');return `<div class="card"><div class="diagnosis-head"><div><h2>项目配置中心</h2><p>统一维护环境、接口资料、抓包、账号、SLA、数据源和报告准入。平台会根据这里自动判断缺口。</p></div><div class="diagnosis-score"><b>${score}</b><span>配置完整度</span></div></div><div class="endpoint-matrix">${sections.map(x=>`<div class="endpoint-card"><span class="tag ${x.status==='READY'?'PASSED':x.status==='MISSING'?'P0':'P1'}">${esc(x.status)}</span><h3>${esc(x.name)}</h3><p style="font-size:12px;color:var(--muted)">${esc(x.summary||'')}</p></div>`).join('')}</div>${missing.length?`<div class="summary-panel"><b>平台判断仍需补齐</b><p>${missing.map(x=>esc(x.name)).join('、')}</p></div>`:''}<button class="primary" onclick="showQualityProfileModal()">维护配置</button></div>`}
function showQualityProfileModal(){let p=data.quality_profile||{},project=p.project||data.project||{},sla=p.sla||{},settings=p.settings||{};$('#modalBody').innerHTML=`<h2>项目配置中心</h2><p style="color:var(--muted);font-size:12px">这些配置只写入平台本地库，用于生成、执行和准入判断，不会回写公司业务系统。</p><label>项目名称</label><input id="profileName" value="${esc(project.name||'')}"><label>测试环境 Base URL</label><input id="profileBaseUrl" value="${esc(project.base_url||'')}"><div class="formrow"><input id="profileOwner" value="${esc(settings.owner||'')}" placeholder="负责人/测试 owner"><input id="profileEnvName" value="${esc(settings.env_name||'Soulfree测试服')}" placeholder="环境名称"></div><label>SLA 来源</label><select id="profileSlaSource"><option value="">待确认</option><option value="team_default" ${sla.source==='team_default'?'selected':''}>团队默认阈值</option><option value="monitoring" ${sla.source==='monitoring'?'selected':''}>监控/APM历史数据</option><option value="business_requirement" ${sla.source==='business_requirement'?'selected':''}>业务需求约定</option></select><div class="formrow"><input id="profileMaxErrorRate" type="number" min="0" max="100" step="0.1" value="${esc(sla.max_error_rate||'0')}" placeholder="最大错误率%"><input id="profileMaxP95" type="number" min="1" value="${esc(sla.max_p95_ms||'3000')}" placeholder="P95阈值ms"><input id="profileMaxP99" type="number" min="1" value="${esc(sla.max_p99_ms||'5000')}" placeholder="P99阈值ms"><input id="profileMinThroughput" type="number" min="0" step="0.1" value="${esc(sla.min_throughput_rps||'0')}" placeholder="最小吞吐req/s"></div><label>监控 / APM 看板地址</label><input id="profileMonitoringUrl" value="${esc(sla.monitoring_url||'')}" placeholder="例如 Grafana、Prometheus、SkyWalking、CAT 链接"><button class="primary" onclick="saveQualityProfile()">保存配置</button>`;$('#modal').classList.remove('hidden')}
async function saveQualityProfile(){let payload={name:$('#profileName').value.trim(),base_url:$('#profileBaseUrl').value.trim(),owner:$('#profileOwner').value.trim(),env_name:$('#profileEnvName').value.trim(),sla_source:$('#profileSlaSource').value,max_error_rate:$('#profileMaxErrorRate').value,max_p95_ms:$('#profileMaxP95').value,max_p99_ms:$('#profileMaxP99').value,min_throughput_rps:$('#profileMinThroughput').value,monitoring_url:$('#profileMonitoringUrl').value.trim()};try{data.quality_profile=await api(`/api/projects/${current}/quality-profile`,{method:'POST',body:JSON.stringify(payload)});closeModal();toast('项目配置已保存，缺口诊断会按新配置刷新','success');await openProject(current);switchTab('overview')}catch(e){toast(e.message,'error')}}
function tableQualityHub(){let req=(data.requirement_items||[]).length,points=(data.points||[]).length,cases=(data.cases||[]).length,endpoints=(data.endpoints||[]).length,reports=(data.generated_reports||[]).length,db=(data.db_tables||[]).length,redis=(data.redis_sources||[]).some(x=>x.status==='connected'),rules=((data.consistency||{}).rules||[]).length,maturity=qualityHubMaturity();let steps=[['需求资产',req||points||cases,`${req}条需求 · ${points}个测试点 · ${cases}条用例`,'sources'],['执行中心',endpoints||reports,`${endpoints}个接口 · ${reports}份执行报告`,'automation'],['数据验证',db||redis||rules,`${db}张表 · Redis ${redis?'已连接':'未连接'} · ${rules}条规则`,'dataquality'],['报告中心',reports,`${reports}份报告与原始证据`,'reports']];return `<div class="card quality-hero"><span class="tag">QUALITY OPERATIONS</span><h2>质量总览</h2><p>围绕需求资产、执行任务、数据验证和报告证据组织测试工作。平台会自动识别缺口，并把处理入口收敛到对应模块。</p><div class="quality-flow">${steps.map(x=>`<button class="quality-step ${x[1]?'':'pending'}" onclick="switchTab('${x[3]}')">${hubStatus(x[1])}<b>${x[0]}</b><small>${esc(x[2])}</small></button>`).join('')}</div></div>${qualityProfilePanel()}${aiControlPlanePanel()}${gapDiagnosisPanel(5)}<div class="closure-grid"><div class="card"><h2>项目能力概览</h2>${[['资产沉淀','需求、测试点、测试用例、接口覆盖矩阵统一归档'],['执行编排','接口自动化、性能测试和真实业务链路由执行中心统一触发'],['数据验证','MySQL、Redis、后台配置与接口结果形成只读核对证据'],['报告证据','原始报告、断言结果、风险归纳和完整证据按类别归档']].map(x=>`<div class="closure-row"><b>${x[0]}</b><p>${x[1]}</p><span class="tag PASSED">模块</span></div>`).join('')}</div><div class="card"><div class="maturity-score"><div><b>${maturity}%</b><span>项目成熟度</span></div></div><div class="tool-badges"><span>需求资产</span><span>执行任务</span><span>数据验证</span><span>报告证据</span></div></div></div>`}
function enterpriseDirectory(){return `<div class="card"><h2>模块摘要</h2><div class="directory-grid">${[['需求资产','需求拆解、测试点、测试用例、接口覆盖矩阵','进入','sources'],['执行中心','流水线生成、接口执行、JMeter性能测试、真实链路触发','进入','automation'],['数据验证','接口返回、MySQL、Redis、后台配置的一致性归纳','进入','dataquality'],['报告中心','接口报告、性能报告、数据报告、缺陷风险、完整证据','进入','reports']].map(x=>`<div class="directory-card"><h3>${x[0]}</h3><p>${x[1]}</p><button class="small" onclick="switchTab('${x[3]}')">${x[2]}</button></div>`).join('')}</div></div>`}
function endpointDataMatrix(){let pack=data.consistency||{},rules=pack.rules||[],runs=pack.runs||[],dbMaps=data.mappings||[],redisMaps=data.redis_mappings||[],cases=data.cases||[];let latestByRule={};runs.forEach(x=>{if(!latestByRule[x.rule_id])latestByRule[x.rule_id]=x});let endpointRuns={};rules.forEach(r=>{let run=latestByRule[r.id];if(run&&!endpointRuns[r.endpoint_id])endpointRuns[r.endpoint_id]=run});return `<div class="card"><h2>4 个接口数据验证覆盖</h2><p class="policy-note">公司 MySQL 与 Redis 只读，不允许修改真实业务数据；平台本地库允许写入规则、映射、快照、报告和归纳结论，用于沉淀测试资产。</p><div class="endpoint-matrix">${(data.endpoints||[]).map(ep=>{let epRules=rules.filter(x=>x.endpoint_id===ep.id),mysql=dbMaps.filter(x=>x.endpoint_id===ep.id),redis=redisMaps.filter(x=>x.endpoint_id===ep.id),epCases=cases.filter(x=>(x.method||'').toUpperCase()===(ep.method||'').toUpperCase()&&(x.path||'').split('?')[0]===ep.path),run=endpointRuns[ep.id],ready=epRules.some(x=>x.case_id);let gaps=[];if(!epCases.length)gaps.push('缺少可执行用例');if(!mysql.length)gaps.push('缺少 MySQL 映射');else if(epRules.some(x=>x.mysql_table&&!x.mysql_condition))gaps.push('MySQL 查询条件待配置');if(!redis.length)gaps.push('缺少 Redis 映射');if(!epRules.length)gaps.push('缺少验证规则');return `<div class="endpoint-card"><span class="tag ${ready?'PASSED':'P1'}">${ready?'可验证':'待补齐'}</span><h3>${esc(ep.summary||ep.path)}</h3><code>${esc(ep.method)} ${esc(ep.path)}</code><div class="checks"><div><span>MySQL</span><b>${mysql.length?mysql[0].table_name:'待映射'}</b></div><div><span>Redis</span><b>${redis.length?redis.length+' 条映射':'待映射'}</b></div><div><span>用例</span><b>${epCases.length?epCases.length+' 条':'待生成'}</b></div><div><span>最近验证</span><b>${run?run.status:'未执行'}</b></div></div><p style="margin-top:12px;color:var(--muted);font-size:12px">${gaps.length?'缺口：'+gaps.join('、'):'当前接口已进入数据验证闭环，可继续执行并归档证据。'}</p></div>`}).join('')}</div></div>`}
function dataQualityClosure(){let pack=data.consistency||{},rules=pack.rules||[],runs=pack.runs||[],summary=data.wealth_latest?.data_consistency||{},e=data.evidence_center||{},t=e.thresholds||{},r=e.redis_snapshot||{},maps=data.redis_mappings||[];return `<div class="card quality-hero"><span class="tag">DATA VALIDATION</span><h2>数据验证</h2><p>验证接口返回、数据库、Redis 缓存、后台配置和报告证据之间是否一致。外部数据源默认只读，平台负责规则编排和证据归档。</p><div class="quality-flow">${[['接口返回',data.runs?.length,`${(data.runs||[]).length}条执行记录`],['MySQL基线',data.db_tables?.length,`${(data.db_tables||[]).length}张表 · ${(data.mappings||[]).length}条映射`],['Redis缓存',data.redis_sources?.length,`${(data.redis_sources||[]).length}个数据源 · ${maps.length}条Key映射`],['验证记录',rules.length||runs.length,`${rules.length}条规则 · ${runs.length}次执行`]].map(x=>`<div class="quality-step ${x[1]?'':'pending'}">${hubStatus(x[1])}<b>${x[0]}</b><small>${esc(x[2])}</small></div>`).join('')}</div></div><div class="metrics"><div class="metric"><span>一致性状态</span><b style="font-size:20px">${esc(summary.status||'PENDING')}</b></div><div class="metric"><span>升级真值表</span><b>${t.loaded?t.rows:'-'}</b></div><div class="metric"><span>Redis快照</span><b>${r.loaded?r.fields:'-'}</b></div><div class="metric"><span>验证规则</span><b>${rules.length}</b></div></div>${endpointDataMatrix()}<div class="closure-grid"><div>${tableConsistency()}</div><div><div class="card"><h2>数据源策略</h2><div class="closure-row"><b>MySQL</b><p>只读访问公司库；查询真实数据用于平台规则、映射、快照和报告归纳。</p><span class="tag PASSED">禁止写业务库</span></div><div class="closure-row"><b>Redis</b><p>只允许读取和扫描类命令；禁止 SET、DEL、FLUSH、CONFIG、SHUTDOWN。</p><span class="tag PASSED">禁止写缓存</span></div><div class="closure-row"><b>平台库</b><p>允许写入平台本地数据，用于保存验证规则、映射、快照、执行报告和缺陷归纳。</p><span class="tag PASSED">允许写平台</span></div></div>${tableEvidenceCenter()}</div></div>`}
function toolchainPanel(){let t=data.toolchain||{},tools=t.tools||[],arts=t.artifacts||[],blockers=t.blockers||[],readyAssets=arts.length&&arts.every(x=>x.status==='READY'),runtimeSample=JSON.stringify({uid:1454428,uids:[1454428,1454694],receiver_uid:1454779,room_uid:123456,pageNo:1,pageSize:50,bill_type:1},null,2);return `<div class="card"><div class="diagnosis-head"><div><h2>企业测试工具链</h2><p>平台先完成预检和标准资产生成，再交给 Newman、JMeter、pytest、Allure 等外部工具执行。</p></div><span class="tag ${t.status==='READY'?'PASSED':'P1'}">${esc(t.status||'PENDING')}</span></div>${blockers.length?`<div class="gap-list">${blockers.map(x=>`<div class="gap-item P1"><span class="tag P1">待补</span><div><b>${esc(x)}</b><p>补齐后即可进入外部工具执行阶段。</p></div></div>`).join('')}</div>`:''}<div class="endpoint-matrix">${tools.map(x=>`<div class="endpoint-card"><span class="tag ${x.status==='READY'?'PASSED':'P1'}">${esc(x.status)}</span><h3>${esc(x.name)}</h3><code>${esc(x.command||'未发现')}</code><p style="font-size:12px;color:var(--muted)">${esc(x.version||x.install_hint||'')}</p></div>`).join('')}</div><div class="summary-panel"><b>执行策略</b><p>登录接口只做前置提取；业务接口使用平台同步后的 ticket、uid、设备上下文和运行参数。</p><select id="toolLoginStrategy"><option value="auto">自动：有登录参数就刷新，否则复用</option><option value="force">强制重新登录</option><option value="reuse">仅复用本机凭证</option></select><div class="formrow"><input id="toolLoginT" placeholder="登录请求头 t（可空，自动生成时间戳）"><input id="toolLoginSn" placeholder="登录请求头 sn（可空；如接口要求签名需补齐）"></div><input id="toolLoginPassword" type="password" placeholder="登录请求体加密密码；重新登录时填写，留空则复用本机凭证"><label>业务运行参数</label><textarea id="toolRuntimeParams" spellcheck="false">${esc(runtimeSample)}</textarea><div class="formrow"><label><input id="toolRunNewman" type="checkbox" checked> Newman</label><label><input id="toolRunJmeter" type="checkbox" checked> JMeter</label><label><input id="toolRunPytest" type="checkbox" checked> pytest</label></div><label>JMeter 压测模型</label><div class="formrow"><input id="toolJmeterThreads" type="number" min="1" max="200" value="2" placeholder="线程数"><input id="toolJmeterLoops" type="number" min="1" max="1000" value="5" placeholder="每线程循环"><input id="toolJmeterRampup" type="number" min="0" max="600" value="2" placeholder="Ramp-up秒"><input id="toolJmeterTimeout" type="number" min="30" max="3600" value="180" placeholder="超时秒"></div><label>性能准入策略</label><div class="formrow"><select id="toolPerfProfile"><option value="smoke">冒烟验证</option><option value="baseline">基准压测</option><option value="load">阶梯负载</option><option value="stability">稳定性</option></select><input id="toolMaxErrorRate" type="number" min="0" max="100" step="0.1" value="0" placeholder="最大错误率%"><input id="toolMaxP95" type="number" min="1" value="3000" placeholder="P95阈值ms"><input id="toolMaxP99" type="number" min="1" value="5000" placeholder="P99阈值ms"><input id="toolMinThroughput" type="number" min="0" step="0.1" value="0" placeholder="最小吞吐req/s"></div><button class="primary" onclick="generateToolAssets()">生成资产</button> <button id="toolchainRunButton" class="small" onclick="runEnterpriseToolchain()" ${readyAssets?'':'disabled'}>执行工具链</button><div id="toolchainRunStatus" style="margin-top:12px"></div></div><div class="evidence-list">${arts.map(x=>`<div class="evidence-item"><b>${esc(x.name)}</b><small>${esc(x.status)}</small>${x.url?`<button class="small" onclick="openReport('${esc(x.url)}')">打开</button>`:''}</div>`).join('')}</div></div>`}
function executionCenter(){let suites=data.automation_suites||[],plans=data.performance_plans||[],reports=data.generated_reports||[],jmeter=reports.filter(x=>x.kind==='JMeter'),hasAccounts=(data.test_accounts||[]).length>0;return `<div class="card quality-hero"><span class="tag">EXECUTION</span><h2>执行中心</h2><p>统一调度接口自动化、性能测试和真实业务链路。平台负责生成执行资产、调用工具、回收原始报告。</p><div class="quality-flow">${[['生成流水线',data.sources?.length,'需求拆解、测试点、用例、链路、性能计划'],['接口自动化',suites.length||data.endpoints?.length,`${suites.length}个套件 · ${(data.endpoints||[]).length}个接口`],['JMeter性能',plans.length||jmeter.length,`${plans.length}个计划 · ${jmeter.length}份报告`],['真实链路',hasAccounts,hasAccounts?'测试账号已配置':'需要测试账号与凭证']].map(x=>`<div class="quality-step ${x[1]?'':'pending'}">${hubStatus(x[1])}<b>${x[0]}</b><small>${esc(x[2])}</small></div>`).join('')}</div></div>${toolchainPanel()}<div class="card"><h2>执行任务</h2><div class="closure-row"><b>资产生成</b><p>根据当前需求、接口资料和抓包样例生成测试点、用例、链路、接口套件、性能计划和数据规则。</p><button class="primary" onclick="runPipeline()">启动</button></div><div class="closure-row"><b>接口与性能</b><p>调用真实接口执行契约、异常场景、快速冒烟和 JMeter 性能测试。</p><button class="primary" onclick="showLeanWealthRunner()">执行</button></div><div class="closure-row"><b>数据验证</b><p>生成并运行接口、MySQL、Redis 的只读一致性验证规则。</p><button class="small" onclick="switchTab('dataquality')">进入</button></div><div class="closure-row"><b>报告归档</b><p>查看原始 JSON、JMeter HTML、断言证据和归纳后的缺陷风险。</p><button class="small" onclick="switchTab('reports')">查看</button></div></div>`}
function showLeanWealthRunner(){let html=tableWealthApiWorkbench();$('#modalBody').innerHTML=`<h2>接口与JMeter执行</h2><p style="color:var(--muted);font-size:12px">该动作调用现有真实接口链路和 JMeter 适配能力，执行后报告进入报告中心。</p>${html}`;$('#modal').classList.remove('hidden')}
function compactAssetsWorkspace(){let reqs=data.requirement_items||[],points=data.points||[],cases=data.cases||[],endpoints=data.endpoints||[],sources=data.sources||[];let priority={};cases.forEach(x=>priority[x.priority||'未标注']=(priority[x.priority||'未标注']||0)+1);let selected=(data.trace_links||[]).filter(x=>+x.selected===1).length;return `<div class="card quality-hero"><span class="tag">ASSETS</span><h2>需求资产</h2><p>统一沉淀需求、测试点、测试用例和接口覆盖。默认展示覆盖摘要，明细按需查看或导出。</p><div class="quality-flow">${[['资料',sources.length,sources.length+'份输入资料'],['需求',reqs.length,reqs.length+'条结构化需求'],['测试资产',points.length||cases.length,points.length+'个测试点 · '+cases.length+'条用例'],['接口覆盖',endpoints.length,endpoints.length+'个接口资产']].map(x=>`<div class="quality-step ${x[1]?'':'pending'}">${hubStatus(x[1])}<b>${x[0]}</b><small>${esc(x[2])}</small></div>`).join('')}</div></div><div class="closure-grid"><div class="card"><h2>资产操作</h2><div class="summary-panel"><b>新增资料</b><p>支持需求文档、图文链接、文字描述、OpenAPI 和 HAR 抓包。保存后进入生成流程。</p><button class="primary" onclick="showSourceModal()">添加</button></div><div class="summary-panel"><b>生成资产</b><p>根据资料生成需求、测试点、用例、接口候选、链路和性能计划。</p><button class="small" onclick="runPipeline()">生成</button></div><div class="summary-panel"><b>接口文档</b><p>把当前接口资产导出为脱敏 OpenAPI 基线，抓包导入的接口会同步进入文档。</p><button class="small" onclick="downloadInterfaceDocument()">导出</button></div><div class="summary-panel"><b>导出资产</b><p>导出测试点、用例、接口资产和报告包，用于评审或项目展示。</p><button class="small" onclick="downloadExport()">导出</button></div></div><div class="card"><h2>资产摘要</h2><div class="evidence-list"><div class="evidence-item"><b>需求覆盖</b><small>${reqs.length}条需求，${selected}条已选接口关联</small></div><div class="evidence-item"><b>用例优先级</b><small>${Object.entries(priority).map(([k,v])=>`${k}:${v}`).join(' · ')||'暂无用例'}</small></div><div class="evidence-item"><b>接口风险</b><small>高风险 ${endpoints.filter(x=>x.risk_level==='high').length} · 中风险 ${endpoints.filter(x=>x.risk_level==='medium').length} · 低风险 ${endpoints.filter(x=>x.risk_level==='low').length}</small></div></div><button class="small" style="margin-top:14px" onclick="showTraceCoverageModal()">查看覆盖明细</button></div></div>`}
function showTraceCoverageModal(){$('#modalBody').innerHTML=`<h2>需求与接口覆盖明细</h2>${traceCoverageHtml()}`;$('#modal').classList.remove('hidden')}
function showSourceModal(){let kindOptions='<option value="requirement">需求文档/描述</option><option value="openapi">OpenAPI / Swagger</option><option value="har">HAR 抓包文件</option><option value="rules">测试规则与约束</option>';$('#modalBody').innerHTML=`<h2>添加资料</h2><label>资料名称</label><input id="srcName" placeholder="例如：工资代理快速结算"><label>资料类型</label><select id="srcKind">${kindOptions}</select><label>需求/文档链接（可选）</label><input id="srcUrl" placeholder="https://docs.example.com/requirement"><label>资料内容</label><textarea id="srcContent" placeholder="粘贴需求描述、OpenAPI JSON/YAML、HAR 或测试规则"></textarea><label>或读取本地文件</label><input type="file" id="srcFile" accept=".txt,.md,.json,.yaml,.yml,.har,.docx,.pdf,.png,.jpg,.jpeg,.webp,.zip"><p class="policy-note">HTML原型请上传 ZIP 包，保留 HTML 与 images 文件夹，平台会自动做图文联合识别。</p><div id="sourceImportStatus" style="margin:10px 0 12px"></div><button id="sourceSaveButton" class="primary" onclick="addSource()">保存并分析</button>`;$('#modal').classList.remove('hidden');bindFile()}
function showInterfaceDocModal(){showSourceModal();$('#modalBody h2').textContent='导入接口文档';$('#srcKind').value='openapi';$('#srcName').placeholder='例如：Soulfree测试服接口基线';$('#srcUrl').placeholder='Swagger / OpenAPI 文档地址';$('#srcContent').placeholder='粘贴 OpenAPI JSON/YAML、Swagger JSON、Markdown接口清单，或 HAR 抓包内容';$('#srcFile').setAttribute('accept','.json,.yaml,.yml,.har,.md,.txt');$('.policy-note').textContent='支持 OpenAPI/Swagger、HAR 和普通 Markdown 接口表格；抓包导入后会沉淀为接口资产，后续生成测试点、用例、链路和JMeter脚本。'}
function legacyProjectReportCenterRemovedA(){return ''}
function showReportCategory(kind){let assertions=allReportAssertions(),failed=assertions.filter(x=>!x.passed),reports=data.generated_reports||[],perf=reports.filter(x=>x.kind==='JMeter'),dataRules=assertions.filter(x=>/redis|threshold|门槛|excel|起始经验|下一等级/i.test(x.name||''));let html={overview:tableReports(),functional:assertionTable(assertions.filter(x=>!dataRules.includes(x))),performance:perf.length?`<div class="card">${perf.map(x=>`<p><b>${esc(x.name)}</b><br>${esc(x.summary)} ${x.html_url?`<button class="small" onclick="openReport('${esc(x.html_url)}')">查看JMeter HTML</button>`:''}</p>`).join('')}</div>`:'<div class="empty"><b>暂无JMeter性能报告</b></div>',data:assertionTable(dataRules),risk:assertionTable(failed,'当前没有失败断言'),evidence:fullEvidenceAuditHtml()}[kind]||tableReports();$('#modalBody').innerHTML=`<h2>报告明细</h2>${html}`;$('#modal').classList.remove('hidden')}
function professionalizeWorkspace(){professionalLabels();if($('#overview'))$('#overview').innerHTML=enterpriseDirectory();if($('#sources'))$('#sources').innerHTML=compactAssetsWorkspace();if($('#dataquality'))$('#dataquality').innerHTML=dataQualityClosure();if($('#automation'))$('#automation').innerHTML=executionCenter();if($('#reports'))$('#reports').innerHTML=packageReportCenter();if(data?.project){switchTab($('.side-tab.active')?.dataset.tab||'overview')}}
const renderWithQualityHub=render;render=function(){renderWithQualityHub();professionalizeWorkspace()};
async function navigateWorkspace(id){if(!current){if(projects.length){await openProject(projects[0].id);switchTab(id)}else toast('请先创建测试项目','warning');return}switchTab(id)}
$$('.tabs button').forEach(x=>x.onclick=()=>switchTab(x.dataset.tab));$$('.side-tab').forEach(x=>x.onclick=()=>navigateWorkspace(x.dataset.tab));mountAssistant();checkPlatformVersion();loadProjects().then(()=>{if(projects.length===1&&!current)openProject(projects[0].id)});

function groupedTestAssets(){let cases=data.cases||[],points=data.points||[],endpoints=data.endpoints||[],groups={};cases.forEach(x=>{let key=x.executor_type==='http'||x.method?'接口自动化':x.executor_type==='workflow'?'业务链路':x.executor_type?.includes('performance')?'性能测试':x.executor_type?.includes('security')?'异常与安全':'设计用例';(groups[key]||(groups[key]=[])).push(x)});return `<div class="card"><div class="diagnosis-head"><div><h2>测试资产中心</h2><p>测试点、测试用例、接口和链路统一归档在这里；执行结果进入报告中心，不再分散到多个页面。</p></div><span class="tag PASSED">${cases.length} CASES</span></div><div class="metrics"><div class="metric"><span>测试点</span><b>${points.length}</b></div><div class="metric"><span>测试用例</span><b>${cases.length}</b></div><div class="metric"><span>接口资产</span><b>${endpoints.length}</b></div><div class="metric"><span>已执行</span><b>${cases.filter(x=>(x.run_count||0)>0).length}</b></div></div>${Object.entries(groups).map(([name,items])=>`<div class="summary-panel"><b>${esc(name)}</b><p>${items.length} 条；通过 ${items.filter(x=>x.execution_status==='PASSED').length}，失败 ${items.filter(x=>['FAILED','ERROR'].includes(x.execution_status)).length}，阻塞 ${items.filter(x=>x.execution_status==='BLOCKED').length}</p><button class="small" onclick="showAssetGroup('${esc(name)}')">查看</button></div>`).join('')}</div>`}
function showAssetGroup(name){let cases=(data.cases||[]).filter(x=>{let key=x.executor_type==='http'||x.method?'接口自动化':x.executor_type==='workflow'?'业务链路':x.executor_type?.includes('performance')?'性能测试':x.executor_type?.includes('security')?'异常与安全':'设计用例';return key===name});$('#modalBody').innerHTML=`<h2>${esc(name)}</h2><table><thead><tr><th>用例</th><th>接口/执行器</th><th>预期</th><th>状态</th></tr></thead><tbody>${cases.slice(0,300).map(x=>`<tr><td><b>${esc(x.title)}</b><br><small>${esc(x.requirement_ref||'')}</small></td><td>${x.method?`<code>${esc(x.method+' '+x.path)}</code>`:esc(x.executor_type||'manual')}</td><td>${esc(x.expected||'-')}</td><td><span class="tag ${x.execution_status||'NOT_RUN'}">${esc(x.execution_status||'NOT_RUN')}</span></td></tr>`).join('')}</tbody></table>`;$('#modal').classList.remove('hidden')}
function compactAssetsWorkspace(){let reqs=data.requirement_items||[],sources=data.sources||[],endpoints=data.endpoints||[],cases=data.cases||[],selected=(data.trace_links||[]).filter(x=>+x.selected===1).length;return `<div class="card quality-hero"><span class="tag">ASSETS</span><h2>需求与测试资产</h2><p>资料、需求、接口、测试点和测试用例统一归纳；你只需要从这里进入资产维护和覆盖查看。</p><div class="quality-flow">${[['资料',sources.length,sources.length+'份输入'],['需求',reqs.length,reqs.length+'条需求'],['接口',endpoints.length,endpoints.length+'个接口'],['用例',cases.length,cases.length+'条用例']].map(x=>`<div class="quality-step ${x[1]?'':'pending'}">${hubStatus(x[1])}<b>${x[0]}</b><small>${esc(x[2])}</small></div>`).join('')}</div></div><div class="closure-grid"><div class="card"><h2>资产操作</h2><div class="summary-panel"><b>新增资料</b><p>需求、链接、图片、OpenAPI、HAR 抓包统一从这里导入。</p><button class="primary" onclick="showSourceModal()">添加资料</button></div><div class="summary-panel"><b>生成与补齐</b><p>生成测试点、用例、接口覆盖、链路和数据验证规则。</p><button class="small" onclick="runPipeline()">启动生成</button></div><div class="summary-panel"><b>接口文档基线</b><p>把当前接口资产导出为脱敏 OpenAPI；抓包导入后也会同步沉淀。</p><button class="small" onclick="downloadInterfaceDocument()">导出</button></div></div><div><div class="card"><h2>覆盖摘要</h2><div class="evidence-list"><div class="evidence-item"><b>需求覆盖</b><small>${reqs.length}条需求，${selected}条已选追踪关系</small></div><div class="evidence-item"><b>接口覆盖</b><small>${endpoints.map(x=>x.method+' '+x.path).join(' · ')}</small></div></div><button class="small" style="margin-top:14px" onclick="showTraceCoverageModal()">覆盖明细</button></div>${groupedTestAssets()}</div></div>`}
function endpointDataMatrix(){let rules=(data.consistency||{}).rules||[],runs=(data.consistency||{}).runs||[],dbMaps=data.mappings||[],redisMaps=data.redis_mappings||[],cases=data.cases||[];return `<div class="card"><h2>接口数据验证覆盖</h2><p class="policy-note">数据库和 Redis 不作为主工作台展开；需要证据时由平台按只读策略调起。没有 Redis 依赖的接口可使用接口返回 + MySQL 候选表闭环。</p><div class="endpoint-matrix">${(data.endpoints||[]).map(ep=>{let epRules=rules.filter(x=>x.endpoint_id===ep.id),mysql=dbMaps.filter(x=>x.endpoint_id===ep.id),redis=redisMaps.filter(x=>x.endpoint_id===ep.id),epCases=cases.filter(x=>(x.method||'').toUpperCase()===(ep.method||'').toUpperCase()&&(x.path||'').split('?')[0]===ep.path),ready=epCases.length&&(mysql.length||redis.length||ep.path==='/userserv/id/login');let gaps=[];if(!epCases.length)gaps.push('缺少可执行用例');if(!mysql.length&&ep.path!=='/userserv/id/login')gaps.push('MySQL候选待确认');if(!redis.length&&ep.path==='/level/exeperience/v2/get')gaps.push('Redis核心Key待验证');return `<div class="endpoint-card"><span class="tag ${ready?'PASSED':'P1'}">${ready?'已归档':'待补齐'}</span><h3>${esc(ep.summary||ep.path)}</h3><code>${esc(ep.method+' '+ep.path)}</code><div class="checks"><div><span>用例</span><b>${epCases.length||'待补'}</b></div><div><span>MySQL</span><b>${mysql[0]?.table_name||'按需'}</b></div><div><span>Redis</span><b>${redis.length?redis.length+'条':'按需'}</b></div><div><span>规则</span><b>${epRules.length||'待生成'}</b></div></div><p style="margin-top:12px;color:var(--muted);font-size:12px">${gaps.length?'缺口：'+gaps.join('、'):'已纳入统一测试资产和按需数据验证。'}</p></div>`}).join('')}</div></div>`}
function tableConsistency(){let pack=data.consistency||{},rules=pack.rules||[],runs=pack.runs||[],summary=pack.summary||{},latest=runs[0];return `<div class="card"><div class="diagnosis-head"><div><span class="tag ${summary.status==='PASSED'?'PASSED':'P1'}">DATA GATE ${esc(summary.status||'PENDING')}</span><h2>数据验证编排</h2><p>核心验证一键执行；MySQL/Redis 明细不常驻展示，需要时按只读策略调起。</p></div><button class="primary" onclick="generateAndRunConsistency()">生成并运行核心验证</button></div><div class="metrics"><div class="metric"><span>核心状态</span><b style="font-size:20px">${esc(summary.core_status||summary.status||'PENDING')}</b></div><div class="metric"><span>验证规则</span><b>${rules.length}</b></div><div class="metric"><span>执行记录</span><b>${runs.length}</b></div><div class="metric"><span>只读策略</span><b style="font-size:18px">启用</b></div></div>${latest?`<div id="consistencyRunStatus" class="summary-panel"><b>最近验证：${esc(latest.status)}</b><p>${esc(latest.path||'')} · ${esc(latest.redis_pattern||'按需数据源')} · ${esc(latest.created_at||'')}</p></div>`:'<div id="consistencyRunStatus"></div>'}<div class="formrow"><button class="small" onclick="showConsistencyRules()">查看规则明细</button><button class="small" onclick="runReadyConsistency('extended')">运行扩展候选</button></div></div>`}
function showConsistencyRules(){let rules=(data.consistency||{}).rules||[];$('#modalBody').innerHTML=`<h2>数据验证规则明细</h2><table><thead><tr><th>接口</th><th>MySQL</th><th>Redis</th><th>状态</th></tr></thead><tbody>${rules.map(x=>`<tr><td><code>${esc((x.method||'')+' '+(x.path||''))}</code></td><td>${esc(x.mysql_table||'按需/待确认')}<br><small>${esc(x.mysql_condition||'')}</small></td><td>${esc(x.redis_pattern||'不常驻')}</td><td><span class="tag ${x.status==='ready'?'PASSED':'P1'}">${esc(x.status)}</span></td></tr>`).join('')}</tbody></table>`;$('#modal').classList.remove('hidden')}
function dataQualityClosure(){let pack=data.consistency||{},rules=pack.rules||[],runs=pack.runs||[],summary=pack.summary||data.wealth_latest?.data_consistency||{},e=data.evidence_center||{},t=e.thresholds||{},r=e.redis_snapshot||{};return `<div class="card quality-hero"><span class="tag">DATA VALIDATION</span><h2>数据验证</h2><p>这里负责数据验证编排和证据归档；MySQL、Redis 是只读外部证据源，需要时由平台调起，不作为主工作台展开。</p><div class="quality-flow">${[['接口证据',(data.runs||[]).length,`${(data.runs||[]).length}条执行记录`],['MySQL证据',(data.db_tables||[]).length,`${(data.db_tables||[]).length}张表元数据`],['Redis证据',(data.redis_sources||[]).length,`${(data.redis_sources||[]).length}个只读连接`],['验证结论',rules.length||runs.length,`${rules.length}条规则 · ${runs.length}次执行`]].map(x=>`<div class="quality-step ${x[1]?'':'pending'}">${hubStatus(x[1])}<b>${x[0]}</b><small>${esc(x[2])}</small></div>`).join('')}</div></div><div class="metrics"><div class="metric"><span>一致性状态</span><b style="font-size:20px">${esc(summary.status||'PENDING')}</b></div><div class="metric"><span>升级真值表</span><b>${t.loaded?t.rows:'-'}</b></div><div class="metric"><span>Redis快照</span><b>${r.loaded?r.fields:'-'}</b></div><div class="metric"><span>外部数据</span><b style="font-size:18px">只读</b></div></div>${endpointDataMatrix()}<div class="closure-grid"><div>${tableConsistency()}</div><div><div class="card"><h2>按需证据源</h2><div class="closure-row"><b>MySQL</b><p>只读查询候选表、业务行和字段，不回写公司库。</p><button class="small" onclick="showConsistencyRules()">查看关联</button></div><div class="closure-row"><b>Redis</b><p>只在需要缓存证据时读取 Key 指纹、TTL 和摘要快照。</p><button class="small" onclick="showConsistencyRules()">查看Key</button></div><div class="closure-row"><b>报告中心</b><p>接口、性能、数据一致性和风险全部归档到报告中心。</p><button class="small" onclick="switchTab('reports')">进入</button></div></div>${tableEvidenceCenter()}</div></div>`}

function assetGroupName(x){return x.executor_type==='http'||x.method?'接口自动化':x.executor_type==='workflow'?'业务链路':x.executor_type?.includes('performance')?'性能测试':x.executor_type?.includes('security')?'异常与安全':'设计用例'}
function assetStatusTag(status){let st=status||'NOT_RUN',labels={NOT_RUN:'未执行',PASSED:'通过',FAILED:'失败',BLOCKED:'阻塞',ERROR:'环境异常',ASSERTION_PASSED:'断言通过'};return `<span class="tag ${esc(st)}">${esc(labels[st]||st)}</span>`}
function openAssetModal(title,html){$('#modalBody').innerHTML=`<h2>${esc(title)}</h2>${html}`;$('#modal').classList.remove('hidden')}
function showTestPointsModal(){let xs=data.points||[];let html=xs.length?`<table><thead><tr><th>优先级</th><th>模块</th><th>测试点</th><th>类型</th><th>风险/依据</th></tr></thead><tbody>${xs.slice(0,500).map(x=>`<tr><td><span class="tag ${esc(x.priority||'')}">${esc(x.priority||'-')}</span></td><td>${esc(x.module||'-')}</td><td><b>${esc(x.title||'-')}</b></td><td>${esc(x.category||'-')}</td><td>${esc(x.risk||'-')}<br><small>${esc(x.rationale||'')}</small></td></tr>`).join('')}</tbody></table>`:'<div class="empty"><b>暂无测试点</b><p>导入需求或接口资料后，执行生成流程即可沉淀到这里。</p></div>';openAssetModal('测试点明细',html)}
function showTestCasesModal(){let xs=data.cases||[];let html=xs.length?`<table><thead><tr><th>优先级</th><th>用例</th><th>场景/执行器</th><th>预期</th><th>状态</th><th></th></tr></thead><tbody>${xs.slice(0,500).map(x=>`<tr><td><span class="tag ${esc(x.priority||'')}">${esc(x.priority||'-')}</span></td><td><b>${esc(x.title||'-')}</b><br><small>${esc(x.requirement_ref||'未标注需求依据')}</small></td><td>${esc(x.scenario_type||'-')}<br><small>${esc(x.executor_type||assetGroupName(x))}</small></td><td>${esc(x.expected||'未填写')}</td><td>${assetStatusTag(x.execution_status)}</td><td>${x.method?`<button class="small" onclick="runCase('${esc(x.id)}')">执行</button>`:'归档'}</td></tr>`).join('')}</tbody></table>`:'<div class="empty"><b>暂无测试用例</b><p>先补齐需求/接口资料，平台会自动生成用例并归档。</p></div>';openAssetModal('测试用例明细',html)}
function showEndpointAssetsModal(){let xs=data.endpoints||[];let html=xs.length?`<table><thead><tr><th>风险</th><th>方法</th><th>接口</th><th>摘要</th><th>关联用例</th></tr></thead><tbody>${xs.slice(0,500).map(ep=>{let count=(data.cases||[]).filter(c=>(c.method||'').toUpperCase()===(ep.method||'').toUpperCase()&&(c.path||'').split('?')[0]===ep.path).length;return `<tr><td><span class="tag ${ep.risk_level==='high'?'P0':ep.risk_level==='medium'?'P1':'PASSED'}">${esc(ep.risk_level||'-')}</span></td><td><code>${esc(ep.method||'-')}</code></td><td><code>${esc(ep.path||'-')}</code></td><td>${esc(ep.summary||'')}</td><td>${count||'待关联'}</td></tr>`}).join('')}</tbody></table>`:'<div class="empty"><b>暂无接口资产</b><p>可导入 OpenAPI、Swagger 或 HAR 抓包自动沉淀接口。</p></div>';openAssetModal('接口资产明细',html)}
function groupedTestAssets(){let cases=data.cases||[],points=data.points||[],endpoints=data.endpoints||[],groups={};cases.forEach(x=>{let key=assetGroupName(x);(groups[key]||(groups[key]=[])).push(x)});let groupHtml=Object.entries(groups).map(([name,items])=>`<div class="summary-panel"><b>${esc(name)}</b><p>${items.length} 条；通过 ${items.filter(x=>x.execution_status==='PASSED').length}，失败 ${items.filter(x=>['FAILED','ERROR'].includes(x.execution_status)).length}，阻塞 ${items.filter(x=>x.execution_status==='BLOCKED').length}</p><button class="small" onclick="showAssetGroup('${esc(name)}')">查看分组</button></div>`).join('')||'<div class="empty"><b>暂无分组用例</b><p>生成后会按接口、链路、性能、异常安全自动归类。</p></div>';return `<div class="card"><div class="diagnosis-head"><div><h2>测试资产中心</h2><p>测试点、测试用例、接口和链路统一归档在这里；执行结果进入报告中心。</p></div><span class="tag PASSED">${cases.length} CASES</span></div><div class="metrics"><button class="metric asset-metric" onclick="showTestPointsModal()"><span>测试点</span><b>${points.length}</b></button><button class="metric asset-metric" onclick="showTestCasesModal()"><span>测试用例</span><b>${cases.length}</b></button><button class="metric asset-metric" onclick="showEndpointAssetsModal()"><span>接口资产</span><b>${endpoints.length}</b></button><button class="metric asset-metric" onclick="showTraceCoverageModal()"><span>覆盖关系</span><b>${(data.trace_links||[]).length}</b></button></div><div class="formrow"><button class="small" onclick="showTestPointsModal()">查看测试点</button><button class="small" onclick="showTestCasesModal()">查看测试用例</button><button class="small" onclick="showEndpointAssetsModal()">查看接口资产</button></div>${groupHtml}</div>`}
function showAssetGroup(name){let cases=(data.cases||[]).filter(x=>assetGroupName(x)===name);let html=cases.length?`<table><thead><tr><th>用例</th><th>接口/执行器</th><th>预期</th><th>状态</th></tr></thead><tbody>${cases.slice(0,300).map(x=>`<tr><td><b>${esc(x.title)}</b><br><small>${esc(x.requirement_ref||'')}</small></td><td>${x.method?`<code>${esc(x.method+' '+x.path)}</code>`:esc(x.executor_type||'manual')}</td><td>${esc(x.expected||'-')}</td><td>${assetStatusTag(x.execution_status)}</td></tr>`).join('')}</tbody></table>`:'<div class="empty"><b>暂无该分组用例</b></div>';openAssetModal(name,html)}
function compactAssetsWorkspace(){let reqs=data.requirement_items||[],sources=data.sources||[],endpoints=data.endpoints||[],cases=data.cases||[],points=data.points||[],selected=(data.trace_links||[]).filter(x=>+x.selected===1).length;return `<div class="card quality-hero"><span class="tag">ASSETS</span><h2>需求与测试资产</h2><p>资料、需求、接口、测试点和测试用例统一归纳；从这里查看明细、维护覆盖和启动生成。</p><div class="quality-flow">${[['资料',sources.length,sources.length+'份输入'],['需求',reqs.length,reqs.length+'条需求'],['测试点',points.length,points.length+'个测试点'],['用例',cases.length,cases.length+'条用例']].map(x=>`<button class="quality-step ${x[1]?'':'pending'}" onclick="${x[0]==='测试点'?'showTestPointsModal()':x[0]==='用例'?'showTestCasesModal()':'showTraceCoverageModal()'}">${hubStatus(x[1])}<b>${x[0]}</b><small>${esc(x[2])}</small></button>`).join('')}</div></div><div class="closure-grid"><div class="card"><h2>资产操作</h2><div class="summary-panel"><b>新增资料</b><p>需求、链接、图片、OpenAPI、HAR 抓包统一从这里导入。</p><button class="primary" onclick="showSourceModal()">添加资料</button></div><div class="summary-panel"><b>生成与补齐</b><p>生成测试点、用例、接口覆盖、链路和数据验证规则。</p><button class="small" onclick="runPipeline()">启动生成</button></div><div class="summary-panel"><b>接口文档基线</b><p>把当前接口资产导出为脱敏 OpenAPI；抓包导入后也会同步沉淀。</p><button class="small" onclick="downloadInterfaceDocument()">导出</button></div></div><div><div class="card"><h2>覆盖摘要</h2><div class="evidence-list"><button class="evidence-item asset-row" onclick="showTraceCoverageModal()"><b>需求覆盖</b><small>${reqs.length}条需求，${selected}条已选追踪关系</small></button><button class="evidence-item asset-row" onclick="showEndpointAssetsModal()"><b>接口覆盖</b><small>${endpoints.length?endpoints.map(x=>x.method+' '+x.path).join(' · '):'暂无接口资产'}</small></button></div></div>${groupedTestAssets()}</div></div>`}
const switchTabBeforeAssetDrilldown=typeof switchTab==='function'?switchTab:null;
switchTab=function(id){let target=id==='points'||id==='cases'||id==='apis'?'sources':id;if(switchTabBeforeAssetDrilldown)switchTabBeforeAssetDrilldown(target);if(id==='points')setTimeout(showTestPointsModal,0);if(id==='cases')setTimeout(showTestCasesModal,0);if(id==='apis')setTimeout(showEndpointAssetsModal,0)}
navigateWorkspace=async function(id){if(!current){if(projects.length){await openProject(projects[0].id)}else{toast('请先创建测试项目','warning');return}}switchTab(id)}
$$('.side-tab').forEach(x=>x.onclick=()=>navigateWorkspace(x.dataset.tab));

function caseBlockerReason(x){let type=x.executor_type||'';if((x.method||'')&&(x.path||''))return '可直接执行真实接口';if(type==='ui_device')return '缺少真机/Appium页面定位与验证脚本';if(type==='workflow')return '缺少已确认的跨接口步骤与变量传递';if(type==='api_ui')return '缺少接口结果到页面展示的联动校验条件';if(type==='performance_ui')return '缺少压测模型、并发账号或UI观测条件';if(type==='db_redis')return '缺少可读数据源规则或Redis Key证据';if(type==='api_db')return '缺少边界账号、业务规则或数据库查询条件';if(type==='api_security')return '缺少允许执行的异常/安全测试策略';return '缺少自动执行器或前置条件'}
function blockedCaseSummary(){let xs=data.cases||[],blocked=xs.filter(x=>x.execution_status==='BLOCKED'),passed=xs.filter(x=>x.execution_status==='PASSED'),failed=xs.filter(x=>x.execution_status==='FAILED'),httpReady=xs.filter(x=>(x.method||'')&&(x.path||''));let buckets={};blocked.forEach(x=>{let reason=caseBlockerReason(x);buckets[reason]=(buckets[reason]||0)+1});return `<div class="card"><h2>用例执行状态说明</h2><p class="policy-note">BLOCKED 在这里表示“待补齐执行条件”，不是接口失败。平台按企业测试视角生成了 UI、链路、数据、性能、安全等完整用例；只有具备接口、账号、工具、数据源和规则的用例才会进入真实执行。</p><div class="metrics"><div class="metric"><span>已通过</span><b>${passed.length}</b></div><div class="metric"><span>待补齐</span><b>${blocked.length}</b></div><div class="metric"><span>失败待分析</span><b>${failed.length}</b></div><div class="metric"><span>接口可执行</span><b>${httpReady.length}</b></div></div>${Object.entries(buckets).length?`<table><thead><tr><th>待补齐原因</th><th>数量</th></tr></thead><tbody>${Object.entries(buckets).map(([k,v])=>`<tr><td>${esc(k)}</td><td>${v}</td></tr>`).join('')}</tbody></table>`:''}</div>`}
function assetStatusTag(status){let st=status||'NOT_RUN',labels={NOT_RUN:'未执行',PASSED:'通过',FAILED:'失败',BLOCKED:'待补齐',ERROR:'环境异常',ASSERTION_PASSED:'断言通过'};return `<span class="tag ${esc(st)}">${esc(labels[st]||st)}</span>`}
function showTestCasesModal(){let xs=data.cases||[];let html=xs.length?`${blockedCaseSummary()}<table><thead><tr><th>优先级</th><th>用例</th><th>执行器</th><th>预期</th><th>状态/原因</th><th></th></tr></thead><tbody>${xs.slice(0,500).map(x=>`<tr><td><span class="tag ${esc(x.priority||'')}">${esc(x.priority||'-')}</span></td><td><b>${esc(x.title||'-')}</b><br><small>${esc(x.requirement_ref||'未标注需求依据')}</small></td><td>${esc(x.scenario_type||'-')}<br><small>${esc(x.executor_type||assetGroupName(x))}</small></td><td>${esc(x.expected||'未填写')}</td><td>${assetStatusTag(x.execution_status)}<br><small>${esc(x.execution_status==='BLOCKED'?caseBlockerReason(x):(x.actual_result||'已归档执行证据'))}</small></td><td>${x.method?`<button class="small" onclick="runCase('${esc(x.id)}')">执行</button>`:'待条件'}</td></tr>`).join('')}</tbody></table>`:'<div class="empty"><b>暂无测试用例</b><p>先补齐需求/接口资料，平台会自动生成用例并归档。</p></div>';openAssetModal('测试用例明细',html)}

const openProjectBeforeExecutionProfile=openProject;
openProject=async function(id){await openProjectBeforeExecutionProfile(id);try{data.execution_profile=await api(`/api/projects/${id}/execution-profile`)}catch{data.execution_profile={runtime_params:{},performance:{},tools:{}}}render()};
function runtimeProfileJson(){let p=data.execution_profile||{},runtime=p.runtime_params||{};return JSON.stringify(runtime,null,2)}
function executionProfilePanel(){let p=data.execution_profile||{},perf=p.performance||{},tools=p.tools||{},runtime=p.runtime_params||{},caseCount=(data.cases||[]).filter(x=>x.method&&x.path).length;return `<div class="card"><div class="diagnosis-head"><div><h2>运行配置中心</h2><p>沉淀业务运行参数、账号变量和性能策略。保存后生成资产与执行工具链都会默认复用。</p></div><span class="tag PASSED">LOCAL ONLY</span></div><div class="metrics"><div class="metric"><span>默认UID</span><b style="font-size:20px">${esc(runtime.uid||'-')}</b></div><div class="metric"><span>账号组</span><b>${Array.isArray(runtime.uids)?runtime.uids.length:0}</b></div><div class="metric"><span>可执行接口用例</span><b>${caseCount}</b></div><div class="metric"><span>压测模型</span><b style="font-size:20px">${esc(perf.profile||'smoke')}</b></div></div><div class="summary-panel"><b>当前默认参数</b><p>JMeter ${perf.jmeter_threads||2}线程 / ${perf.jmeter_loops||5}循环 / ${perf.jmeter_rampup||2}s爬升；工具 ${tools.run_newman!==false?'Newman ':''}${tools.run_jmeter!==false?'JMeter ':''}${tools.run_pytest!==false?'pytest':''}</p><button class="primary" onclick="showExecutionProfileModal()">维护</button></div></div>`}
function showExecutionProfileModal(){let p=data.execution_profile||{},perf=p.performance||{},tools=p.tools||{};$('#modalBody').innerHTML=`<h2>运行配置中心</h2><p style="color:var(--muted);font-size:12px">这里只保存非敏感默认参数。ticket、密码、sn 等敏感凭证仍按运行时处理，不在这里明文展示。</p><label>业务运行参数 JSON</label><textarea id="execRuntimeParams" spellcheck="false" style="min-height:220px">${esc(runtimeProfileJson())}</textarea><label>性能模型</label><div class="formrow"><select id="execPerfProfile"><option value="smoke" ${perf.profile==='smoke'?'selected':''}>冒烟验证</option><option value="baseline" ${perf.profile==='baseline'?'selected':''}>基准压测</option><option value="load" ${perf.profile==='load'?'selected':''}>阶梯负载</option><option value="stability" ${perf.profile==='stability'?'selected':''}>稳定性</option></select><input id="execThreads" type="number" min="1" max="200" value="${esc(perf.jmeter_threads||2)}" placeholder="线程数"><input id="execLoops" type="number" min="1" max="1000" value="${esc(perf.jmeter_loops||5)}" placeholder="循环"><input id="execRampup" type="number" min="0" max="600" value="${esc(perf.jmeter_rampup||2)}" placeholder="爬升秒"></div><div class="formrow"><input id="execTimeout" type="number" min="30" max="3600" value="${esc(perf.jmeter_timeout||180)}" placeholder="超时秒"><input id="execErrorRate" type="number" min="0" max="100" step="0.1" value="${esc(perf.max_error_rate??0)}" placeholder="错误率%"><input id="execP95" type="number" min="1" value="${esc(perf.max_p95_ms||3000)}" placeholder="P95 ms"><input id="execP99" type="number" min="1" value="${esc(perf.max_p99_ms||5000)}" placeholder="P99 ms"></div><label>外部工具</label><div class="formrow"><label><input id="execNewman" type="checkbox" ${tools.run_newman!==false?'checked':''}> Newman</label><label><input id="execJmeter" type="checkbox" ${tools.run_jmeter!==false?'checked':''}> JMeter</label><label><input id="execPytest" type="checkbox" ${tools.run_pytest!==false?'checked':''}> pytest</label></div><button class="primary" onclick="saveExecutionProfile()">保存运行配置</button>`;$('#modal').classList.remove('hidden')}
async function saveExecutionProfile(){let runtime={};try{runtime=JSON.parse($('#execRuntimeParams').value||'{}')}catch{return toast('业务运行参数必须是合法 JSON','warning')}let payload={runtime_params:runtime,performance:{profile:$('#execPerfProfile').value,jmeter_threads:+$('#execThreads').value||2,jmeter_loops:+$('#execLoops').value||5,jmeter_rampup:+$('#execRampup').value||2,jmeter_timeout:+$('#execTimeout').value||180,max_error_rate:+$('#execErrorRate').value||0,max_p95_ms:+$('#execP95').value||3000,max_p99_ms:+$('#execP99').value||5000,min_throughput_rps:0},tools:{run_newman:$('#execNewman').checked,run_jmeter:$('#execJmeter').checked,run_pytest:$('#execPytest').checked}};try{data.execution_profile=await api(`/api/projects/${current}/execution-profile`,{method:'POST',body:JSON.stringify(payload)});closeModal();toast('运行配置已保存，后续工具链会自动复用','success');await openProject(current);switchTab('automation')}catch(e){toast(e.message,'error')}}
function toolchainPanel(){let t=data.toolchain||{},tools=t.tools||[],arts=t.artifacts||[],blockers=t.blockers||[],readyAssets=arts.length&&arts.every(x=>x.status==='READY'),profile=data.execution_profile||{},perf=profile.performance||{},runTools=profile.tools||{},runtimeSample=runtimeProfileJson();return `${executionProfilePanel()}<div class="card"><div class="diagnosis-head"><div><h2>企业测试工具链</h2><p>平台先读取运行配置，再完成预检和标准资产生成，最后交给 Newman、JMeter、pytest、JMeter 报告执行归档。</p></div><span class="tag ${t.status==='READY'?'PASSED':'P1'}">${esc(t.status||'PENDING')}</span></div>${blockers.length?`<div class="gap-list">${blockers.map(x=>`<div class="gap-item P1"><span class="tag P1">待补</span><div><b>${esc(x)}</b><p>补齐后即可进入外部工具执行阶段。</p></div></div>`).join('')}</div>`:''}<div class="endpoint-matrix">${tools.map(x=>`<div class="endpoint-card"><span class="tag ${x.status==='READY'?'PASSED':'P1'}">${esc(x.status)}</span><h3>${esc(x.name)}</h3><code>${esc(x.command||'未发现')}</code><p style="font-size:12px;color:var(--muted)">${esc(x.version||x.install_hint||'')}</p></div>`).join('')}</div><div class="summary-panel"><b>执行策略</b><p>登录接口只做前置提取；业务接口使用平台同步后的 ticket、uid、设备上下文和运行参数。</p><select id="toolLoginStrategy"><option value="auto">自动：有登录参数就刷新，否则复用</option><option value="force">强制重新登录</option><option value="reuse">仅复用本机凭证</option></select><div class="formrow"><input id="toolLoginT" placeholder="登录请求头 t（可空，自动生成时间戳）"><input id="toolLoginSn" placeholder="登录请求头 sn（可空；如接口要求签名需补齐）"></div><input id="toolLoginPassword" type="password" placeholder="登录请求体加密密码；重新登录时填写，留空则复用本机凭证"><label>业务运行参数</label><textarea id="toolRuntimeParams" spellcheck="false">${esc(runtimeSample)}</textarea><div class="formrow"><label><input id="toolRunNewman" type="checkbox" ${runTools.run_newman!==false?'checked':''}> Newman</label><label><input id="toolRunJmeter" type="checkbox" ${runTools.run_jmeter!==false?'checked':''}> JMeter</label><label><input id="toolRunPytest" type="checkbox" ${runTools.run_pytest!==false?'checked':''}> pytest</label></div><label>JMeter 压测模型</label><div class="formrow"><input id="toolJmeterThreads" type="number" min="1" max="200" value="${esc(perf.jmeter_threads||2)}" placeholder="线程数"><input id="toolJmeterLoops" type="number" min="1" max="1000" value="${esc(perf.jmeter_loops||5)}" placeholder="每线程循环"><input id="toolJmeterRampup" type="number" min="0" max="600" value="${esc(perf.jmeter_rampup||2)}" placeholder="Ramp-up秒"><input id="toolJmeterTimeout" type="number" min="30" max="3600" value="${esc(perf.jmeter_timeout||180)}" placeholder="超时秒"></div><label>性能准入策略</label><div class="formrow"><select id="toolPerfProfile"><option value="smoke" ${perf.profile==='smoke'?'selected':''}>冒烟验证</option><option value="baseline" ${perf.profile==='baseline'?'selected':''}>基准压测</option><option value="load" ${perf.profile==='load'?'selected':''}>阶梯负载</option><option value="stability" ${perf.profile==='stability'?'selected':''}>稳定性</option></select><input id="toolMaxErrorRate" type="number" min="0" max="100" step="0.1" value="${esc(perf.max_error_rate??0)}" placeholder="最大错误率%"><input id="toolMaxP95" type="number" min="1" value="${esc(perf.max_p95_ms||3000)}" placeholder="P95阈值ms"><input id="toolMaxP99" type="number" min="1" value="${esc(perf.max_p99_ms||5000)}" placeholder="P99阈值ms"><input id="toolMinThroughput" type="number" min="0" step="0.1" value="${esc(perf.min_throughput_rps??0)}" placeholder="最小吞吐req/s"></div><button class="primary" onclick="generateToolAssets()">生成资产</button> <button id="toolchainRunButton" class="small" onclick="runEnterpriseToolchain()" ${readyAssets?'':'disabled'}>执行工具链</button><div id="toolchainRunStatus" style="margin-top:12px"></div></div><div class="evidence-list">${arts.map(x=>`<div class="evidence-item"><b>${esc(x.name)}</b><small>${esc(x.status)}</small>${x.url?`<button class="small" onclick="openReport('${esc(x.url)}')">打开</button>`:''}</div>`).join('')}</div></div>`}

function openDownload(url){if(!url)return;window.open(url,'_blank')}
async function createApifoxPackage(){let packageId=selectedRequirementPackageId(),pkg=currentRequirementPackage();if(!packageId)return toast('请先选择需求包','warning');try{toast(`正在生成 ${pkg.name} 的 Apifox 交换包…`);let x=await api(`/api/projects/${current}/requirement-packages/${packageId}/apifox-export`,{method:'POST',body:'{}'});let s=x.summary||{};$('#modalBody').innerHTML=`<h2>${esc(pkg.name)} · Apifox交换包</h2><p class="policy-note">只导出当前需求包。真实ticket、token、密码和数据库凭证不会写入文件。</p><div class="metrics"><div class="metric"><span>接口</span><b>${esc(s.interfaces||0)}</b></div><div class="metric"><span>用例</span><b>${esc(s.cases||0)}</b></div><div class="metric"><span>cURL</span><b>${esc(s.curl_files||0)}</b></div></div><div class="formrow"><button class="primary" onclick="openDownload('${esc(x.zip_url||'')}')">下载交换包</button><button class="small" onclick="openReport('${esc(x.openapi_url||'')}')">OpenAPI</button><button class="small" onclick="openReport('${esc(x.postman_url||'')}')">请求集合</button><button class="small" onclick="openReport('${esc(x.environment_url||'')}')">环境模板</button><button class="small" onclick="openReport('${esc(x.mapping_url||'')}')">用例映射</button></div><label>输出目录</label><code>${esc(x.zip_path||'')}</code><h3>包内文件</h3><div class="evidence-list">${(x.files||[]).map(f=>`<div class="evidence-item"><b>${esc(f)}</b><small>Apifox可维护资产</small></div>`).join('')}</div>`;$('#modal').classList.remove('hidden');toast('Apifox交换包已生成','success')}catch(e){toast(e.message,'error')}}
function showApifoxEnterpriseFlow(){let pkg=currentRequirementPackage();if(!pkg)return toast('请先选择需求包','warning');$('#modalBody').innerHTML=`<h2>${esc(pkg.name)} · Apifox企业链路</h2><p class="policy-note">Apifox是接口文档真相源。完整导出OpenAPI 3.0后在这里导入；平台只覆盖pytest generated目录，不覆盖人工business目录。</p><label>Apifox OpenAPI 3.0文件</label><input id="apifoxOpenapiFile" type="file" accept=".json,.yaml,.yml"><div class="formrow"><button class="primary" onclick="importApifoxOpenapi()">导入并生成pytest基础层</button><button class="small" onclick="runApifoxCliSmoke()">运行发布冒烟</button></div><div id="apifoxFlowResult"></div><p class="policy-note">CLI首次使用：把Apifox CI/CD页面生成的命令写入当前需求包 apifox/cli-profile.yaml，access token只配置为系统环境变量。</p>`;$('#modal').classList.remove('hidden')}
async function importApifoxOpenapi(){let packageId=selectedRequirementPackageId(),file=$('#apifoxOpenapiFile')?.files?.[0];if(!file)return toast('请选择Apifox导出的OpenAPI文件','warning');try{let content=await file.text();toast('正在解析OpenAPI并生成pytest基础层…');let x=await api(`/api/projects/${current}/requirement-packages/${packageId}/apifox/openapi/import`,{method:'POST',body:JSON.stringify({name:file.name,content})}),s=x.summary||{};$('#apifoxFlowResult').innerHTML=`<div class="summary-panel"><b>${esc(x.status)} · ${esc(x.selection_mode)}</b><p>OpenAPI路径 ${esc(s.openapi_paths||0)} · pytest接口 ${esc(s.pytest_operations||0)} · ${x.source_changed?'检测到接口变化':'接口定义未变化'}</p><button class="small" onclick="openReport('${esc(x.generated_url||'')}')">查看生成脚本</button></div>`;toast('pytest基础层已生成','success')}catch(e){toast(e.message,'error')}}
async function runApifoxCliSmoke(){let packageId=selectedRequirementPackageId();try{toast('正在运行Apifox发布冒烟…');let x=await api(`/api/projects/${current}/requirement-packages/${packageId}/apifox-cli/run`,{method:'POST',body:JSON.stringify({run_id:activeRequirementRunId()||''})}),s=x.summary||{};$('#apifoxFlowResult').innerHTML=`<div class="summary-panel"><b>${esc(x.status)}</b><p>退出码 ${esc(s.exit_code??'-')} · 请求 ${esc(s.requests||0)} · 失败 ${esc(s.failures||0)} · ${esc(s.duration_ms||0)}ms</p>${(x.blockers||[]).map(v=>`<small>${esc(v)}</small><br>`).join('')}${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">查看冒烟报告</button>`:''}</div>`;toast(x.status==='PASSED'?'Apifox冒烟通过':'Apifox冒烟需要处理',x.status==='PASSED'?'success':'warning');await openProject(current)}catch(e){toast(e.message,'error')}}
async function createDeliveryPackage(){try{toast('正在生成测试资产交付包…');let x=await api(`/api/projects/${current}/delivery-package`,{method:'POST',body:'{}'});toast('测试资产交付包已生成','success');showPackageResult('测试资产交付包',x)}catch(e){toast(e.message,'error')}}
function showPackageResult(title,x){let summary=x.summary?`<div class="metrics">${Object.entries(x.summary).map(([k,v])=>`<div class="metric"><span>${esc(k)}</span><b>${esc(v)}</b></div>`).join('')}</div>`:'';$('#modalBody').innerHTML=`<h2>${esc(title)}</h2><p class="policy-note">已生成可迁移交付文件；敏感凭证不会导出，MySQL/Redis 仍按只读证据源处理。</p>${summary}<label>包内文件</label><div class="evidence-list">${(x.files||[]).map(f=>`<div class="evidence-item"><b>${esc(f)}</b><small>已归档</small></div>`).join('')}</div><button class="primary" onclick="openDownload('${esc(x.zip_url||'')}')">下载 ZIP</button>`;$('#modal').classList.remove('hidden')}
function collaborationPackagePanel(){let endpoints=(data.endpoints||[]).length,cases=(data.cases||[]).length,points=(data.points||[]).length,rules=((data.consistency||{}).rules||[]).length,reports=(data.generated_reports||[]).length;return `<div class="card"><div class="diagnosis-head"><div><h2>协同与交付</h2><p>Apifox维护接口真相和发布冒烟，平台生成pytest、回收执行结果并完成复盘。</p></div><span class="tag PASSED">ENTERPRISE FLOW</span></div><div class="endpoint-matrix"><div class="endpoint-card"><span class="tag PASSED">APIFOX</span><h3>Apifox企业链路</h3><p style="font-size:12px;color:var(--muted)">导入企业Apifox的OpenAPI生成pytest基础层，或运行Apifox CLI发布冒烟。</p><button class="primary" onclick="showApifoxEnterpriseFlow()">进入</button></div><div class="endpoint-card"><span class="tag PASSED">DELIVERY</span><h3>测试资产交付包</h3><p style="font-size:12px;color:var(--muted)">打包接口文档、测试点、测试用例、追踪关系、数据规则、运行配置、外部工具脚本和报告索引。</p><button class="primary" onclick="createDeliveryPackage()">生成交付包</button></div></div><div class="metrics" style="margin-top:16px"><div class="metric"><span>接口</span><b>${endpoints}</b></div><div class="metric"><span>测试点</span><b>${points}</b></div><div class="metric"><span>用例</span><b>${cases}</b></div><div class="metric"><span>规则/报告</span><b>${rules}/${reports}</b></div></div></div>`}
function compactAssetsWorkspace(){let reqs=data.requirement_items||[],sources=data.sources||[],endpoints=data.endpoints||[],cases=data.cases||[],points=data.points||[],selected=(data.trace_links||[]).filter(x=>+x.selected===1).length;return `<div class="card quality-hero"><span class="tag">ASSETS</span><h2>需求与测试资产</h2><p>资料、需求、接口、测试点和测试用例统一归纳；从这里查看明细、维护覆盖、协同交付和启动生成。</p><div class="quality-flow">${[['资料',sources.length,sources.length+'份输入'],['需求',reqs.length,reqs.length+'条需求'],['测试点',points.length,points.length+'个测试点'],['用例',cases.length,cases.length+'条用例']].map(x=>`<button class="quality-step ${x[1]?'':'pending'}" onclick="${x[0]==='测试点'?'showTestPointsModal()':x[0]==='用例'?'showTestCasesModal()':'showTraceCoverageModal()'}">${hubStatus(x[1])}<b>${x[0]}</b><small>${esc(x[2])}</small></button>`).join('')}</div></div>${collaborationPackagePanel()}<div class="closure-grid"><div class="card"><h2>资产操作</h2><div class="summary-panel"><b>新增需求资料</b><p>需求描述、原型链接、图片、HTML原型包统一从这里导入。</p><button class="primary" onclick="showSourceModal()">添加需求</button></div><div class="summary-panel"><b>导入接口文档</b><p>上传或粘贴 OpenAPI/Swagger/HAR，形成接口基线并同步进入覆盖矩阵。</p><button class="primary" onclick="showInterfaceDocModal()">导入接口</button></div><div class="summary-panel"><b>生成与补齐</b><p>生成测试点、用例、接口覆盖、链路和数据验证规则。缺原始接口文档时会提示补齐，不再中断。</p><button class="small" onclick="runPipeline()">启动生成</button></div><div class="summary-panel"><b>接口文档基线</b><p>把当前接口资产导出为脱敏 OpenAPI；抓包导入后也会同步沉淀。</p><button class="small" onclick="downloadInterfaceDocument()">导出</button></div></div><div><div class="card"><h2>覆盖摘要</h2><div class="evidence-list"><button class="evidence-item asset-row" onclick="showTraceCoverageModal()"><b>需求覆盖</b><small>${reqs.length}条需求，${selected}条已选追踪关系</small></button><button class="evidence-item asset-row" onclick="showEndpointAssetsModal()"><b>接口覆盖</b><small>${endpoints.length?endpoints.map(x=>x.method+' '+x.path).join(' · '):'暂无接口资产'}</small></button></div></div>${groupedTestAssets()}</div></div>`}

function collectJmeterWorkbenchPayload(){
  let runtime_params={};
  try{runtime_params=JSON.parse($('#toolRuntimeParams')?.value.trim()||'{}')}catch{throw new Error('运行参数必须是合法 JSON')}
  return {
    package_id:selectedRequirementPackageId(),
    run_id:activeRequirementRunId(),
    runtime_params,
    login_t:$('#toolLoginT')?.value.trim()||'',
    login_sn:$('#toolLoginSn')?.value.trim()||'',
    login_password_encrypted:$('#toolLoginPassword')?.value.trim()||'',
    jmeter_threads:+$('#toolJmeterThreads')?.value||2,
    jmeter_loops:+$('#toolJmeterLoops')?.value||5,
    jmeter_rampup:+$('#toolJmeterRampup')?.value||2,
    jmeter_timeout:+$('#toolJmeterTimeout')?.value||180,
    performance_profile:$('#toolPerfProfile')?.value||'smoke',
    max_error_rate:+$('#toolMaxErrorRate')?.value||0,
    max_p95_ms:+$('#toolMaxP95')?.value||3000,
    max_p99_ms:+$('#toolMaxP99')?.value||5000,
    min_throughput_rps:+$('#toolMinThroughput')?.value||0,
    run_jmeter:true
  };
}
async function openJmeterWorkbench(){
  try{
    toast('正在打开真实 JMeter，并加载平台生成的线程组脚本…');
    let x=await api(`/api/projects/${current}/jmeter/open-gui`,{method:'POST',body:JSON.stringify(collectJmeterWorkbenchPayload())});
    let s=x.summary||{},groups=s.groups||[];
    $('#modalBody').innerHTML=`<h2>JMeter 工作台已打开</h2><p class="policy-note">平台已覆盖更新固定工作台 .jmx，并用真实 JMeter GUI 打开。登录接口作为 setUp 前置提取 access_token；没有登录输入时，会优先复用平台本机加密凭证。自动压测与报告归档仍由“执行工具链”完成。</p><div class="metrics"><div class="metric"><span>登录前置</span><b>${esc(s.setup_thread_groups||0)}</b></div><div class="metric"><span>业务线程组</span><b>${esc(s.thread_groups||0)}</b></div><div class="metric"><span>HTTP Sampler</span><b>${esc(s.http_samplers||0)}</b></div><div class="metric"><span>提取/同步</span><b>${esc((s.extractors||0)+(s.post_processors||0))}</b></div><div class="metric"><span>运行参数</span><b>${x.runtime_parameters_passed?'已注入':'待补'}</b></div><div class="metric"><span>登录密码</span><b>${x.login_password_available?'可用':'未传'}</b></div></div>${groups.length?`<table><thead><tr><th>线程组</th><th>线程数</th><th>循环</th><th>爬升秒</th></tr></thead><tbody>${groups.map(g=>`<tr><td>${esc(g.name)}</td><td>${esc(g.threads)}</td><td>${esc(g.loops)}</td><td>${esc(g.rampup)}</td></tr>`).join('')}</tbody></table>`:''}<label>固定工作台文件</label><code>${esc(x.jmx_path||'')}</code><label>JMeter 程序</label><code>${esc(x.jmeter_command||'')}</code>`;
    $('#modal').classList.remove('hidden');
    toast(x.message||'JMeter 工作台已打开','success');
  }catch(e){toast(e.message,'error')}
}
async function harvestJmeterGuiReport(){
  try{
    toast('正在回收 JMeter GUI 执行结果…');
    let runId=await ensureRequirementRunContext(),payload=collectJmeterWorkbenchPayload();
    payload.run_id=runId;
    payload.package_id=selectedRequirementPackageId();
    let x=await api(`/api/projects/${current}/jmeter/harvest-gui-report`,{method:'POST',body:JSON.stringify(payload)});
    let s=x.summary||{},g=x.performance_gate||{},d=x.performance_diagnosis||{};
    $('#modalBody').innerHTML=`<h2>JMeter GUI 报告已回收</h2><p class="policy-note">平台已读取固定 JTL，生成性能摘要、准入判断和瓶颈诊断，并归档到报告中心。</p><div class="metrics"><div class="metric"><span>请求数</span><b>${esc(s.requests||0)}</b></div><div class="metric"><span>错误率</span><b>${esc(s.error_rate??'-')}%</b></div><div class="metric"><span>P95 / P99</span><b>${esc(s.p95_ms??'-')} / ${esc(s.p99_ms??'-')}ms</b></div><div class="metric"><span>平均 / 中位</span><b>${esc(s.average_ms??'-')} / ${esc(s.p50_ms??'-')}ms</b></div><div class="metric"><span>准入</span><b>${esc(g.status||x.status)}</b></div></div>${performanceDiagnosisHtml(d,s)}<button class="primary" onclick="openReport('${esc(x.report_url||'')}')">查看JSON</button> ${x.html_url?`<button class="small" onclick="openReport('${esc(x.html_url)}')">查看HTML</button>`:''}`;
    $('#modal').classList.remove('hidden');
    toast(`JMeter GUI 报告已回收：${x.status}`,(x.status==='PASSED')?'success':'warning');
    await openProject(current);
    switchTab('reports');
  }catch(e){toast(e.message,'error')}
}
function performanceDiagnosisHtml(d,s){d=d||{};s=s||{};let findings=d.findings||[],b=d.bottlenecks||[],slow=d.slowest_samples||[];return `<div class="card"><h3>性能诊断结论 <span class="tag ${findings.some(x=>x.severity==='P0')?'FAILED':findings.length?'P1':'PASSED'}">${esc(d.sample_grade||'OBSERVE')}</span></h3><p>${esc(d.conclusion||s.tail_note||'暂无自动诊断')}</p>${findings.length?`<div class="gap-list">${findings.map(x=>`<div class="gap-item ${x.severity==='P0'?'P0':x.severity==='P1'?'P1':'PASSED'}"><span class="tag ${x.severity==='P0'?'FAILED':x.severity==='P1'?'P1':'PASSED'}">${esc(x.severity)}</span><div><b>${esc(x.title)}</b><p>${esc(x.detail)}</p></div></div>`).join('')}</div>`:''}${b.length?`<h3>慢接口 Top</h3><table><thead><tr><th>接口/步骤</th><th>样本</th><th>平均</th><th>P95</th><th>最大</th></tr></thead><tbody>${b.map(x=>`<tr><td>${esc(x.label)}</td><td>${esc(x.samples)}</td><td>${esc(x.average_ms)}ms</td><td>${esc(x.p95_ms)}ms</td><td>${esc(x.max_ms)}ms</td></tr>`).join('')}</tbody></table>`:''}${slow.length?`<h3>最慢样本</h3><table><thead><tr><th>步骤</th><th>耗时</th><th>响应码</th><th>结果</th></tr></thead><tbody>${slow.slice(0,5).map(x=>`<tr><td>${esc(x.label)}</td><td>${esc(x.elapsed_ms)}ms</td><td>${esc(x.response_code)}</td><td><span class="tag ${x.success?'PASSED':'FAILED'}">${x.success?'成功':'失败'}</span></td></tr>`).join('')}</tbody></table>`:''}</div>`}
function toolchainPanel(){let t=data.toolchain||{},tools=t.tools||[],arts=t.artifacts||[],blockers=t.blockers||[],readyAssets=arts.length&&arts.every(x=>x.status==='READY'),profile=data.execution_profile||{},perf=profile.performance||{},runTools=profile.tools||{},runtimeSample=runtimeProfileJson();return `${executionProfilePanel()}<div class="card"><div class="diagnosis-head"><div><h2>企业测试工具链</h2><p>平台生成可维护脚本，调起 Apifox / JMeter / Newman / pytest 等外部工具，并把执行报告归档回工作台。</p></div><span class="tag ${t.status==='READY'?'PASSED':'P1'}">${esc(t.status||'PENDING')}</span></div>${blockers.length?`<div class="gap-list">${blockers.map(x=>`<div class="gap-item P1"><span class="tag P1">待补</span><div><b>${esc(x)}</b><p>补齐后即可进入外部工具执行阶段。</p></div></div>`).join('')}</div>`:''}<div class="endpoint-matrix">${tools.map(x=>`<div class="endpoint-card"><span class="tag ${x.status==='READY'?'PASSED':'P1'}">${esc(x.status)}</span><h3>${esc(x.name)}</h3><code>${esc(x.command||'未发现')}</code><p style="font-size:12px;color:var(--muted)">${esc(x.version||x.install_hint||'')}</p></div>`).join('')}</div><div class="summary-panel"><b>执行策略</b><p>登录接口只做前置提取；业务接口使用平台同步后的 ticket、uid、设备上下文和运行参数。</p><select id="toolLoginStrategy"><option value="auto">自动：有登录参数就刷新，否则复用</option><option value="force">强制重新登录</option><option value="reuse">仅复用本机凭证</option></select><div class="formrow"><input id="toolLoginT" placeholder="登录请求头 t（可空，自动生成时间戳）"><input id="toolLoginSn" placeholder="登录请求头 sn（可空；如接口要求签名需补齐）"></div><input id="toolLoginPassword" type="password" placeholder="登录请求体加密密码；重新登录时填写，留空则复用本机凭证"><label>业务运行参数</label><textarea id="toolRuntimeParams" spellcheck="false">${esc(runtimeSample)}</textarea><div class="formrow"><label><input id="toolRunNewman" type="checkbox" ${runTools.run_newman!==false?'checked':''}> Newman</label><label><input id="toolRunJmeter" type="checkbox" ${runTools.run_jmeter!==false?'checked':''}> JMeter</label><label><input id="toolRunPytest" type="checkbox" ${runTools.run_pytest!==false?'checked':''}> pytest</label></div><label>JMeter 压测模型</label><div class="formrow"><input id="toolJmeterThreads" type="number" min="1" max="200" value="${esc(perf.jmeter_threads||2)}" placeholder="线程数"><input id="toolJmeterLoops" type="number" min="1" max="1000" value="${esc(perf.jmeter_loops||5)}" placeholder="每线程循环"><input id="toolJmeterRampup" type="number" min="0" max="600" value="${esc(perf.jmeter_rampup||2)}" placeholder="Ramp-up秒"><input id="toolJmeterTimeout" type="number" min="30" max="3600" value="${esc(perf.jmeter_timeout||180)}" placeholder="超时秒"></div><label>性能准入策略</label><div class="formrow"><select id="toolPerfProfile"><option value="smoke" ${perf.profile==='smoke'?'selected':''}>冒烟验证</option><option value="baseline" ${perf.profile==='baseline'?'selected':''}>基准压测</option><option value="load" ${perf.profile==='load'?'selected':''}>阶梯负载</option><option value="stability" ${perf.profile==='stability'?'selected':''}>稳定性</option></select><input id="toolMaxErrorRate" type="number" min="0" max="100" step="0.1" value="${esc(perf.max_error_rate??0)}" placeholder="最大错误率%"><input id="toolMaxP95" type="number" min="1" value="${esc(perf.max_p95_ms||3000)}" placeholder="P95阈值ms"><input id="toolMaxP99" type="number" min="1" value="${esc(perf.max_p99_ms||5000)}" placeholder="P99阈值ms"><input id="toolMinThroughput" type="number" min="0" step="0.1" value="${esc(perf.min_throughput_rps??0)}" placeholder="最小吞吐req/s"></div><button class="primary" onclick="generateToolAssets()">生成资产</button> <button class="small" onclick="showJmeterScriptChooser()">选择 JMeter 脚本</button> <button id="toolchainRunButton" class="small" onclick="runEnterpriseToolchain()" ${readyAssets?'':'disabled'}>执行工具链</button><div id="toolchainRunStatus" style="margin-top:12px"></div></div><div class="evidence-list">${arts.map(x=>`<div class="evidence-item"><b>${esc(x.name)}</b><small>${esc(x.status)}</small>${x.url?`<button class="small" onclick="openReport('${esc(x.url)}')">打开</button>`:''}</div>`).join('')}</div></div>`}
const toolchainPanelWithGuiHarvest=toolchainPanel;
toolchainPanel=function(){return toolchainPanelWithGuiHarvest().replace('<button id="toolchainRunButton"','<button class="small" onclick="harvestJmeterGuiReport()">回收 GUI 报告</button> <button id="toolchainRunButton"')}
function jmeterGuiFlowPanel(){
  return `<div class="card jmeter-flow-panel"><div class="diagnosis-head"><div><h2>JMeter GUI 调起链路</h2><p>平台生成或复用固定 JMX，自动打开真实 JMeter 并加载线程组；你在 JMeter 里维护和运行，完成后回收 JTL/HTML 到报告中心。</p></div><span class="tag PASSED">GUI READY</span></div><div class="quality-flow"><div class="quality-step"><span class="tag PASSED">1</span><b>生成脚本</b><small>固定写入 D:\\apache-jmeter-5.6.3\\jmx\\20260826\\性能基线.jmx</small></div><div class="quality-step"><span class="tag PASSED">2</span><b>打开 JMeter</b><small>使用 jmeter.bat -t 自动加载线程组和请求</small></div><div class="quality-step"><span class="tag PASSED">3</span><b>回收报告</b><small>读取固定 JTL，生成准入、诊断和 HTML 报告</small></div></div></div>`
}
const toolchainPanelWithJmeterFlow=toolchainPanel;
toolchainPanel=function(){return toolchainPanelWithJmeterFlow().replace('<div class="summary-panel"><b>执行策略</b>',jmeterGuiFlowPanel()+'<div class="summary-panel"><b>执行策略</b>')}
function performanceAccountUsageHtml(summary){let usage=(summary||{}).account_usage||{},threads=usage.by_thread||[];if(!threads.length)return'';let rows=threads.map(thread=>{let accounts=(thread.accounts||[]).map(item=>`${esc(item.role||'unknown')} ${esc(item.uid||'-')} · ${esc(item.source||'-')} · 请求${esc(item.requests||0)} / 错误${esc(item.errors||0)}`).join('<br>');return `<tr><td>${esc(thread.thread_name||'-')}</td><td>${accounts}</td><td>${esc(thread.rotation_count||0)}</td></tr>`}).join('');return `<div class="account-usage-block"><b>多账号实际使用</b><p>线程 ${esc(usage.threads||0)} · 账号 ${esc(usage.unique_accounts||0)} · 切换 ${esc(usage.rotation_count||0)} · ${esc(usage.status||'UNAVAILABLE')}</p><table><thead><tr><th>线程</th><th>账号角色、UID与来源</th><th>切换</th></tr></thead><tbody>${rows}</tbody></table></div>`}
function performanceReportListHtml(){let perf=(data.generated_reports||[]).filter(x=>x.kind==='JMeter');if(!perf.length)return '<div class="empty"><b>暂无JMeter性能报告</b></div>';return `<div class="card">${perf.map(x=>`<div class="summary-panel"><b>${esc(x.name)}</b><p>${esc(x.summary)}</p>${performanceAccountUsageHtml(x.performance_summary||{})}${x.performance_diagnosis?performanceDiagnosisHtml(x.performance_diagnosis,x.performance_summary||{}):''}${x.html_url?`<button class="small" onclick="openReport('${esc(x.html_url)}')">查看JMeter HTML</button> `:''}${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">查看JSON</button>`:''}</div>`).join('')}</div>`}
const showReportCategoryBase=showReportCategory;
showReportCategory=function(kind){if(kind==='performance'){$('#modalBody').innerHTML=`<h2>性能测试</h2>${performanceReportListHtml()}`;$('#modal').classList.remove('hidden');return}showReportCategoryBase(kind)}

function deliveryReportModel(){
  let assertions=allReportAssertions(),failed=assertions.filter(x=>!x.passed),reports=data.generated_reports||[],runs=data.runs||[],cases=data.cases||[],points=data.points||[],reqs=data.requirement_items||[],endpoints=data.endpoints||[];
  let perf=reports.filter(x=>x.kind==='JMeter'),latest=reports[0]||{},latestPerf=perf[0]||{},diag=latestPerf.performance_diagnosis||{},perfFindings=diag.findings||[];
  let blocked=cases.filter(x=>x.execution_status==='BLOCKED'),runFailed=runs.filter(x=>['FAILED','ERROR'].includes(x.status));
  let hardRisk=failed.length||runFailed.length||perfFindings.some(x=>x.severity==='P0')||latestPerf.status==='FAILED';
  let softRisk=blocked.length||perfFindings.length||!reports.length;
  let conclusion=!reports.length?'暂无正式验收结论':hardRisk?'不建议通过，需先定位失败项':softRisk?'阶段可观察，仍有待补齐项':'可作为阶段验收通过';
  let status=!reports.length?'P1':hardRisk?'FAILED':softRisk?'P1':'PASSED';
  return {assertions,failed,reports,runs,cases,points,reqs,endpoints,perf,latest,latestPerf,diag,perfFindings,blocked,runFailed,conclusion,status}
}
function deliveryStatusTag(status,text){return `<span class="tag ${esc(status)}">${esc(text||status)}</span>`}
function deliveryArtifactCard(kind,title,status,count,desc,meta){
  return `<button class="delivery-card" onclick="showDeliveryArtifact('${kind}')"><div><b>${esc(title)}</b>${deliveryStatusTag(status,status==='PASSED'?'已归档':status==='FAILED'?'需处理':'待完善')}</div><p>${esc(desc)}</p><small>${esc(meta||count+' 项')}</small></button>`
}
function deliveryReadinessHtml(m){
  let gaps=platformGaps().filter(x=>x.level!=='PASSED'),ready=[
    ['测试方案',m.reqs.length&&m.endpoints.length,'需求、接口范围和测试环境已具备',m.reqs.length?'继续补齐接口范围或SLA':'补齐需求资料'],
    ['测试用例',m.cases.length&&m.points.length,`已沉淀 ${m.points.length} 个测试点、${m.cases.length} 条用例`,'先执行生成流程形成测试点和用例'],
    ['执行记录',m.runs.length||m.reports.length,`已有 ${m.runs.length} 条执行记录、${m.reports.length} 份报告`,'执行工具链或回收 JMeter GUI 报告'],
    ['缺陷风险',true,m.failed.length?`${m.failed.length} 条失败断言需处理`:'风险区已可归纳','完成一次执行后自动归纳'],
    ['测试报告',m.reports.length,`已归档 ${m.reports.length} 份正式报告`,'回收或生成一次正式报告'],
    ['原始证据',m.reports.length||(data.gift_latest?.assertions||[]).length,`报告文件与断言证据可追溯`,'先完成真实执行并归档证据']
  ];
  return `<div class="card delivery-readiness"><div class="diagnosis-head"><div><h2>交付完整度</h2><p>按企业测试交付物检查当前项目是否能形成可迁移、可复盘、可验收的材料。</p></div><div class="diagnosis-score"><b>${ready.filter(x=>x[1]).length}/${ready.length}</b><span>已具备</span></div></div><div class="readiness-list">${ready.map(x=>`<div class="readiness-row ${x[1]?'ready':'pending'}"><span>${deliveryStatusTag(x[1]?'PASSED':'P1',x[1]?'已齐':'待补')}</span><b>${esc(x[0])}</b><p>${esc(x[1]?x[2]:x[3])}</p></div>`).join('')}</div>${gaps.length?`<div class="summary-panel"><b>平台建议下一步</b><p>${esc(gaps[0].title)}：${esc(gaps[0].desc)}</p><button class="small" onclick="switchTab('${esc(gaps[0].tab||'overview')}')">${esc(gaps[0].action||'处理')}</button></div>`:''}</div>`
}
function legacyProjectReportCenterRemovedB(){
  let m=deliveryReportModel(),p=m.latestPerf.performance_summary||{},gate=m.latestPerf.performance_gate||{},riskCount=m.failed.length+m.runFailed.length+m.perfFindings.length;
  return `<div class="card delivery-hero"><div><span class="tag ${m.status}">ACCEPTANCE</span><h2>企业交付物中心</h2><p>按测试交付物归档：先看验收结论，再进入方案、用例、执行、风险、报告和原始证据。</p></div><button class="primary" onclick="createDeliveryPackage()">生成交付包</button></div><div class="card acceptance-card"><div><span>本次验收结论</span><h2>${esc(m.conclusion)}</h2><p>${m.reports.length?esc(m.latest.summary||'最新报告已归档'):'完成一次工具链或回收 JMeter GUI 报告后，这里会形成正式结论。'}</p></div><div class="acceptance-metrics"><div><b>${m.reports.length}</b><small>报告</small></div><div><b>${m.assertions.length}</b><small>断言</small></div><div><b>${riskCount}</b><small>风险</small></div><div><b>${m.perf.length}</b><small>性能</small></div></div></div>${deliveryReadinessHtml(m)}<div class="delivery-grid">${deliveryArtifactCard('plan','测试方案','PASSED',m.reqs.length+m.endpoints.length,`需求 ${m.reqs.length} 条，接口 ${m.endpoints.length} 个，运行配置与准入策略统一沉淀。`,'需求、范围、环境、SLA、工具策略')}${deliveryArtifactCard('cases','测试用例',m.blocked.length?'P1':'PASSED',m.cases.length,`用例 ${m.cases.length} 条，测试点 ${m.points.length} 个，待补齐 ${m.blocked.length} 条。`,'测试点、用例、覆盖关系')}${deliveryArtifactCard('execution','执行记录',m.runFailed.length?'FAILED':m.runs.length?'PASSED':'P1',m.runs.length,`真实执行记录 ${m.runs.length} 条，异常 ${m.runFailed.length} 条。`,'接口、链路、JMeter、pytest/Newman')}${deliveryArtifactCard('risk','缺陷风险',riskCount?'FAILED':'PASSED',riskCount, riskCount?`发现 ${riskCount} 个需要处理或复核的风险。`:'当前没有归纳到失败断言或执行异常。','失败断言、错误采样、待确认差异')}${deliveryArtifactCard('report','测试报告',m.reports.length?'PASSED':'P1',m.reports.length,`正式报告 ${m.reports.length} 份；${m.latestPerf.summary||'性能报告待回收或待执行'}。`,'验收摘要、性能准入、HTML/JSON')}${deliveryArtifactCard('evidence','原始证据','PASSED',m.reports.length+(data.gift_latest?.assertions?.length||0),`保留 JMeter HTML、JSON、断言证据和脱敏执行明细。`,'审计追溯、原始文件、明细证据')}</div>${m.latestPerf.summary?`<div class="card"><h2>性能准入摘要</h2><div class="metrics"><div class="metric"><span>错误率</span><b>${esc((m.latestPerf.performance_summary||{}).error_rate??'-')}%</b></div><div class="metric"><span>P95 / P99</span><b style="font-size:20px">${esc((m.latestPerf.performance_summary||{}).p95_ms??'-')} / ${esc((m.latestPerf.performance_summary||{}).p99_ms??'-')}ms</b></div><div class="metric"><span>请求数</span><b>${esc((m.latestPerf.performance_summary||{}).requests??'-')}</b></div><div class="metric"><span>准入</span><b style="font-size:20px">${esc(gate.status||m.latestPerf.status||'-')}</b></div></div><p>${esc(m.diag.conclusion||m.latestPerf.summary||'')}</p><button class="small" onclick="showDeliveryArtifact('report')">查看正式报告</button></div>`:''}`
}
function showDeliveryArtifact(kind){
  let m=deliveryReportModel(),html='',title='交付物明细';
  if(kind==='plan'){title='测试方案';html=`<div class="card"><h2>范围与策略</h2><table><tbody><tr><td>需求范围</td><td>${m.reqs.length} 条需求</td><td>接口范围</td><td>${m.endpoints.length} 个接口</td></tr><tr><td>测试工具</td><td>JMeter / Newman / pytest / Apifox</td><td>数据源</td><td>MySQL、Redis 只读取证据</td></tr><tr><td>性能模型</td><td>${esc((data.execution_profile?.performance||{}).profile||'smoke')}</td><td>敏感信息</td><td>运行时使用，报告脱敏</td></tr></tbody></table></div>${typeof traceCoverageHtml==='function'?traceCoverageHtml():''}`}
  if(kind==='cases'){title='测试用例';html=`${blockedCaseSummary()}${assertionTable(m.assertions,'暂无已执行断言')}<div class="card"><button class="primary" onclick="showTestCasesModal()">查看全部用例</button> <button class="small" onclick="showTestPointsModal()">查看测试点</button></div>`}
  if(kind==='execution'){title='执行记录';html=m.runs.length?`<div class="card"><table><thead><tr><th>时间</th><th>用例</th><th>状态</th><th>HTTP</th><th>耗时</th></tr></thead><tbody>${m.runs.slice(0,300).map(x=>`<tr><td>${esc((x.executed_at||x.created_at||'').replace('T',' '))}</td><td>${esc(x.case_title||x.name||'-')}</td><td>${deliveryStatusTag(x.status,x.status)}</td><td>${esc(x.http_status??'-')}</td><td>${esc(x.duration_ms??'-')}ms</td></tr>`).join('')}</tbody></table></div>`:'<div class="card empty"><b>暂无执行记录</b></div>'}
  if(kind==='risk'){title='缺陷风险';html=`${assertionTable(m.failed,'当前没有失败断言')}${m.perfFindings.length?`<div class="card"><h2>性能风险</h2><div class="gap-list">${m.perfFindings.map(x=>`<div class="gap-item ${x.severity==='P0'?'P0':'P1'}"><span class="tag ${x.severity==='P0'?'FAILED':'P1'}">${esc(x.severity)}</span><div><b>${esc(x.title)}</b><p>${esc(x.detail)}</p></div></div>`).join('')}</div></div>`:''}`}
  if(kind==='report'){title='测试报告';html=`<div class="card"><h2>正式报告清单</h2>${m.reports.length?`<table><thead><tr><th>生成时间</th><th>报告</th><th>状态</th><th>摘要</th><th>操作</th></tr></thead><tbody>${m.reports.map(x=>`<tr><td>${esc((x.created_at||'').replace('T',' '))}</td><td><b>${esc(x.name)}</b><br><small>${esc(x.kind)} · ${esc(x.file_name)}</small></td><td>${deliveryStatusTag(x.status,x.status)}</td><td>${esc(x.summary)}</td><td>${x.html_url?`<button class="small" onclick="openReport('${esc(x.html_url)}')">HTML</button> `:''}${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">JSON</button>`:''}</td></tr>`).join('')}</tbody></table>`:'<div class="empty"><b>暂无正式报告</b></div>'}</div>${performanceReportListHtml()}`}
  if(kind==='evidence'){title='原始证据';html=`${fullEvidenceAuditHtml().replace('enterprise-report-view hidden','')}${tableReports()}`}
  $('#modalBody').innerHTML=`<h2>${esc(title)}</h2>${html}`;
  $('#modal').classList.remove('hidden')
}

async function autoEvidenceCheck(){
  let box=$('#evidenceAutoStatus');
  try{
    if(box)box.innerHTML='<div class="summary-panel"><b>正在自动核查</b><p>平台会按需匹配接口、MySQL候选表与Redis Key，并以只读方式执行可运行规则。</p></div>';
    toast('正在自动调用证据连接器…');
    let matched={};
    try{matched=await api(`/api/projects/${current}/auto-match-data`,{method:'POST',body:'{}'})}catch(e){matched={warning:e.message}}
    let generated=await api(`/api/projects/${current}/generate-consistency`,{method:'POST',body:'{}'});
    let executed=await api(`/api/projects/${current}/consistency/run-ready`,{method:'POST',body:JSON.stringify({scope:'all',limit:10})});
    let msg=`自动核查完成：${executed.status}，通过${executed.passed||0}，阻断${executed.blocked||0}，失败${executed.failed||0}`;
    if(box)box.innerHTML=`<div class="summary-panel"><b>${esc(msg)}</b><p>匹配Redis Key ${esc(matched.redis_mappings??0)} 条；生成规则 ${esc((generated.generated||{}).rules??0)} 条。${matched.warning?` ${esc(matched.warning)}`:''}</p></div>`;
    toast(msg,executed.status==='PASSED'?'success':executed.status==='FAILED'?'error':'warning');
    await refreshConsistency();
  }catch(e){
    if(box)box.innerHTML=`<div class="summary-panel"><b>自动核查未完成</b><p>${esc(e.message)}</p></div>`;
    toast(e.message,'error')
  }
}
function showConnectorDetailModal(){
  let db=(data.db_tables||[]),maps=(data.mappings||[]),redis=data.redis_sources||[],redisMaps=data.redis_mappings||[],rules=((data.consistency||{}).rules||[]),runs=((data.consistency||{}).runs||[]);
  $('#modalBody').innerHTML=`<h2>证据连接器明细</h2><p class="policy-note">这些只是外部证据源配置和摘要，默认不进入主工作台。执行数据核查时才会被平台只读调用。</p><div class="metrics"><div class="metric"><span>MySQL表结构</span><b>${db.length}</b></div><div class="metric"><span>接口表映射</span><b>${maps.length}</b></div><div class="metric"><span>Redis连接</span><b>${redis.filter(x=>x.status==='connected').length}/${redis.length}</b></div><div class="metric"><span>验证规则/记录</span><b>${rules.length}/${runs.length}</b></div></div><h3>工资交易候选表</h3><div class="evidence-list">${db.filter(x=>String(x.table_name||'').includes('salary_trade')).map(x=>`<div class="evidence-item"><b>${esc(x.table_name)}</b><small>${esc(x.table_comment||'')}</small></div>`).join('')||'<div class="empty">未识别到 salary_trade 相关表</div>'}</div><h3>最近核查记录</h3>${runs.length?`<table><thead><tr><th>状态</th><th>接口</th><th>时间</th></tr></thead><tbody>${runs.slice(0,20).map(x=>`<tr><td><span class="tag ${esc(x.status)}">${esc(x.status)}</span></td><td><code>${esc(x.path||'-')}</code></td><td>${esc(x.created_at||'')}</td></tr>`).join('')}</tbody></table>`:'<div class="empty">尚无自动核查记录</div>'}`;
  $('#modal').classList.remove('hidden')
}
dataQualityClosure=function(){
  let pack=data.consistency||{},rules=pack.rules||[],runs=pack.runs||[],summary=pack.summary||{},db=(data.db_tables||[]),maps=(data.mappings||[]),redis=data.redis_sources||[],redisReady=redis.some(x=>x.status==='connected'),salaryTables=db.filter(x=>String(x.table_name||'').includes('salary_trade')).length,latest=runs[0];
  return `<div class="card quality-hero"><span class="tag">EVIDENCE CONNECTORS</span><h2>证据连接</h2><p>工作台不常驻展示数据库和Redis明细。需要核查数据时，由平台自动调起只读连接器，完成接口返回、表结构/业务行、缓存快照的证据归档。</p><div class="quality-flow">${[['MySQL连接器',db.length,db.length?`${db.length}张表结构 · 工资交易${salaryTables}张`:'按需接入'],['Redis连接器',redisReady,redisReady?'已连接，可只读取证':'按需连接'],['自动核查',rules.length||runs.length,`${rules.length}条规则 · ${runs.length}次记录`],['报告归档',true,'只展示结论，明细进报告中心']].map(x=>`<div class="quality-step ${x[1]?'':'pending'}">${hubStatus(x[1])}<b>${x[0]}</b><small>${esc(x[2])}</small></div>`).join('')}</div></div><div class="card"><div class="diagnosis-head"><div><h2>自动数据核查</h2><p>执行时才调用 MySQL / Redis：先匹配候选证据，再只读查询或读取快照，最后把结论写入报告。</p></div><button class="primary" onclick="autoEvidenceCheck()">自动核查数据</button></div><div class="metrics"><div class="metric"><span>MySQL候选</span><b>${maps.length}</b></div><div class="metric"><span>Redis状态</span><b style="font-size:20px">${redisReady?'可调用':'未连接'}</b></div><div class="metric"><span>核查状态</span><b style="font-size:20px">${esc(summary.status||'PENDING')}</b></div><div class="metric"><span>执行记录</span><b>${runs.length}</b></div></div><div id="evidenceAutoStatus">${latest?`<div class="summary-panel"><b>最近核查：${esc(latest.status)}</b><p>${esc(latest.path||'')} · ${esc(latest.created_at||'')}</p></div>`:''}</div><div class="formrow"><button class="small" onclick="showConnectorDetailModal()">查看连接器明细</button><button class="small" onclick="switchTab('reports')">查看归档报告</button></div></div><div class="card"><h2>连接器原则</h2><div class="closure-row"><b>默认隐藏明细</b><p>表、Key、字段映射不铺在主工作台，只在自动核查或排错时展开。</p><span class="tag PASSED">收敛</span></div><div class="closure-row"><b>只读调用</b><p>MySQL 用 SELECT/SHOW/DESCRIBE/EXPLAIN；Redis 只允许读取和扫描类命令。</p><span class="tag PASSED">安全</span></div><div class="closure-row"><b>按需取证</b><p>普通接口测试不强制核库；涉及订单状态、金额、流水、缓存一致性时才自动调用。</p><span class="tag PASSED">按需</span></div></div>`
}
connectorOverviewPanel=function(){
  let db=(data.db_tables||[]).length,maps=(data.mappings||[]).length,redis=(data.redis_sources||[]),redisReady=redis.some(x=>x.status==='connected'),rules=((data.consistency||{}).rules||[]).length;
  return `<div class="card"><div class="diagnosis-head"><div><h2>外部连接器</h2><p>它们是平台的四肢，不是工作台主体。主流程只保留任务和结论，需要执行时才调起外部软件或只读数据源。</p></div><span class="tag PASSED">按需调起</span></div><div class="endpoint-matrix"><div class="endpoint-card"><span class="tag PASSED">接口协同</span><h3>Apifox</h3><p>导入企业接口基线，生成pytest基础层并执行发布冒烟。</p><button class="small" onclick="showApifoxEnterpriseFlow()">进入企业链路</button></div><div class="endpoint-card"><span class="tag PASSED">性能执行</span><h3>JMeter</h3><p>平台生成 JMX、打开 GUI、回收报告，不在工作台重做 JMeter。</p><button class="small" onclick="showJmeterScriptChooser()">选择脚本</button></div><div class="endpoint-card"><span class="tag ${db?'PASSED':'P1'}">数据取证</span><h3>MySQL / Redis</h3><p>${db||redisReady?`MySQL ${db} 张表 · ${maps}条候选 · Redis ${redisReady?'可调用':'按需'}`:'需要数据证据时再接入'}</p><button class="small" onclick="switchTab('dataquality')">自动核查</button></div></div></div>`
}
tableTaskCommandCenter=function(){let req=(data.requirement_items||[]).length,eps=(data.endpoints||[]).length,cases=(data.cases||[]).length,flows=(data.workflows||[]).length,latest=wealthLastResult||data.wealth_latest||{},hasReport=latest&&Object.keys(latest).length;return `<div class="card" style="background:linear-gradient(135deg,#123d2b,#24704e);color:white"><span style="color:var(--lime);font-size:11px">AI TEST ORCHESTRATION</span><h2 style="font-size:28px;margin:10px 0 6px">从需求到报告，只在这里操作</h2><p style="color:#c9ded3">主干只保留资料接入、AI生成、链路确认、外部工具执行和报告输出；数据源按需自动取证。</p><div class="grid2" style="margin-top:20px"><button class="card" style="text-align:left;cursor:pointer" onclick="switchTab('sources')"><b>① 导入需求与接口</b><br><small>${req}条需求 · ${eps}个接口<br>上传需求文档、图文链接和OpenAPI</small></button><button class="card" style="text-align:left;cursor:pointer" onclick="switchTab('points')"><b>② 查看AI测试资产</b><br><small>${cases}条用例<br>检查测试点、预期结果和覆盖缺口</small></button><button class="card" style="text-align:left;cursor:pointer" onclick="switchTab('flows')"><b>③ 确认跨接口链路</b><br><small>${flows}条业务链路<br>核对登录、变量提取和下游接口</small></button><button class="card" style="text-align:left;cursor:pointer" onclick="switchTab('automation')"><b>④ 执行并归档报告</b><br><small>调起外部工具；需要时自动调用只读数据证据</small></button></div><div style="margin-top:16px"><button class="primary" onclick="switchTab('sources')">开始测试任务</button> <button class="small" onclick="switchTab('dataquality')">自动核查数据</button> ${hasReport?`<button class="small" onclick="switchTab('reports')">查看报告</button>`:''}</div></div>`}

function trunkMaturity(){
  let checks=[
    (data.sources||[]).length,
    (data.requirement_items||[]).length,
    (data.endpoints||[]).length,
    (data.cases||[]).some(x=>x.method&&x.path),
    (data.workflows||[]).length,
    (data.automation_suites||[]).length||(data.performance_plans||[]).length,
    (data.generated_reports||[]).length
  ];
  return Math.round(checks.filter(Boolean).length/checks.length*100)
}
qualityHubMaturity=trunkMaturity;
professionalLabels=function(){
  let labels={overview:'质量总览',sources:'需求资产',dataquality:'证据连接',automation:'执行中心',reports:'报告中心'};
  $$('.tabs button,.side-tab').forEach(b=>{if(labels[b.dataset.tab])b.textContent=labels[b.dataset.tab]});
  let runAllBtn=$('.toolbar .primary');if(runAllBtn)runAllBtn.textContent='启动生成流程'
}
function connectorOverviewPanel(){
  let db=(data.db_tables||[]).length,maps=(data.mappings||[]).length,redis=(data.redis_sources||[]),redisReady=redis.some(x=>x.status==='connected'),rules=((data.consistency||{}).rules||[]).length;
  return `<div class="card"><div class="diagnosis-head"><div><h2>外部连接器</h2><p>这些不是工作台主体，只在需要时被平台调起：接口基线和发布冒烟来自 Apifox，压测交给 JMeter，数据核对交给只读 MySQL/Redis。</p></div><span class="tag PASSED">按需启用</span></div><div class="endpoint-matrix"><div class="endpoint-card"><span class="tag PASSED">接口协同</span><h3>Apifox</h3><p>导入OpenAPI生成pytest基础层，执行CLI发布冒烟。</p><button class="small" onclick="showApifoxEnterpriseFlow()">进入企业链路</button></div><div class="endpoint-card"><span class="tag PASSED">性能执行</span><h3>JMeter</h3><p>生成可维护 JMX，打开真实 JMeter，回收 JTL/HTML 报告。</p><button class="small" onclick="showJmeterScriptChooser()">选择脚本</button></div><div class="endpoint-card"><span class="tag ${db?'PASSED':'P1'}">只读</span><h3>MySQL</h3><p>${db?`${db} 张表结构 · ${maps} 条候选映射`:'需要核对状态、金额、流水时再接入 Schema'}</p><button class="small" onclick="switchTab('dataquality')">查看</button></div><div class="endpoint-card"><span class="tag ${redisReady?'PASSED':'P1'}">只读</span><h3>Redis</h3><p>${redisReady?'已连接，只读取 Key 快照':'需要缓存证据时再连接，不作为必填项'}</p><button class="small" onclick="switchTab('dataquality')">查看</button></div></div></div>`
}
tableQualityHub=function(){
  let req=(data.requirement_items||[]).length,points=(data.points||[]).length,cases=(data.cases||[]).length,endpoints=(data.endpoints||[]).length,workflows=(data.workflows||[]).length,reports=(data.generated_reports||[]).length,maturity=trunkMaturity();
  let executable=(data.cases||[]).filter(x=>x.method&&x.path).length;
  let steps=[['需求资产',req||points,`${req}条需求 · ${points}个测试点`,'sources'],['接口与用例',endpoints||cases,`${endpoints}个接口 · ${cases}条用例 · ${executable}条可执行`,'sources'],['执行编排',workflows,`${workflows}条流程 · 外部工具按需调起`,'automation'],['报告交付',reports,`${reports}份报告与原始证据`,'reports']];
  return `<div class="card quality-hero"><span class="tag">QUALITY HUB</span><h2>质量中枢</h2><p>工作台只保留主干：理解需求、沉淀接口与用例、编排外部工具执行、归档报告证据。数据库、Redis、JMeter、Apifox 都作为连接器按需接入。</p><div class="quality-flow">${steps.map(x=>`<button class="quality-step ${x[1]?'':'pending'}" onclick="switchTab('${x[3]}')">${hubStatus(x[1])}<b>${x[0]}</b><small>${esc(x[2])}</small></button>`).join('')}</div></div>${qualityProfilePanel()}${aiControlPlanePanel()}${gapDiagnosisPanel(5)}${connectorOverviewPanel()}<div class="closure-grid"><div class="card"><h2>主干能力</h2>${[['需求理解','需求、图片、接口文档、HAR 被统一沉淀成可追踪资产'],['测试设计','测试点、测试用例、接口覆盖和业务链路统一归纳'],['执行编排','平台生成脚本并调起外部标准工具，不自己冒充测试工具'],['报告交付','结果、风险、性能和原始证据集中归档']].map(x=>`<div class="closure-row"><b>${x[0]}</b><p>${x[1]}</p><span class="tag PASSED">主干</span></div>`).join('')}</div><div class="card"><div class="maturity-score"><div><b>${maturity}%</b><span>主干成熟度</span></div></div><div class="tool-badges"><span>需求</span><span>接口</span><span>用例</span><span>执行</span><span>报告</span></div></div></div>`
}
enterpriseDirectory=function(){
  return `<div class="card"><h2>工作区结构</h2><div class="directory-grid">${[['需求资产','资料、接口、测试点、测试用例、覆盖关系统一归纳','进入','sources'],['执行中心','生成脚本、调起外部工具、执行链路和回收报告','进入','automation'],['证据连接','MySQL、Redis、后台配置等只读证据源按需接入','进入','dataquality'],['报告中心','方案、用例、执行、风险、报告和原始证据集中交付','进入','reports']].map(x=>`<div class="directory-card"><h3>${x[0]}</h3><p>${x[1]}</p><button class="small" onclick="switchTab('${x[3]}')">${x[2]}</button></div>`).join('')}</div></div>`
}
dataQualityClosure=function(){
  let pack=data.consistency||{},rules=pack.rules||[],runs=pack.runs||[],db=(data.db_tables||[]).length,maps=(data.mappings||[]).length,redis=data.redis_sources||[],redisReady=redis.some(x=>x.status==='connected'),snap=(data.redis_snapshots||[]).length;
  return `<div class="card quality-hero"><span class="tag">EVIDENCE CONNECTORS</span><h2>证据连接</h2><p>这里不是主流程页面，只负责在需要时连接外部证据源。MySQL 和 Redis 均只读；没有数据核对要求的接口，不强制映射。</p><div class="quality-flow">${[['MySQL只读',db,db?`${db}张表结构 · ${maps}条映射`:'按需导入Schema'],['Redis只读',redisReady,redisReady?`${redis.length}个连接 · ${snap}份快照`:'按需连接Key证据'],['验证规则',rules.length,`${rules.length}条规则 · ${runs.length}次执行`],['本地归档',true,'规则、快照、结论只写平台本地库']].map(x=>`<div class="quality-step ${x[1]?'':'pending'}">${hubStatus(x[1])}<b>${x[0]}</b><small>${esc(x[2])}</small></div>`).join('')}</div></div><div class="closure-grid"><div class="card"><h2>按需接入原则</h2><div class="closure-row"><b>接口测试</b><p>优先按接口文档和运行参数执行，不要求数据库/Redis 映射。</p><span class="tag PASSED">主干</span></div><div class="closure-row"><b>业务数据核对</b><p>涉及状态、金额、余额、订单流水、缓存一致性时，再选择表和Key做只读证据。</p><span class="tag P1">增强</span></div><div class="closure-row"><b>外部数据安全</b><p>平台不提供写入公司 MySQL/Redis 的入口，只保存本地证据摘要和报告。</p><span class="tag PASSED">只读</span></div></div><div>${tableEvidenceCenter()}</div></div>${rules.length?tableConsistency():''}`
}

function dataEvidenceStatus(){
  let redisReady=(data.redis_sources||[]).some(x=>x.status==='connected');
  let mysql=data.mysql_status||data.environment_config?.data_sources?.mysql_live||{};
  let dbReady=(data.db_tables||[]).length>0||mysql.status==='CONFIGURED'||mysql.status==='CONNECTED';
  let runs=((data.consistency||{}).runs||[]),latest=runs[0];
  return {redisReady,dbReady,runs,latest,mysql}
}
function mysqlEvidencePanel(){
  let s=dataEvidenceStatus(),m=s.mysql||{},configured=m.status==='CONFIGURED'||m.status==='CONNECTED';
  return `<div class="card"><div class="diagnosis-head"><div><h2>MySQL 只读查询</h2><p>真实连接测试库，用于核查订单、金额、状态、流水等业务证据。密码只从本机配置读取，不显示在页面。</p></div><span class="tag ${configured?'PASSED':'P1'}">${configured?'已配置':'待配置'}</span></div><div class="metrics"><div class="metric"><span>Host</span><b style="font-size:18px">${esc(m.host||'-')}</b></div><div class="metric"><span>Database</span><b style="font-size:18px">${esc(m.database||'-')}</b></div><div class="metric"><span>User</span><b style="font-size:18px">${esc(m.user||'-')}</b></div><div class="metric"><span>模式</span><b style="font-size:18px">只读</b></div></div><div class="formrow"><button class="small" onclick="testMysqlConnection()">测试连接</button><button class="small" onclick="importMysqlSchemaLive()">读取Schema</button></div><h3>工资交易DB证据</h3><div class="grid2"><div><label>订单号</label><input id="salaryEvidenceOrderNo" placeholder="可空：为空时按账号查最新订单"><label>申请人UID</label><input id="salaryEvidenceApplicantUid" value="1454696"><label>代理UID</label><input id="salaryEvidenceProxyUid" value="1454097"></div><div><label>国家 / 币种</label><div class="formrow"><input id="salaryEvidenceCountry" value="MA"><input id="salaryEvidenceCurrency" value="USD"></div><label>预期最终状态</label><input id="salaryEvidenceExpectedStatus" placeholder="例如 50 / 80 / 90"><label>预期日志状态</label><input id="salaryEvidenceLogStatuses" placeholder="例如 10,50 或 10,20,30,40"></div></div><label><input id="salaryEvidenceExpectEvidence" type="checkbox" style="width:auto"> 本流程应产生投诉/凭证 evidence</label><button class="primary" onclick="runSalaryTradeDbEvidence()">核查工资交易DB证据</button><div id="salaryDbEvidenceResult"></div><label>只读SQL</label><textarea id="mysqlReadonlySql" rows="5" placeholder="SELECT * FROM anchor_salary_trade_order WHERE uid = 1454696 ORDER BY id DESC"></textarea><div class="formrow"><input id="mysqlReadonlyLimit" type="number" value="100" min="1" max="500"><button class="small" onclick="runMysqlReadonlyQuery()">执行只读查询</button></div><div id="mysqlQueryResult"></div></div>`
}
async function testMysqlConnection(){
  try{
    toast('正在测试 MySQL 只读连接…');
    let x=await api(`/api/projects/${current}/mysql/test`,{method:'POST',body:'{}'});
    data.mysql_status=x;
    toast(`MySQL连接成功：${x.duration_ms||0}ms`,'success');
    render();switchTab('dataquality')
  }catch(e){toast(e.message,'error')}
}
async function importMysqlSchemaLive(){
  try{
    toast('正在从 MySQL 读取表结构…');
    let x=await api(`/api/projects/${current}/mysql/import-schema-live`,{method:'POST',body:'{}'});
    toast(`已读取 ${x.tables||0} 张表，建立 ${x.mappings||0} 条候选映射`,'success');
    await openProject(current);switchTab('dataquality')
  }catch(e){toast(e.message,'error')}
}
async function runMysqlReadonlyQuery(){
  let sql=$('#mysqlReadonlySql')?.value.trim()||'',limit=+($('#mysqlReadonlyLimit')?.value||100),box=$('#mysqlQueryResult');
  if(!sql)return toast('先填写一条 SELECT / SHOW / DESCRIBE / EXPLAIN','warning');
  if(box)box.innerHTML='<div class="summary-panel"><b>正在查询</b><p>只会执行只读SQL。</p></div>';
  try{
    let x=await api(`/api/projects/${current}/mysql/query`,{method:'POST',body:JSON.stringify({sql,limit})});
    let cols=x.columns||[],rows=x.rows||[];
    if(box)box.innerHTML=`<div class="summary-panel"><b>查询完成：${x.row_count} 行 · ${x.duration_ms}ms</b><p><code>${esc(x.sql)}</code></p></div>${rows.length?`<div style="overflow:auto;max-height:420px"><table><thead><tr>${cols.map(c=>`<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${rows.slice(0,100).map(r=>`<tr>${cols.map(c=>`<td>${esc(r[c])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`:'<div class="empty">没有返回数据</div>'}`;
    toast('MySQL只读查询完成','success')
  }catch(e){
    if(box)box.innerHTML=`<div class="summary-panel"><b>查询被拦截或失败</b><p>${esc(e.message)}</p></div>`;
    toast(e.message,'error')
  }
}
async function runSalaryTradeDbEvidence(){
  let box=$('#salaryDbEvidenceResult');
  let statuses=($('#salaryEvidenceLogStatuses')?.value||'').split(/[,，\s]+/).map(x=>x.trim()).filter(Boolean).map(Number).filter(x=>!Number.isNaN(x));
  let expected=$('#salaryEvidenceExpectedStatus')?.value.trim();
  let payload={
    order_no:$('#salaryEvidenceOrderNo')?.value.trim()||'',
    applicant_uid:$('#salaryEvidenceApplicantUid')?.value.trim()||'',
    proxy_uid:$('#salaryEvidenceProxyUid')?.value.trim()||'',
    country_code:$('#salaryEvidenceCountry')?.value.trim()||'',
    currency:$('#salaryEvidenceCurrency')?.value.trim()||'',
    expected_status:expected?Number(expected):'',
    expected_log_statuses:statuses,
    expect_evidence:$('#salaryEvidenceExpectEvidence')?.checked||false
  };
  if(box)box.innerHTML='<div class="summary-panel"><b>正在核查工资交易DB证据</b><p>平台将只读查询订单主表、日志表、凭证表和代理白名单。</p></div>';
  try{
    let x=await api(`/api/projects/${current}/salary-trade/db-evidence`,{method:'POST',body:JSON.stringify(payload)});
    let s=x.summary||{};
    if(box)box.innerHTML=`<div class="summary-panel"><b>${esc(x.status)} · 订单 ${esc(x.order_no)}</b><p>断言 ${s.assertions_passed||0}/${s.assertions_total||0} · 日志 ${s.log_rows||0} · 凭证 ${s.evidence_rows||0} · 白名单 ${s.whitelist_rows||0}</p>${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">查看报告</button>`:''}</div>`;
    toast(`工资交易DB核查完成：${x.status}`,x.status==='PASSED'?'success':'error');
    await openProject(current);switchTab('dataquality')
  }catch(e){
    if(box)box.innerHTML=`<div class="summary-panel"><b>核查失败</b><p>${esc(e.message)}</p></div>`;
    toast(e.message,'error')
  }
}
async function autoEvidenceCheck(){
  let box=$('#evidenceAutoStatus');
  try{
    if(box)box.innerHTML='<div class="summary-panel"><b>正在自动核查</b><p>平台会按当前接口、参数和需求语义，在后台选择只读数据源并执行核查；表名和Key不作为工作台固定配置维护。</p></div>';
    toast('正在自动调用只读数据证据…');
    try{await api(`/api/projects/${current}/auto-match-data`,{method:'POST',body:'{}'})}catch{}
    await api(`/api/projects/${current}/generate-consistency`,{method:'POST',body:'{}'});
    let executed=await api(`/api/projects/${current}/consistency/run-ready`,{method:'POST',body:JSON.stringify({scope:'all',limit:10})});
    let msg=`自动核查完成：${executed.status}，通过${executed.passed||0}，阻断${executed.blocked||0}，失败${executed.failed||0}`;
    if(box)box.innerHTML=`<div class="summary-panel"><b>${esc(msg)}</b><p>本次实际使用的数据位置会写入报告证据，工作台只保留结论和追溯入口。</p></div>`;
    toast(msg,executed.status==='PASSED'?'success':executed.status==='FAILED'?'error':'warning');
    await refreshConsistency();
  }catch(e){
    if(box)box.innerHTML=`<div class="summary-panel"><b>自动核查未完成</b><p>${esc(e.message)}</p></div>`;
    toast(e.message,'error')
  }
}
function showConnectorDetailModal(){
  let s=dataEvidenceStatus(),rules=((data.consistency||{}).rules||[]),runs=s.runs;
  $('#modalBody').innerHTML=`<h2>数据核查策略</h2><p class="policy-note">不在工作台维护固定表名或Key清单。每次执行时，平台根据接口路径、请求参数、响应字段、需求语义和已有只读连接动态选择证据位置；本次查了哪里只进入报告证据。</p><div class="metrics"><div class="metric"><span>关系库证据</span><b>${s.dbReady?'可调用':'按需接入'}</b></div><div class="metric"><span>缓存证据</span><b>${s.redisReady?'可调用':'按需接入'}</b></div><div class="metric"><span>策略状态</span><b>${rules.length?'已生成':'待生成'}</b></div><div class="metric"><span>核查记录</span><b>${runs.length}</b></div></div><div class="card"><h2>运行时怎么找</h2><div class="closure-row"><b>先看需求</b><p>判断是否真的需要数据核查：状态、金额、余额、流水、缓存一致性才触发。</p><span class="tag PASSED">自动</span></div><div class="closure-row"><b>再看接口</b><p>从路径、参数、响应字段和链路变量推断本次证据来源。</p><span class="tag PASSED">动态</span></div><div class="closure-row"><b>最后取证</b><p>只读查询并保存摘要，报告里说明本次实际核查位置和结论。</p><span class="tag PASSED">可追溯</span></div></div><h3>最近核查</h3>${runs.length?`<table><thead><tr><th>状态</th><th>对象</th><th>时间</th></tr></thead><tbody>${runs.slice(0,20).map(x=>`<tr><td><span class="tag ${esc(x.status)}">${esc(x.status)}</span></td><td>${esc(x.path||'业务接口')}</td><td>${esc(x.created_at||'')}</td></tr>`).join('')}</tbody></table>`:'<div class="empty">尚无自动核查记录</div>'}`;
  $('#modal').classList.remove('hidden')
}
dataQualityClosure=function(){
  let s=dataEvidenceStatus(),summary=(data.consistency||{}).summary||{},rules=((data.consistency||{}).rules||[]);
  return `<div class="card quality-hero"><span class="tag">EVIDENCE ON DEMAND</span><h2>数据证据</h2><p>平台不固定展示表名、Key或映射清单。需要数据核查时，后台自动判断去哪查、怎么查，并把本次实际取证位置写入报告。</p><div class="quality-flow">${[['关系库证据',s.dbReady,'可按需只读查询'],['缓存证据',s.redisReady,'可按需读取快照'],['核查策略',rules.length,rules.length?'已可自动执行':'待按需求生成'],['报告追溯',s.runs.length,s.runs.length?'已有核查记录':'执行后归档']].map(x=>`<div class="quality-step ${x[1]?'':'pending'}">${hubStatus(x[1])}<b>${x[0]}</b><small>${esc(x[2])}</small></div>`).join('')}</div></div><div class="closure-grid"><div><div class="card"><div class="diagnosis-head"><div><h2>自动核查数据</h2><p>不需要你在工作台维护表和Key。点击后平台按本次测试目标动态选择只读证据源，完成后只返回结论。</p></div><button class="primary" onclick="autoEvidenceCheck()">自动核查</button></div><div class="metrics"><div class="metric"><span>核查状态</span><b style="font-size:20px">${esc(summary.status||'PENDING')}</b></div><div class="metric"><span>关系库</span><b>${s.dbReady?'可调用':'未接入'}</b></div><div class="metric"><span>缓存</span><b>${s.redisReady?'可调用':'未接入'}</b></div><div class="metric"><span>记录</span><b>${s.runs.length}</b></div></div><div id="evidenceAutoStatus">${s.latest?`<div class="summary-panel"><b>最近核查：${esc(s.latest.status)}</b><p>本次取证位置已归档到报告，不作为页面固定配置。</p></div>`:''}</div><div class="formrow"><button class="small" onclick="showConnectorDetailModal()">查看核查策略</button><button class="small" onclick="switchTab('reports')">查看报告证据</button></div></div>${mysqlEvidencePanel()}</div><div class="card"><h2>为什么不写死</h2><div class="closure-row"><b>业务会变</b><p>新需求可能新增表、换字段、拆缓存，固定清单会很快失效。</p><span class="tag PASSED">动态</span></div><div class="closure-row"><b>平台只做编排</b><p>工作台保存策略、运行记录和报告，不让测试人员长期维护底层数据位置。</p><span class="tag PASSED">中枢</span></div><div class="closure-row"><b>报告可追溯</b><p>只有每次执行产生的报告，才记录本次实际查询的数据来源和结果。</p><span class="tag PASSED">证据</span></div></div></div>`
}
connectorOverviewPanel=function(){
  let s=dataEvidenceStatus();
  return `<div class="card"><div class="diagnosis-head"><div><h2>外部连接器</h2><p>它们是平台的四肢：接口真相、性能执行、数据取证都在需要时调起；工作台不重复维护企业工具资产。</p></div><span class="tag PASSED">按需调起</span></div><div class="endpoint-matrix"><div class="endpoint-card"><span class="tag PASSED">接口协同</span><h3>Apifox</h3><p>读取企业OpenAPI并运行发布冒烟，平台负责pytest和报告。</p><button class="small" onclick="showApifoxEnterpriseFlow()">进入企业链路</button></div><div class="endpoint-card"><span class="tag PASSED">性能执行</span><h3>JMeter</h3><p>平台生成 JMX、打开 GUI、回收报告，不在工作台重做 JMeter。</p><button class="small" onclick="showJmeterScriptChooser()">选择脚本</button></div><div class="endpoint-card"><span class="tag ${(s.dbReady||s.redisReady)?'PASSED':'P1'}">数据取证</span><h3>只读数据源</h3><p>需要核查时自动选择证据位置，结果进入报告。</p><button class="small" onclick="switchTab('dataquality')">自动核查</button></div></div></div>`
}

function latestEvidenceReports(){
  return (data.generated_reports||[]).filter(x=>x.kind==='数据核查').slice(0,5)
}
function showManualEvidenceCheckModal(){
  let eps=data.endpoints||[];
  $('#modalBody').innerHTML=`<h2>指定数据核查</h2><p class="policy-note">你可以直接指定本次要查的表、字段、Key和条件。平台按只读策略取值，并把结果作为运行变量注入接口和JMeter。</p><div class="card"><label>核查目标</label><textarea id="manualEvidenceTarget" rows="3" placeholder="例如：订单状态流转、金额扣减、流水记录、缓存一致性"></textarea><label>关联接口</label><select id="manualEvidenceEndpoint"><option value="">不指定，由平台按需求判断</option>${eps.map(ep=>`<option value="${esc(ep.id)}">${esc((ep.method||'GET')+' '+(ep.path||''))}</option>`).join('')}</select><label>表名线索</label><textarea id="manualEvidenceTables" rows="3" placeholder="一行一个，例如 salary_trade_order、salary_account"></textarea><label>Redis Key线索</label><textarea id="manualEvidenceRedis" rows="3" placeholder="可选，支持写完整Key或业务关键词"></textarea><label>变量取数规则</label><textarea id="manualEvidenceBindings" rows="5" placeholder="一行一个：applicant_uid = salary_user.uid where country_code='EG' and role='applicant'\nproxy_uid = salary_agent.uid where country_code='EG' and status=1\norder_no = redis:salary:order:{uid} field orderNo\ncurrency = value:EGP"></textarea><label>补充说明</label><textarea id="manualEvidenceNote" rows="2" placeholder="可选，例如本次重点看申请人、代理人、投诉流转或结算结果"></textarea><div class="formrow"><button id="manualEvidenceButton" class="primary" onclick="runManualEvidenceCheck()">发起核查</button><button class="small" onclick="$('#modal').classList.add('hidden')">取消</button></div><div id="manualEvidenceResult"></div></div>`;
  $('#modal').classList.remove('hidden')
}
async function runManualEvidenceCheck(){
  let target=$('#manualEvidenceTarget')?.value.trim()||'',button=$('#manualEvidenceButton'),box=$('#manualEvidenceResult');
  if(!target)return toast('先写本次要核查什么，比如订单状态、金额或流水','warning');
  if(button){button.disabled=true;button.textContent='正在发起核查…'}
  if(box)box.innerHTML='<div class="summary-panel"><b>正在生成本次核查任务</b><p>平台会按只读策略记录核查计划和证据报告。</p></div>';
  try{
    let result=await api(`/api/projects/${current}/evidence-check`,{method:'POST',body:JSON.stringify({target,endpoint_id:$('#manualEvidenceEndpoint')?.value||'',table_hints:$('#manualEvidenceTables')?.value||'',redis_hints:$('#manualEvidenceRedis')?.value||'',variable_bindings:$('#manualEvidenceBindings')?.value||'',note:$('#manualEvidenceNote')?.value||''})});
    if(box)box.innerHTML=`<div class="summary-panel"><b>${esc(result.status)}：${esc(result.target)}</b><p>候选表 ${esc((result.matched_tables||[]).length)} 个，变量规则 ${esc(result.runtime_injection?.binding_count||0)} 条，提醒 ${esc((result.blockers||[]).length)} 项。报告已归档。</p>${result.json_url?`<button class="small" onclick="openReport('${esc(result.json_url)}')">查看JSON</button>`:''}</div>`;
    toast('指定核查任务已归档','success');
    await openProject(current);
    switchTab('dataquality')
  }catch(e){
    if(box)box.innerHTML=`<div class="summary-panel"><b>发起失败</b><p>${esc(e.message)}</p></div>`;
    toast(e.message,'error')
  }finally{
    let b=$('#manualEvidenceButton');if(b){b.disabled=false;b.textContent='发起核查'}
  }
}
showConnectorDetailModal=function(){
  let s=dataEvidenceStatus(),reports=latestEvidenceReports();
  $('#modalBody').innerHTML=`<h2>核查记录</h2><p class="policy-note">这里只看任务和报告，不维护固定表清单。需要排错时，再打开单次报告看平台本次实际参考的线索和取证计划。</p><div class="metrics"><div class="metric"><span>关系库</span><b>${s.dbReady?'可调用':'按需接入'}</b></div><div class="metric"><span>缓存</span><b>${s.redisReady?'可调用':'按需接入'}</b></div><div class="metric"><span>自动记录</span><b>${s.runs.length}</b></div><div class="metric"><span>指定核查</span><b>${reports.length}</b></div></div>${reports.length?`<table><thead><tr><th>时间</th><th>状态</th><th>摘要</th><th>操作</th></tr></thead><tbody>${reports.map(x=>`<tr><td>${esc((x.created_at||'').replace('T',' '))}</td><td><span class="tag ${esc(x.status)}">${esc(x.status)}</span></td><td>${esc(x.summary||'')}</td><td>${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">查看</button>`:''}</td></tr>`).join('')}</tbody></table>`:'<div class="empty"><b>暂无指定核查报告</b></div>'}`;
  $('#modal').classList.remove('hidden')
}
dataQualityClosure=function(){
  let s=dataEvidenceStatus(),summary=(data.consistency||{}).summary||{},reports=latestEvidenceReports();
  return `<div class="card quality-hero"><span class="tag">DATA EVIDENCE</span><h2>数据核查</h2><p>数据库和Redis只作为外部只读连接器使用。平台执行时判断是否需要核查、去哪取证，工作台只保留入口、状态和报告。</p><div class="quality-flow">${[['自动核查',true,'按当前测试目标执行'],['指定核查',true,'手动补充本次线索'],['只读连接',s.dbReady||s.redisReady,s.dbReady||s.redisReady?'可按需调用':'需要时接入'],['报告归档',s.runs.length||reports.length,(s.runs.length||reports.length)?'已有证据':'执行后生成']].map(x=>`<div class="quality-step ${x[1]?'':'pending'}">${hubStatus(x[1])}<b>${x[0]}</b><small>${esc(x[2])}</small></div>`).join('')}</div></div><div class="closure-grid"><div class="card"><div class="diagnosis-head"><div><h2>自动核查</h2><p>由平台根据需求、接口、参数和响应字段自动选择只读证据源。</p></div><button class="primary" onclick="autoEvidenceCheck()">自动核查</button></div><div id="evidenceAutoStatus">${s.latest?`<div class="summary-panel"><b>最近自动核查：${esc(s.latest.status)}</b><p>${esc(s.latest.created_at||'')}</p></div>`:`<div class="empty"><b>暂无自动核查记录</b></div>`}</div></div><div class="card"><div class="diagnosis-head"><div><h2>指定核查</h2><p>当你知道这次可能涉及订单、金额、流水或缓存时，可以给平台一个核查目标和线索。</p></div><button class="primary" onclick="showManualEvidenceCheckModal()">指定核查</button></div><div>${reports.length?reports.map(x=>`<div class="summary-panel"><b>${esc(x.status)} · ${esc((x.created_at||'').replace('T',' '))}</b><p>${esc(x.summary||'')}</p>${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">查看报告</button>`:''}</div>`).join(''):'<div class="empty"><b>暂无指定核查报告</b></div>'}</div></div></div><div class="card"><h2>最近状态</h2><div class="metrics"><div class="metric"><span>核查结论</span><b style="font-size:20px">${esc(summary.status||'PENDING')}</b></div><div class="metric"><span>自动记录</span><b>${s.runs.length}</b></div><div class="metric"><span>指定报告</span><b>${reports.length}</b></div><div class="metric"><span>数据源策略</span><b style="font-size:20px">只读</b></div></div><div class="formrow"><button class="small" onclick="showConnectorDetailModal()">查看核查记录</button><button class="small" onclick="switchTab('reports')">报告中心</button></div></div>`
}
tableEvidenceCenter=function(){
  let latest=data.gift_latest||{},sender=latest.accounts?.sender?.uid||1454428;
  return `<div class="card"><span class="tag">DATA EVIDENCE</span><h2>按需数据证据</h2><p>执行真实链路时才读取或补录数据证据。工作台不常驻展示升级表、Redis Key 或固定映射。</p><div class="formrow"><button class="small" onclick="switchTab('dataquality')">进入数据核查</button><button class="small" onclick="showManualEvidenceCheckModal()">指定核查</button></div><h3>人工证据补录</h3><div class="formrow"><input id="manualRedisUid" value="${sender}" placeholder="UID"><input id="manualRedisValue" placeholder="输入本次只读查询返回值"></div><button class="small" onclick="submitManualRedisResult()">保存到本地报告</button><p><small>只更新平台本地报告，不写入公司数据库或Redis。</small></p></div>`
}

function cleanAssetSourceName(name){
  let text=String(name||'未命名需求')
    .replace(/\.(md|txt|html|json|yaml|yml|har|zip|docx|pdf)$/i,'')
    .replace(/^0+\d*[-_]/,'')
    .replace(/^CoDesign需求[-_]?/i,'')
    .replace(/[-_ ]*(App)?接口文档$/i,'')
    .replace(/[-_ ]*接口文档$/,'')
    .replace(/[-_ ]*需求文档$/,'')
    .replace(/[-_ ]*需求$/,'')
    .replace(/[-_ ]*原型$/,'')
    .trim();
  return text||'未命名需求'
}
function sourceDisplayKind(kind){
  return {requirement:'需求资料',openapi:'接口文档',har:'抓包样例',rules:'规则约束'}[kind]||kind||'资料'
}
function requirementAssetGroups(){
  let sources=data.sources||[],reqs=data.requirement_items||[],points=data.points||[],cases=data.cases||[],endpoints=data.endpoints||[],pointById={};
  points.forEach(p=>pointById[p.id]=p);
  let groups={},sourceKey={};
  function ensure(key,label){
    if(!groups[key])groups[key]={key,label,sources:[],requirements:[],points:[],cases:[],endpoints:[],updated_at:''};
    return groups[key]
  }
  sources.forEach(s=>{
    let key=cleanAssetSourceName(s.name);
    sourceKey[s.id]=key;
    let g=ensure(key,key);
    g.sources.push(s);
    if((s.created_at||'')>g.updated_at)g.updated_at=s.created_at||''
  });
  reqs.forEach(r=>{
    let key=sourceKey[r.source_id]||'未关联需求';
    let g=ensure(key,key);
    g.requirements.push(r);
    if((r.created_at||'')>g.updated_at)g.updated_at=r.created_at||''
  });
  points.forEach(p=>{
    let key=sourceKey[p.source_id]||'未关联需求';
    let g=ensure(key,key);
    g.points.push(p);
    if((p.created_at||'')>g.updated_at)g.updated_at=p.created_at||''
  });
  endpoints.forEach(ep=>{
    let key=sourceKey[ep.source_id]||'手工接口';
    let g=ensure(key,key);
    g.endpoints.push(ep);
    if((ep.created_at||'')>g.updated_at)g.updated_at=ep.created_at||''
  });
  cases.forEach(c=>{
    let p=pointById[c.point_id],matchedEp=endpoints.find(ep=>(ep.method||'').toUpperCase()===(c.method||'').toUpperCase()&&(c.path||'').split('?')[0]===ep.path);
    let key=(p&&sourceKey[p.source_id])||(matchedEp&&sourceKey[matchedEp.source_id])||'未关联需求';
    let g=ensure(key,key);
    g.cases.push(c);
    if((c.created_at||'')>g.updated_at)g.updated_at=c.created_at||''
  });
  return Object.values(groups).filter(g=>g.sources.length||g.requirements.length||g.points.length||g.cases.length||g.endpoints.length).sort((a,b)=>(b.updated_at||'').localeCompare(a.updated_at||''))
}
function assetGroupSummary(g){
  let docs=g.sources.reduce((m,s)=>{let k=sourceDisplayKind(s.kind);m[k]=(m[k]||0)+1;return m},{});
  let docText=Object.entries(docs).map(([k,v])=>`${k}${v}`).join(' · ')||'无资料';
  let executable=g.cases.filter(x=>x.method&&x.path).length;
  return `${docText} · 需求${g.requirements.length} · 接口${g.endpoints.length} · 测试点${g.points.length} · 用例${g.cases.length} · 可执行${executable}`
}
function requirementAssetGroupCards(){
  let groups=requirementAssetGroups();
  window.__requirementAssetGroups=groups;
  if(!groups.length)return '<div class="card empty"><b>暂无需求包</b><p>导入需求资料或接口文档后会按需求分开归纳。</p></div>';
  return `<div class="card"><div class="diagnosis-head"><div><h2>按需求归纳</h2><p>每个需求包独立查看接口文档、测试点和测试用例，避免新旧需求挤在一张大表里。</p></div><span class="tag PASSED">${groups.length} 个需求包</span></div><div class="endpoint-matrix">${groups.map((g,i)=>{let status=g.endpoints.length&&g.cases.length?'PASSED':g.requirements.length||g.points.length?'P1':'NOT_RUN';return `<div class="endpoint-card"><span class="tag ${status}">${esc(status==='PASSED'?'已生成':status==='P1'?'待补齐':'资料')}</span><h3>${esc(g.label)}</h3><p>${esc(assetGroupSummary(g))}</p><div class="formrow"><button class="small" onclick="showRequirementAssetGroup(${i},'overview')">总览</button><button class="small" onclick="showRequirementAssetGroup(${i},'apis')">接口文档</button><button class="small" onclick="showRequirementAssetGroup(${i},'points')">测试点</button><button class="small" onclick="showRequirementAssetGroup(${i},'cases')">测试用例</button></div></div>`}).join('')}</div></div>`
}
function groupNav(index,active){
  return `<div class="formrow report-menu">${[['overview','总览'],['apis','接口文档'],['points','测试点'],['cases','测试用例'],['requirements','需求条目']].map(x=>`<button class="${active===x[0]?'primary':'small'}" onclick="showRequirementAssetGroup(${index},'${x[0]}')">${x[1]}</button>`).join('')}</div>`
}
function showRequirementAssetGroup(index,view='overview'){
  let groups=window.__requirementAssetGroups||requirementAssetGroups(),g=groups[index];
  if(!g)return toast('没有找到这个需求包，请刷新后再试','warning');
  let html='';
  if(view==='overview')html=`<div class="metrics"><div class="metric"><span>需求</span><b>${g.requirements.length}</b></div><div class="metric"><span>接口</span><b>${g.endpoints.length}</b></div><div class="metric"><span>测试点</span><b>${g.points.length}</b></div><div class="metric"><span>测试用例</span><b>${g.cases.length}</b></div></div><div class="card"><h2>资料来源</h2>${g.sources.length?g.sources.map(s=>`<div class="summary-panel"><b>${esc(s.name)}</b><p>${esc(sourceDisplayKind(s.kind))} · ${esc((s.created_at||'').replace('T',' '))}</p></div>`).join(''):'<div class="empty">暂无直接资料来源</div>'}</div>`;
  if(view==='apis')html=g.endpoints.length?`<table><thead><tr><th>风险</th><th>方法</th><th>接口</th><th>摘要</th><th>认证</th></tr></thead><tbody>${g.endpoints.map(ep=>`<tr><td><span class="tag ${ep.risk_level==='high'?'P0':ep.risk_level==='medium'?'P1':'PASSED'}">${esc(ep.risk_level||'-')}</span></td><td><code>${esc(ep.method||'-')}</code></td><td><code>${esc(ep.path||'-')}</code></td><td>${esc(ep.summary||'')}</td><td>${+ep.auth_required?'需要':'不强制'}</td></tr>`).join('')}</tbody></table>`:'<div class="empty"><b>这个需求包下暂无接口文档</b></div>';
  if(view==='points')html=g.points.length?`<table><thead><tr><th>优先级</th><th>模块</th><th>测试点</th><th>类型</th><th>依据</th></tr></thead><tbody>${g.points.map(p=>`<tr><td><span class="tag ${esc(p.priority||'')}">${esc(p.priority||'-')}</span></td><td>${esc(p.module||'-')}</td><td><b>${esc(p.title||'-')}</b></td><td>${esc(p.category||'-')}</td><td>${esc(p.rationale||'')}</td></tr>`).join('')}</tbody></table>`:'<div class="empty"><b>这个需求包下暂无测试点</b></div>';
  if(view==='cases')html=g.cases.length?`<table><thead><tr><th>优先级</th><th>用例</th><th>接口/执行器</th><th>预期</th><th>状态</th></tr></thead><tbody>${g.cases.map(c=>`<tr><td><span class="tag ${esc(c.priority||'')}">${esc(c.priority||'-')}</span></td><td><b>${esc(c.title||'-')}</b><br><small>${esc(c.requirement_ref||'')}</small></td><td>${c.method?`<code>${esc(c.method+' '+c.path)}</code>`:esc(c.executor_type||'manual')}</td><td>${esc(c.expected||'-')}</td><td>${assetStatusTag(c.execution_status)}</td></tr>`).join('')}</tbody></table>`:'<div class="empty"><b>这个需求包下暂无测试用例</b></div>';
  if(view==='requirements')html=g.requirements.length?`<table><thead><tr><th>优先级</th><th>需求</th><th>验收/说明</th><th>状态</th></tr></thead><tbody>${g.requirements.map(r=>`<tr><td><span class="tag ${esc(r.priority||'')}">${esc(r.priority||'-')}</span></td><td><b>${esc(r.title||'-')}</b></td><td>${esc(r.acceptance_criteria||r.description||'')}</td><td>${esc(r.status||'-')}</td></tr>`).join('')}</tbody></table>`:'<div class="empty"><b>这个需求包下暂无结构化需求</b></div>';
  $('#modalBody').innerHTML=`<h2>${esc(g.label)}</h2>${groupNav(index,view)}${html}`;
  $('#modal').classList.remove('hidden')
}
showTestPointsModal=function(){
  let groups=requirementAssetGroups();window.__requirementAssetGroups=groups;
  let html=groups.length?groups.map((g,i)=>`<div class="summary-panel"><b>${esc(g.label)}</b><p>测试点 ${g.points.length} 个 · 需求 ${g.requirements.length} 条 · 接口 ${g.endpoints.length} 个</p><button class="small" onclick="showRequirementAssetGroup(${i},'points')">查看测试点</button></div>`).join(''):'<div class="empty"><b>暂无测试点</b></div>';
  openAssetModal('按需求查看测试点',html)
}
showTestCasesModal=function(){
  let groups=requirementAssetGroups();window.__requirementAssetGroups=groups;
  let html=groups.length?groups.map((g,i)=>`<div class="summary-panel"><b>${esc(g.label)}</b><p>用例 ${g.cases.length} 条 · 可执行 ${g.cases.filter(x=>x.method&&x.path).length} 条 · 待补齐 ${g.cases.filter(x=>x.execution_status==='BLOCKED').length} 条</p><button class="small" onclick="showRequirementAssetGroup(${i},'cases')">查看测试用例</button></div>`).join(''):'<div class="empty"><b>暂无测试用例</b></div>';
  openAssetModal('按需求查看测试用例',html)
}
showEndpointAssetsModal=function(){
  let groups=requirementAssetGroups();window.__requirementAssetGroups=groups;
  let html=groups.length?groups.map((g,i)=>`<div class="summary-panel"><b>${esc(g.label)}</b><p>接口 ${g.endpoints.length} 个 · 文档 ${g.sources.filter(s=>['openapi','har'].includes(s.kind)).length} 份</p><button class="small" onclick="showRequirementAssetGroup(${i},'apis')">查看接口文档</button></div>`).join(''):'<div class="empty"><b>暂无接口资产</b></div>';
  openAssetModal('按需求查看接口文档',html)
}
groupedTestAssets=function(){
  let groups=requirementAssetGroups(),latest=groups[0];
  return `<div class="card"><div class="diagnosis-head"><div><h2>测试资产中心</h2><p>资产按需求包归纳；每个需求包内再看接口文档、测试点和测试用例。</p></div><span class="tag PASSED">${(data.cases||[]).length} CASES</span></div><div class="metrics"><div class="metric"><span>需求包</span><b>${groups.length}</b></div><div class="metric"><span>测试点</span><b>${(data.points||[]).length}</b></div><div class="metric"><span>测试用例</span><b>${(data.cases||[]).length}</b></div><div class="metric"><span>接口</span><b>${(data.endpoints||[]).length}</b></div></div>${latest?`<div class="summary-panel"><b>最近需求包：${esc(latest.label)}</b><p>${esc(assetGroupSummary(latest))}</p><button class="small" onclick="showRequirementAssetGroup(0,'overview')">打开</button></div>`:''}</div>`
}
compactAssetsWorkspace=function(){
  let reqs=data.requirement_items||[],sources=data.sources||[],endpoints=data.endpoints||[],cases=data.cases||[],points=data.points||[],selected=(data.trace_links||[]).filter(x=>+x.selected===1).length;
  return `<div class="card quality-hero"><span class="tag">ASSETS</span><h2>需求与测试资产</h2><p>按需求包归纳资料、接口文档、测试点和测试用例；新旧需求分开管理，报告和执行结果再统一归档。</p><div class="quality-flow">${[['资料',sources.length,sources.length+'份输入'],['需求',reqs.length,reqs.length+'条需求'],['测试点',points.length,points.length+'个测试点'],['用例',cases.length,cases.length+'条用例']].map(x=>`<button class="quality-step ${x[1]?'':'pending'}" onclick="${x[0]==='测试点'?'showTestPointsModal()':x[0]==='用例'?'showTestCasesModal()':x[0]==='资料'?'showSourceModal()':'showTraceCoverageModal()'}">${hubStatus(x[1])}<b>${x[0]}</b><small>${esc(x[2])}</small></button>`).join('')}</div></div>${requirementAssetGroupCards()}${collaborationPackagePanel()}<div class="closure-grid"><div class="card"><h2>资产操作</h2><div class="summary-panel"><b>新增需求资料</b><p>需求描述、原型链接、图片、HTML原型包统一从这里导入。</p><button class="primary" onclick="showSourceModal()">添加需求</button></div><div class="summary-panel"><b>导入接口文档</b><p>上传或粘贴 OpenAPI/Swagger/HAR/Markdown 接口文档，形成对应需求包下的接口基线。</p><button class="primary" onclick="showInterfaceDocModal()">导入接口</button></div><div class="summary-panel"><b>生成与补齐</b><p>按当前资料生成测试点、用例、接口覆盖、链路和按需数据核查策略。</p><button class="small" onclick="runPipeline()">启动生成</button></div><div class="summary-panel"><b>接口文档基线</b><p>把当前接口资产导出为脱敏 OpenAPI，方便同步到 Apifox 或团队文档。</p><button class="small" onclick="downloadInterfaceDocument()">导出</button></div></div><div><div class="card"><h2>覆盖摘要</h2><div class="evidence-list"><button class="evidence-item asset-row" onclick="showTraceCoverageModal()"><b>需求覆盖</b><small>${reqs.length}条需求，${selected}条已选追踪关系</small></button><button class="evidence-item asset-row" onclick="showEndpointAssetsModal()"><b>接口文档</b><small>${endpoints.length}个接口，按需求包查看</small></button><button class="evidence-item asset-row" onclick="showTestPointsModal()"><b>测试点</b><small>${points.length}个测试点，按需求包查看</small></button><button class="evidence-item asset-row" onclick="showTestCasesModal()"><b>测试用例</b><small>${cases.length}条用例，按需求包查看</small></button></div></div>${groupedTestAssets()}</div></div>`
}

function caseToJmeterPanel(){
  let m=data.case_jmeter_model||{},flows=m.flows||[],gaps=m.gaps||[],coverage=m.coverage||{},components=m.jmeter_components||[];
  if(!m.requirement)return `<div class="card"><h2>用例生成 JMeter</h2><p>当前后端尚未加载用例到脚本模型，重启工作台后可使用。</p></div>`;
  let ready=flows.filter(x=>x.automation_status==='ready').length,planned=flows.filter(x=>x.automation_status==='planned').length,blocked=flows.filter(x=>x.automation_status==='blocked').length;
  return `<div class="card"><div class="diagnosis-head"><div><h2>用例生成 JMeter</h2><p>测试用例是输入，JMeter 是执行载体。平台按用例步骤生成线程组、请求、提取器、断言和报告标签。</p></div><span class="tag ${gaps.some(x=>x.level==='P0')?'P1':'PASSED'}">${esc(m.status||'READY')}</span></div><div class="metrics"><div class="metric"><span>业务流</span><b>${coverage.required_flows||flows.length}</b></div><div class="metric"><span>可执行</span><b>${ready}</b></div><div class="metric"><span>待脚本化</span><b>${planned}</b></div><div class="metric"><span>条件阻塞</span><b>${blocked}</b></div></div><div class="summary-panel"><b>转换关系</b><p>${esc(m.principle||'')}</p><button class="primary" onclick="generateJmeterFromCases()">生成用例驱动脚本</button> <button class="small" onclick="showCaseJmeterModel()">查看映射</button></div>${gaps.length?`<div class="gap-list">${gaps.map(x=>`<div class="gap-item ${x.level==='P0'?'P0':'P1'}"><span class="tag ${x.level==='P0'?'FAILED':'P1'}">${esc(x.level)}</span><div><b>${esc(x.item)}</b><p>${esc(x.detail)}</p></div></div>`).join('')}</div>`:''}<h3>工资交易状态流</h3><table><thead><tr><th>流</th><th>测试用例</th><th>账号槽位</th><th>JMeter线程组</th><th>脚本状态</th></tr></thead><tbody>${flows.map(x=>`<tr><td><span class="tag ${x.priority}">${esc(x.code)}</span></td><td><b>${esc(x.name)}</b><br><small>${esc((x.steps||[]).join(' -> '))}</small></td><td><code>${esc(x.account_slot)}</code></td><td>${esc(x.thread_group)}</td><td><span class="tag ${x.automation_status==='ready'?'PASSED':x.automation_status==='blocked'?'P1':'NOT_RUN'}">${esc(x.automation_status)}</span></td></tr>`).join('')}</tbody></table><h3>JMeter组件生成规则</h3><div class="endpoint-matrix">${components.map(x=>`<div class="endpoint-card"><span class="tag">CASE</span><h3>${esc(x.jmeter)}</h3><p><b>${esc(x.case_part)}</b><br>${esc(x.example)}</p></div>`).join('')}</div></div>`
}

function showCaseJmeterModel(){
  let m=data.case_jmeter_model||{},fields=m.required_case_fields||[],flows=m.flows||[];
  $('#modalBody').innerHTML=`<h2>测试用例如何变成 JMeter</h2><p class="policy-note">这里不是展示脚本源码，而是展示生成器需要从用例里读取什么，以及每个字段进入 JMeter 的哪个位置。</p><h3>用例必备字段</h3><table><thead><tr><th>字段</th><th>生成用途</th></tr></thead><tbody>${fields.map(x=>`<tr><td><code>${esc(x.field)}</code></td><td>${esc(x.use)}</td></tr>`).join('')}</tbody></table><h3>流程到脚本追踪</h3><table><thead><tr><th>Case</th><th>订单变量</th><th>数据证据</th><th>阻塞说明</th></tr></thead><tbody>${flows.map(x=>`<tr><td>${esc(x.code+' '+x.name)}</td><td><code>${esc(x.order_var)}</code></td><td>${esc((x.data_evidence||[]).join(' / '))}</td><td>${esc(x.blocker||'可按接口步骤生成')}</td></tr>`).join('')}</tbody></table>`;
  $('#modal').classList.remove('hidden')
}

async function generateJmeterFromCases(){
  try{
    toast('正在按测试用例生成 JMeter 脚本索引…');
    let x=await api(`/api/projects/${current}/jmeter/generate-from-cases`,{method:'POST',body:'{}'});
    data.case_jmeter_model=x.model;
    $('#modalBody').innerHTML=`<h2>用例驱动脚本已生成</h2><p class="policy-note">${esc(x.message)}</p><div class="metrics"><div class="metric"><span>状态</span><b>${esc(x.status)}</b></div><div class="metric"><span>流程</span><b>${esc((x.model?.flows||[]).length)}</b></div><div class="metric"><span>缺口</span><b>${esc((x.model?.gaps||[]).length)}</b></div></div><label>JMX</label><code>${esc(x.jmx_path||'')}</code><label>映射清单</label><code>${esc(x.manifest_path||'')}</code><label>说明文档</label><code>${esc(x.summary_path||'')}</code><label>流程槽位CSV</label><code>${esc(x.flow_slots_csv_path||'')}</code><label>运行参数说明</label><code>${esc(x.runtime_parameters_path||'')}</code>`;
    $('#modal').classList.remove('hidden');
    toast('JMeter 用例驱动脚本已生成','success');
    render();
  }catch(e){toast(e.message,'error')}
}

function groupHasSalaryTrade(g){
  let text=[g.label,...(g.sources||[]).map(x=>x.name),...(g.requirements||[]).map(x=>x.title),...(g.cases||[]).map(x=>x.title+' '+(x.requirement_ref||''))].join(' ');
  return /工资|薪资|salary|代理.*交易|快速结算/i.test(text)
}

function requirementJmeterSummary(g,index){
  if(!groupHasSalaryTrade(g))return '';
  let m=data.case_jmeter_model||{},flows=m.flows||[],gaps=m.gaps||[],ready=flows.filter(x=>x.automation_status==='ready').length;
  return `<div class="summary-panel"><b>JMeter脚本映射</b><p>这个需求包含复杂状态流，可按测试用例生成独立 JMeter 脚本；当前归纳 ${flows.length||0} 条流程，${ready} 条已具备自动化基础，${gaps.length} 个待补条件。</p><button class="small" onclick="showRequirementAssetGroup(${index},'jmeter')">查看脚本映射</button></div>`
}

const requirementAssetGroupCardsByRequirement=typeof requirementAssetGroupCards==='function'?requirementAssetGroupCards:null;
requirementAssetGroupCards=function(){
  let groups=requirementAssetGroups();
  window.__requirementAssetGroups=groups;
  if(!groups.length)return '<div class="card empty"><b>暂无需求包</b><p>导入需求资料或接口文档后会按需求分开归纳。</p></div>';
  return `<div class="card"><div class="diagnosis-head"><div><h2>按需求归纳</h2><p>每个需求包独立查看接口文档、测试点、测试用例和脚本映射。执行中心只负责调起工具和回收报告。</p></div><span class="tag PASSED">${groups.length} 个需求包</span></div><div class="endpoint-matrix">${groups.map((g,i)=>{let status=g.endpoints.length&&g.cases.length?'PASSED':g.requirements.length||g.points.length?'P1':'NOT_RUN';return `<div class="endpoint-card"><span class="tag ${status}">${esc(status==='PASSED'?'已生成':status==='P1'?'待补齐':'资料')}</span><h3>${esc(g.label)}</h3><p>${esc(assetGroupSummary(g))}</p>${requirementJmeterSummary(g,i)}<div class="formrow"><button class="small" onclick="showRequirementAssetGroup(${i},'overview')">总览</button><button class="small" onclick="showRequirementAssetGroup(${i},'apis')">接口文档</button><button class="small" onclick="showRequirementAssetGroup(${i},'points')">测试点</button><button class="small" onclick="showRequirementAssetGroup(${i},'cases')">测试用例</button></div></div>`}).join('')}</div></div>`
}

groupNav=function(index,active){
  let groups=window.__requirementAssetGroups||requirementAssetGroups(),g=groups[index],items=[['overview','总览'],['apis','接口文档'],['points','测试点'],['cases','测试用例'],['requirements','需求条目']];
  if(g&&groupHasSalaryTrade(g))items.push(['jmeter','JMeter映射']);
  return `<div class="formrow report-menu">${items.map(x=>`<button class="${active===x[0]?'primary':'small'}" onclick="showRequirementAssetGroup(${index},'${x[0]}')">${x[1]}</button>`).join('')}</div>`
}

const showRequirementAssetGroupBeforeJmeterView=showRequirementAssetGroup;
showRequirementAssetGroup=function(index,view='overview'){
  let groups=window.__requirementAssetGroups||requirementAssetGroups(),g=groups[index];
  if(view!=='jmeter')return showRequirementAssetGroupBeforeJmeterView(index,view);
  if(!g)return toast('没有找到这个需求包，请刷新后再试','warning');
  if(!groupHasSalaryTrade(g))return toast('这个需求暂未识别到复杂 JMeter 状态流','warning');
  let m=data.case_jmeter_model||{},flows=m.flows||[],gaps=m.gaps||[],components=m.jmeter_components||[];
  $('#modalBody').innerHTML=`<h2>${esc(g.label)}</h2>${groupNav(index,view)}<div class="card"><div class="diagnosis-head"><div><h2>用例到 JMeter 映射</h2><p>这里属于当前需求包，不是全局执行中心。平台从本需求的测试用例读取步骤、角色、提取规则和断言，再生成独立 JMeter 脚本。</p></div><span class="tag ${gaps.some(x=>x.level==='P0')?'P1':'PASSED'}">${esc(m.status||'READY')}</span></div><div class="formrow"><button class="primary" onclick="generateJmeterFromCases()">生成用例驱动脚本</button><button class="small" onclick="showCaseJmeterModel()">查看字段规则</button></div>${gaps.length?`<div class="gap-list">${gaps.map(x=>`<div class="gap-item ${x.level==='P0'?'P0':'P1'}"><span class="tag ${x.level==='P0'?'FAILED':'P1'}">${esc(x.level)}</span><div><b>${esc(x.item)}</b><p>${esc(x.detail)}</p></div></div>`).join('')}</div>`:''}<table><thead><tr><th>流</th><th>测试用例</th><th>账号槽位</th><th>JMeter线程组</th><th>脚本状态</th></tr></thead><tbody>${flows.map(x=>`<tr><td><span class="tag ${x.priority}">${esc(x.code)}</span></td><td><b>${esc(x.name)}</b><br><small>${esc((x.steps||[]).join(' -> '))}</small></td><td><code>${esc(x.account_slot)}</code></td><td>${esc(x.thread_group)}</td><td><span class="tag ${x.automation_status==='ready'?'PASSED':x.automation_status==='blocked'?'P1':'NOT_RUN'}">${esc(x.automation_status)}</span></td></tr>`).join('')}</tbody></table><h3>组件生成规则</h3><div class="endpoint-matrix">${components.map(x=>`<div class="endpoint-card"><span class="tag">CASE</span><h3>${esc(x.jmeter)}</h3><p><b>${esc(x.case_part)}</b><br>${esc(x.example)}</p></div>`).join('')}</div></div>`;
  $('#modal').classList.remove('hidden')
}

const toolchainPanelBeforeCaseDrivenJmeter=toolchainPanel;
function showRequirementPackageChooser(){
  let groups=requirementAssetGroups();
  window.__requirementAssetGroups=groups;
  if(!groups.length){
    toast('当前还没有可选择的需求包，请先导入需求资料或接口文档','warning');
    switchTab('sources');
    return
  }
  $('#modalBody').innerHTML=`<h2>选择需求包</h2><p class="policy-note">先选本次要执行或生成脚本的需求范围。每个需求包独立查看接口文档、测试点、测试用例和脚本映射，避免多个需求混在一起。</p><div class="endpoint-matrix">${groups.map((g,i)=>{let jmeter=groupHasSalaryTrade(g),status=g.cases.length&&g.endpoints.length?'PASSED':g.cases.length||g.endpoints.length?'P1':'NOT_RUN';return `<div class="endpoint-card"><span class="tag ${status}">${esc(status==='PASSED'?'可执行':status==='P1'?'待补齐':'资料')}</span><h3>${esc(g.label)}</h3><p>${esc(assetGroupSummary(g))}</p><div class="formrow"><button class="primary" onclick="showRequirementAssetGroup(${i},'overview')">打开需求包</button>${jmeter?`<button class="small" onclick="showRequirementAssetGroup(${i},'jmeter')">JMeter映射</button>`:''}</div></div>`}).join('')}</div>`;
  $('#modal').classList.remove('hidden')
}
toolchainPanel=function(){
  return `<div class="card"><div class="diagnosis-head"><div><h2>用例生成脚本</h2><p>执行中心只负责把已选需求包的用例交给外部工具执行。复杂流程请先选择需求包，再确认对应的 JMeter 映射。</p></div><button class="primary" onclick="showRequirementPackageChooser()">选择需求包</button></div></div>`+toolchainPanelBeforeCaseDrivenJmeter()
}

function groupRequirementSourceId(g){
  let requirement=(g.sources||[]).find(x=>x.kind==='requirement');
  return requirement?.id||''
}

function requirementPackageMaintainHtml(g,index){
  let reqSourceId=groupRequirementSourceId(g),lastSource=(g.sources||[])[0],canGenerate=!!lastSource;
  return `<div class="card package-maintain-card"><div class="diagnosis-head"><div><h2>维护需求包</h2><p>在当前需求包内追加需求、接口文档或抓包资料。保存后平台会按同一个业务主题重新归纳，不再散成新的孤立卡片。</p></div><span class="tag PASSED">PACKAGE</span></div><div class="package-maintain-grid"><div class="summary-panel"><b>追加需求资料</b><p>补充规则、异常场景、原型说明、验收口径或变更说明。</p><button class="primary" onclick="showPackageSourceEditor(${index},'requirement')">新增需求</button></div><div class="summary-panel"><b>追加接口文档</b><p>导入 OpenAPI、Swagger、Markdown接口清单或 HAR 抓包，自动关联到当前需求包。</p><button class="primary" onclick="showPackageSourceEditor(${index},'openapi')">新增接口</button></div><div class="summary-panel"><b>重新生成资产</b><p>基于当前资料重新生成测试点、用例、链路和脚本映射。</p><button class="small" ${canGenerate?'':'disabled'} onclick="generate('${esc(lastSource?.id||'')}')">重新生成</button></div><div class="summary-panel"><b>交付与同步</b><p>导出接口基线或测试资产包，用于 Apifox 协同、评审和迁移。</p><button class="small" onclick="downloadInterfaceDocument()">导出接口基线</button></div></div><h3>当前资料</h3><div class="table-scroll">${(g.sources||[]).length?`<table><thead><tr><th>资料</th><th>类型</th><th>时间</th></tr></thead><tbody>${g.sources.map(s=>`<tr><td><b>${esc(s.name)}</b></td><td>${esc(sourceDisplayKind(s.kind))}</td><td>${esc((s.created_at||'').replace('T',' '))}</td></tr>`).join('')}</tbody></table>`:'<div class="empty"><b>暂无资料</b></div>'}</div>${reqSourceId?`<p class="policy-note">接口文档会默认关联到当前需求资料：${esc((g.sources||[]).find(x=>x.id===reqSourceId)?.name||g.label)}</p>`:''}</div>`
}

function showPackageSourceEditor(index,kind='requirement'){
  let groups=window.__requirementAssetGroups||requirementAssetGroups(),g=groups[index];
  if(!g)return toast('没有找到这个需求包，请刷新后再试','warning');
  let isApi=kind==='openapi'||kind==='har',reqSourceId=groupRequirementSourceId(g);
  $('#modalBody').innerHTML=`<h2>${esc(g.label)} · ${isApi?'新增接口':'新增需求'}</h2><p class="policy-note">本次保存会追加到当前需求包。接口文档会关联当前需求来源；需求补充会使用同一个业务主题命名，自动归并。</p><input id="requirementSource" type="hidden" value="${esc(reqSourceId)}"><label>资料名称</label><input id="srcName" value="${esc(g.label+(isApi?'-接口文档':'-需求补充'))}"><label>资料类型</label><select id="srcKind"><option value="requirement" ${kind==='requirement'?'selected':''}>需求文档</option><option value="openapi" ${kind==='openapi'?'selected':''}>OpenAPI / Swagger / Markdown接口</option><option value="har" ${kind==='har'?'selected':''}>HAR 抓包文件</option><option value="rules" ${kind==='rules'?'selected':''}>测试规则与约束</option></select><label>需求/文档链接（可选）</label><input id="srcUrl" placeholder="需求、接口文档或原型地址"><label>资料内容</label><textarea id="srcContent" placeholder="${isApi?'粘贴 OpenAPI、Swagger、Markdown接口清单或 HAR 内容':'补充需求规则、异常场景、验收口径或变更说明'}"></textarea><label>或读取本地文件</label><input type="file" id="srcFile" accept=".txt,.md,.json,.yaml,.yml,.har,.docx,.pdf,.png,.jpg,.jpeg,.webp,.zip"><div id="sourceImportStatus" style="margin:10px 0 12px"></div><div class="formrow"><button id="sourceSaveButton" class="primary" onclick="addSource()">保存到需求包</button><button class="small" onclick="showRequirementAssetGroup(${index},'maintain')">返回维护</button></div>`;
  $('#modal').classList.remove('hidden');
  bindFile()
}

const groupNavBeforePackageMaintain=groupNav;
groupNav=function(index,active){
  let base=groupNavBeforePackageMaintain(index,active);
  return base.replace('</div>',`<button class="${active==='maintain'?'primary':'small'}" onclick="showRequirementAssetGroup(${index},'maintain')">维护</button></div>`)
}

const showRequirementAssetGroupBeforeMaintain=showRequirementAssetGroup;
showRequirementAssetGroup=function(index,view='overview'){
  if(view!=='maintain')return showRequirementAssetGroupBeforeMaintain(index,view);
  let groups=window.__requirementAssetGroups||requirementAssetGroups(),g=groups[index];
  if(!g)return toast('没有找到这个需求包，请刷新后再试','warning');
  $('#modalBody').innerHTML=`<h2>${esc(g.label)}</h2>${groupNav(index,view)}${requirementPackageMaintainHtml(g,index)}`;
  $('#modal').classList.remove('hidden')
}

function environmentConfigPanel(){
  let c=data.environment_config||{},p=c.project||{},tools=c.tools||{},ds=c.data_sources||{},reports=c.reports||{};
  return `<div class="card"><div class="diagnosis-head"><div><h2>YAML 环境配置</h2><p>YAML 管环境、工具、开关和路径；运行数据由测试用例决定，复杂数据驱动场景才启用账号槽位。</p></div><span class="tag ${c.status==='READY'?'PASSED':'P1'}">${esc(c.status||'PENDING')}</span></div><div class="metrics"><div class="metric"><span>环境</span><b style="font-size:20px">${esc(p.env||c.env_name||'-')}</b></div><div class="metric"><span>JMeter</span><b style="font-size:20px">${esc(tools.jmeter_home?'已配置':'待配置')}</b></div><div class="metric"><span>Redis</span><b style="font-size:20px">${esc(ds.redis_configured?'只读':'按需')}</b></div><div class="metric"><span>报告</span><b style="font-size:20px">${esc(reports.group_by||'需求包')}</b></div></div><div class="summary-panel"><b>配置边界</b><p>${esc(c.env_file||'config/env.test.yaml')} · 敏感 token 和密码不进入 YAML，单账号走运行参数，多账号再走数据文件。</p><button class="small" onclick="showEnvironmentConfigModal()">查看</button></div></div>`
}

function showEnvironmentConfigModal(){
  let c=data.environment_config||{};
  $('#modalBody').innerHTML=`<h2>YAML 环境配置</h2><p class="policy-note">配置文件只保存环境、路径、开关、超时和只读策略。账号密码、ticket、sn 等敏感值不写进公开配置；运行数据由测试用例判断，单账号不强制数据文件。</p><table><tbody>${[
    ['配置文件',c.env_file],
    ['测试环境',c.project?.base_url],
    ['JMeter命令',c.tools?.jmeter_command],
    ['Redis',c.data_sources?.redis_configured?`${c.data_sources.redis_host}:${c.data_sources.redis_port}`:'按需接入'],
    ['账号策略',c.accounts?.strategy],
    ['账号文件',c.accounts?.csv_path],
    ['报告归档',`${c.reports?.root||'reports'} / ${c.reports?.group_by||'requirement_package'}`],
  ].map(x=>`<tr><th>${esc(x[0])}</th><td>${esc(x[1]||'-')}</td></tr>`).join('')}</tbody></table>`;
  $('#modal').classList.remove('hidden')
}

function multiAccountContextPanel(){
  let m=data.multi_account_context||{},counts=m.counts||{},gaps=m.gaps||[];
  return `<div class="card"><div class="diagnosis-head"><div><h2>运行数据上下文</h2><p>平台按测试用例判断运行数据方式：单账号走运行参数，多角色或多流程再启用账号槽位。</p></div><span class="tag ${m.status==='READY'?'PASSED':'P1'}">${esc(m.status||'PENDING')}</span></div><div class="metrics"><div class="metric"><span>账号池</span><b>${esc(counts.accounts_table||0)}</b></div><div class="metric"><span>申请人</span><b>${esc(counts.applicant||0)}</b></div><div class="metric"><span>代理人</span><b>${esc(counts.proxy||0)}</b></div><div class="metric"><span>可用账号</span><b>${esc(counts.salary_account_csv_enabled||0)}</b></div></div>${gaps.length?`<div class="gap-list">${gaps.map(x=>`<div class="gap-item ${x.level==='P0'?'P0':'P1'}"><span class="tag ${x.level==='P0'?'FAILED':'P1'}">${esc(x.level)}</span><div><b>${esc(x.item)}</b><p>${esc(x.detail)}</p></div></div>`).join('')}</div>`:''}<div class="summary-panel"><b>数据准备</b><p>需要补账号、参数或环境能力时，平台只提示缺口；具体采用运行参数还是账号槽位由用例结构决定。</p><button class="small" onclick="showMultiAccountContextModal()">查看</button></div></div>`
}

function showMultiAccountContextModal(){
  let m=data.multi_account_context||{},roles=m.roles||[],policy=m.variable_policy||{},contract=m.csv_contract||{};
  $('#modalBody').innerHTML=`<h2>运行数据上下文</h2><p class="policy-note">平台从测试用例判断需要单账号、双角色还是多流程账号槽位。这里主要用于确认数据是否够跑，不展示内部决策细节。</p><h3>数据入口</h3><table><tbody><tr><th>账号数据</th><td>${esc(contract.account_csv||'-')}</td></tr><tr><th>申请人数据</th><td>${esc(contract.applicant_csv||'-')}</td></tr><tr><th>模板目录</th><td>${esc(contract.template_dir||'-')}</td></tr><tr><th>规则</th><td>${esc(contract.rule||'')}</td></tr></tbody></table><h3>角色</h3><div class="endpoint-matrix">${roles.map(x=>`<div class="endpoint-card"><span class="tag">ROLE</span><h3>${esc(x.role)}</h3><p>${esc(x.purpose)}</p></div>`).join('')}</div><h3>变量命名</h3><table><tbody><tr><th>财富等级</th><td>${esc((policy.wealth||[]).join('、'))}</td></tr><tr><th>工资交易</th><td>${esc((policy.salary_trade||[]).join('、'))}</td></tr><tr><th>规则</th><td>${esc(policy.rule||'')}</td></tr></tbody></table>`;
  $('#modal').classList.remove('hidden')
}

function accountStrategyHtml(){
  let m=data.multi_account_context||{},strategies=m.requirement_strategies||[],rules=m.standard_rules||[];
  return `<div class="card"><div class="diagnosis-head"><div><h2>多账号标准化规则</h2><p>平台按测试用例判断账号模型：单账号不强制CSV，多角色和多流程才启用账号槽位。</p></div><span class="tag ${m.status==='READY'?'PASSED':'P1'}">${esc(m.status||'PENDING')}</span></div><div class="endpoint-matrix">${strategies.map(s=>`<div class="endpoint-card"><span class="tag ${s.csv_required?'P1':'PASSED'}">${esc(s.mode)}</span><h3>${esc(s.package_name||s.package_id)}</h3><p>${esc(s.blocking_rule||'')}</p><small>${esc((s.reasons||[]).join(' · '))}</small><table><thead><tr><th>角色</th><th>需要</th><th>当前</th></tr></thead><tbody>${(s.readiness||[]).map(r=>`<tr><td>${esc(r.role)}</td><td>${esc(r.needed)}</td><td><span class="tag ${r.status==='READY'?'PASSED':'P1'}">${esc(r.actual)}</span></td></tr>`).join('')}</tbody></table></div>`).join('')}</div><h3>统一规则</h3><div class="evidence-list">${rules.map(r=>`<div class="evidence-item"><b>${esc(r.mode)}</b><small>${esc(r.when)} · ${esc(r.data_source)} · ${esc(r.example)}</small></div>`).join('')}</div><h3>身份获取顺序</h3><ol>${(m.credential_resolution_order||[]).map(x=>`<li>${esc(x)}</li>`).join('')}</ol><h3>匹配规则</h3><ol>${(m.matching_rules||[]).map(x=>`<li>${esc(x)}</li>`).join('')}</ol></div>`
}

const multiAccountContextPanelBeforeStandardRules=typeof multiAccountContextPanel==='function'?multiAccountContextPanel:null;
multiAccountContextPanel=function(){
  let base=multiAccountContextPanelBeforeStandardRules?multiAccountContextPanelBeforeStandardRules():'';
  return accountStrategyHtml()+base
}

function jmeterSkillPanel(){
  let s=data.jmeter_generation_skill||{},coverage=s.coverage||[],model=s.case_model||{};
  return `<div class="card"><div class="diagnosis-head"><div><h2>JMeter 脚本生成 Skill</h2><p>把“测试用例如何生成 JMX”沉淀成平台规则：线程组、请求、CSV参数化、断言、监听器、压测模型和指标回收。</p></div><span class="tag ${s.status==='READY'?'PASSED':'P1'}">${esc(s.status||'PENDING')}</span></div><div class="metrics"><div class="metric"><span>规则覆盖</span><b>${coverage.filter(x=>x.status==='READY').length}/${coverage.length||0}</b></div><div class="metric"><span>业务流</span><b>${esc(model.flows||0)}</b></div><div class="metric"><span>可脚本化</span><b>${esc(model.ready_flows||0)}</b></div><div class="metric"><span>待补条件</span><b>${esc(model.gaps||0)}</b></div></div><div class="summary-panel"><b>生成标准</b><p>${esc(s.summary||'')}</p><button class="small" onclick="showJmeterSkillModal()">查看规则</button></div></div>`
}

function showJmeterSkillModal(){
  let s=data.jmeter_generation_skill||{},coverage=s.coverage||[],outputs=s.output_contract||[];
  $('#modalBody').innerHTML=`<h2>JMeter 脚本生成 Skill</h2><p class="policy-note">这是平台内部生成规范，不是页面说明。后续从测试用例生成 JMX 时，必须按这套结构生成可维护、可打开、可回收报告的脚本。</p><h3>规则覆盖</h3><table><thead><tr><th>能力</th><th>状态</th></tr></thead><tbody>${coverage.map(x=>`<tr><td>${esc(x.name)}</td><td><span class="tag ${x.status==='READY'?'PASSED':'P1'}">${esc(x.status)}</span></td></tr>`).join('')}</tbody></table><h3>输出物</h3><div class="evidence-list">${outputs.map(x=>`<div class="evidence-item"><b>${esc(x)}</b></div>`).join('')}</div><p><code>${esc(s.path||'')}</code></p>`;
  $('#modal').classList.remove('hidden')
}

const qualityProfilePanelBeforeConfigYaml=qualityProfilePanel;
qualityProfilePanel=function(){
  return environmentConfigPanel()+qualityProfilePanelBeforeConfigYaml()+multiAccountContextPanel()
}

const toolchainPanelBeforeJmeterSkill=toolchainPanel;
toolchainPanel=function(){
  return jmeterSkillPanel()+toolchainPanelBeforeJmeterSkill()
}

function salaryTradeJmeterMappingCard(){
  let m=data.salary_trade_jmeter_mapping||{},ready=m.status==='READY';
  return `<div class="card"><div class="diagnosis-head"><div><h2>JMeter 执行映射</h2><p>回收外部 JMeter 运行结果，把需求包、测试用例、业务流程、订单号和数据证据归档到同一份报告。</p></div><span class="tag ${ready?'PASSED':'P1'}">${esc(m.status||'PENDING')}</span></div><div class="metrics"><div class="metric"><span>流程模型</span><b>${esc(m.flows||0)}</b></div><div class="metric"><span>JTL样本</span><b>${esc(m.jtl_rows||0)}</b></div><div class="metric"><span>映射变量</span><b>${esc((m.sample_variables||[]).length)}</b></div><div class="metric"><span>状态</span><b style="font-size:20px">${ready?'可归档':'需运行'}</b></div></div><p>${esc(m.message||'先用对应需求包的JMeter脚本运行一次，再回收执行报告。')}</p><div class="formrow"><button class="small" onclick="showJmeterScriptChooser()">选择脚本</button><button class="primary" onclick="harvestSalaryTradeJmeter()">回收执行报告</button></div><div id="salaryJmeterMappingResult"></div></div>`
}

async function harvestSalaryTradeJmeter(){
  let box=$('#salaryJmeterMappingResult');
  if(box)box.innerHTML='<div class="summary-panel"><b>正在回收 JMeter 结果</b><p>平台正在读取JTL、匹配流程和订单号，并调用MySQL证据核查。</p></div>';
  try{
    let runId=await ensureRequirementRunContext();
    let x=await api(`/api/projects/${current}/salary-trade/jmeter-harvest`,{method:'POST',body:JSON.stringify({run_id:runId})});
    let s=x.summary||{};
    if(box)box.innerHTML=`<div class="summary-panel"><b>${esc(x.status)} · 执行报告已归档</b><p>${esc(x.requirement||'当前需求包')} · 流程 ${esc(s.flows_passed||0)}/${esc(s.flows_total||0)} 通过 · DB证据 ${esc(s.db_passed||0)} 通过 · JMeter ${esc(s.jmeter_requests||0)} 次 · 错误率 ${esc(s.jmeter_error_rate||0)}%</p>${(x.warnings||[]).length?`<p>${esc((x.warnings||[]).join('；'))}</p>`:''}${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">查看执行报告</button>`:''}</div>`;
    toast(`JMeter执行报告回收完成：${x.status}`,x.status==='PASSED'?'success':x.status==='FAILED'?'error':'warning');
    await openProject(current);
    switchTab('reports')
  }catch(e){
    if(box)box.innerHTML=`<div class="summary-panel"><b>回收失败</b><p>${esc(e.message)}</p></div>`;
    toast(e.message,'error')
  }
}

const toolchainPanelBeforeSalaryMapping=toolchainPanel;
toolchainPanel=function(){
  return salaryTradeJmeterMappingCard()+toolchainPanelBeforeSalaryMapping()
}

function hubCounts(){
  let reports=data.generated_reports||[],groups=typeof requirementAssetGroups==='function'?requirementAssetGroups():[];
  return {
    sources:(data.sources||[]).length,
    requirements:(data.requirement_items||[]).length,
    points:(data.points||[]).length,
    cases:(data.cases||[]).length,
    endpoints:(data.endpoints||[]).length,
    reports:reports.length,
    jmeterReports:reports.filter(x=>/JMeter/.test(x.kind||x.name||'')).length,
    evidenceReports:reports.filter(x=>/数据|证据|映射/.test(x.kind||x.name||'')).length,
    groups
  }
}

function requirementPackageBoard(){
  let c=hubCounts(),groups=c.groups;
  if(!groups.length)return `<div class="card empty"><b>暂无需求包</b><p>先导入需求资料或接口文档，平台会按需求自动归纳。</p><button class="primary" onclick="showSourceModal()">导入资料</button></div>`;
  return `<div class="card"><div class="diagnosis-head"><div><h2>需求包</h2><p>需求、接口、测试点、测试用例和脚本映射都归到需求包里，不再散落在多个页面。</p></div><span class="tag PASSED">${groups.length} 个</span></div><div class="endpoint-matrix">${groups.map((g,i)=>{let jmeter=groupHasSalaryTrade(g),status=g.cases.length&&g.endpoints.length?'PASSED':g.cases.length||g.endpoints.length?'P1':'NOT_RUN';return `<div class="endpoint-card"><span class="tag ${status}">${esc(status==='PASSED'?'已归纳':status==='P1'?'待补齐':'资料')}</span><h3>${esc(g.label)}</h3><p>${esc(assetGroupSummary(g))}</p><div class="formrow"><button class="primary" onclick="showRequirementAssetGroup(${i},'overview')">打开</button><button class="small" onclick="showRequirementAssetGroup(${i},'maintain')">维护</button>${jmeter?`<button class="small" onclick="showRequirementAssetGroup(${i},'jmeter')">脚本</button>`:''}</div></div>`}).join('')}</div></div>`
}

function unifiedExecutionFlow(){
  let map=data.salary_trade_jmeter_mapping||{},m=data.case_jmeter_model||{},flows=m.flows||[],ready=flows.filter(x=>x.automation_status==='ready').length;
  return `<div class="card"><div class="diagnosis-head"><div><h2>执行闭环</h2><p>所有执行动作收敛到这里：资产生成、脚本生成、打开 JMeter、回收报告、数据证据核查。</p></div><span class="tag ${map.status==='READY'?'PASSED':'P1'}">${esc(map.status||'PENDING')}</span></div><div class="quality-flow compact-flow">${[
    ['1','生成测试资产',`${hubCounts().cases}条用例 · ${hubCounts().endpoints}个接口`],
    ['2','生成JMeter脚本',`${flows.length||0}条流程 · ${ready}条可脚本化`],
    ['3','打开外部工具','真实JMeter GUI加载线程组'],
    ['4','回收执行报告',`${map.jtl_rows||0}条JTL采样 · ${(map.sample_variables||[]).length}个映射变量`]
  ].map(x=>`<div class="quality-step"><span class="tag PASSED">${x[0]}</span><b>${x[1]}</b><small>${esc(x[2])}</small></div>`).join('')}</div><div class="hub-action-row"><button class="primary" onclick="runPipeline()">生成测试资产</button><button class="primary" onclick="generateJmeterFromCases()">生成JMeter脚本</button><button class="small" onclick="showJmeterScriptChooser()">选择并打开JMeter</button><button class="small" onclick="harvestSalaryTradeJmeter()">回收执行报告</button><button class="small" onclick="switchTab('reports')">查看报告</button></div><div id="salaryJmeterMappingResult"></div></div>`
}

function unifiedDataEvidenceSummary(){
  let s=typeof dataEvidenceStatus==='function'?dataEvidenceStatus():{},reports=hubCounts().evidenceReports,runs=((data.consistency||{}).runs||[]).length;
  return `<div class="card"><div class="diagnosis-head"><div><h2>数据证据</h2><p>数据库和 Redis 不铺成配置清单，需要核查时按需求调用，结果进入报告。</p></div><span class="tag ${(s.dbReady||s.redisReady)?'PASSED':'P1'}">${(s.dbReady||s.redisReady)?'可调用':'待接入'}</span></div><div class="metrics"><div class="metric"><span>MySQL</span><b>${s.dbReady?'可查':'待配置'}</b></div><div class="metric"><span>Redis</span><b>${s.redisReady?'可读':'按需'}</b></div><div class="metric"><span>核查记录</span><b>${runs}</b></div><div class="metric"><span>证据报告</span><b>${reports}</b></div></div><div class="hub-action-row"><button class="primary" onclick="autoEvidenceCheck()">自动核查</button><button class="small" onclick="showManualEvidenceCheckModal()">指定核查</button><button class="small" onclick="switchTab('reports')">证据报告</button></div></div>`
}

function unifiedDeliverySummary(){
  let c=hubCounts(),latest=(data.generated_reports||[])[0];
  return `<div class="card"><div class="diagnosis-head"><div><h2>交付归档</h2><p>最后只看报告中心：测试结论、性能结果、数据证据、失败风险和原始文件统一归档。</p></div><span class="tag ${c.reports?'PASSED':'P1'}">${c.reports} 份</span></div><div class="summary-panel"><b>最新结论</b><p>${esc(latest?`${latest.name} · ${latest.summary}`:'暂无正式报告，完成一次执行或回收后生成。')}</p><button class="small" onclick="switchTab('reports')">进入</button></div><div class="hub-action-row"><button class="small" onclick="createDeliveryPackage()">生成交付包</button><button class="small" onclick="showApifoxEnterpriseFlow()">Apifox企业链路</button><button class="small" onclick="downloadExport()">导出资产</button></div></div>`
}

function unifiedQualityWorkspace(){
  let c=hubCounts(),maturity=typeof trunkMaturity==='function'?trunkMaturity():qualityHubMaturity();
  return `<div class="card quality-hero"><span class="tag">QUALITY HUB</span><h2>质量中枢工作台</h2><p>把资料、需求包、测试资产、JMeter脚本、外部执行、数据证据和报告交付归纳成一条链路。需要维护时进需求包，需要执行时走执行闭环，最后统一看报告。</p><div class="quality-flow">${[
    ['需求包',c.groups.length,`${c.sources}份资料 · ${c.requirements}条需求`,'sources'],
    ['测试资产',c.cases||c.points,`${c.points}个测试点 · ${c.cases}条用例`,'sources'],
    ['执行闭环',c.endpoints||c.jmeterReports,`${c.endpoints}个接口 · ${c.jmeterReports}份JMeter报告`,'automation'],
    ['报告交付',c.reports,`${c.reports}份报告 · ${c.evidenceReports}份证据`,'reports']
  ].map(x=>`<button class="quality-step ${x[1]?'':'pending'}" onclick="switchTab('${x[3]}')">${hubStatus(x[1])}<b>${x[0]}</b><small>${esc(x[2])}</small></button>`).join('')}</div></div><div class="metrics"><div class="metric"><span>成熟度</span><b>${maturity}%</b></div><div class="metric"><span>需求包</span><b>${c.groups.length}</b></div><div class="metric"><span>用例</span><b>${c.cases}</b></div><div class="metric"><span>报告</span><b>${c.reports}</b></div></div>${requirementPackageBoard()}<div class="card"><div class="diagnosis-head"><div><h2>继续工作</h2><p>总览只负责判断状态。维护、执行和报告分别进入对应工作区。</p></div></div><div class="hub-action-row primary-actions"><button class="primary" onclick="switchTab('sources')">维护需求资产</button><button class="primary" onclick="switchTab('automation')">进入执行中心</button><button class="primary" onclick="switchTab('reports')">查看报告中心</button></div></div>`
}

function compactToolSettingsPanel(){
  return `<details class="card compact-details"><summary><b>环境与工具配置</b><span>YAML、账号上下文、JMeter Skill、工具链预检</span></summary>${environmentConfigPanel()}${multiAccountContextPanel()}${jmeterSkillPanel()}</details>`
}

tableQualityHub=function(){
  return unifiedQualityWorkspace()+compactToolSettingsPanel()
}

compactAssetsWorkspace=function(){
  return `<div class="card quality-hero"><span class="tag">REQUIREMENT PACKAGES</span><h2>需求资产</h2><p>这里只做资料和需求包维护。生成脚本、打开JMeter、回收报告全部去执行闭环。</p><div class="hub-action-row"><button class="primary" onclick="showSourceModal()">导入需求资料</button><button class="primary" onclick="showInterfaceDocModal()">导入接口文档</button><button class="small" onclick="runPipeline()">生成测试资产</button><button class="small" onclick="downloadInterfaceDocument()">导出接口基线</button></div></div>${requirementPackageBoard()}`
}

toolchainPanel=function(){
  return unifiedExecutionFlow()+`<details class="card compact-details"><summary><b>高级工具链</b><span>Newman / pytest / 通用JMeter / 运行参数</span></summary>${executionProfilePanel()}${jmeterSkillPanel()}${salaryTradeJmeterMappingCard()}${toolchainPanelBeforeSalaryMapping?toolchainPanelBeforeSalaryMapping():''}</details>`
}

executionCenter=function(){
  return `<div class="card quality-hero"><span class="tag">EXECUTION</span><h2>执行中心</h2><p>执行动作只保留一条主链路：生成测试资产、生成JMeter脚本、打开外部工具、回收报告和证据。</p></div>${unifiedExecutionFlow()}${compactToolSettingsPanel()}`
}

dataQualityClosure=function(){
  return `<div class="card quality-hero"><span class="tag">DATA EVIDENCE</span><h2>数据证据</h2><p>数据源只作为证据连接器，不再和主流程混在一起。需要核查时自动或指定调用，结果统一进入报告中心。</p></div>${unifiedDataEvidenceSummary()}<details class="card compact-details"><summary><b>查看数据核查明细</b><span>MySQL只读查询、规则记录、最近核查</span></summary>${mysqlEvidencePanel()}${tableConsistency()}</details>`
}

professionalizeWorkspace=function(){
  professionalLabels();
  if($('#overview'))$('#overview').innerHTML=unifiedQualityWorkspace();
  if($('#sources'))$('#sources').innerHTML=compactAssetsWorkspace();
  if($('#automation'))$('#automation').innerHTML=executionCenter();
  if($('#dataquality'))$('#dataquality').innerHTML=dataQualityClosure();
  if($('#reports'))$('#reports').innerHTML=packageReportCenter();
  if(data?.project){switchTab($('.side-tab.active')?.dataset.tab||'overview')}
}

function copyText(value){
  if(!value)return;
  navigator.clipboard?.writeText(value).then(()=>toast('已复制路径')).catch(()=>toast(value))
}

function showJmeterScriptChooser(){
  let p=salaryTradeScriptPaths(),wealth='D:\\apache-jmeter-5.6.3\\jmx\\20260826\\性能基线.jmx';
  $('#modalBody').innerHTML=`<h2>选择 JMeter 脚本</h2><p class="policy-note">先选择本次要打开的需求脚本。平台不会默认打开财富等级，避免不同需求混在一起。</p><div class="endpoint-matrix"><div class="endpoint-card"><span class="tag PASSED">当前复杂需求</span><h3>工资代理快速结算</h3><p>独立 JMX、独立 JTL、支持流程/订单号/DB证据映射。</p><code>${esc(p.jmx)}</code><button class="primary" onclick="openJmeterWorkbench('salary_trade')">打开这个脚本</button></div><div class="endpoint-card"><span class="tag">专项需求</span><h3>财富等级</h3><p>财富等级专项脚本，和工资交易分开维护、分开报告。</p><code>${esc(wealth)}</code><button class="small" onclick="openJmeterWorkbench('wealth_level')">打开这个脚本</button></div></div>`;
  $('#modal').classList.remove('hidden')
}

function salaryTradeScriptPaths(){
  let m=data.case_jmeter_model||{},map=data.salary_trade_jmeter_mapping||{},art=m.artifacts||{};
  return {
    jmx:art.jmx||map.jmx_path||'C:\\Users\\DELL\\Documents\\Codex\\2026-08-19\\new-chat\\outputs\\AutoTest-AI\\outputs\\salary-trade-case-driven.jmx',
    launcher:art.launcher||'C:\\Users\\DELL\\Documents\\Codex\\2026-08-19\\new-chat\\outputs\\AutoTest-AI\\outputs\\open-salary-trade-state-machine.ps1',
    manifest:art.manifest||map.manifest_path||'C:\\Users\\DELL\\Documents\\Codex\\2026-08-19\\new-chat\\outputs\\AutoTest-AI\\outputs\\salary-trade-case-jmeter-manifest.json',
    jtl:map.jtl_path||'D:\\apache-jmeter-5.6.3\\jmx\\20260826\\工资代理结算-result.jtl'
  }
}

function salaryTradeScriptPathCard(){
  let p=salaryTradeScriptPaths();
  return `<div class="card script-path-card"><div class="diagnosis-head"><div><h2>当前需求脚本位置</h2><p>正式执行只看这三类文件：JMeter脚本、启动脚本、结果文件。具体属于哪个需求包，在报告里归档。</p></div><span class="tag PASSED">JMETER</span></div><div class="evidence-list">${[
    ['JMeter脚本',p.jmx,'在JMeter里打开和维护的JMX'],
    ['启动脚本',p.launcher,'用它自动准备账号、ticket和运行参数，然后打开JMeter'],
    ['映射清单',p.manifest,'平台用它把流程、用例和订单号对应起来'],
    ['结果文件',p.jtl,'JMeter运行后平台从这里回收执行报告']
  ].map(x=>`<div class="evidence-item script-path-row"><div><b>${esc(x[0])}</b><small>${esc(x[2])}</small><code>${esc(x[1])}</code></div><button class="small" onclick="copyText('${esc(x[1]).replace(/\\/g,'\\\\')}')">复制</button></div>`).join('')}</div></div>`
}

unifiedExecutionFlow=function(){
  let map=data.salary_trade_jmeter_mapping||{},m=data.case_jmeter_model||{},flows=m.flows||[],ready=flows.filter(x=>x.automation_status==='ready').length;
  return `<div class="card"><div class="diagnosis-head"><div><h2>执行闭环</h2><p>所有执行动作收敛到这里：生成测试资产、生成JMeter脚本、打开外部工具、回收报告、数据证据核查。</p></div><span class="tag ${map.status==='READY'?'PASSED':'P1'}">${esc(map.status||'PENDING')}</span></div><div class="quality-flow compact-flow">${[
    ['1','生成测试资产',`${hubCounts().cases}条用例 · ${hubCounts().endpoints}个接口`],
    ['2','生成JMeter脚本',`${flows.length||0}条流程 · ${ready}条可脚本化`],
    ['3','打开外部工具','真实JMeter GUI加载线程组'],
    ['4','回收执行报告',`${map.jtl_rows||0}条JTL采样 · ${(map.sample_variables||[]).length}个映射变量`]
  ].map(x=>`<div class="quality-step"><span class="tag PASSED">${x[0]}</span><b>${x[1]}</b><small>${esc(x[2])}</small></div>`).join('')}</div><div class="hub-action-row"><button class="primary" onclick="runPipeline()">生成测试资产</button><button class="primary" onclick="generateJmeterFromCases()">生成JMeter脚本</button><button class="small" onclick="showJmeterScriptChooser()">选择并打开JMeter</button><button class="small" onclick="harvestSalaryTradeJmeter()">回收执行报告</button><button class="small" onclick="switchTab('reports')">查看报告</button></div><div id="salaryJmeterMappingResult"></div></div>${salaryTradeScriptPathCard()}`
}

openJmeterWorkbench=async function(scriptKey){
  if(!scriptKey){
    showJmeterScriptChooser();
    return
  }
  try{
    toast('正在打开真实 JMeter，并加载所选需求脚本…');
    let runId=await ensureRequirementRunContext();
    let payload=collectJmeterWorkbenchPayload();
    payload.script_key=scriptKey;
    payload.package_id=selectedRequirementPackageId();
    payload.run_id=runId;
    let x=await api(`/api/projects/${current}/jmeter/open-gui`,{method:'POST',body:JSON.stringify(payload)});
    let s=x.summary||{},groups=s.groups||[];
    $('#modalBody').innerHTML=`<h2>JMeter 已打开</h2><p class="policy-note">已打开：${esc(x.script_name||'所选脚本')}。脚本、结果文件和报告会按需求包归档，不会和其他需求混在一起。</p><div class="metrics"><div class="metric"><span>线程组</span><b>${esc(s.thread_groups||0)}</b></div><div class="metric"><span>HTTP请求</span><b>${esc(s.http_samplers||0)}</b></div><div class="metric"><span>断言</span><b>${esc(s.assertions||0)}</b></div><div class="metric"><span>监听器</span><b>${esc(s.listeners||0)}</b></div></div>${groups.length?`<table><thead><tr><th>线程组</th><th>线程数</th><th>循环</th><th>爬升秒</th></tr></thead><tbody>${groups.map(g=>`<tr><td>${esc(g.name)}</td><td>${esc(g.threads)}</td><td>${esc(g.loops)}</td><td>${esc(g.rampup)}</td></tr>`).join('')}</tbody></table>`:''}<label>JMX</label><code>${esc(x.jmx_path||'')}</code><label>JTL</label><code>${esc(x.jtl_path||'')}</code>`;
    $('#modal').classList.remove('hidden');
    toast(x.message||'JMeter 已打开','success')
  }catch(e){toast(e.message,'error')}
}

function portableRequirementPackages(){
  return data?.requirement_packages?.packages || []
}

function packageArtifactSummary(pkg){
  let artifacts=Object.values(pkg.artifacts||{}), ready=artifacts.filter(x=>x.exists).length;
  return `${pkg.counts?.sources||0}份资料 · ${pkg.counts?.test_points||0}个测试点 · ${pkg.counts?.test_cases||0}条用例 · ${ready}/${artifacts.length||0}个文件已就绪`
}

function packageStatusModel(pkg){
  let model=pkg?.status_model||{};
  return {
    asset:model.asset_status||pkg?.status||'EMPTY',
    preflight:model.preflight_status||'NOT_RUN',
    execution:model.latest_execution_status||'NOT_RUN',
    quality:model.quality_status||'NOT_RUN',
    reason:model.quality_reason||''
  }
}

function packageStatusClass(status){
  return status==='READY'||status==='PASSED'?'PASSED':status==='FAILED'||status==='BLOCKED'?'FAILED':status==='READY_WITH_WARNINGS'||status==='ATTENTION'||status==='DRAFT'?'P1':'NOT_RUN'
}

function packageStatusStrip(pkg){
  let s=packageStatusModel(pkg);
  return `<div class="package-assets"><span class="asset-chip ${s.asset==='READY'?'ready':'pending'}">资产 ${esc(s.asset)}</span><span class="tag ${packageStatusClass(s.preflight)}">预检 ${esc(s.preflight)}</span><span class="tag ${packageStatusClass(s.execution)}">执行 ${esc(s.execution)}</span><span class="tag ${packageStatusClass(s.quality)}">质量 ${esc(s.quality)}</span></div>`
}

function requirementPackageFlowCard(){
  let catalog=data.requirement_packages||{},packages=portableRequirementPackages(),summary=catalog.summary||{};
  return `<div class="card"><div class="diagnosis-head"><div><h2>可迁移需求包流程</h2><p>每个需求独立沉淀资料、数据、脚本和报告；执行中心只按选中的需求包调工具。</p></div><span class="tag ${summary.quality_passed===summary.total&&summary.total?'PASSED':'P1'}">质量通过 ${esc(summary.quality_passed||0)}/${esc(summary.total||0)}</span></div><div class="quality-flow compact-flow">${(catalog.process||[]).map((x,i)=>`<div class="quality-step"><span class="tag PASSED">${i+1}</span><b>${esc(x.step)}</b><small>${esc(x.output)}</small></div>`).join('')}</div>${packages.length?`<div class="endpoint-matrix">${packages.map((pkg,i)=>{let s=packageStatusModel(pkg);return `<div class="endpoint-card"><span class="tag ${packageStatusClass(s.quality)}">${esc(s.quality)}</span><h3>${esc(pkg.name)}</h3><p>${esc(packageArtifactSummary(pkg))}</p>${packageStatusStrip(pkg)}<p><b>${esc(pkg.primary_tool)}</b> · ${esc(pkg.description)}</p><div class="formrow"><button class="primary" onclick="showPortableRequirementPackage(${i})">打开需求包</button>${requirementPackageId(pkg)==='salary-trade'?`<button class="small" onclick="openJmeterWorkbench('salary_trade')">打开JMeter</button>`:''}</div></div>`}).join('')}</div>`:'<div class="empty"><b>暂无需求包</b></div>'}<p class="policy-note">目录根：${esc(summary.root||'requirements')}</p></div>`
}

function showPortableRequirementPackage(index){
  let pkg=portableRequirementPackages()[index];
  if(!pkg)return toast('没有找到这个需求包','warning');
  let artifacts=Object.entries(pkg.artifacts||{}),status=packageStatusModel(pkg);
  let tools=Object.entries(pkg.tool_strategy||{});
  $('#modalBody').innerHTML=`<h2>${esc(pkg.name)}</h2><p class="policy-note">${esc(pkg.description)}</p><div class="formrow"><button class="primary" onclick="showRequirementResourceCenter('${esc(requirementPackageId(pkg))}')">资源与预检</button></div><div class="metrics"><div class="metric"><span>资产</span><b style="font-size:18px">${esc(status.asset)}</b></div><div class="metric"><span>资源预检</span><b style="font-size:18px">${esc(status.preflight)}</b></div><div class="metric"><span>最近执行</span><b style="font-size:18px">${esc(status.execution)}</b></div><div class="metric"><span>质量结论</span><b style="font-size:18px">${esc(status.quality)}</b></div></div><div class="summary-panel"><b>当前结论</b><p>${esc(status.reason||'等待平台形成质量结论。')}</p></div><h3>工具分工</h3><div class="evidence-list">${tools.map(([k,v])=>`<div class="evidence-item"><b>${esc(k)}</b><small>${esc(v)}</small></div>`).join('')}</div><h3>可迁移目录</h3><code>${esc(pkg.root||'')}</code><h3>关键资产</h3><table><thead><tr><th>资产</th><th>状态</th><th>位置</th></tr></thead><tbody>${artifacts.map(([name,item])=>`<tr><td>${esc(name)}</td><td><span class="tag ${item.exists?'PASSED':'P1'}">${item.exists?'READY':'待补'}</span></td><td><code>${esc(item.path||'')}</code></td></tr>`).join('')}</tbody></table><h3>流程</h3><ol>${(pkg.workflow||[]).map(x=>`<li>${esc(x)}</li>`).join('')}</ol><p class="policy-note">数据规则：${esc(pkg.data_policy||'')}</p>`;
  $('#modal').classList.remove('hidden')
}

function resourceManifestLines(items,type){
  if(type==='datasets')return (items||[]).map(x=>[x.role||'',x.path||'',x.purpose||''].join('|')).join('\n');
  if(type==='mysql')return (items||[]).map(x=>[x.name||'',x.purpose||''].join('|')).join('\n');
  if(type==='redis')return (items||[]).map(x=>[x.pattern||'',x.purpose||''].join('|')).join('\n');
  if(type==='runtime')return (items||[]).map(x=>typeof x==='string'?x:[x.name||'',x.value||'',x.purpose||''].join('|')).join('\n');
  if(type==='extractions')return (items||[]).map(x=>[x.variable||'',x.source||'',(x.json_paths||[]).join(',')].join('|')).join('\n');
  return ''
}

function resourceFindingHtml(item,packageId){
  let cls=item.status==='BLOCKED'?'FAILED':item.status==='WARNING'?'P1':item.status==='SUGGESTION'?'P2':'PASSED';
  let action=item.status==='CONFIRMED_IGNORED'?'':`<button class="small" onclick="ignoreRequirementResourceGap('${esc(packageId)}','${esc(item.id)}')">确认不需要</button>`;
  return `<div class="evidence-item"><div><span class="tag ${cls}">${esc(item.status)}</span> <b>${esc(item.title)}</b><small>${esc(item.reason)}</small><small>处理建议：${esc(item.next_action||'-')}</small></div>${action}</div>`
}

async function showRequirementResourceCenter(packageId){
  packageId=packageId||selectedRequirementPackageId();
  if(!packageId)return toast('当前没有需求包','warning');
  $('#modal').classList.remove('hidden');
  $('#modalBody').innerHTML='<h2>资源与预检</h2><div class="summary-panel"><b>正在检查当前需求需要哪些资源</b><p>平台会按账号模型、测试用例、场景计划和证据规则检查，不会默认强加CSV、数据库或Redis。</p></div>';
  try{
    let [manifest,preflight]=await Promise.all([
      requirementPackagesApi.resourceManifest(current,packageId),
      requirementPackagesApi.resourcePreflight(current,packageId)
    ]);
    activeResourceManifest=manifest;
    let s=preflight.summary||{},credentials=manifest.credentials||[],findings=preflight.findings||[];
    $('#modalBody').innerHTML=`<h2>${esc(requirementPackageName(packageId))} · 资源与预检</h2><p class="policy-note">${esc(preflight.policy||'')}</p><div class="metrics"><div class="metric"><span>状态</span><b style="font-size:20px">${esc(preflight.status)}</b></div><div class="metric"><span>阻断</span><b>${esc(s.blocked||0)}</b></div><div class="metric"><span>提醒</span><b>${esc(s.warnings||0)}</b></div><div class="metric"><span>建议</span><b>${esc(s.suggestions||0)}</b></div></div><h3>角色凭证</h3><div class="evidence-list">${credentials.length?credentials.map(x=>`<div class="evidence-item"><b>${esc(x.role)}</b><small>至少 ${esc(x.min_count||1)} 个 · 必填 ${esc((x.required_fields||[]).join('、')||'-')} · 来源 ${esc((x.sources||[]).map(y=>y.type).join('、')||'未登记')}</small></div>`).join(''):'<div class="empty">当前需求没有声明账号角色</div>'}</div><h3>预检结论</h3><div class="evidence-list" id="resourcePreflightFindings">${findings.length?findings.map(x=>resourceFindingHtml(x,packageId)).join(''):'<div class="summary-panel"><b>当前没有发现资源缺口</b></div>'}</div><details class="compact-details" open><summary><b>维护资源登记</b><span>只影响当前需求包</span></summary><label>账号/参数文件</label><textarea id="resourceDatasets" rows="5" placeholder="角色|文件路径|用途">${esc(resourceManifestLines(manifest.datasets,'datasets'))}</textarea><label>数据库表</label><textarea id="resourceMysqlTables" rows="5" placeholder="表名|用途">${esc(resourceManifestLines(manifest.mysql_tables,'mysql'))}</textarea><label>Redis Key模式</label><textarea id="resourceRedisPatterns" rows="4" placeholder="Key模式|用途；不需要可留空">${esc(resourceManifestLines(manifest.redis_patterns,'redis'))}</textarea><label>运行参数</label><textarea id="resourceRuntimeParameters" rows="3" placeholder="参数名|测试值|用途；Token/密码请使用运行环境，不要写入这里">${esc(resourceManifestLines(manifest.runtime_parameters,'runtime'))}</textarea><label>接口变量提取</label><textarea id="resourceExtractions" rows="4" placeholder="变量名|来源接口|JSON路径1,JSON路径2">${esc(resourceManifestLines(manifest.variable_extractions,'extractions'))}</textarea><div class="formrow"><button class="primary" onclick="saveRequirementResourceManifest('${esc(packageId)}')">保存并重新预检</button></div></details><p class="policy-note">资源清单：${esc(manifest.path||'')}</p>`;
  }catch(e){
    $('#modalBody').innerHTML=`<h2>资源与预检失败</h2><div class="summary-panel"><b>${esc(e.message)}</b></div>`
  }
}

function parseResourceLines(id,mapper){
  return ($('#'+id)?.value||'').split(/\r?\n/).map(x=>x.trim()).filter(Boolean).map(line=>mapper(line.split('|').map(x=>x.trim())))
}

async function saveRequirementResourceManifest(packageId){
  try{
    let payload={
      credentials:activeResourceManifest?.credentials||[],
      datasets:parseResourceLines('resourceDatasets',x=>({id:(x[0]||'dataset').replace(/\W+/g,'_'),role:x[0]||'',type:(x[1]||'').toLowerCase().endsWith('.xlsx')?'excel':'csv',path:x[1]||'',purpose:x[2]||''})),
      mysql_tables:parseResourceLines('resourceMysqlTables',x=>({name:x[0]||'',purpose:x[1]||'',required:true})),
      redis_patterns:parseResourceLines('resourceRedisPatterns',x=>({pattern:x[0]||'',purpose:x[1]||'',required:false})),
      runtime_parameters:parseResourceLines('resourceRuntimeParameters',x=>({name:x[0]||'',value:x[1]||'',purpose:x[2]||''})),
      variable_extractions:parseResourceLines('resourceExtractions',x=>({variable:x[0]||'',source:x[1]||'',json_paths:(x[2]||'').split(',').map(y=>y.trim()).filter(Boolean),required:true})),
      confirmed_ignored:activeResourceManifest?.confirmed_ignored||[]
    };
    await requirementPackagesApi.saveResourceManifest(current,packageId,payload);
    toast('资源登记已保存，正在重新预检','success');
    await showRequirementResourceCenter(packageId)
  }catch(e){toast(e.message,'error')}
}

async function ignoreRequirementResourceGap(packageId,gapId){
  try{
    await requirementPackagesApi.saveResourceManifest(current,packageId,{confirm_ignore_gap_id:gapId});
    toast('已记录为当前需求不需要，不再重复提醒','success');
    await showRequirementResourceCenter(packageId)
  }catch(e){toast(e.message,'error')}
}

const tableQualityHubBeforePortablePackages=tableQualityHub;
tableQualityHub=function(){
  return requirementPackageFlowCard()+tableQualityHubBeforePortablePackages()
}

const compactAssetsWorkspaceBeforePortablePackages=compactAssetsWorkspace;
compactAssetsWorkspace=function(){
  return requirementPackageFlowCard()+compactAssetsWorkspaceBeforePortablePackages()
}

function requirementPackageId(pkg){
  return pkg?.package_id || pkg?.id || ''
}

function selectedRequirementPackageId(){
  let packages=portableRequirementPackages();
  let saved=localStorage.getItem('autotest_selected_requirement_package')||'';
  if(packages.some(pkg=>requirementPackageId(pkg)===saved))return saved;
  return requirementPackageId(packages.find(pkg=>pkg.status==='READY')||packages[0]||{})
}

async function setSelectedRequirementPackage(id){
  if(!id)return;
  localStorage.setItem('autotest_selected_requirement_package',id);
  await loadRequirementReportIndex(id);
  render();
  toast(`已选择需求包：${requirementPackageName(id)}`,'success')
}

function requirementPackageName(id){
  let pkg=portableRequirementPackages().find(x=>requirementPackageId(x)===id);
  return pkg?.name || id || '未选择'
}

function requirementPackageOptionsHtml(selected){
  let packages=portableRequirementPackages();
  return packages.map(pkg=>`<option value="${esc(requirementPackageId(pkg))}" ${requirementPackageId(pkg)===selected?'selected':''}>${esc(pkg.name)} · ${esc(packageStatusModel(pkg).quality)}</option>`).join('')
}

function currentRequirementPackage(){
  let id=selectedRequirementPackageId();
  return portableRequirementPackages().find(pkg=>requirementPackageId(pkg)===id)||portableRequirementPackages()[0]||{}
}

function requirementRunStorageKey(packageId){
  return `autotest_requirement_run_${current||'project'}_${packageId}`
}

function reportRunStorageKey(packageId){
  return `autotest_report_run_${current||'project'}_${packageId}`
}

function activeRequirementRunId(packageId=selectedRequirementPackageId()){
  return localStorage.getItem(requirementRunStorageKey(packageId))||''
}

function selectedReportRunId(packageId=selectedRequirementPackageId()){
  let saved=localStorage.getItem(reportRunStorageKey(packageId))||'';
  let index=data?.requirement_report_indexes?.[packageId]||{},runs=index.runs||[];
  return runs.some(x=>x.run_id===saved)?saved:(index.latest_run_id||runs[0]?.run_id||'')
}

function setSelectedReportRun(packageId,runId){
  if(runId)localStorage.setItem(reportRunStorageKey(packageId),runId);
  render();
  switchTab('reports')
}

async function loadRequirementReportIndex(packageId=selectedRequirementPackageId()){
  if(!current||!packageId)return null;
  data.requirement_report_indexes=data.requirement_report_indexes||{};
  try{
    let index=await requirementPackagesApi.reportIndex(current,packageId);
    data.requirement_report_indexes[packageId]=index;
    return index
  }catch(e){
    data.requirement_report_indexes[packageId]={status:'ERROR',runs:[],latest_reports:[],history:[],message:e.message};
    return data.requirement_report_indexes[packageId]
  }
}

let requirementReportPollBusy=false;

function requirementReportFingerprint(index){
  return JSON.stringify((index?.runs||[]).map(x=>[x.run_id,x.status,x.updated_at,x.report_count]))
}

async function pollRequirementReportChanges(){
  let reports=$('#reports'),packageId=selectedRequirementPackageId();
  if(requirementReportPollBusy||!current||!packageId||!reports||reports.classList.contains('hidden'))return;
  requirementReportPollBusy=true;
  try{
    let before=requirementReportFingerprint(currentPackageReportIndex());
    let index=await loadRequirementReportIndex(packageId);
    let after=requirementReportFingerprint(index);
    if(before!==after){
      render();
      switchTab('reports');
      toast('当前运行批次已回收新的执行报告','success')
    }
  }catch{}finally{requirementReportPollBusy=false}
}

setInterval(pollRequirementReportChanges,8000);

async function ensureRequirementRunContext(forceNew=false){
  let pkg=currentRequirementPackage(),packageId=requirementPackageId(pkg);
  if(!packageId)throw new Error('当前没有可执行的需求包');
  let runId=forceNew?'':activeRequirementRunId(packageId);
  if(runId)return runId;
  let context=await requirementPackagesApi.createRun(current,packageId,{name:`${pkg.name} · 手工执行批次`});
  localStorage.setItem(requirementRunStorageKey(packageId),context.run_id);
  localStorage.setItem(reportRunStorageKey(packageId),context.run_id);
  await loadRequirementReportIndex(packageId);
  return context.run_id
}

async function startNewRequirementRun(){
  try{
    let runId=await ensureRequirementRunContext(true),pkg=currentRequirementPackage();
    toast(`${pkg.name} 已创建空运行批次，请继续在执行中心运行工具生成报告`,'success');
    render();
    switchTab('automation')
  }catch(e){toast(e.message,'error')}
}

const openProjectBeforePackageReportIndex=openProject;
openProject=async function(id){
  await openProjectBeforePackageReportIndex(id);
  await Promise.all(portableRequirementPackages().map(pkg=>loadRequirementReportIndex(requirementPackageId(pkg))));
  render()
}

async function generateSelectedRequirementPackageAssets(){
  let pkg=currentRequirementPackage(),packageId=requirementPackageId(pkg);
  if(!packageId)return toast('当前没有可生成的需求包','warning');
  try{
    toast(`正在为 ${pkg.name} 生成工具资产…`);
    let x=await requirementPackagesApi.toolAssets(current,packageId,collectJmeterWorkbenchPayload());
    let files=x.generated||[];
    $('#modalBody').innerHTML=`<h2>${esc(pkg.name)} · 工具资产已生成</h2><p class="policy-note">本次只写入当前需求包目录。Newman、JMeter、pytest 分开保存，报告后续也按需求包归档。</p><div class="metrics"><div class="metric"><span>状态</span><b>${esc(x.status)}</b></div><div class="metric"><span>文件</span><b>${esc(files.length)}</b></div><div class="metric"><span>需求包</span><b style="font-size:20px">${esc(packageId)}</b></div></div>${(x.warnings||[]).length?`<div class="summary-panel"><b>生成提醒</b><p>${esc((x.warnings||[]).join('；'))}</p></div>`:''}<h3>生成文件</h3><div class="evidence-list">${files.map(f=>`<div class="evidence-item"><b>${esc(f.tool||'asset')}</b><small>${esc(f.path||'')}</small></div>`).join('')}</div><label>资产清单</label><code>${esc(x.manifest_path||'')}</code>`;
    $('#modal').classList.remove('hidden');
    toast(`${pkg.name} 工具资产生成完成`,'success');
    await openProject(current);
    switchTab('automation')
  }catch(e){toast(e.message,'error')}
}

async function generateSelectedRequirementApiTestCases(){
  let pkg=currentRequirementPackage(),packageId=requirementPackageId(pkg);
  if(!packageId)return toast('当前没有可生成接口测试用例的需求包','warning');
  try{
    toast(`正在按Schema生成 ${pkg.name} 的接口测试用例…`);
    let x=await requirementPackagesApi.apiTestCases(current,packageId,{}),s=x.summary||{},dimensions=s.dimensions||{};
    let dimensionRows=Object.entries(dimensions).map(([name,count])=>`<div class="evidence-item"><b>${esc(name)}</b><small>${esc(count)} 条用例</small></div>`).join('');
    $('#modalBody').innerHTML=`<h2>${esc(pkg.name)} · Schema接口测试用例设计</h2><p class="policy-note">这是接口测试专用设计，独立于需求业务测试用例。它根据OpenAPI字段约束生成契约、等价类、边界值、认证、异常、可靠性、并发和隔离安全场景；不会替代业务流程、多角色和状态流转用例。</p><div class="metrics"><div class="metric"><span>状态</span><b style="font-size:20px">${esc(x.status)}</b></div><div class="metric"><span>接口</span><b>${esc(s.interfaces||0)}</b></div><div class="metric"><span>接口用例</span><b>${esc(s.cases||0)}</b></div><div class="metric"><span>待复核</span><b>${esc(s.review_required||0)}</b></div></div>${x.message?`<div class="summary-panel"><b>需要补充</b><p>${esc(x.message)}</p></div>`:`<h3>接口测试维度</h3><div class="evidence-list">${dimensionRows}</div>`}<div class="hub-action-row">${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">查看JSON</button>`:''}${x.markdown_url?`<button class="small" onclick="openReport('${esc(x.markdown_url)}')">查看Markdown</button>`:''}${x.xlsx_url?`<button class="primary" onclick="openDownload('${esc(x.xlsx_url)}')">下载接口用例Excel</button>`:''}</div><label>接口用例Skill契约</label><code>${esc(x.skill_contract||'')}</code>`;
    $('#modal').classList.remove('hidden');
    toast(`${pkg.name} 接口测试用例已生成：${s.cases||0}条`,'success')
  }catch(e){toast(e.message,'error')}
}

async function compileSelectedRequirementInterfaceTests(){
  let pkg=currentRequirementPackage(),packageId=requirementPackageId(pkg);
  if(!packageId)return toast('当前没有可编译接口测试脚本的需求包','warning');
  try{
    toast(`正在把 ${pkg.name} 的接口测试用例编译为Newman集合…`);
    let x=await requirementPackagesApi.compileInterfaceTests(current,packageId,{}),s=x.summary||{};
    $('#modalBody').innerHTML=`<h2>${esc(pkg.name)} · 接口测试脚本</h2><p class="policy-note">脚本仅来自接口测试用例设计，不包含复杂业务场景和性能测试计划。</p><div class="metrics"><div class="metric"><span>状态</span><b>${esc(x.status)}</b></div><div class="metric"><span>接口用例</span><b>${esc(s.source_cases||0)}</b></div><div class="metric"><span>已编译</span><b>${esc(s.compiled_newman_cases||0)}</b></div><div class="metric"><span>其他工具/待复核</span><b>${esc(s.skipped_cases||0)}</b></div></div><div class="hub-action-row">${x.collection_url?`<button class="primary" onclick="openReport('${esc(x.collection_url)}')">查看Newman集合</button>`:''}${x.manifest_url?`<button class="small" onclick="openReport('${esc(x.manifest_url)}')">查看用例映射</button>`:''}<button class="primary" onclick="runSelectedRequirementInterfaceTests()">运行接口测试</button></div>`;
    $('#modal').classList.remove('hidden');
    toast(`${pkg.name} 接口测试脚本已生成：${s.compiled_newman_cases||0}条`,'success')
  }catch(e){toast(e.message,'error')}
}

async function runSelectedRequirementInterfaceTests(){
  let pkg=currentRequirementPackage(),packageId=requirementPackageId(pkg);
  if(!packageId)return toast('当前没有可运行接口测试的需求包','warning');
  try{
    toast(`正在执行 ${pkg.name} 的接口测试用例…`);
    let x=await requirementPackagesApi.runInterfaceTests(current,packageId,{}),s=x.summary||{};
    $('#modalBody').innerHTML=`<h2>${esc(pkg.name)} · 接口测试执行结果</h2><p class="policy-note">该结果按接口用例ID回收，与复杂业务场景报告、性能报告分别保存。</p><div class="metrics"><div class="metric"><span>状态</span><b>${esc(x.status)}</b></div><div class="metric"><span>执行</span><b>${esc(s.executed_cases||0)}</b></div><div class="metric"><span>通过</span><b>${esc(s.passed_cases||0)}</b></div><div class="metric"><span>失败</span><b>${esc(s.failed_cases||0)}</b></div></div>${x.message?`<div class="summary-panel"><b>当前阻断</b><p>${esc(x.message)}</p></div>`:''}<div class="hub-action-row">${x.json_url?`<button class="primary" onclick="openReport('${esc(x.json_url)}')">查看接口测试报告</button>`:''}${x.raw_report_url?`<button class="small" onclick="openReport('${esc(x.raw_report_url)}')">查看Newman原始报告</button>`:''}</div>`;
    $('#modal').classList.remove('hidden');
    toast(`${pkg.name} 接口测试：${x.status}`,x.status==='PASSED'?'success':'warning');
    await openProject(current)
  }catch(e){toast(e.message,'error')}
}

function jmeterScriptKeyForPackage(packageId){
  return packageId
}

function requirementPackageSelectorHtml(){
  let packages=portableRequirementPackages(),selected=selectedRequirementPackageId(),pkg=currentRequirementPackage();
  if(!packages.length)return `<div class="card empty"><b>暂无需求包</b><p>先导入需求资料或接口文档。</p></div>`;
  return `<div class="card selected-package-card"><div class="diagnosis-head"><div><h2>当前执行需求包</h2><p>先选需求包，再生成脚本、打开JMeter、回收报告。这样财富等级、工资交易和后续新需求不会混在一起。</p></div><span class="tag ${pkg.status==='READY'?'PASSED':'P1'}">${esc(pkg.status||'PENDING')}</span></div><div class="formrow"><select id="requirementPackageSelect" onchange="setSelectedRequirementPackage(this.value)">${requirementPackageOptionsHtml(selected)}</select><button class="small" onclick="showPortableRequirementPackage(portableRequirementPackages().findIndex(x=>requirementPackageId(x)===selectedRequirementPackageId()))">查看需求包</button></div><div class="metrics"><div class="metric"><span>资料</span><b>${esc(pkg.counts?.sources||0)}</b></div><div class="metric"><span>测试点</span><b>${esc(pkg.counts?.test_points||0)}</b></div><div class="metric"><span>用例</span><b>${esc(pkg.counts?.test_cases||0)}</b></div><div class="metric"><span>主工具</span><b style="font-size:20px">${esc(pkg.primary_tool||'-')}</b></div></div><p class="policy-note">${esc(pkg.root||'')}</p></div>`
}

requirementPackageFlowCard=function(){
  let catalog=data.requirement_packages||{},packages=portableRequirementPackages(),summary=catalog.summary||{},selected=selectedRequirementPackageId();
  return `<div class="card"><div class="diagnosis-head"><div><h2>可迁移需求包流程</h2><p>每个需求独立沉淀资料、数据、脚本和报告；执行中心只按选中的需求包调工具。</p></div><span class="tag ${summary.quality_passed===summary.total&&summary.total?'PASSED':'P1'}">质量通过 ${esc(summary.quality_passed||0)}/${esc(summary.total||0)}</span></div><div class="quality-flow compact-flow">${(catalog.process||[]).map((x,i)=>`<div class="quality-step"><span class="tag PASSED">${i+1}</span><b>${esc(x.step)}</b><small>${esc(x.output)}</small></div>`).join('')}</div>${packages.length?`<div class="endpoint-matrix">${packages.map((pkg,i)=>{let pid=requirementPackageId(pkg),chosen=pid===selected,status=packageStatusModel(pkg);return `<div class="endpoint-card ${chosen?'selected-package':''}"><span class="tag ${packageStatusClass(status.quality)}">${chosen?'当前 · ':''}${esc(status.quality)}</span><h3>${esc(pkg.name)}</h3><p>${esc(packageArtifactSummary(pkg))}</p>${packageStatusStrip(pkg)}<p><b>${esc(pkg.primary_tool)}</b> · ${esc(pkg.description)}</p><div class="formrow"><button class="${chosen?'primary':'small'}" onclick="setSelectedRequirementPackage('${esc(pid)}')">${chosen?'已选择':'选择'}</button><button class="small" onclick="showPortableRequirementPackage(${i})">详情</button><button class="small" onclick="openJmeterWorkbench('${esc(jmeterScriptKeyForPackage(pid))}')">打开JMeter</button></div></div>`}).join('')}</div>`:'<div class="empty"><b>暂无需求包</b></div>'}<p class="policy-note">目录根：${esc(summary.root||'requirements')}</p></div>`
}

unifiedExecutionFlow=function(){
  let pkg=currentRequirementPackage(),pid=requirementPackageId(pkg),isSalary=pid==='salary-trade',map=data.salary_trade_jmeter_mapping||{},m=data.case_jmeter_model||{},flows=isSalary?(m.flows||[]):[],ready=flows.filter(x=>x.automation_status==='ready').length;
  return `${requirementPackageSelectorHtml()}<div class="card"><div class="diagnosis-head"><div><h2>执行闭环</h2><p>当前只操作：${esc(pkg.name||'未选择需求包')}。先生成本包资产，再打开对应JMeter，最后回收本包报告。</p></div><span class="tag ${pkg.status==='READY'?'PASSED':'P1'}">${esc(pkg.status||'PENDING')}</span></div><div class="quality-flow compact-flow">${[
    ['1','生成本包测试资产',`${pkg.counts?.test_cases||0}条用例 · ${pkg.counts?.test_points||0}个测试点`],
    ['2','生成工具脚本',isSalary?`${flows.length||0}条流程 · ${ready}条可脚本化`:'Newman / JMeter / pytest 分包输出'],
    ['3','打开外部工具','真实JMeter GUI加载当前需求脚本'],
    ['4','回收执行报告',isSalary?`${map.jtl_rows||0}条JTL采样 · ${(map.sample_variables||[]).length}个映射变量`:'报告进入当前需求包和报告中心']
  ].map(x=>`<div class="quality-step"><span class="tag PASSED">${x[0]}</span><b>${x[1]}</b><small>${esc(x[2])}</small></div>`).join('')}</div><div class="hub-action-row"><button class="primary" onclick="generateSelectedRequirementApiTestCases()">生成接口测试用例</button><button class="small" onclick="compileSelectedRequirementInterfaceTests()">生成接口测试脚本</button><button class="small" onclick="runSelectedRequirementInterfaceTests()">运行接口测试</button><button class="small" onclick="runPipeline()">生成完整测试资产</button><button class="primary" onclick="generateSelectedRequirementPackageAssets()">生成本包脚本</button><button class="small" onclick="openJmeterWorkbench('${esc(jmeterScriptKeyForPackage(pid))}')">打开本包JMeter</button>${isSalary?`<button class="small" onclick="harvestSalaryTradeJmeter()">回收工资交易报告</button>`:`<button class="small" onclick="harvestJmeterGuiReport()">回收GUI报告</button>`}<button class="small" onclick="switchTab('reports')">查看报告</button></div><div id="salaryJmeterMappingResult"></div></div>${isSalary?salaryTradeScriptPathCard():''}`
}

showJmeterScriptChooser=function(){
  let packages=portableRequirementPackages(),selected=selectedRequirementPackageId();
  $('#modalBody').innerHTML=`<h2>选择 JMeter 脚本</h2><p class="policy-note">按需求包选择脚本。平台不会再默认打开某一个需求，避免多个需求互相污染。</p><div class="endpoint-matrix">${packages.map(pkg=>{let pid=requirementPackageId(pkg);return `<div class="endpoint-card"><span class="tag ${pid===selected?'PASSED':'P1'}">${pid===selected?'当前':'可选'}</span><h3>${esc(pkg.name)}</h3><p>${esc(pkg.description||'')}</p><code>${esc(pkg.artifacts?.jmeter?.path||pkg.root||'')}</code><div class="formrow"><button class="primary" onclick="setSelectedRequirementPackage('${esc(pid)}');openJmeterWorkbench('${esc(jmeterScriptKeyForPackage(pid))}')">选择并打开</button><button class="small" onclick="setSelectedRequirementPackage('${esc(pid)}');generateSelectedRequirementPackageAssets()">生成脚本</button></div></div>`}).join('')}</div>`;
  $('#modal').classList.remove('hidden')
}

function showCreateRequirementPackageModal(){
  $('#modalBody').innerHTML=`<h2>新建需求包</h2><p class="policy-note">一个需求包对应一个独立业务需求。创建后会自动生成 docs、data、outputs/newman、outputs/jmeter、outputs/pytest 和 reports 目录。</p><label>需求包名称</label><input id="newPackageName" placeholder="例如 工资代理投诉处理"><label>业务领域</label><input id="newPackageDomain" placeholder="例如 工资交易 / 财富等级 / 公会"><label>主执行工具</label><select id="newPackagePrimaryTool"><option value="JMeter">JMeter</option><option value="Newman">Newman</option><option value="pytest">pytest</option></select><label>说明</label><textarea id="newPackageDescription" rows="5" placeholder="这个需求包要测什么、主要流程是什么、有没有多账号或数据核查"></textarea><button class="primary" onclick="createRequirementPackage()">创建需求包</button>`;
  $('#modal').classList.remove('hidden')
}

async function createRequirementPackage(){
  let payload={
    name:$('#newPackageName')?.value.trim()||'',
    domain:$('#newPackageDomain')?.value.trim()||'',
    primary_tool:$('#newPackagePrimaryTool')?.value||'JMeter',
    description:$('#newPackageDescription')?.value.trim()||''
  };
  if(!payload.name)return toast('请填写需求包名称','warning');
  try{
    let x=await requirementPackagesApi.create(current,payload);
    data.requirement_packages=x.catalog;
    localStorage.setItem('autotest_selected_requirement_package',requirementPackageId(x.package));
    closeModal();
    toast(`需求包已创建：${x.package.name}`,'success');
    await openProject(current);
    switchTab('sources')
  }catch(e){toast(e.message,'error')}
}

async function runSelectedRequirementPackageNewman(){
  let pkg=currentRequirementPackage(),packageId=requirementPackageId(pkg);
  if(!packageId)return toast('当前没有可执行的需求包','warning');
  try{
    toast(`正在运行 ${pkg.name} 的 Newman 回归…`);
    let runId=await ensureRequirementRunContext();
    let x=await requirementPackagesApi.runNewman(current,packageId,{timeout:180,run_id:runId});
    let failures=x.failures||[],s=x.summary||{};
    $('#modalBody').innerHTML=`<h2>${esc(pkg.name)} · Newman执行结果</h2><p class="policy-note">${esc(x.message||'Newman 已按当前需求包 collection 执行，结果归档到需求包 reports。')}</p><div class="metrics"><div class="metric"><span>状态</span><b>${esc(x.status)}</b></div><div class="metric"><span>请求</span><b>${esc(s.requests??'-')}</b></div><div class="metric"><span>断言失败</span><b>${esc(s.failed_assertions??failures.length)}</b></div><div class="metric"><span>耗时</span><b>${esc(x.duration_ms??'-')}ms</b></div></div>${x.install_command?`<div class="summary-panel"><b>需要安装 Newman</b><p><code>${esc(x.install_command)}</code></p></div>`:''}${failures.length?`<h3>失败接口</h3><table><thead><tr><th>接口/步骤</th><th>错误</th></tr></thead><tbody>${failures.map(f=>`<tr><td>${esc(f.source||'-')}</td><td>${esc(f.error||'-')}</td></tr>`).join('')}</tbody></table>`:''}<label>Collection</label><code>${esc(x.collection||'')}</code>${x.summary_path?`<label>执行摘要</label><code>${esc(x.summary_path)}</code>`:''}${x.json_report?`<label>Newman原始报告</label><code>${esc(x.json_report)}</code>`:''}${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">打开报告</button>`:''}`;
    $('#modal').classList.remove('hidden');
    toast(`${pkg.name} Newman：${x.status}`,x.status==='PASSED'?'success':x.status==='BLOCKED'?'warning':'error');
    await openProject(current)
  }catch(e){toast(e.message,'error')}
}

function statusTag(status){
  return status==='PASSED'||status==='READY'?'PASSED':status==='FAILED'?'FAILED':'P1'
}

function pytestScenarioReportHtml(report){
  let scenarios=report?.scenarios||[],orchestration=report?.orchestration||{},summary=report?.summary||{},rules=report?.evidence_rules||[];
  let scenarioCards=scenarios.length?scenarios.map(s=>{
    let http=s.http_results||[],evidence=s.evidence_results||[],failedHttp=http.filter(x=>x.status!==x.expected_status||String(x.business_code||'200')!=='200'),blockedEvidence=evidence.filter(x=>x.status==='BLOCKED'),failedEvidence=evidence.filter(x=>x.status==='FAILED');
    return `<div class="endpoint-card scenario-plan-card"><span class="tag ${statusTag(s.status)}">${esc(s.status||'UNKNOWN')}</span><h3>${esc(s.name||s.scenario_id||'未命名场景')}</h3><p>${esc(s.source==='orchestration'?'来自主编排文件':'来自用例场景归类')}</p><div class="metrics compact-metrics"><div class="metric"><span>HTTP</span><b>${esc(s.http_cases??http.length)}</b></div><div class="metric"><span>HTTP失败</span><b>${esc(s.http_failed??failedHttp.length)}</b></div><div class="metric"><span>证据失败</span><b>${failedEvidence.length}</b></div><div class="metric"><span>证据阻断</span><b>${blockedEvidence.length}</b></div></div>${(s.evidence_rule_ids||[]).length?`<label>本场景证据规则</label><code>${esc((s.evidence_rule_ids||[]).join('\\n'))}</code>`:''}${failedHttp.length?`<label>失败接口</label><div class="gap-list">${failedHttp.slice(0,8).map(x=>`<div class="gap-item FAILED"><span class="tag FAILED">${esc(x.business_code||x.status)}</span><div><b>${esc(x.title||x.id)}</b><p>${esc(x.business_message||x.response_preview||'')}</p><small>${esc(x.method||'')} ${esc(x.path||'')}</small></div></div>`).join('')}</div>`:''}${(blockedEvidence.length||failedEvidence.length)?`<label>证据问题</label><div class="gap-list">${blockedEvidence.concat(failedEvidence).slice(0,8).map(x=>`<div class="gap-item ${x.status==='FAILED'?'P1':'FAILED'}"><span class="tag ${statusTag(x.status)}">${esc(x.status)}</span><div><b>${esc(x.name||x.id)}</b><p>${esc((x.blockers||[]).join('；')||x.sql||'')}</p><small>${esc(x.source||'')}</small></div></div>`).join('')}</div>`:''}</div>`
  }).join(''):'<div class="card empty"><b>暂无场景结果</b><p>旧报告可能还没有场景级结构，重新运行 pytest 后会生成。</p></div>';
  return `<div class="metrics"><div class="metric"><span>状态</span><b style="font-size:20px">${esc(report?.status||'UNKNOWN')}</b></div><div class="metric"><span>场景</span><b>${scenarios.length}</b></div><div class="metric"><span>HTTP失败</span><b>${esc(summary.http_failed??0)}</b></div><div class="metric"><span>证据失败/阻断</span><b>${esc(summary.rules_failed??0)}/${esc(summary.rules_blocked??0)}</b></div></div><div class="summary-panel"><b>编排来源</b><p>${esc(orchestration.exists?'已读取主编排文件':'未找到正式编排，按用例场景归类')} · ${esc(orchestration.path||'-')}</p></div><div class="scenario-plan-list">${scenarioCards}</div>${rules.length?`<details class="compact-details"><summary><b>全部证据规则明细</b><span>${rules.length}条</span></summary><div class="gap-list">${rules.slice(0,30).map(r=>`<div class="gap-item ${statusTag(r.status)}"><span class="tag ${statusTag(r.status)}">${esc(r.status)}</span><div><b>${esc(r.name||r.id)}</b><p>${esc(r.sql||(r.blockers||[]).join('；')||'')}</p><small>${esc(r.source||'')}</small></div></div>`).join('')}</div></details>`:''}`
}

function unifiedScenarioReportHtml(report){
  let scenarios=report?.scenarios||[],summary=report?.summary||{};
  let cards=scenarios.length?scenarios.map(s=>{
    let tools=s.tools||{},pre=s.data_preflight||{},pytest=tools.pytest||{},newman=tools.newman||{},jmeter=tools.jmeter||{};
    let failedHttp=pytest.failed_http||[],evidenceProblems=pytest.evidence_problems||[];
    return `<div class="endpoint-card scenario-plan-card"><span class="tag ${statusTag(s.status)}">${esc(s.status||'UNKNOWN')}</span><h3>${esc(s.name||s.scenario_id||'未命名场景')}</h3><p>${esc(s.business_goal||'')}</p><div class="metrics compact-metrics"><div class="metric"><span>数据准备</span><b>${esc(pre.status||'PENDING')}</b></div><div class="metric"><span>Newman</span><b>${esc(newman.status||'PENDING')}</b></div><div class="metric"><span>JMeter</span><b>${esc(jmeter.status||'PENDING')}</b></div><div class="metric"><span>pytest</span><b>${esc(pytest.status||'PENDING')}</b></div></div><div class="asset-chip-row"><span class="asset-chip ${pre.blockers?.length?'pending':'ready'}">阻断 ${esc((pre.blockers||[]).length)}</span><span class="asset-chip ${(pre.attentions||[]).length?'pending':'ready'}">提醒 ${esc((pre.attentions||[]).length)}</span><span class="asset-chip ${failedHttp.length?'pending':'ready'}">HTTP失败 ${esc(failedHttp.length)}</span><span class="asset-chip ${evidenceProblems.length?'pending':'ready'}">证据问题 ${esc(evidenceProblems.length)}</span></div>${(pre.blockers||[]).length?`<label>数据阻断</label><div class="gap-list">${pre.blockers.map(x=>`<div class="gap-item FAILED"><span class="tag FAILED">阻断</span><div><b>${esc(x)}</b></div></div>`).join('')}</div>`:''}${failedHttp.length?`<label>pytest失败接口</label><div class="gap-list">${failedHttp.map(x=>`<div class="gap-item FAILED"><span class="tag FAILED">${esc(x.business_code||x.status||'FAIL')}</span><div><b>${esc(x.title||x.id)}</b><p>${esc(x.message||'')}</p></div></div>`).join('')}</div>`:''}${evidenceProblems.length?`<label>证据问题</label><div class="gap-list">${evidenceProblems.map(x=>`<div class="gap-item P1"><span class="tag ${statusTag(x.status)}">${esc(x.status)}</span><div><b>${esc(x.name||x.id)}</b><p>${esc((x.blockers||[]).join('；'))}</p></div></div>`).join('')}</div>`:''}${(s.maintenance_targets||[]).length?`<label>维护点</label><code>${esc((s.maintenance_targets||[]).join('\\n'))}</code>`:''}</div>`
  }).join(''):'<div class="card empty"><b>暂无场景</b><p>先生成场景执行计划或运行 pytest 场景证据。</p></div>';
  return `<div class="metrics"><div class="metric"><span>结论</span><b style="font-size:20px">${esc(report?.status||'UNKNOWN')}</b></div><div class="metric"><span>场景</span><b>${esc(summary.scenarios||scenarios.length)}</b></div><div class="metric"><span>通过/失败</span><b>${esc(summary.passed||0)}/${esc(summary.failed||0)}</b></div><div class="metric"><span>阻断/提醒</span><b>${esc(summary.blocked||0)}/${esc(summary.warning||0)}</b></div></div><div class="summary-panel"><b>统一场景视角</b><p>${esc(report?.business_value||'')}</p></div><div class="scenario-plan-list">${cards}</div>`
}

async function showUnifiedScenarioReport(url){
  try{
    let report=await fetch(url).then(r=>{if(!r.ok)throw new Error('报告读取失败：HTTP '+r.status);return r.json()});
    $('#modalBody').innerHTML=`<h2>${esc(report.package_name||report.package_id||'需求包')} · 统一场景报告</h2><p class="policy-note">同一个业务场景下汇总 Newman、JMeter、pytest、数据准备和维护点。</p>${unifiedScenarioReportHtml(report)}<label>报告文件</label><code>${esc(url)}</code><button class="small" onclick="openReport('${esc(url)}')">打开JSON</button>`;
    $('#modal').classList.remove('hidden')
  }catch(e){toast(e.message,'error')}
}

async function generateSelectedRequirementScenarioReport(){
  let pkg=currentRequirementPackage(),packageId=requirementPackageId(pkg);
  if(!packageId)return toast('当前没有可汇总的需求包','warning');
  try{
    toast(`正在生成 ${pkg.name} 的统一场景报告…`);
    let runId=await ensureRequirementRunContext();
    let x=await requirementPackagesApi.scenarioReport(current,packageId,{run_id:runId});
    $('#modalBody').innerHTML=`<h2>${esc(pkg.name)} · 统一场景报告</h2><p class="policy-note">这份报告按业务流程收拢 Newman、JMeter、pytest 和数据准备结果，方便人工复核和后续维护。</p>${unifiedScenarioReportHtml(x)}<label>JSON报告</label><code>${esc(x.summary_path||'')}</code>${x.markdown_path?`<label>Markdown报告</label><code>${esc(x.markdown_path)}</code>`:''}${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">打开JSON</button>`:''}`;
    $('#modal').classList.remove('hidden');
    toast(`${pkg.name} 场景总报告：${x.status}`,x.status==='FAILED'?'error':x.status==='BLOCKED'?'warning':'success');
    await openProject(current)
  }catch(e){toast(e.message,'error')}
}

function scenarioPreflightHtml(preflight){
  let sp=preflight?.scenario_preflight||preflight?.details?.scenario_preflight||{},summary=sp.summary||{},scenarios=sp.scenarios||[];
  if(!scenarios.length)return '';
  return `<div class="summary-panel"><b>场景数据准备：${esc(sp.status||'UNKNOWN')}</b><p>场景 ${esc(summary.scenarios||0)} 个，通过 ${esc(summary.ready||0)}，提醒 ${esc(summary.warnings||0)}，阻断 ${esc(summary.blocked||0)}。</p></div><div class="scenario-plan-list">${scenarios.map(s=>`<div class="endpoint-card scenario-plan-card"><span class="tag ${statusTag(s.status)}">${esc(s.status)}</span><h3>${esc(s.name||s.scenario_id)}</h3><p>账号槽位 ${esc(s.account_slot||'-')} · 申请人 ${esc(s.applicant_uid||'-')} · ${esc(s.countryCode||'-')}/${esc(s.currency||'-')}</p><div class="asset-chip-row"><span class="asset-chip ready">用例 ${esc(s.case_count||0)}</span><span class="asset-chip ${(s.evidence_rule_ids||[]).length?'ready':'pending'}">证据规则 ${(s.evidence_rule_ids||[]).length}</span></div>${(s.blockers||[]).length?`<label>阻断</label><div class="gap-list">${s.blockers.map(x=>`<div class="gap-item FAILED"><span class="tag FAILED">阻断</span><div><b>${esc(x)}</b></div></div>`).join('')}</div>`:''}${(s.attentions||[]).length?`<label>提醒</label><div class="gap-list">${s.attentions.slice(0,5).map(x=>`<div class="gap-item P1"><span class="tag P1">提醒</span><div><b>${esc(x)}</b></div></div>`).join('')}</div>`:''}</div>`).join('')}</div>`
}

async function showPytestScenarioReport(url){
  try{
    let report=await fetch(url).then(r=>{if(!r.ok)throw new Error('报告读取失败：HTTP '+r.status);return r.json()});
    $('#modalBody').innerHTML=`<h2>${esc(report.package_id||'需求包')} · pytest场景证据报告</h2><p class="policy-note">按业务场景查看接口执行、运行变量和 DB/Redis 证据，不需要直接翻 JSON。</p>${pytestScenarioReportHtml(report)}<label>报告文件</label><code>${esc(url)}</code><button class="small" onclick="openReport('${esc(url)}')">打开JSON</button>`;
    $('#modal').classList.remove('hidden')
  }catch(e){toast(e.message,'error')}
}

async function runSelectedRequirementPackagePytest(){
  let pkg=currentRequirementPackage(),packageId=requirementPackageId(pkg);
  if(!packageId)return toast('当前没有可执行的需求包','warning');
  try{
    toast(`正在运行 ${pkg.name} 的 pytest 深度证据复核…`);
    let runId=await ensureRequirementRunContext();
    let x=await requirementPackagesApi.runPytest(current,packageId,{timeout:240,run_id:runId});
    let report=x.evidence_report||{};
    $('#modalBody').innerHTML=`<h2>${esc(pkg.name)} · pytest深度证据复核</h2><p class="policy-note">pytest 会按当前需求包主编排文件执行场景，并结合 HTTP、JMeter/Newman、DB/Redis 证据输出报告。</p>${pytestScenarioReportHtml(report)}<label>pytest脚本</label><code>${esc(x.pytest_file||'')}</code><label>证据报告</label><code>${esc(x.summary_path||'')}</code>${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">打开JSON</button>`:''}`;
    $('#modal').classList.remove('hidden');
    toast(`${pkg.name} pytest证据：${x.status}`,x.status==='PASSED'?'success':x.status==='BLOCKED'?'warning':'error');
    await openProject(current)
  }catch(e){toast(e.message,'error')}
}

async function runSelectedRequirementPackagePipeline(){
  let pkg=currentRequirementPackage(),packageId=requirementPackageId(pkg);
  if(!packageId)return toast('当前没有可执行的需求包','warning');
  if(!confirm(`确认执行“${pkg.name}”的自动闭环吗？\n\n平台会真实运行可安全自动执行的 Newman 和 pytest，并生成接口分析、场景报告与 AI 复盘。包含写接口时只自动运行只读冒烟，JMeter 长压测和写流程不会静默启动。`))return;
  try{
    let runId=await ensureRequirementRunContext(true);
    closeModal();
    toast(`${pkg.name} 自动闭环已开始，请稍候…`);
    let x=await requirementPackagesApi.runPipeline(current,packageId,{run_id:runId,run_newman:true,run_pytest:true,create_load_plan:true});
    let s=x.summary||{},steps=x.steps||[];
    $('#modalBody').innerHTML=`<h2>${esc(pkg.name)} · 一键执行结果</h2><p class="policy-note">本次已创建独立运行批次。平台先检查资源和运行凭证，再执行安全接口冒烟、回收原始报告并生成场景报告与 AI 复盘；JMeter 写流程和持续压测仍需人工明确启动。</p><div class="metrics"><div class="metric"><span>结论</span><b style="font-size:20px">${esc(x.status)}</b></div><div class="metric"><span>通过</span><b>${esc(s.passed||0)}</b></div><div class="metric"><span>失败</span><b>${esc(s.failed||0)}</b></div><div class="metric"><span>阻断/提醒</span><b>${esc(s.blocked||0)}/${esc(s.warnings||0)}</b></div></div><div class="gap-list">${steps.map(item=>`<div class="gap-item ${item.status==='FAILED'?'P0':item.status==='BLOCKED'?'P1':''}"><span class="tag ${statusTag(item.status)}">${esc(item.status)}</span><div><b>${esc(item.name)}</b><p>${esc(item.message||'')}</p>${item.json_url?`<button class="small" onclick="openReport('${esc(item.json_url)}')">查看报告</button>`:''}</div></div>`).join('')}</div><div class="hub-action-row"><button class="primary" onclick="switchTab('reports');closeModal()">进入报告中心</button>${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">执行摘要JSON</button>`:''}</div>`;
    $('#modal').classList.remove('hidden');
    toast(`${pkg.name} 自动闭环：${x.status}`,x.status==='PASSED'?'success':x.status==='FAILED'?'error':'warning');
    await openProject(current)
  }catch(e){toast(e.message,'error')}
}

async function generateSelectedRequirementPackageAiReview(){
  let pkg=currentRequirementPackage(),packageId=requirementPackageId(pkg);
  if(!packageId)return toast('当前没有可复盘的需求包','warning');
  try{
    toast(`正在复盘 ${pkg.name} 的执行证据…`);
    let runId=await ensureRequirementRunContext();
    let x=await requirementPackagesApi.aiReview(current,packageId,{run_id:runId});
    let s=x.summary||{},findings=x.findings||[],actions=x.next_actions||[],cats=x.root_cause_categories||{},signals=x.execution_signals||{};
    let catLabels={authentication:'鉴权/登录态',request_contract:'请求契约',business_assertion:'业务断言',test_data:'测试数据',data_evidence:'DB/Redis证据',manual_or_timing:'人工/定时流程',performance:'性能',environment:'环境/工具',server:'服务异常',unknown:'待补证据'};
    let catText=Object.entries(cats).map(([k,v])=>`${catLabels[k]||k}:${v}`).join(' · ')||'-';
    $('#modalBody').innerHTML=`<h2>${esc(pkg.name)} · AI复盘</h2><p class="policy-note">${esc(x.business_value||'')}</p><div class="metrics"><div class="metric"><span>结论</span><b style="font-size:20px">${esc(x.status)}</b></div><div class="metric"><span>P0/P1</span><b>${esc(s.p0||0)}/${esc(s.p1||0)}</b></div><div class="metric"><span>HTTP失败</span><b>${esc(signals.http_failed||s.http_failed||0)}</b></div><div class="metric"><span>证据报告</span><b>${esc(signals.business_evidence_reports||0)}</b></div></div><div class="summary-panel"><b>复盘结论</b><p>${esc(x.conclusion||'')}</p><p>根因分布：${esc(catText)}</p></div>${findings.length?`<h3>问题归纳</h3><div class="gap-list">${findings.map(f=>`<div class="gap-item ${f.level==='P0'?'P0':'P1'}"><span class="tag ${f.level==='P0'?'FAILED':'P1'}">${esc(f.level)}</span><div><b>${esc(f.title)}</b><p>${esc(f.evidence||'')}</p><small>${esc(f.recommendation||f.owner||'')}</small></div></div>`).join('')}</div>`:'<div class="card empty"><b>暂无阻断问题</b></div>'}<h3>下一步</h3><ol>${actions.map(a=>`<li>${esc(a)}</li>`).join('')}</ol><label>复盘报告</label><code>${esc(x.summary_path||'')}</code>${x.markdown_path?`<label>Markdown报告</label><code>${esc(x.markdown_path)}</code>`:''}${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">打开JSON</button>`:''}`;
    $('#modal').classList.remove('hidden');
    toast(`${pkg.name} AI复盘：${x.status}`,x.status==='FAILED'?'error':x.status==='NO_RUN_DATA'?'warning':'success');
    await openProject(current)
  }catch(e){toast(e.message,'error')}
}

async function generateSelectedRequirementPerformanceAiReview(runIdOverride=''){
  let pkg=currentRequirementPackage(),packageId=requirementPackageId(pkg);
  if(!packageId)return toast('当前没有可分析的需求包','warning');
  try{
    toast(`正在分析 ${pkg.name} 的 JMeter 性能报告…`);
    let runId=runIdOverride||await ensureRequirementRunContext();
    let x=await requirementPackagesApi.performanceReview(current,packageId,{run_id:runId});
    let s=x.summary||{},a=x.analysis||{},findings=a.findings||[],recommendations=a.recommendations||[],obs=x.observability_evidence||{};
    let source=x.source||{};
    let tps=s.measurement_mode==='business_transaction'?(s.transaction_throughput_tps??'-'):'-';
    let obsCategories=(obs.available_categories||[]).join('、')||'未接入';
    let obsMissing=(obs.missing_core_categories||[]).join('、');
    $('#modalBody').innerHTML=`<h2>${esc(pkg.name)} · 性能报告AI分析</h2><p class="policy-note">${esc(x.business_value||'')}</p><div class="metrics"><div class="metric"><span>错误率</span><b>${esc(s.error_rate??'-')}%</b></div><div class="metric"><span>P95 / P99</span><b>${esc(s.p95_ms??'-')} / ${esc(s.p99_ms??'-')}ms</b></div><div class="metric"><span>RPS / TPS</span><b>${esc(s.throughput_rps??'-')} / ${esc(tps)}</b><small>${esc(s.measurement_mode||'request_only')}</small></div><div class="metric"><span>风险</span><b>${esc(s.risk_level||'-')}</b></div></div><div class="summary-panel"><b>分析结论</b><p>${esc(a.conclusion||'')}</p><small>${a.mode==='configured_model'?'已使用平台配置模型':'使用内置性能分析规则'}</small></div><div class="summary-panel"><b>外部监控证据：${esc(obs.status||'MISSING')}</b><p>已接入：${esc(obsCategories)}${obsMissing?`；仍缺：${esc(obsMissing)}`:''}</p><small>${esc(obs.statement||'JTL可确认慢请求与失败分布，根因需外部证据确认。')}</small></div>${findings.length?`<h3>性能发现</h3><div class="gap-list">${findings.map(f=>`<div class="gap-item ${['P0','FAILED'].includes(f.severity)?'P0':'P1'}"><span class="tag ${['P0','FAILED'].includes(f.severity)?'FAILED':'P1'}">${esc(f.severity||'P1')}</span><div><b>${esc(f.title||'性能提醒')}</b><p>${esc(f.detail||'')}</p></div></div>`).join('')}</div>`:''}<h3>处理建议</h3><ol>${recommendations.map(item=>`<li>${esc(item)}</li>`).join('')}</ol><h3>同批原始证据</h3><div class="hub-action-row">${source.jmeter_html_url?`<button class="small" onclick="openReport('${esc(source.jmeter_html_url)}')">JMeter HTML</button>`:''}${source.jmeter_jtl_url?`<button class="small" onclick="openReport('${esc(source.jmeter_jtl_url)}')">原始 JTL</button>`:''}${source.jmeter_json_url?`<button class="small" onclick="openReport('${esc(source.jmeter_json_url)}')">原始 JSON</button>`:''}${source.observability_json_url?`<button class="small" onclick="openReport('${esc(source.observability_json_url)}')">监控证据</button>`:''}</div><label>分析报告</label><code>${esc(x.summary_path||'')}</code>${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">打开分析JSON</button>`:''}`;
    $('#modal').classList.remove('hidden');
    toast(`性能分析已生成：${x.status}`,x.status==='FAILED'?'error':'success');
    await openProject(current)
  }catch(e){toast(e.message,'error')}
}

async function generateSelectedRequirementNewmanAnalysis(runIdOverride=''){
  let pkg=currentRequirementPackage(),packageId=requirementPackageId(pkg);
  if(!packageId)return toast('当前没有可分析的需求包','warning');
  try{
    let runId=runIdOverride||await ensureRequirementRunContext();
    let x=await requirementPackagesApi.newmanAnalysis(current,packageId,{run_id:runId});
    let s=x.summary||{},incidents=x.incidents||[],source=x.source||{};
    $('#modalBody').innerHTML=`<h2>${esc(pkg.name)} · Newman接口冒烟分析</h2><p class="policy-note">${esc(x.business_value||'')}</p><div class="metrics"><div class="metric"><span>请求</span><b>${esc(s.requests||0)}</b></div><div class="metric"><span>接口</span><b>${esc(s.endpoints||0)}</b></div><div class="metric"><span>异常接口</span><b>${esc(s.failed_endpoints||0)}</b></div><div class="metric"><span>待分派</span><b>${esc(s.incidents||0)}</b></div></div><div class="summary-panel"><b>结论</b><p>${esc(x.conclusion||'')}</p></div>${incidents.length?`<h3>接口问题清单</h3><div class="gap-list">${incidents.slice(0,100).map(i=>`<div class="gap-item ${i.severity==='P0'?'P0':'P1'}"><span class="tag ${i.severity==='P0'?'FAILED':'P1'}">${esc(i.severity)}</span><div><b>${esc(i.method)} ${esc(i.path)}</b><p>${esc(i.interface)} · HTTP ${esc(i.http_status)} · ${esc(i.error)}</p><small>建议负责人：${esc(i.suggested_owner)}</small><br><small>复核动作：${esc(i.review_action)}</small></div></div>`).join('')}</div>`:'<div class="card empty"><b>本批次没有接口失败</b></div>'}<h3>原始证据</h3><div class="hub-action-row">${source.newman_json_url?`<button class="small" onclick="openReport('${esc(source.newman_json_url)}')">Newman原始JSON</button>`:''}${source.newman_summary_url?`<button class="small" onclick="openReport('${esc(source.newman_summary_url)}')">执行摘要</button>`:''}${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">分析JSON</button>`:''}</div>`;
    $('#modal').classList.remove('hidden');
    toast(`接口冒烟分析：${x.status}`,x.status==='PASSED'?'success':'error');
    await openProject(current)
  }catch(e){toast(e.message,'error')}
}

function selectedPerformanceTransaction(){
  let pending=window.pendingPerformanceOptions||{},scenarioId=$('#performanceTransaction')?.value||'';
  return (pending.transactions||[]).find(item=>item.scenario_id===scenarioId)||null;
}

function performanceTransactionStatusLabel(status){
  if(status==='READY')return '可直接执行';
  if(status==='NEEDS_INPUT')return '需补运行参数';
  return '已阻断';
}

function renderPerformanceRuntimeInputs(){
  let container=$('#performanceRuntimeInputs');
  if(!container)return;
  let transaction=selectedPerformanceTransaction();
  if(!transaction){container.innerHTML='';return}
  let inputs=(transaction.required_runtime_inputs||[]).filter(item=>item.fillable!==false&&!item.sensitive);
  if(transaction.status==='BLOCKED'){
    let blockers=transaction.hard_blockers||transaction.blockers||[];
    container.innerHTML=`<div class="summary-panel"><b>该事务暂时不能执行</b><p>${esc(blockers.join('；')||'缺少不可由普通运行参数补齐的资源。')}</p></div>`;
    return;
  }
  if(!inputs.length){
    container.innerHTML='<div class="summary-panel"><b>事务数据已就绪</b><p>账号池、前置变量和请求字段均已找到明确来源。</p></div>';
    return;
  }
  container.innerHTML=`<div class="summary-panel"><b>本次运行需要补充 ${esc(inputs.length)} 个参数</b><p>平台不会自动编造业务值。这里填写的普通参数会随当前压测预案保存；ticket、token、password 等凭证仍只从账号池或凭证源读取。</p></div><div class="formrow">${inputs.map(item=>`<div><label>${esc(item.name)} <small>${esc(item.location||'runtime')}</small></label><input data-performance-runtime-input="true" data-runtime-name="${esc(item.name)}" autocomplete="off" placeholder="请填写 ${esc(item.name)}"></div>`).join('')}</div>`;
}

async function generateSelectedRequirementLoadPlan(){
  let pkg=currentRequirementPackage(),packageId=requirementPackageId(pkg);
  if(!packageId)return toast('当前没有可生成压测预案的需求包','warning');
  try{
    let options=await requirementPackagesApi.performanceOptions(current,packageId),profiles=options.profiles||[],targets=options.targets||[],transactions=options.transactions||[];
    if(!profiles.length)throw new Error('平台没有可用的性能Profile');
    if(!targets.length)throw new Error('当前需求包没有可安全执行的只读目标接口');
    window.pendingPerformanceOptions={projectId:current,packageId,packageName:pkg.name||packageId,profiles,targets,transactions,observability:options.observability||{}};
    let defaultProfile=profiles.find(item=>item.profile===options.default_profile)||profiles[0],thresholds=defaultProfile.thresholds||{};
    let readyTargets=targets.filter(item=>item.status!=='BLOCKED'),blockedTargets=targets.filter(item=>item.status==='BLOCKED'),pool=options.account_pool||{},observability=options.observability||{};
    let observabilityReady=(observability.configured_categories||[]).join('、')||'未配置',observabilityMissing=(observability.missing_core_categories||[]).join('、')||'无';
    let blockedHtml=blockedTargets.length?`<h3>运行前待补数据</h3><div class="gap-list">${blockedTargets.map(item=>`<div class="gap-item P0"><span class="tag FAILED">BLOCKED</span><div><b>${esc(item.method)} ${esc(item.path)}</b><p>${esc((item.missing||[]).map(x=>x.name).join('、')||'缺少必填运行数据')}</p><small>${esc((item.missing||[]).map(x=>x.reason).join('；'))}</small></div></div>`).join('')}</div>`:'';
    let transactionHtml=transactions.length?`<div class="formrow"><div><label>业务事务</label><select id="performanceTransaction" onchange="applySelectedPerformanceTransaction()"><option value="">不选择，仅统计接口RPS</option>${transactions.map(item=>`<option value="${esc(item.scenario_id)}" ${item.status==='BLOCKED'?'disabled':''}>${esc(item.name)} · ${esc((item.steps||[]).length)}步 · ${esc(performanceTransactionStatusLabel(item.status))}</option>`).join('')}</select></div><div><label>测试服写入</label><label class="checkbox-line"><input id="performanceAllowMutations" type="checkbox" disabled> 允许当前业务事务写入</label></div></div><div id="performanceRuntimeInputs"></div>`:'';
    $('#modalBody').innerHTML=`<h2>${esc(pkg.name)} · 性能测试配置</h2><p class="policy-note">性能Skill根据Profile生成受约束JMX；静态门禁通过后，JMeter MCP只负责导入与执行。</p><div class="formrow"><div><label>测试类型</label><select id="performanceProfile" onchange="applySelectedPerformanceProfile()">${profiles.map(item=>`<option value="${esc(item.profile)}" ${item.profile===defaultProfile.profile?'selected':''}>${esc(item.label)} (${esc(item.profile)})</option>`).join('')}</select></div><div><label>目标接口</label><select id="performanceTarget"><option value="">全部已就绪接口</option>${targets.map(item=>`<option value="${esc(item.key)}" ${item.status==='BLOCKED'?'disabled':''}>${esc(item.method)} ${esc(item.path)} · ${item.status==='BLOCKED'?'缺少数据':'就绪'}</option>`).join('')}</select></div></div>${transactionHtml}<div class="formrow"><div><label>并发线程</label><input id="performanceThreads" type="number" min="1" max="500" value="${esc(defaultProfile.threads)}"></div><div><label>升压时间（秒）</label><input id="performanceRampup" type="number" min="0" max="3600" value="${esc(defaultProfile.rampup_seconds)}"></div></div><div class="formrow"><div><label>持续时间（秒）</label><input id="performanceDuration" type="number" min="10" max="604800" value="${esc(defaultProfile.duration_seconds)}"></div><div><label>每接口预热样本</label><input id="performanceWarmupSamples" type="number" min="0" max="100" value="${esc(defaultProfile.warmup_samples_per_label??0)}"></div></div><div class="formrow"><div><label>账号复用策略</label><select id="performanceAccountPolicy"><option value="round_robin">账号不足时受控轮询</option><option value="strict_unique">每线程必须独占账号</option></select></div><div><label>最低业务事务TPS</label><input id="performanceMinTps" type="number" min="0" step="0.1" value="${esc(thresholds.min_transaction_tps??0)}"></div></div><div class="formrow"><div><label>最大错误率（%）</label><input id="performanceErrorRate" type="number" min="0" max="100" step="0.1" value="${esc(thresholds.max_error_rate??1)}"></div><div><label>最低请求吞吐量（RPS）</label><input id="performanceMinRps" type="number" min="0" step="0.1" value="${esc(thresholds.min_throughput_rps??0)}"></div></div><div class="formrow"><div><label>P95上限（ms）</label><input id="performanceP95" type="number" min="1" value="${esc(thresholds.max_p95_ms??2000)}"></div><div><label>P99上限（ms）</label><input id="performanceP99" type="number" min="1" value="${esc(thresholds.max_p99_ms??4000)}"></div></div><div class="summary-panel"><b>数据准备</b><p>目标接口已就绪 ${esc(readyTargets.length)}/${esc(targets.length)}；账号池 ${esc(pool.accounts??'-')} 个，默认策略 ${esc(pool.policy||defaultProfile.account_reuse_policy||'-')}。分页参数只使用OpenAPI中的安全示例自动补齐，业务ID不会臆造。</p></div><div class="summary-panel"><b>根因证据准备：${esc(observability.status||'MISSING')}</b><p>已配置：${esc(observabilityReady)}；仍缺：${esc(observabilityMissing)}。</p><small>${esc(observability.statement||'')}</small></div>${blockedHtml}<div class="summary-panel"><b>执行边界</b><p>未选择业务事务时只统计RPS；只有多步骤场景通过预检并明确授权写入后才统计TPS。</p></div><button class="primary" onclick="confirmSelectedRequirementLoadPlan()">生成受约束JMX预案</button>`;
    $('#modal').classList.remove('hidden');
  }catch(e){toast(e.message,'error')}
}

function applySelectedPerformanceProfile(){
  let pending=window.pendingPerformanceOptions||{},profile=(pending.profiles||[]).find(item=>item.profile===$('#performanceProfile')?.value);
  if(!profile)return;
  let thresholds=profile.thresholds||{};
  $('#performanceThreads').value=profile.threads;
  $('#performanceRampup').value=profile.rampup_seconds;
  $('#performanceDuration').value=profile.duration_seconds;
  $('#performanceWarmupSamples').value=profile.warmup_samples_per_label??0;
  $('#performanceErrorRate').value=thresholds.max_error_rate??1;
  $('#performanceP95').value=thresholds.max_p95_ms??2000;
  $('#performanceP99').value=thresholds.max_p99_ms??4000;
  $('#performanceMinRps').value=thresholds.min_throughput_rps??0;
  $('#performanceMinTps').value=thresholds.min_transaction_tps??0;
  $('#performanceAccountPolicy').value=profile.account_reuse_policy||'round_robin';
}

function applySelectedPerformanceTransaction(){
  let selected=$('#performanceTransaction')?.value||'',target=$('#performanceTarget'),allow=$('#performanceAllowMutations');
  if(target){target.disabled=!!selected;if(selected)target.value=''}
  if(allow){allow.disabled=!selected;if(!selected)allow.checked=false}
  renderPerformanceRuntimeInputs();
}

async function confirmSelectedRequirementLoadPlan(){
  let pending=window.pendingPerformanceOptions||{},packageId=pending.packageId;
  if(!packageId)return toast('性能配置已失效，请重新打开','warning');
  try{
    let runId=await ensureRequirementRunContext(),target=$('#performanceTarget').value,scenarioId=$('#performanceTransaction')?.value||'',allowMutations=!!$('#performanceAllowMutations')?.checked;
    let payload={run_id:runId,performance_profile:$('#performanceProfile').value,jmeter_threads:Number($('#performanceThreads').value),jmeter_rampup:Number($('#performanceRampup').value),duration_seconds:Number($('#performanceDuration').value),warmup_samples_per_label:Number($('#performanceWarmupSamples').value),account_reuse_policy:$('#performanceAccountPolicy').value,max_error_rate:Number($('#performanceErrorRate').value),max_p95_ms:Number($('#performanceP95').value),max_p99_ms:Number($('#performanceP99').value),min_throughput_rps:Number($('#performanceMinRps').value),min_transaction_tps:Number($('#performanceMinTps').value)};
    if(scenarioId){
      let transaction=selectedPerformanceTransaction();
      if(!transaction||transaction.status==='BLOCKED')throw new Error('该业务事务仍有不可补齐的资源阻断');
      if(!allowMutations)throw new Error('业务事务包含测试服写操作，请先确认本批次允许写入');
      let runtimeParams={},missingInputs=[];
      document.querySelectorAll('[data-performance-runtime-input="true"]').forEach(input=>{
        let name=input.dataset.runtimeName||'',value=input.value.trim();
        if(!value)missingInputs.push(name);else runtimeParams[name]=value;
      });
      if(missingInputs.length)throw new Error(`请先填写运行参数：${missingInputs.join('、')}`);
      payload.scenario_id=scenarioId;payload.allow_mutations=true;payload.transaction_mode='business_transaction';
      if(Object.keys(runtimeParams).length)payload.runtime_params=runtimeParams;
    }else if(target)payload.target_api=target;
    let x=await requirementPackagesApi.loadPlan(current,packageId,payload);
    let s=x.summary||{},stages=x.stages||[];
    $('#modalBody').innerHTML=`<h2>${esc(pending.packageName)} · JMeter性能预案</h2><p class="policy-note">Profile、目标接口、账号池和阈值已经写入本批次执行上下文。</p><div class="metrics"><div class="metric"><span>安全接口</span><b>${esc(s.safe_endpoints||0)}</b></div><div class="metric"><span>数据阻断</span><b>${esc(s.blocked_targets||0)}</b></div><div class="metric"><span>执行阶梯</span><b>${esc(s.stages||0)}</b></div><div class="metric"><span>状态</span><b>${esc(x.status)}</b></div></div><h3>可执行阶梯</h3><div class="gap-list">${stages.map(i=>`<div class="gap-item"><span class="tag PASSED">${esc(i.profile||i.stage)}</span><div><b>${esc(i.name)} · ${esc(i.threads)}线程</b><p>${esc(i.workload_model||'steady')} · 升压 ${esc(i.rampup_seconds)}秒 · 持续 ${esc(i.duration_seconds)}秒 · 账号 ${esc(i.account_pool?.accounts??'-')} 个</p><small>${esc(i.jmx_path)}</small><br><button class="small" onclick="runSelectedRequirementLoadStage(${Number(i.stage)||1},'${esc(i.name||'性能测试')}',${Number(i.duration_seconds)||60})">后台运行此阶梯</button></div></div>`).join('')}</div><div class="summary-panel"><b>目标接口</b><p>${esc((x.execution_context?.target_apis||[]).join('、')||'未记录')}</p></div><div class="summary-panel"><b>容量判断</b><p>${esc(x.capacity_rule||'')}</p></div><h3>报告要求</h3><p>每个阶梯保留原始JMX、JTL、JMeter HTML、指标、诊断和AI分析。</p>${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">打开预案JSON</button>`:''}`;
    toast('可执行JMeter压测预案已生成','success');
    await openProject(current)
  }catch(e){toast(e.message,'error')}
}

async function runSelectedRequirementLoadStage(stage,name,durationSeconds){
  let pkg=currentRequirementPackage(),packageId=requirementPackageId(pkg),minutes=Math.max(1,Math.ceil((durationSeconds||60)/60));
  if(!confirm(`确认执行“${name}”吗？预计持续约 ${minutes} 分钟。平台只会压测预案中已筛选的只读接口。`))return;
  try{
    let runId=await ensureRequirementRunContext();
    closeModal();
    toast(`JMeter ${name} 已转入后台执行，可刷新页面或在任务区停止。`,'success');
    let task=await window.QualityHub.services.tasks.submit('requirement_performance',{project_id:current,package_id,options:{run_id:runId,stage}});
    data.background_tasks=await api('/api/tasks?limit=20');render();
    window.QualityHub.services.tasks.wait(task.task_id,{timeout:Math.max(120000,(durationSeconds+300)*1000),onProgress:async state=>{data.background_tasks=[state,...(data.background_tasks||[]).filter(item=>item.task_id!==state.task_id)];render()}}).then(async state=>{
      let x=state.result||{},s=x.summary||{},capacity=x.capacity_progress||{},analysis=x.performance_analysis||{};
      if(state.status==='CANCELLED')return toast('性能任务已停止','warning');
      $('#modalBody').innerHTML=`<h2>${esc(pkg.name)} · ${esc(name)}执行结果</h2><div class="metrics"><div class="metric"><span>HTTP请求</span><b>${esc(s.requests||0)}</b></div><div class="metric"><span>错误率</span><b>${esc(s.error_rate??'-')}%</b></div><div class="metric"><span>RPS / TPS</span><b>${esc(s.throughput_rps??'-')} / ${esc(x.performance_summary?.transaction_throughput_tps??'-')}</b></div><div class="metric"><span>P95/P99</span><b>${esc(s.p95_ms??'-')}/${esc(s.p99_ms??'-')}ms</b></div></div><div class="summary-panel"><b>容量进度</b><p>${esc(capacity.capacity_conclusion||x.message||'')}</p></div>${performanceAccountUsageHtml(x.performance_summary||{})}<div class="hub-action-row">${x.html_url?`<button class="small" onclick="openReport('${esc(x.html_url)}')">JMeter HTML</button>`:''}${x.jtl_url?`<button class="small" onclick="openReport('${esc(x.jtl_url)}')">原始JTL</button>`:''}${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">执行JSON</button>`:''}${analysis.json_url?`<button class="small" onclick="openReport('${esc(analysis.json_url)}')">性能分析</button>`:''}</div>`;
      $('#modal').classList.remove('hidden');toast(`压测阶梯完成：${x.status||state.status}`,x.status==='PASSED'?'success':'error');await openProject(current)
    }).catch(error=>toast(error.message,'warning'))
  }catch(e){toast(e.message,'error')}
}

async function cancelBackgroundTask(taskId){
  try{await window.QualityHub.services.tasks.cancel(taskId);toast('已发送停止请求','warning');data.background_tasks=await api('/api/tasks?limit=20');render()}catch(error){toast(error.message,'error')}
}

async function generateSelectedRequirementPackageAccountModel(){
  let pkg=currentRequirementPackage(),packageId=requirementPackageId(pkg);
  if(!packageId)return toast('当前没有可生成账号模型的需求包','warning');
  try{
    toast(`正在生成 ${pkg.name} 的账号模型…`);
    let x=await requirementPackagesApi.accountModel(current,packageId,true);
    let roles=x.roles||[],pending=x.extensions?.pending||[];
    $('#modalBody').innerHTML=`<h2>${esc(pkg.name)} · 账号模型</h2><p class="policy-note">这是当前需求包自己的 account_model.yaml。通用Skill只提供能力，实际启用哪些账号场景由需求和测试用例判断。</p><div class="metrics"><div class="metric"><span>模型</span><b style="font-size:20px">${esc(x.mode)}</b></div><div class="metric"><span>CSV</span><b>${x.csv_required?'需要':'不强制'}</b></div><div class="metric"><span>角色</span><b>${roles.length}</b></div><div class="metric"><span>待确认扩展</span><b>${pending.length}</b></div></div><h3>角色规则</h3><table><thead><tr><th>角色</th><th>最少账号</th><th>可复用</th><th>匹配规则</th><th>凭证来源</th></tr></thead><tbody>${roles.map(r=>`<tr><td>${esc(r.name)}</td><td>${esc(r.min_count)}</td><td>${r.reusable?'是':'否'}</td><td>${esc((r.match_rules||[]).join('、')||'-')}</td><td>${esc((r.credential_sources||[]).join(' -> '))}</td></tr>`).join('')}</tbody></table>${pending.length?`<h3>待确认扩展</h3><div class="gap-list">${pending.map(p=>`<div class="gap-item P1"><span class="tag P1">待确认</span><div><b>${esc(p.name)}</b><p>${esc(p.reason)}</p></div></div>`).join('')}</div>`:'<div class="card empty"><b>没有未知账号场景</b></div>'}<h3>阻断规则</h3><ol>${(x.blocking_rules||[]).map(r=>`<li>${esc(r)}</li>`).join('')}</ol><label>模型文件</label><code>${esc(x.path||'')}</code>`;
    $('#modal').classList.remove('hidden');
    toast(`${pkg.name} 账号模型已生成`,'success');
    await openProject(current)
  }catch(e){toast(e.message,'error')}
}

async function generateSelectedRequirementExecutionPlan(){
  let pkg=currentRequirementPackage(),packageId=requirementPackageId(pkg);
  if(!packageId)return toast('当前没有可规划的需求包','warning');
  try{
    toast(`正在生成 ${pkg.name} 的场景执行计划…`);
    let x=await requirementPackagesApi.executionPlan(current,packageId,true);
    let s=x.summary||{},scenarios=x.scenarios||[],statusCounts=s.status_counts||{},toolCounts=s.tool_counts||{};
    let statusLabel={READY:'可执行',READY_WITH_WARNINGS:'可执行但需关注',NEEDS_REVIEW:'需人工复核',BLOCKED:'阻断'};
    $('#modalBody').innerHTML=`<h2>${esc(pkg.name)} · 场景执行计划</h2><p class="policy-note">${esc(x.business_value||'')}</p><div class="metrics"><div class="metric"><span>状态</span><b style="font-size:20px">${esc(x.status)}</b></div><div class="metric"><span>场景/用例</span><b>${esc(s.scenarios||0)}/${esc(s.cases||0)}</b></div><div class="metric"><span>待复核/阻断</span><b>${esc((statusCounts.NEEDS_REVIEW||0)+(statusCounts.READY_WITH_WARNINGS||0))}/${esc(statusCounts.BLOCKED||0)}</b></div><div class="metric"><span>N/J/P</span><b>${esc(toolCounts.newman||0)}/${esc(toolCounts.jmeter||0)}/${esc(toolCounts.pytest||0)}</b></div></div><div class="scenario-plan-list">${scenarios.map(item=>{let tasks=item.tool_tasks||[],human=item.human_review||{};return `<div class="endpoint-card scenario-plan-card"><span class="tag ${item.status==='READY'?'PASSED':item.status==='BLOCKED'?'FAILED':'P1'}">${esc(statusLabel[item.status]||item.status)}</span><h3>${esc(item.name)}</h3><p>${esc(item.business_goal||'')}</p><div class="asset-chip-row">${tasks.map(t=>`<span class="asset-chip ${t.blockers?.length?'pending':'ready'}">${esc(t.tool)} · ${esc(t.case_count||0)}</span>`).join('')}</div><small>${esc(human.review_question||'')}</small>${(human.human_actions||[]).length?`<ol>${human.human_actions.map(a=>`<li>${esc(a)}</li>`).join('')}</ol>`:''}${(human.maintenance_targets||[]).length?`<label>维护点</label><code>${esc(human.maintenance_targets.slice(0,4).join('\\n'))}</code>`:''}</div>`}).join('')}</div><label>计划文件</label><code>${esc(x.output_json||'')}</code>${x.output_markdown?`<label>Markdown</label><code>${esc(x.output_markdown)}</code>`:''}${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">打开JSON报告</button>`:''}`;
    $('#modal').classList.remove('hidden');
    toast(`${pkg.name} 场景执行计划：${x.status}`,x.status==='BLOCKED'?'warning':'success');
    await openProject(current)
  }catch(e){toast(e.message,'error')}
}

const requirementPackageFlowCardWithCreate=typeof requirementPackageFlowCard==='function'?requirementPackageFlowCard:null;
requirementPackageFlowCard=function(){
  let html=requirementPackageFlowCardWithCreate?requirementPackageFlowCardWithCreate():'';
  return html.replace('<p class="policy-note">目录根：', '<div class="hub-action-row"><button class="primary" onclick="showCreateRequirementPackageModal()">新建需求包</button><button class="small" onclick="showRequirementPackageChooser()">选择需求包</button></div><p class="policy-note">目录根：')
}

const requirementPackageSelectorHtmlWithCreate=typeof requirementPackageSelectorHtml==='function'?requirementPackageSelectorHtml:null;
requirementPackageSelectorHtml=function(){
  let html=requirementPackageSelectorHtmlWithCreate?requirementPackageSelectorHtmlWithCreate():'';
  return html.replace('</div><div class="metrics">','<button class="small" onclick="showCreateRequirementPackageModal()">新建</button><button class="small" onclick="generateSelectedRequirementPackageAccountModel()">账号模型</button><button class="small" onclick="generateSelectedRequirementExecutionPlan()">场景计划</button></div><div class="metrics">')
}

const unifiedExecutionFlowWithNewman=typeof unifiedExecutionFlow==='function'?unifiedExecutionFlow:null;
unifiedExecutionFlow=function(){
  let html=unifiedExecutionFlowWithNewman?unifiedExecutionFlowWithNewman():'';
  return html.replace('<button class="small" onclick="switchTab(\'reports\')">查看报告</button>', '<button class="small" onclick="generateSelectedRequirementPackageAccountModel()">账号模型</button><button class="small" onclick="runSelectedRequirementPackageNewman()">运行本包Newman</button><button class="small" onclick="generateSelectedRequirementScenarioReport()">场景总报告</button><button class="small" onclick="generateSelectedRequirementPackageAiReview()">AI复盘</button><button class="small" onclick="switchTab(\'reports\')">查看报告</button>')
}

function requirementPackagePills(){
  let selected=selectedRequirementPackageId();
  return portableRequirementPackages().map(pkg=>{
    let pid=requirementPackageId(pkg),chosen=pid===selected,status=packageStatusModel(pkg);
    return `<button class="package-pill ${chosen?'active':''}" onclick="setSelectedRequirementPackage('${esc(pid)}')"><b>${esc(pkg.name)}</b><span>质量 ${esc(status.quality)} · 执行 ${esc(status.execution)}</span></button>`
  }).join('')
}

function selectedPackageAssetLine(pkg){
  let artifacts=pkg.artifacts||{};
  let jmeter=artifacts.jmeter||{},account=artifacts.account_model||{},manifest=artifacts.manifest||{};
  return [
    ['账号模型',account.exists],
    ['证据规则',artifacts.evidence_rules?.exists],
    ['JMeter脚本',jmeter.exists],
    ['需求清单',manifest.exists]
  ].map(x=>`<span class="asset-chip ${x[1]?'ready':'pending'}">${esc(x[0])}</span>`).join('')
}

function packageStageTag(status){
  return status==='READY'||status==='PASSED'||status==='READY_WITH_WARNINGS'?'PASSED':status==='FAILED'||status==='BLOCKED'?'FAILED':'P1'
}

function runRequirementWorkflowStage(code){
  let pid=selectedRequirementPackageId();
  if(code==='01')return runPipeline();
  if(code==='02')return generateSelectedRequirementPackageAssets();
  if(code==='03')return generateStructuredTestCases();
  if(code==='04')return generateSelectedRequirementPackageAssets();
  if(code==='05')return openJmeterWorkbench(jmeterScriptKeyForPackage(pid));
  if(code==='06')return generateSelectedRequirementPackageAiReview();
  return switchTab('reports')
}

function requirementExecutionConsole(){
  let pkg=currentRequirementPackage(),pid=requirementPackageId(pkg),isSalary=pid==='salary-trade',map=data.salary_trade_jmeter_mapping||{},m=data.case_jmeter_model||{},flows=isSalary?(m.flows||[]):[],ready=flows.filter(x=>x.automation_status==='ready').length,activeRun=activeRequirementRunId(pid);
  if(!pid)return `<div class="card empty"><b>暂无需求包</b><p>先在需求资产里导入资料或新建需求包。</p></div>`;
  let wf=pkg.workflow_status||{},stages=wf.stages||[],next=wf.next_step||{},status=packageStatusModel(pkg);
  let fallback=[
    {code:'01',name:'生成测试用例',summary:`${pkg.counts?.test_cases||0}条用例 · ${pkg.counts?.test_points||0}个测试点`,status:pkg.counts?.test_cases?'READY':'PENDING'},
    {code:'02',name:'生成本包脚本',summary:isSalary?`${flows.length||0}条流程 · ${ready}条可脚本化`:'按账号模型输出工具脚本',status:'PENDING'},
    {code:'03',name:'打开外部工具',summary:`加载 ${pkg.name||pid} 的独立 JMX`,status:'PENDING'},
    {code:'04',name:'回收并复盘',summary:isSalary?`${map.jtl_rows||0}条JTL采样`:'报告回到当前需求包',status:'PENDING'}
  ];
  let visibleStages=stages.length?stages:fallback;
  return `<div class="execution-console"><div class="card package-focus"><div class="diagnosis-head"><div><h2>当前需求包</h2><p>执行中心只围绕这个需求包操作，脚本和报告不会串到别的需求。</p></div><span class="tag ${packageStatusClass(status.quality)}">质量 ${esc(status.quality)}</span></div><div class="package-title-block"><h3>${esc(pkg.name||pid)}</h3><p>${esc(pkg.description||'')}</p></div><div class="package-pills">${requirementPackagePills()}</div>${packageStatusStrip(pkg)}<div class="package-assets">${selectedPackageAssetLine(pkg)}</div><div class="summary-panel"><b>运行批次：${esc(activeRun||'尚未开始')}</b><p>${activeRun?'本轮所有工具和报告会归到同一个批次。':'第一次执行时自动创建，也可以现在手动新建。'}</p><button class="small" onclick="startNewRequirementRun()">新建运行批次</button></div><div class="summary-panel"><b>下一步：${esc(next.name||'继续执行')}</b><p>${esc(next.next_action||status.reason||'按当前需求包执行下一步。')}</p></div><div class="hub-action-row"><button class="small" onclick="showPortableRequirementPackage(portableRequirementPackages().findIndex(x=>requirementPackageId(x)===selectedRequirementPackageId()))">查看需求包</button><button class="small" onclick="showCreateRequirementPackageModal()">新建需求包</button><button class="small" onclick="showRequirementResourceCenter('${esc(pid)}')">资源与预检</button><button class="small" onclick="generateSelectedRequirementPackageAccountModel()">账号模型</button><button class="small" onclick="generateSelectedRequirementExecutionPlan()">场景计划</button></div><p class="policy-note">${esc(pkg.root||'')}</p></div><div class="card execution-focus"><div class="diagnosis-head"><div><h2>执行闭环</h2><p>接口测试、复杂业务场景和性能测试分别生成脚本与报告。</p></div><span class="tag PASSED">PACKAGE RUN</span></div><div class="execution-steps">${visibleStages.map(x=>`<button class="execution-step" onclick="runRequirementWorkflowStage('${esc(x.code)}')"><span>${esc(x.code)}</span><b>${esc(x.name)}</b><small>${esc(x.summary||'')}</small><em class="tag ${packageStageTag(x.status)}">${esc(x.status||'PENDING')}</em></button>`).join('')}</div><div class="hub-action-row primary-actions"><button class="primary" onclick="generateSelectedRequirementApiTestCases()">生成接口测试用例</button><button class="small" onclick="compileSelectedRequirementInterfaceTests()">生成接口测试脚本</button><button class="primary" onclick="runSelectedRequirementInterfaceTests()">运行接口测试</button><button class="primary" onclick="generateSelectedRequirementExecutionPlan()">生成场景计划</button><button class="primary" onclick="generateSelectedRequirementPackageAssets()">生成本包脚本</button><button class="primary" onclick="openJmeterWorkbench('${esc(jmeterScriptKeyForPackage(pid))}')">打开场景JMeter</button><button class="small" onclick="runSelectedRequirementPackageNewman()">业务冒烟</button><button class="small" onclick="generateSelectedRequirementNewmanAnalysis()">接口分析</button><button class="small" onclick="runSelectedRequirementPackagePytest()">pytest证据</button><button class="small" onclick="generateSelectedRequirementLoadPlan()">生成性能计划</button><button class="small" onclick="generateSelectedRequirementPerformanceAiReview()">性能分析</button><button class="small" onclick="generateSelectedRequirementScenarioReport()">场景总报告</button><button class="small" onclick="generateSelectedRequirementPackageAiReview()">AI复盘</button><button class="small" onclick="switchTab('reports')">报告中心</button></div><div id="salaryJmeterMappingResult"></div></div></div>${isSalary?`<details class="card compact-details"><summary><b>工资交易脚本明细</b><span>JMX、启动脚本、JTL位置</span></summary>${salaryTradeScriptPathCard()}</details>`:''}`
}

const requirementExecutionConsoleWithPipeline=requirementExecutionConsole;
requirementExecutionConsole=function(){
  let pkg=currentRequirementPackage(),pid=requirementPackageId(pkg),status=packageStatusModel(pkg),activeRun=activeRequirementRunId(pid);
  if(!pid)return `<div class="card empty"><b>暂无需求包</b><p>先在需求资产里导入资料或新建需求包。</p></div>`;
  let preparationStatus=status.preflight==='BLOCKED'?'BLOCKED':status.assets==='READY'?'READY':status.assets||'PENDING';
  let executionStatus=activeRun?(status.execution||'PENDING'):'NOT_RUN';
  let reviewStatus=activeRun?(status.quality||'PENDING'):'NOT_RUN';
  return `<div class="execution-console"><div class="card package-focus"><div class="diagnosis-head"><div><h2>当前需求包</h2><p>本页只负责当前需求包的一次完整执行，不在这里维护需求和接口资产。</p></div><span class="tag ${packageStatusClass(status.quality)}">质量 ${esc(status.quality)}</span></div><div class="package-title-block"><h3>${esc(pkg.name||pid)}</h3><p>${esc(pkg.description||'')}</p></div><div class="package-pills">${requirementPackagePills()}</div>${packageStatusStrip(pkg)}<div class="summary-panel"><b>运行批次：${esc(activeRun||'尚未开始')}</b><p>${activeRun?'本轮接口、流程、证据和报告都会归入这个批次。':'开始执行时自动创建新批次，历史结果不会冒充本轮结果。'}</p></div><div class="hub-action-row"><button class="small" onclick="switchTab('sources')">维护需求资产</button><button class="small" onclick="showRequirementResourceCenter('${esc(pid)}')">查看资源预检</button><button class="small" onclick="startNewRequirementRun()">新建空批次</button></div></div><div class="card execution-focus"><div class="diagnosis-head"><div><h2>执行主线</h2><p>按准备、执行、复盘三个阶段完成；具体工具由场景计划决定。</p></div><span class="tag PASSED">PACKAGE RUN</span></div><div class="execution-steps"><button class="execution-step" onclick="generateSelectedRequirementPackageAssets()"><span>01</span><b>准备</b><small>检查账号、数据来源和场景计划，生成本包脚本</small><em class="tag ${packageStageTag(preparationStatus)}">${esc(preparationStatus)}</em></button><button class="execution-step" onclick="submitCurrentPackageBackgroundTask()"><span>02</span><b>执行</b><small>后台运行当前需求包，避免页面长时间等待</small><em class="tag ${packageStageTag(executionStatus)}">${esc(executionStatus)}</em></button><button class="execution-step" onclick="switchTab('reports')"><span>03</span><b>复盘</b><small>查看原始报告、场景结论、数据证据和 AI 分析</small><em class="tag ${packageStageTag(reviewStatus)}">${esc(reviewStatus)}</em></button></div><div class="hub-action-row primary-actions"><button class="primary" onclick="generateSelectedRequirementPackageAssets()">准备执行</button><button class="primary" onclick="submitCurrentPackageBackgroundTask()">后台运行</button><button class="primary" onclick="switchTab('reports')">查看本包报告</button></div><details class="compact-details"><summary><b>维护与高级操作</b><span>接口用例、JMeter、pytest、性能与单项复盘</span></summary><div class="summary-panel"><b>资产准备</b><div class="hub-action-row"><button class="small" onclick="generateSelectedRequirementApiTestCases()">生成接口用例</button><button class="small" onclick="compileSelectedRequirementInterfaceTests()">生成接口脚本</button><button class="small" onclick="generateSelectedRequirementExecutionPlan()">更新场景计划</button><button class="small" onclick="generateSelectedRequirementPackageAccountModel()">账号模型</button><button class="small" onclick="showApifoxEnterpriseFlow()">Apifox交换</button></div></div><div class="summary-panel"><b>单项执行</b><div class="hub-action-row"><button class="small" onclick="runSelectedRequirementInterfaceTests()">接口测试</button><button class="small" onclick="runSelectedRequirementPackageNewman()">业务冒烟</button><button class="small" onclick="openJmeterWorkbench('${esc(jmeterScriptKeyForPackage(pid))}')">打开场景JMeter</button><button class="small" onclick="runSelectedRequirementPackagePytest()">pytest证据</button><button class="small" onclick="generateSelectedRequirementLoadPlan()">性能计划</button></div></div><div class="summary-panel"><b>单项复盘</b><div class="hub-action-row"><button class="small" onclick="generateSelectedRequirementNewmanAnalysis()">接口分析</button><button class="small" onclick="generateSelectedRequirementPerformanceAiReview()">性能分析</button><button class="small" onclick="generateSelectedRequirementScenarioReport()">场景总报告</button><button class="small" onclick="generateSelectedRequirementPackageAiReview()">AI复盘</button></div></div></details><div id="salaryJmeterMappingResult"></div></div></div>`
}

unifiedExecutionFlow=function(){
  return requirementExecutionConsole()
}

function reportPackageId(report){
  return report?.package_id || 'general'
}

function currentPackageReportIndex(){
  return data?.requirement_report_indexes?.[selectedRequirementPackageId()]||{runs:[],latest_reports:[],history:[],summary:{}}
}

function currentPackageReportRun(){
  let index=currentPackageReportIndex(),runId=selectedReportRunId();
  return (index.runs||[]).find(x=>x.run_id===runId)||index.runs?.[0]||null
}

function latestPackageRunWithReports(){
  return (currentPackageReportIndex().runs||[]).find(x=>(x.report_count||0)>0)||null
}

function packageReportCategoryConfig(){
  return [
    ['overview','测试总览','统一场景结论和本批次整体状态'],
    ['interface','接口测试','Newman与pytest接口执行结果'],
    ['performance','性能测试','JMeter请求、错误率与响应指标'],
    ['data','数据一致性','DB、Redis及业务证据结果'],
    ['risk','缺陷与风险','AI复盘、失败原因和处理建议'],
    ['evidence','完整证据','当前批次全部原始报告文件']
  ]
}

function reportsForCategory(reports,category){
  return category==='evidence'?reports:reports.filter(x=>(x.category||'evidence')===category)
}

function packageReportActionButtons(report){
  let type=report.report_type||'';
  return `${type==='REQUIREMENT_PACKAGE_NEWMAN_RUN'?`<button class="small" onclick="generateSelectedRequirementNewmanAnalysis('${esc(report.run_id||'')}')">接口分析</button> `:''}${type==='REQUIREMENT_PACKAGE_JMETER_RUN'?`<button class="small" onclick="generateSelectedRequirementPerformanceAiReview('${esc(report.run_id||'')}')">AI分析</button> `:''}${type==='REQUIREMENT_PACKAGE_UNIFIED_SCENARIO_REPORT'&&report.json_url?`<button class="small" onclick="showUnifiedScenarioReport('${esc(report.json_url)}')">场景</button> `:''}${['REQUIREMENT_PACKAGE_PYTEST_EVIDENCE_RUN','PYTEST_DEEP_EVIDENCE_REVIEW'].includes(type)&&report.json_url?`<button class="small" onclick="showPytestScenarioReport('${esc(report.json_url)}')">场景</button> `:''}${report.html_url?`<button class="small" onclick="openReport('${esc(report.html_url)}')">HTML</button> `:''}${report.jtl_url?`<button class="small" onclick="openReport('${esc(report.jtl_url)}')">JTL</button> `:''}${report.json_url?`<button class="small" onclick="openReport('${esc(report.json_url)}')">JSON</button>`:''}`
}

function packageReportLayer(report){
  let type=report?.report_type||'';
  if(['REQUIREMENT_PACKAGE_NEWMAN_RUN','REQUIREMENT_PACKAGE_JMETER_RUN','REQUIREMENT_PACKAGE_PYTEST_EVIDENCE_RUN'].includes(type))return ['原始执行','PASSED'];
  if(['REQUIREMENT_PACKAGE_NEWMAN_ANALYSIS','REQUIREMENT_PACKAGE_PERFORMANCE_AI_REVIEW','REQUIREMENT_PACKAGE_AI_REVIEW'].includes(type))return ['自动分析','P1'];
  if(type==='REQUIREMENT_PACKAGE_JMETER_LOAD_PLAN')return ['执行预案','P1'];
  if(type.includes('EVIDENCE'))return ['数据证据','PASSED'];
  if(type==='REQUIREMENT_PACKAGE_UNIFIED_SCENARIO_REPORT')return ['汇总结论','PASSED'];
  return ['原始证据',''];
}

function packageReportRows(reports,framed=true){
  if(!reports.length)return `<div class="${framed?'card ':''}empty"><b>这个批次还没有报告</b><p>从执行中心运行工具或生成场景报告后，会归档到当前批次。</p></div>`;
  return `<div class="${framed?'card ':''}report-table-card"><table><thead><tr><th>生成时间</th><th>层级</th><th>报告</th><th>状态</th><th>摘要</th><th>操作</th></tr></thead><tbody>${reports.map(x=>{let layer=packageReportLayer(x);return `<tr><td>${esc((x.created_at||'').replace('T',' '))}</td><td><span class="tag ${layer[1]}">${esc(layer[0])}</span></td><td><b>${esc(x.name||x.report_type)}</b><br><small>${esc(x.report_type||'')}</small></td><td><span class="tag ${statusTag(x.status)}">${esc(x.status)}</span></td><td>${esc(x.summary||'')}</td><td>${packageReportActionButtons(x)}</td></tr>`}).join('')}</tbody></table></div>`
}

function showPackageReportCategory(category){
  let pkg=currentRequirementPackage(),run=currentPackageReportRun(),source=category==='evidence'?(run?.reports||[]):(run?.latest_reports||run?.reports||[]),reports=reportsForCategory(source,category),config=packageReportCategoryConfig().find(x=>x[0]===category)||['','报告明细',''];
  $('#modalBody').innerHTML=`<h2>${esc(pkg.name||'需求包')} · ${esc(config[1])}</h2><p class="policy-note">运行批次：${esc(run?.run_id||'尚未运行')}。这里只显示这个需求包、这个批次的报告。</p>${packageReportRows(reports)}`;
  $('#modal').classList.remove('hidden')
}

function performanceBaselinePanel(run){
  let performance=run?.performance||{},baseline=performance.baseline||{},comparison=performance.comparison||{};
  if(!baseline.status||baseline.status==='unset'&&!comparison.reference_run_id)return '';
  let baselineLabel={unset:'未设置',candidate:'候选基线',active:'正式基线',invalid:'已失效'}[baseline.status]||baseline.status;
  let comparisonLabel={unknown:'尚未比较',pass:'与基线稳定',improved:'优于基线',regressed:'较基线回退'}[comparison.result]||comparison.result||'尚未比较';
  let changes=Object.entries(comparison.changes||{}).filter(([,item])=>item?.assessment&&item.assessment!=='stable');
  let changeRows=changes.slice(0,6).map(([name,item])=>`<div class="evidence-item"><b>${esc(name)}</b><small>${esc(item.assessment)} · 当前 ${esc(item.current)} · 基线 ${esc(item.baseline)} · ${esc(item.delta_pct)}%</small></div>`).join('');
  return `<div class="card"><div class="diagnosis-head"><div><h2>性能基线</h2><p>${esc(baseline.profile||'-')} · ${esc(baseline.environment||'-')} · 目标指纹 ${esc(baseline.target_fingerprint||'-')}</p></div><div class="formrow"><span class="tag ${baseline.status==='active'?'PASSED':baseline.status==='candidate'?'P1':''}">${esc(baselineLabel)}</span><span class="tag ${comparison.result==='regressed'?'P0':comparison.result==='improved'?'PASSED':'P1'}">${esc(comparisonLabel)}</span></div></div><p>${esc(comparison.reason||'首次有效结果先作为候选，人工确认后才参与后续比较。')}</p>${baseline.status==='candidate'?`<button class="primary" onclick="approveCurrentPerformanceBaseline()">批准为正式基线</button>`:''}${changeRows?`<div class="evidence-list">${changeRows}</div>`:''}</div>`
}

function performanceTrendPanel(index){
  let trends=index?.performance_trends||{},series=trends.series||[];
  if(!series.length)return '';
  let current=series[0],points=(current.points||[]).slice(-8).reverse();
  let rows=points.map(point=>{
    let metrics=point.metrics||{},result=point.comparison_result||'unknown';
    return `<button class="evidence-item asset-row" onclick="setSelectedReportRun('${esc(selectedRequirementPackageId())}','${esc(point.run_id)}')"><b>${esc(point.run_id)} ${point.baseline_status==='active'?'<span class="tag PASSED">正式基线</span>':''}</b><small>P95 ${esc(metrics.p95_ms??'-')}ms · 错误率 ${esc(metrics.error_rate??'-')}% · RPS ${esc(metrics.request_throughput_rps??'-')} · TPS ${esc(metrics.transaction_throughput_tps??'-')} · ${esc(result)}</small></button>`
  }).join('');
  return `<details class="card compact-details" open><summary><b>性能趋势</b><span>${esc(current.profile)} · ${esc(current.environment)} · ${points.length}个最近批次</span></summary><div class="summary-panel"><b>同环境、同 Profile、同目标才进入同一趋势</b><p>当前正式基线：${esc(current.active_baseline_run_id||'尚未批准')}；回退批次：${esc(trends.summary?.regressed_runs||0)}。</p></div><div class="evidence-list">${rows}</div></details>`
}

async function approveCurrentPerformanceBaseline(){
  let pid=selectedRequirementPackageId(),run=currentPackageReportRun();
  if(!pid||!run?.run_id)return toast('请先选择包含性能结果的运行批次','warning');
  try{
    await api(`/api/projects/${current}/requirement-packages/${pid}/performance-baselines/${run.run_id}/approve`,{method:'POST',body:JSON.stringify({approved_by:'workbench-user'})});
    toast('性能基线已批准，后续相同环境和Profile将自动对比','success');
    await loadRequirementReportIndex();
    render()
  }catch(e){toast(e.message,'error')}
}

function packageReportCenter(){
  let pkg=currentRequirementPackage(),pid=selectedRequirementPackageId(),index=currentPackageReportIndex(),runs=index.runs||[],run=currentPackageReportRun(),reports=run?.latest_reports||run?.reports||[],failed=reports.filter(x=>!['PASSED','READY'].includes(x.status)),latestReportedRun=latestPackageRunWithReports(),emptyCreatedRun=run&&!(run.report_count||0)&&run.status==='CREATED';
  let packagePills=portableRequirementPackages().map(item=>{let key=requirementPackageId(item),idx=data?.requirement_report_indexes?.[key],count=idx?.summary?.runs??item?.status_model?.report_count??0;return `<button class="package-pill ${key===pid?'active':''}" onclick="setSelectedRequirementPackage('${esc(key)}')"><b>${esc(item.name)}</b><span>${esc(count)}个批次</span></button>`}).join('');
  let categoryCards=packageReportCategoryConfig().map(([key,title,desc])=>{let count=reportsForCategory(reports,key).length;return `<button class="delivery-card" onclick="showPackageReportCategory('${key}')"><div><b>${title}</b><span class="tag ${count?'PASSED':'P1'}">${count}</span></div><p>${desc}</p><small>${count?'点击查看本批次明细':emptyCreatedRun?'当前批次尚未执行':'本批次暂无此类报告'}</small></button>`}).join('');
  let runOptions=runs.map(x=>`<option value="${esc(x.run_id)}" ${x.run_id===run?.run_id?'selected':''}>${esc((x.created_at||'').replace('T',' ').slice(0,19))} · ${esc(x.status)} · ${esc(x.report_count||0)}份报告 · ${esc(x.name||x.run_id)}</option>`).join('');
  let history=runs.filter(x=>x.run_id!==run?.run_id);
  return `<div class="card report-workbench"><div class="diagnosis-head"><div><span class="tag PASSED">PACKAGE REPORTS</span><h2>报告中心</h2><p>先选需求包，再选运行批次。分类入口保留，但不同需求、不同批次不会混在一起。</p></div><span class="tag ${statusTag(run?.status)}">${esc(run?.status||'NOT_RUN')}</span></div><div class="report-package-strip">${packagePills}</div><div class="report-scope-row"><select onchange="setSelectedReportRun('${esc(pid)}',this.value)">${runOptions||'<option value="">尚无运行批次</option>'}</select><button class="small" onclick="startNewRequirementRun()">新建运行批次</button>${emptyCreatedRun&&latestReportedRun&&latestReportedRun.run_id!==run.run_id?`<button class="small" onclick="setSelectedReportRun('${esc(pid)}','${esc(latestReportedRun.run_id)}')">查看最近有报告批次</button>`:''}<button class="small" onclick="loadRequirementReportIndex().then(()=>render())">刷新报告</button></div>${emptyCreatedRun?`<div class="summary-panel"><b>当前批次只完成了创建，尚未执行</b><p>新建批次不会自动产生报告。请前往执行中心运行对应工具，或者切换到已有报告的历史批次查看结果。</p></div>`:''}<div class="metrics"><div class="metric"><span>当前需求包</span><b style="font-size:20px">${esc(pkg.name||pid||'-')}</b></div><div class="metric"><span>当前批次报告</span><b>${emptyCreatedRun?'尚未执行':reports.length}</b></div><div class="metric"><span>异常/待处理</span><b>${failed.length}</b></div><div class="metric"><span>历史批次</span><b>${history.length}</b></div></div></div>${performanceBaselinePanel(run)}${performanceTrendPanel(index)}<div class="delivery-grid">${categoryCards}</div>${run?`<div class="card"><div class="diagnosis-head"><div><h2>当前运行批次</h2><p>${esc(run.name||run.run_id)} · ${esc((run.created_at||'').replace('T',' '))}</p></div><code>${esc(run.run_id)}</code></div>${packageReportRows(reports,false)}</div>`:'<div class="card empty"><b>当前需求包还没有新运行报告</b><p>旧报告不再回退展示。请新建运行批次并重新执行。</p><button class="primary" onclick="startNewRequirementRun()">新建运行批次</button></div>'}${history.length?`<details class="card compact-details"><summary><b>历史运行批次</b><span>${history.length}个，仅按批次进入</span></summary><div class="evidence-list">${history.map(x=>`<button class="evidence-item asset-row" onclick="setSelectedReportRun('${esc(pid)}','${esc(x.run_id)}')"><b>${esc(x.name||x.run_id)}</b><small>${esc((x.created_at||'').replace('T',' '))} · ${esc(x.status)} · ${esc(x.report_count||0)}份报告</small></button>`).join('')}</div></details>`:''}`
}

enterpriseReportCenter=function(){
  return packageReportCenter()
}

function latestMetadataAuditReports(){
  return (data.generated_reports||[]).filter(x=>x.kind==='元数据校验').slice(0,5)
}

function latestBusinessEvidencePlanReports(){
  return (data.generated_reports||[]).filter(x=>x.kind==='业务证据规则').slice(0,5)
}

function latestBusinessEvidenceRunReports(){
  return (data.generated_reports||[]).filter(x=>x.kind==='业务证据执行').slice(0,5)
}

function latestCandidateEvidenceRuleReports(){
  return (data.generated_reports||[]).filter(x=>x.kind==='候选证据规则').slice(0,5)
}

function latestStructuredTestCaseReports(){
  return (data.generated_reports||[]).filter(x=>x.kind==='结构化用例').slice(0,5)
}

async function runMetadataHallucinationAudit(){
  let box=$('#metadataAuditStatus'),pkg=currentRequirementPackage(),pid=requirementPackageId(pkg)||selectedRequirementPackageId();
  try{
    if(box)box.innerHTML='<div class="summary-panel"><b>正在校验AI输出</b><p>平台会把需求包、测试用例、脚本资产里出现的表、字段和Redis Key，与已保存元数据做比对。</p></div>';
    toast('正在做元数据幻觉校验…');
    let result=await api(`/api/projects/${current}/metadata-hallucination-audit`,{method:'POST',body:JSON.stringify({package_id:pid})});
    let s=result.summary||{},msg=`校验完成：${result.status}，已证实${(s.db_references_verified||0)+(s.redis_references_verified||0)}项，提醒${s.attention_items||0}项`;
    if(box)box.innerHTML=`<div class="summary-panel"><b>${esc(msg)}</b><p>扫描 ${esc(s.sources_scanned||0)} 处资产；报告已进入当前需求包的报告中心。</p>${result.json_url?`<button class="small" onclick="openReport('${esc(result.json_url)}')">查看JSON</button>`:''}</div>`;
    toast(msg,result.status==='PASSED'?'success':result.status==='ATTENTION'?'warning':'error');
    await openProject(current);
    switchTab('dataquality')
  }catch(e){
    if(box)box.innerHTML=`<div class="summary-panel"><b>校验失败</b><p>${esc(e.message)}</p></div>`;
    toast(e.message,'error')
  }
}

async function generateMetadataHallucinationCorrection(){
  let box=$('#metadataAuditStatus'),pkg=currentRequirementPackage(),pid=requirementPackageId(pkg)||selectedRequirementPackageId();
  try{
    if(box)box.innerHTML='<div class="summary-panel"><b>正在生成一次修正版</b><p>平台会读取最新元数据校验报告，把未证实的DB/Redis引用降级为待确认项，并保存为候选修正版。</p></div>';
    toast('正在生成AI输出修正版…');
    let result=await api(`/api/projects/${current}/metadata-hallucination-correction`,{method:'POST',body:JSON.stringify({package_id:pid})});
    let s=result.summary||{},changes=result.changes||[],refs=result.unverified_references||[],files=result.generated_files||[],msg=`修正完成：${result.status}，生成${s.assets_generated||0}份，调整${s.changes||0}处`;
    let fileRows=files.map(f=>{let safe=String(f||'').replace(/\\/g,'\\\\').replace(/'/g,"\\'");return `<div class="evidence-item script-path-row"><div><b>${esc((f||'').split(/[\\/]/).pop()||'候选文件')}</b><small>${esc(f)}</small></div><button class="small" onclick="copyText('${esc(safe)}')">复制</button></div>`}).join('');
    let changeRows=changes.map(x=>`<div class="gap-item P1"><span class="tag P1">待确认</span><div><b>${esc(x.asset||'资产')}</b><p>${esc(x.action||'')}</p><small>调整 ${esc(x.changed_items||0)} 处</small></div></div>`).join('');
    if(box)box.innerHTML=`<div class="summary-panel"><b>${esc(msg)}</b><p>修正版不会覆盖正式资产；请确认后再采纳。</p>${result.json_url?`<button class="small" onclick="openReport('${esc(result.json_url)}')">查看JSON</button>`:''}</div>`;
    $('#modalBody').innerHTML=`<h2>${esc(pkg.name||pid)} · 一次修正版</h2><p class="policy-note">本次只生成候选修正版，不覆盖正式资产。确认元数据真实存在后，再人工采纳。</p><div class="metrics"><div class="metric"><span>状态</span><b style="font-size:20px">${esc(result.status)}</b></div><div class="metric"><span>未证实引用</span><b>${esc(s.unverified_references||0)}</b></div><div class="metric"><span>候选文件</span><b>${esc(s.assets_generated||0)}</b></div><div class="metric"><span>调整</span><b>${esc(s.changes||0)}</b></div></div>${refs.length?`<h3>未证实引用</h3><div class="evidence-list">${refs.map(r=>`<div class="evidence-item"><b>${esc(r)}</b><small>DB/Redis 元数据中暂未证实</small></div>`).join('')}</div>`:''}${changeRows?`<h3>修正动作</h3><div class="gap-list">${changeRows}</div>`:''}${fileRows?`<h3>候选修正版文件</h3><div class="evidence-list">${fileRows}</div>`:''}<label>输出目录</label><code>${esc(result.output_dir||'')}</code>${result.json_url?`<button class="small" onclick="openReport('${esc(result.json_url)}')">打开报告JSON</button>`:''}`;
    $('#modal').classList.remove('hidden');
    toast(msg,result.status==='CORRECTED'?'success':result.status==='NO_FINDINGS'?'success':'warning');
    await openProject(current);
    switchTab('dataquality')
  }catch(e){
    if(box)box.innerHTML=`<div class="summary-panel"><b>生成修正版失败</b><p>${esc(e.message)}</p></div>`;
    toast(e.message,'error')
  }
}

const dataQualityClosureBeforeMetadataAudit=dataQualityClosure;
dataQualityClosure=function(){
  let html=dataQualityClosureBeforeMetadataAudit?dataQualityClosureBeforeMetadataAudit():'';
  let reports=latestMetadataAuditReports(),corrections=(data.generated_reports||[]).filter(x=>x.kind==='元数据修正').slice(0,5),plans=latestBusinessEvidencePlanReports(),runs=latestBusinessEvidenceRunReports(),candidates=latestCandidateEvidenceRuleReports(),structured=latestStructuredTestCaseReports();
  let auditReports=[...reports,...corrections].slice(0,6);
  let audit=`<div class="card"><div class="diagnosis-head"><div><h2>AI输出校验</h2><p>用已保存的数据库表、字段和Redis Key核查AI生成内容，发现未证实引用后只生成一次候选修正版。</p></div><div class="formrow"><button class="primary" onclick="runMetadataHallucinationAudit()">元数据幻觉校验</button><button class="small" onclick="generateMetadataHallucinationCorrection()">生成一次修正版</button></div></div><div id="metadataAuditStatus">${auditReports.length?auditReports.map(x=>`<div class="summary-panel"><b>${esc(x.kind||'报告')} · ${esc(x.status)} · ${esc((x.created_at||'').replace('T',' '))}</b><p>${esc(x.summary||'')}</p>${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">查看报告</button>`:''}</div>`).join(''):'<div class="empty"><b>暂无AI输出校验报告</b></div>'}</div></div>`;
  let structuredPanel=`<div class="card"><div class="diagnosis-head"><div><h2>结构化测试用例</h2><p>按当前需求包生成增强用例，把接口字段、运行变量、DB/Redis证据规则、质量分级和脚本生成就绪状态写进用例。</p></div><div class="formrow"><button class="primary" onclick="generateStructuredTestCases()">生成结构化用例</button><button class="small" onclick="showRegressionSelectionModal()">选择回归范围</button></div></div><div id="structuredTestCaseStatus">${structured.length?structured.map(x=>`<div class="summary-panel"><b>${esc(x.status)} · ${esc((x.created_at||'').replace('T',' '))}</b><p>${esc(x.summary||'')}</p>${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">查看报告</button>`:''}</div>`).join(''):'<div class="empty"><b>暂无结构化用例报告</b></div>'}</div></div>`;
  let candidatePanel=`<div class="card"><div class="diagnosis-head"><div><h2>候选证据规则</h2><p>根据当前需求包的测试用例和数据范围，自动推荐执行后应该查哪些表、用哪些变量和断言；没有数据范围时只给待确认候选。</p></div><div class="formrow"><button class="primary" onclick="generateCandidateEvidenceRules()">生成候选规则</button><button class="small" onclick="showAcceptCandidateEvidenceRulesModal()">采纳候选</button></div></div><div id="candidateEvidenceRuleStatus">${candidates.length?candidates.map(x=>`<div class="summary-panel"><b>${esc(x.status)} · ${esc((x.created_at||'').replace('T',' '))}</b><p>${esc(x.summary||'')}</p>${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">查看报告</button>`:''}</div>`).join(''):'<div class="empty"><b>暂无候选证据规则</b></div>'}</div></div>`;
  let evidencePlan=`<div class="card"><div class="diagnosis-head"><div><h2>执行后业务证据</h2><p>把当前需求包的证据规则整理成计划并执行：接口跑完后去哪张表或哪个Key查、用什么变量定位、期望什么结果。</p></div><div class="formrow"><button class="primary" onclick="generateBusinessEvidencePlan()">生成证据计划</button><button class="primary" onclick="showBusinessEvidenceRunModal()">执行证据规则</button></div></div><div id="businessEvidencePlanStatus">${plans.length?plans.map(x=>`<div class="summary-panel"><b>${esc(x.status)} · ${esc((x.created_at||'').replace('T',' '))}</b><p>${esc(x.summary||'')}</p>${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">查看报告</button>`:''}</div>`).join(''):'<div class="empty"><b>暂无业务证据规则报告</b></div>'}</div><div id="businessEvidenceRunStatus">${runs.length?runs.map(x=>`<div class="summary-panel"><b>${esc(x.status)} · ${esc((x.created_at||'').replace('T',' '))}</b><p>${esc(x.summary||'')}</p>${x.json_url?`<button class="small" onclick="openReport('${esc(x.json_url)}')">查看执行报告</button>`:''}</div>`).join(''):''}</div></div>`;
  return html + audit + structuredPanel + candidatePanel + evidencePlan
}

async function generateStructuredTestCases(){
  let box=$('#structuredTestCaseStatus'),pkg=currentRequirementPackage(),pid=requirementPackageId(pkg)||selectedRequirementPackageId();
  try{
    if(box)box.innerHTML='<div class="summary-panel"><b>正在生成结构化用例</b><p>平台会读取当前需求包测试用例，并把接口字段、DB/Redis证据校验点补进用例步骤和预期结果。</p></div>';
    toast('正在生成结构化测试用例…');
    let result=await api(`/api/projects/${current}/structured-test-cases`,{method:'POST',body:JSON.stringify({package_id:pid})});
    let s=result.summary||{},q=s.quality_counts||{},r=s.readiness_counts||s.automation_counts||{},ready=r.SCRIPT_GENERATION_READY||r.AUTO_READY||0,d=result.coverage_dashboard||{},gaps=result.gap_list||[],jm=result.jmeter_mapping||{},pf=result.data_preflight||{},detail=pf.details||{},cred=detail.credential_sources||{},msg=`结构化用例完成：${result.status}，用例${s.cases||0}条`;
    let input=detail.input_detection||{},roles=input.roles||{},appIn=roles.applicant||{},proxyIn=roles.proxy||{};
    let preflightLine=detail.applicants?`申请人 ${detail.applicants.length||0} 个 · 国家币种 ${detail.country_currency_pairs?.length||0} 组 · 代理匹配 ${detail.proxy_matches?.filter(x=>x.matched).length||0}/${detail.proxy_matches?.length||0} · 代理凭证 ${cred.proxy_ready||0}/${cred.proxy_total||0}`:'';
    let inputLine=input.policy?`输入检测：启用 ${esc((input.enabled_sources||[]).join('、')||'-')}；默认不强制 ${esc((input.disabled_by_default||[]).join('、')||'-')}。申请人可用 ${esc(appIn.usable??'-')}/${esc(appIn.total??'-')}，代理可用 ${esc(proxyIn.usable??'-')}/${esc(proxyIn.total??'-')}。`:'';
    if(box)box.innerHTML=`<div class="summary-panel"><b>${esc(msg)}</b><p>${esc(d.headline||`READY ${q.READY||0} 条，脚本生成就绪 ${ready} 条，待证据 ${(q.NEEDS_EVIDENCE||0)+(q.NEEDS_EVIDENCE_REVIEW||0)} 条，人工 ${q.MANUAL_ONLY||0} 条。`)}</p><p>JMeter目标 ${esc(jm.summary?.jmeter_targets||jm.jmeter_targets||0)} 条，Redis可选建议 ${esc(s.with_optional_redis_suggestions||0)} 条，数据预检 ${esc(pf.status||'-')}，缺口分组 ${esc(gaps.length)} 类。</p>${preflightLine?`<p>${esc(preflightLine)}</p>`:''}${inputLine?`<p>${inputLine}</p>`:''}${result.json_url?`<button class="small" onclick="openReport('${esc(result.json_url)}')">查看JSON</button>`:''}</div>${scenarioPreflightHtml(pf)}`;
    toast(msg,result.status==='READY'?'success':'warning');
    await openProject(current);
    switchTab('dataquality')
  }catch(e){
    if(box)box.innerHTML=`<div class="summary-panel"><b>生成失败</b><p>${esc(e.message)}</p></div>`;
    toast(e.message,'error')
  }
}

function showAcceptCandidateEvidenceRulesModal(){
  let pkg=currentRequirementPackage(),pid=requirementPackageId(pkg)||selectedRequirementPackageId();
  $('#modalBody').innerHTML=`<h2>${esc(requirementPackageName(pid))} · 采纳候选规则</h2><p class="policy-note">只会追加到正式 evidence_rules.yaml，不会覆盖已有规则。留空表示采纳全部已确认范围的候选；缺少数据范围确认的候选不会被采纳。</p><label>规则ID</label><textarea id="acceptCandidateRuleIds" rows="8" placeholder="一行一个，或用逗号分隔；留空采纳全部可采纳候选"></textarea><div class="formrow"><button id="acceptCandidateRulesButton" class="primary" onclick="acceptCandidateEvidenceRules()">采纳</button><button class="small" onclick="$('#modal').classList.add('hidden')">取消</button></div><div id="acceptCandidateRulesStatus"></div>`;
  $('#modal').classList.remove('hidden')
}

async function acceptCandidateEvidenceRules(){
  let button=$('#acceptCandidateRulesButton'),box=$('#acceptCandidateRulesStatus'),pkg=currentRequirementPackage(),pid=requirementPackageId(pkg)||selectedRequirementPackageId();
  let ids=($('#acceptCandidateRuleIds')?.value||'').split(/[\n,，;；\s]+/).map(x=>x.trim()).filter(Boolean);
  try{
    if(button){button.disabled=true;button.textContent='采纳中…'}
    if(box)box.innerHTML='<div class="summary-panel"><b>正在写入正式规则</b><p>平台会跳过已存在规则，并生成采纳报告。</p></div>';
    let result=await api(`/api/projects/${current}/accept-candidate-evidence-rules`,{method:'POST',body:JSON.stringify({package_id:pid,rule_ids:ids})});
    let s=result.summary||{},msg=`采纳完成：新增${s.accepted||0}条，跳过${s.skipped||0}条`;
    if(box)box.innerHTML=`<div class="summary-panel"><b>${esc(msg)}</b><p>正式规则当前 ${esc(s.official_rules||0)} 条。</p>${result.json_url?`<button class="small" onclick="openReport('${esc(result.json_url)}')">查看JSON</button>`:''}</div>`;
    toast(msg,result.status==='READY'?'success':'warning');
    await openProject(current);
    switchTab('dataquality')
  }catch(e){
    if(box)box.innerHTML=`<div class="summary-panel"><b>采纳失败</b><p>${esc(e.message)}</p></div>`;
    toast(e.message,'error')
  }finally{
    let b=$('#acceptCandidateRulesButton');if(b){b.disabled=false;b.textContent='采纳'}
  }
}

async function generateCandidateEvidenceRules(){
  let box=$('#candidateEvidenceRuleStatus'),pkg=currentRequirementPackage(),pid=requirementPackageId(pkg)||selectedRequirementPackageId();
  try{
    if(box)box.innerHTML='<div class="summary-panel"><b>正在生成候选规则</b><p>平台会读取当前需求包测试用例，并结合数据库表元数据推荐证据规则，不覆盖正式规则。</p></div>';
    toast('正在根据测试用例生成候选证据规则…');
    let result=await api(`/api/projects/${current}/candidate-evidence-rules`,{method:'POST',body:JSON.stringify({package_id:pid})});
    let s=result.summary||{},msg=`候选规则完成：${result.status}，生成${s.candidates||0}条`;
    if(box)box.innerHTML=`<div class="summary-panel"><b>${esc(msg)}</b><p>扫描用例 ${esc(s.cases_scanned||0)} 条，表范围 ${esc(s.db_tables_scanned||0)} 张，范围来源 ${esc(s.scope||'-')}；${s.needs_scope_confirmation?'需要先确认数据范围。':'候选文件已写入需求包。'}</p>${result.json_url?`<button class="small" onclick="openReport('${esc(result.json_url)}')">查看JSON</button>`:''}</div>`;
    toast(msg,result.status==='READY'?'success':'warning');
    await openProject(current);
    switchTab('dataquality')
  }catch(e){
    if(box)box.innerHTML=`<div class="summary-panel"><b>生成失败</b><p>${esc(e.message)}</p></div>`;
    toast(e.message,'error')
  }
}

async function generateBusinessEvidencePlan(){
  let box=$('#businessEvidencePlanStatus'),pkg=currentRequirementPackage(),pid=requirementPackageId(pkg)||selectedRequirementPackageId();
  try{
    if(box)box.innerHTML='<div class="summary-panel"><b>正在生成证据计划</b><p>平台会读取当前需求包的 evidence_rules.yaml，并检查规则能否被已保存元数据支撑。</p></div>';
    toast('正在生成执行后业务证据计划…');
    let result=await api(`/api/projects/${current}/business-evidence-plan`,{method:'POST',body:JSON.stringify({package_id:pid})});
    let s=result.summary||{},msg=`证据计划完成：${result.status}，规则${s.ready||0}/${s.rules||0}可用`;
    if(box)box.innerHTML=`<div class="summary-panel"><b>${esc(msg)}</b><p>MySQL ${esc(s.mysql_rules||0)} 条，Redis ${esc(s.redis_rules||0)} 条，提醒 ${esc(s.attention||0)} 项。</p>${result.json_url?`<button class="small" onclick="openReport('${esc(result.json_url)}')">查看JSON</button>`:''}</div>`;
    toast(msg,result.status==='READY'?'success':'warning');
    await openProject(current);
    switchTab('dataquality')
  }catch(e){
    if(box)box.innerHTML=`<div class="summary-panel"><b>生成失败</b><p>${esc(e.message)}</p></div>`;
    toast(e.message,'error')
  }
}

function showBusinessEvidenceRunModal(){
  let pkg=currentRequirementPackage(),pid=requirementPackageId(pkg)||selectedRequirementPackageId();
  let sample={package_id:pid,scenarios:[{name:"流程A：创建后取消",rule_ids:["salary_trade_agent_whitelist_matched","salary_trade_cancelled","salary_trade_status_log_traceable"],order_no:"",applicant_uid:"",proxy_uid:"",country_code:"",currency:"",expected_log_statuses:"10,50"},{name:"流程C：确认收款完成",rule_ids:["salary_trade_agent_whitelist_matched","salary_trade_finished","salary_trade_status_log_traceable"],order_no:"",applicant_uid:"",proxy_uid:"",country_code:"",currency:"",expected_log_statuses:"10,20,30,100"}]};
  $('#modalBody').innerHTML=`<h2>${esc(requirementPackageName(pid))} · 执行业务证据规则</h2><p class="policy-note">这里不写业务库，只用运行变量去只读查询DB/Redis。JMeter跑完后，把订单号和账号上下文填进来。</p><label>运行变量 JSON</label><textarea id="businessEvidenceRunJson" rows="10">${esc(JSON.stringify(sample,null,2))}</textarea><div class="formrow"><button id="businessEvidenceRunButton" class="primary" onclick="runBusinessEvidenceRules()">执行规则</button><button class="small" onclick="$('#modal').classList.add('hidden')">取消</button></div><div id="businessEvidenceRunModalStatus"></div>`;
  $('#modal').classList.remove('hidden')
}

async function runBusinessEvidenceRules(){
  let button=$('#businessEvidenceRunButton'),box=$('#businessEvidenceRunModalStatus'),payload={};
  try{payload=JSON.parse($('#businessEvidenceRunJson')?.value||'{}')}catch{return toast('运行变量必须是合法 JSON','warning')}
  try{
    if(button){button.disabled=true;button.textContent='执行中…'}
    if(box)box.innerHTML='<div class="summary-panel"><b>正在只读查询业务证据</b><p>平台会按 evidence_rules.yaml 执行规则，并生成证据报告。</p></div>';
    let result=await api(`/api/projects/${current}/business-evidence-run`,{method:'POST',body:JSON.stringify(payload)});
    let s=result.summary||{},msg=`执行完成：${result.status}，通过${s.rules_passed||0}/${s.rules_total||0}`;
    if(box)box.innerHTML=`<div class="summary-panel"><b>${esc(msg)}</b><p>失败 ${esc(s.rules_failed||0)}，阻断 ${esc(s.rules_blocked||0)}。</p>${result.json_url?`<button class="small" onclick="openReport('${esc(result.json_url)}')">查看JSON</button>`:''}</div>`;
    toast(msg,result.status==='PASSED'?'success':result.status==='FAILED'?'error':'warning');
    await openProject(current);
    switchTab('dataquality')
  }catch(e){
    if(box)box.innerHTML=`<div class="summary-panel"><b>执行失败</b><p>${esc(e.message)}</p></div>`;
    toast(e.message,'error')
  }finally{
    let b=$('#businessEvidenceRunButton');if(b){b.disabled=false;b.textContent='执行规则'}
  }
}

function showRegressionSelectionModal(){
  let pkg=currentRequirementPackage(),pid=requirementPackageId(pkg)||selectedRequirementPackageId();
  $('#modalBody').innerHTML=`<h2>${esc(requirementPackageName(pid))} · 回归用例选择</h2><p class="policy-note">填写本次真实变更范围。默认只选择 ACTIVE 用例；DRAFT 和 DEPRECATED 仅在人工勾选后进入候选，完整用例集不会被修改。</p><label>变更需求ID</label><textarea id="regressionRequirements" rows="2" placeholder="例如 REQ-ORDER，一行一个"></textarea><label>变更接口</label><textarea id="regressionEndpoints" rows="3" placeholder="例如 POST /orders 或 /orders/{id}"></textarea><label>变更数据库表</label><textarea id="regressionTables" rows="2" placeholder="例如 anchor_salary_trade_order"></textarea><label>变更Redis Key</label><textarea id="regressionRedisKeys" rows="2" placeholder="没有则留空"></textarea><label>角色、状态或业务关键词</label><textarea id="regressionKeywords" rows="2" placeholder="例如 applicant、PENDING、取消订单"></textarea><div class="formrow"><label><input id="regressionIncludeRelated" type="checkbox" checked> 包含关联影响用例</label><label><input id="regressionIncludeCritical" type="checkbox" checked> 包含P0关键路径</label><label><input id="regressionIncludeDraft" type="checkbox"> 包含DRAFT</label><label><input id="regressionIncludeDeprecated" type="checkbox"> 包含DEPRECATED</label></div><div class="formrow"><button id="regressionSelectionButton" class="primary" onclick="generateRegressionSelection()">生成回归清单</button><button class="small" onclick="$('#modal').classList.add('hidden')">取消</button></div><div id="regressionSelectionStatus"></div>`;
  $('#modal').classList.remove('hidden')
}

function regressionLines(id){return ($('#'+id)?.value||'').split(/[\n,，;；]+/).map(x=>x.trim()).filter(Boolean)}

async function generateRegressionSelection(){
  let pkg=currentRequirementPackage(),pid=requirementPackageId(pkg)||selectedRequirementPackageId(),button=$('#regressionSelectionButton'),box=$('#regressionSelectionStatus');
  let lifecycleStatuses=['ACTIVE'];if($('#regressionIncludeDraft')?.checked)lifecycleStatuses.push('DRAFT');if($('#regressionIncludeDeprecated')?.checked)lifecycleStatuses.push('DEPRECATED');let payload={changed_requirements:regressionLines('regressionRequirements'),changed_endpoints:regressionLines('regressionEndpoints'),changed_tables:regressionLines('regressionTables'),changed_redis_keys:regressionLines('regressionRedisKeys'),keywords:regressionLines('regressionKeywords'),lifecycle_statuses:lifecycleStatuses,include_related:$('#regressionIncludeRelated')?.checked!==false,include_critical:$('#regressionIncludeCritical')?.checked!==false};
  try{
    if(button){button.disabled=true;button.textContent='分析中…'}
    let result=await api(`/api/projects/${current}/requirement-packages/${pid}/regression-selection`,{method:'POST',body:JSON.stringify(payload)}),s=result.summary||{},items=result.selected_cases||[];
    if(box)box.innerHTML=`<div class="summary-panel"><b>${esc(result.status)} · 选择 ${esc(s.selected||0)}/${esc(s.source_cases||0)} 条</b><p>${esc(result.message||'')}</p>${result.path?`<code>${esc(result.path)}</code>`:''}</div>${items.length?`<table><thead><tr><th>用例</th><th>类型</th><th>原因</th></tr></thead><tbody>${items.slice(0,50).map(x=>`<tr><td><b>${esc(x.title||x.case_id)}</b><small>${esc(x.method||'')} ${esc(x.path||'')}</small></td><td><span class="tag ${x.selection_type==='DIRECT'?'P0':'P1'}">${esc(x.selection_type)}</span></td><td>${esc((x.reasons||[]).join('；'))}</td></tr>`).join('')}</tbody></table>`:''}`;
    toast(result.message||'回归清单已生成',result.status==='READY'?'success':'warning')
  }catch(e){if(box)box.innerHTML=`<div class="summary-panel"><b>回归选择失败</b><p>${esc(e.message)}</p></div>`;toast(e.message,'error')}
  finally{if(button){button.disabled=false;button.textContent='生成回归清单'}}
}

const openProjectBeforeBackgroundTasks=openProject;
openProject=async function(id){
  await openProjectBeforeBackgroundTasks(id);
  try{data.background_tasks=await api('/api/tasks?limit=20')}catch{data.background_tasks=[]}
  try{data.mobile_catalog=await window.QualityHub.services.mobile.catalog()}catch(error){data.mobile_catalog={status:'BLOCKED',blockers:[error.message],devices:[],scenarios:[],page_objects:[],latest_runs:[]}}
  render()
};

const renderBeforeBackgroundTasks=render;
render=function(){
  renderBeforeBackgroundTasks();
  const automation=$('#automation');
  if(!automation)return;
  const mobilePanel=window.QualityHub.components.mobilePanel.render(data?.mobile_catalog,data?.background_tasks||[],esc);
  const taskPanel=window.QualityHub.components.taskPanel.render(data?.background_tasks||[],esc);
  automation.insertAdjacentHTML('afterbegin',mobilePanel);
  automation.insertAdjacentHTML('afterbegin',taskPanel)
};

async function refreshMobileCatalog(){
  try{
    const configPath=$('#mobileConfigPath')?.value.trim()||'';
    data.mobile_catalog=await window.QualityHub.services.mobile.catalog(configPath);
    data.background_tasks=await api('/api/tasks?limit=20');
    render();
    toast(data.mobile_catalog.status==='READY'?'移动端设备与场景已刷新':'移动端预检仍有待处理项',data.mobile_catalog.status==='READY'?'success':'warning')
  }catch(error){toast(error.message,'error')}
}

async function submitMobileAutomationTask(){
  const scenarios=$$('input[name="mobileScenario"]:checked').map(item=>item.value);
  const devices=$$('input[name="mobileDevice"]:checked').map(item=>item.value);
  const configPath=$('#mobileConfigPath')?.value.trim()||'';
  const apkPath=$('#mobileApkPath')?.value.trim()||'';
  if(!scenarios.length)return toast('请至少选择一个移动端场景','warning');
  if(!devices.length)return toast('请至少选择一台真机或模拟器','warning');
  try{
    const task=await window.QualityHub.services.mobile.run({config_path:configPath,apk_path:apkPath,scenarios,devices});
    data.background_tasks=[task,...(data.background_tasks||[]).filter(item=>item.task_id!==task.task_id)];
    render();
    toast(`移动端任务已进入后台：${task.task_id}`,'success');
    let lastPaint=0;
    window.QualityHub.services.tasks.wait(task.task_id,{timeout:7200000,interval:1000,onProgress:state=>{
      data.background_tasks=[state,...(data.background_tasks||[]).filter(item=>item.task_id!==state.task_id)];
      if(Date.now()-lastPaint>1500||['PASSED','FAILED','CANCELLED','INTERRUPTED'].includes(state.status)){lastPaint=Date.now();render()}
    }}).then(async state=>{
      data.mobile_catalog=await window.QualityHub.services.mobile.catalog(configPath);
      data.background_tasks=await api('/api/tasks?limit=20');
      render();
      toast(state.status==='PASSED'?'移动端自动化完成，Allure报告已生成':`移动端任务结束：${state.status}`,state.status==='PASSED'?'success':state.status==='CANCELLED'?'warning':'error')
    }).catch(error=>toast(error.message,'warning'))
  }catch(error){toast(error.message,'error')}
}

async function submitCurrentPackageBackgroundTask(){
  const pkg=currentRequirementPackage(),packageId=requirementPackageId(pkg);
  if(!current||!packageId)return toast('请先选择可执行需求包','warning');
  if(window.platformHealth?.external_mutations_allowed!==true)return toast('平台当前是只读模式，请重启后再运行真实测试服流程','warning');
  try{
    const task=await window.QualityHub.services.tasks.submit('requirement_pipeline',{project_id:current,package_id:packageId,options:{run_newman:true,run_pytest:true,allow_mutations:true,execution_mode:'real_test'}});
    toast(`后台任务已提交：${task.task_id}`,'success');
    data.background_tasks=await api('/api/tasks?limit=20');
    render();
    window.QualityHub.services.tasks.wait(task.task_id,{onProgress:async state=>{if(['PASSED','FAILED','CANCELLED','INTERRUPTED'].includes(state.status)){data.background_tasks=await api('/api/tasks?limit=20');render();toast(`后台任务${state.status==='PASSED'?'完成':'结束'}：${state.status}`,state.status==='PASSED'?'success':'error')}}}).catch(error=>toast(error.message,'warning'))
  }catch(error){toast(error.message,'error')}
}

const PERFORMANCE_PROFILE_OPTIONS=[
  ['smoke','冒烟验证'],
  ['baseline','基准测试'],
  ['load','负载测试'],
  ['concurrency','并发测试'],
  ['spike','突增测试'],
  ['stress','压力测试'],
  ['soak','稳定性测试']
];

function hydratePerformanceProfileSelect(selector){
  let select=$(selector);if(!select)return;
  let selected=select.value||'smoke';selected=selected==='stability'?'soak':selected;
  select.innerHTML=PERFORMANCE_PROFILE_OPTIONS.map(([value,label])=>`<option value="${value}" ${value===selected?'selected':''}>${label}</option>`).join('');
  if(selector==='#toolPerfProfile')select.onchange=applyPerformanceProfile
}

const showExecutionProfileModalBeforePerformanceProfiles=showExecutionProfileModal;
showExecutionProfileModal=function(){
  showExecutionProfileModalBeforePerformanceProfiles();
  hydratePerformanceProfileSelect('#execPerfProfile')
};

const renderBeforePerformanceProfiles=render;
render=function(){
  renderBeforePerformanceProfiles();
  hydratePerformanceProfileSelect('#toolPerfProfile')
};

