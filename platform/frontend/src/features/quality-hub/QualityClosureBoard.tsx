import { Link } from "react-router-dom";

type ClosureStep = {
  key: string;
  title: string;
  ready: boolean;
  summary: string;
  route: string;
};

type QualityClosureBoardProps = {
  steps: ClosureStep[];
};

export function QualityClosureBoard({ steps }: QualityClosureBoardProps) {
  const maturity = Math.round((steps.filter((step) => step.ready).length / steps.length) * 100);

  return (
    <section className="quality-closure-board">
      <header>
        <span>AI QUALITY HUB</span>
        <h1>AI 自动质量中枢</h1>
        <p>
          AI 负责编排测试设计和质量归纳，Newman、pytest、JMeter、MySQL、Redis 等工具负责执行和取证。
        </p>
      </header>

      <div className="maturity">
        <strong>{maturity}%</strong>
        <span>闭环完整度</span>
      </div>

      <div className="closure-steps">
        {steps.map((step) => (
          <Link className={step.ready ? "step ready" : "step pending"} key={step.key} to={step.route}>
            <small>{step.ready ? "已就绪" : "待补齐"}</small>
            <b>{step.title}</b>
            <span>{step.summary}</span>
          </Link>
        ))}
      </div>
    </section>
  );
}
