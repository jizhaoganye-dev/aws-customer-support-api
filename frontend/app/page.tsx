'use client'

import { useState } from 'react'
import Link from 'next/link'

// ── Architecture Diagram (SVG) ──────────────────────────────────────────────
function ArchitectureDiagram() {
  return (
    <div className="w-full overflow-x-auto py-4">
      <svg viewBox="0 0 900 520" className="w-full max-w-4xl mx-auto" xmlns="http://www.w3.org/2000/svg">
        {/* Background */}
        <rect x="0" y="0" width="900" height="520" rx="16" fill="#0f172a" stroke="#334155" strokeWidth="1"/>

        {/* API Gateway */}
        <rect x="300" y="20" width="300" height="60" rx="12" fill="#1e293b" stroke="#f59e0b" strokeWidth="2"/>
        <text x="450" y="48" textAnchor="middle" fill="#f59e0b" fontSize="14" fontWeight="bold">Amazon API Gateway</text>
        <text x="450" y="66" textAnchor="middle" fill="#94a3b8" fontSize="10">REST API + CORS + Rate Limiting</text>

        {/* Lambda Functions */}
        <rect x="60" y="130" width="220" height="80" rx="12" fill="#1e293b" stroke="#f97316" strokeWidth="2"/>
        <text x="170" y="158" textAnchor="middle" fill="#f97316" fontSize="13" fontWeight="bold">Lambda: Chat</text>
        <text x="170" y="176" textAnchor="middle" fill="#94a3b8" fontSize="10">AI Response + Handoff</text>
        <text x="170" y="192" textAnchor="middle" fill="#64748b" fontSize="9">POST /api/chat</text>

        <rect x="340" y="130" width="220" height="80" rx="12" fill="#1e293b" stroke="#f97316" strokeWidth="2"/>
        <text x="450" y="158" textAnchor="middle" fill="#f97316" fontSize="13" fontWeight="bold">Lambda: Analyze</text>
        <text x="450" y="176" textAnchor="middle" fill="#94a3b8" fontSize="10">Harassment + Sentiment</text>
        <text x="450" y="192" textAnchor="middle" fill="#64748b" fontSize="9">POST /api/analyze</text>

        <rect x="620" y="130" width="220" height="80" rx="12" fill="#1e293b" stroke="#f97316" strokeWidth="2"/>
        <text x="730" y="158" textAnchor="middle" fill="#f97316" fontSize="13" fontWeight="bold">Lambda: Health</text>
        <text x="730" y="176" textAnchor="middle" fill="#94a3b8" fontSize="10">System Status</text>
        <text x="730" y="192" textAnchor="middle" fill="#64748b" fontSize="9">GET /api/health</text>

        {/* Lines from API GW to Lambdas */}
        <line x1="380" y1="80" x2="170" y2="130" stroke="#f59e0b" strokeWidth="1.5" className="arch-line"/>
        <line x1="450" y1="80" x2="450" y2="130" stroke="#f59e0b" strokeWidth="1.5" className="arch-line"/>
        <line x1="520" y1="80" x2="730" y2="130" stroke="#f59e0b" strokeWidth="1.5" className="arch-line"/>

        {/* Lambda Layer */}
        <rect x="140" y="250" width="620" height="70" rx="12" fill="#1e293b" stroke="#a78bfa" strokeWidth="2" strokeDasharray="6"/>
        <text x="450" y="278" textAnchor="middle" fill="#a78bfa" fontSize="13" fontWeight="bold">Lambda Layer (Shared)</text>
        <text x="450" y="298" textAnchor="middle" fill="#94a3b8" fontSize="10">DB Pool | Harassment Detection | Sentiment Analysis | Handoff Builder</text>

        {/* Lines from Lambdas to Layer */}
        <line x1="170" y1="210" x2="300" y2="250" stroke="#a78bfa" strokeWidth="1" strokeDasharray="4"/>
        <line x1="450" y1="210" x2="450" y2="250" stroke="#a78bfa" strokeWidth="1" strokeDasharray="4"/>
        <line x1="730" y1="210" x2="600" y2="250" stroke="#a78bfa" strokeWidth="1" strokeDasharray="4"/>

        {/* VPC Box */}
        <rect x="40" y="350" width="500" height="140" rx="12" fill="#0c1425" stroke="#3b82f6" strokeWidth="1.5"/>
        <text x="60" y="375" fill="#3b82f6" fontSize="11" fontWeight="bold">VPC (10.0.0.0/16)</text>

        {/* Private Subnets */}
        <rect x="60" y="390" width="200" height="80" rx="8" fill="#1e293b" stroke="#22d3ee" strokeWidth="1"/>
        <text x="160" y="415" textAnchor="middle" fill="#22d3ee" fontSize="11" fontWeight="bold">Private Subnets</text>
        <text x="160" y="435" textAnchor="middle" fill="#94a3b8" fontSize="10">Lambda + RDS</text>
        <text x="160" y="452" textAnchor="middle" fill="#64748b" fontSize="9">10.0.1.0/24, 10.0.2.0/24</text>

        {/* RDS */}
        <rect x="290" y="390" width="230" height="80" rx="8" fill="#1e293b" stroke="#3b82f6" strokeWidth="2"/>
        <text x="405" y="415" textAnchor="middle" fill="#3b82f6" fontSize="11" fontWeight="bold">RDS PostgreSQL 16.1</text>
        <text x="405" y="435" textAnchor="middle" fill="#94a3b8" fontSize="10">conversations, messages</text>
        <text x="405" y="452" textAnchor="middle" fill="#94a3b8" fontSize="10">harassment_events, handoffs</text>

        {/* Line from Layer to VPC */}
        <line x1="350" y1="320" x2="300" y2="350" stroke="#3b82f6" strokeWidth="1.5" className="arch-line"/>

        {/* S3 */}
        <rect x="600" y="370" width="250" height="100" rx="12" fill="#1e293b" stroke="#22c55e" strokeWidth="2"/>
        <text x="725" y="400" textAnchor="middle" fill="#22c55e" fontSize="13" fontWeight="bold">Amazon S3</text>
        <text x="725" y="420" textAnchor="middle" fill="#94a3b8" fontSize="10">Static Assets + Logs</text>
        <text x="725" y="440" textAnchor="middle" fill="#64748b" fontSize="9">CORS Enabled</text>

        {/* Claude API (external) */}
        <rect x="700" y="20" width="180" height="60" rx="12" fill="#1e293b" stroke="#ec4899" strokeWidth="1.5"/>
        <text x="790" y="48" textAnchor="middle" fill="#ec4899" fontSize="12" fontWeight="bold">Claude Opus 4.6</text>
        <text x="790" y="64" textAnchor="middle" fill="#94a3b8" fontSize="9">Anthropic API</text>
        <line x1="700" y1="50" x2="600" y2="50" stroke="#ec4899" strokeWidth="1" strokeDasharray="4"/>

        {/* NAT Gateway */}
        <rect x="20" y="20" width="160" height="50" rx="8" fill="#1e293b" stroke="#a3e635" strokeWidth="1"/>
        <text x="100" y="42" textAnchor="middle" fill="#a3e635" fontSize="11" fontWeight="bold">NAT Gateway</text>
        <text x="100" y="58" textAnchor="middle" fill="#64748b" fontSize="9">Public Subnet</text>
      </svg>
    </div>
  )
}

// ── Tech Stack Badge ─────────────────────────────────────────────────────────
function Badge({ label, color }: { label: string; color: string }) {
  return (
    <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${color}`}>
      {label}
    </span>
  )
}

// ── API Endpoint Card ────────────────────────────────────────────────────────
function EndpointCard({ method, path, desc, example }: { method: string; path: string; desc: string; example: string }) {
  const [open, setOpen] = useState(false)
  const methodColor = method === 'POST' ? 'bg-blue-600' : 'bg-green-600'
  return (
    <div className="card-glass p-5 hover:border-gray-600 transition-colors">
      <div className="flex items-center gap-3 mb-2">
        <span className={`${methodColor} text-white text-xs px-2 py-0.5 rounded font-mono font-bold`}>{method}</span>
        <code className="text-amber-400 font-mono text-sm">{path}</code>
      </div>
      <p className="text-gray-400 text-sm mb-3">{desc}</p>
      <button onClick={() => setOpen(!open)} className="text-xs text-orange-400 hover:text-orange-300 transition-colors">
        {open ? 'Hide' : 'Show'} Response Example
      </button>
      {open && (
        <pre className="mt-3 bg-gray-950 border border-gray-800 rounded-lg p-4 text-xs text-gray-300 overflow-x-auto">
          {example}
        </pre>
      )}
    </div>
  )
}

// ── Skill Item ───────────────────────────────────────────────────────────────
function SkillRow({ skill, impl }: { skill: string; impl: string }) {
  return (
    <tr className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
      <td className="py-3 px-4 font-semibold text-orange-400 text-sm whitespace-nowrap">{skill}</td>
      <td className="py-3 px-4 text-gray-300 text-sm">{impl}</td>
    </tr>
  )
}

// ── DB Table Card ────────────────────────────────────────────────────────────
function DBTable({ name, desc, cols }: { name: string; desc: string; cols: string[] }) {
  return (
    <div className="card-glass p-4">
      <h4 className="text-blue-400 font-mono font-bold text-sm">{name}</h4>
      <p className="text-gray-500 text-xs mt-1 mb-2">{desc}</p>
      <div className="flex flex-wrap gap-1">
        {cols.map(c => (
          <span key={c} className="text-[10px] bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full font-mono">{c}</span>
        ))}
      </div>
    </div>
  )
}

// ── Main Page ────────────────────────────────────────────────────────────────
export default function Home() {
  return (
    <main className="max-w-6xl mx-auto px-4 sm:px-8 py-10">
      {/* Hero */}
      <section className="text-center py-12 animate-fade-in">
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-amber-400 rounded-xl flex items-center justify-center text-white font-black text-lg shadow-lg">
            AWS
          </div>
          <h1 className="text-3xl sm:text-5xl font-black gradient-text">
            Customer Support API
          </h1>
        </div>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto mt-4">
          AWS Lambda + API Gateway + RDS + S3 によるサーバーレス構成<br/>
          AI カスタマーハラスメント検知 &amp; 感情分析プラットフォーム
        </p>
        <div className="flex flex-wrap justify-center gap-2 mt-6">
          <Badge label="AWS SAM" color="bg-orange-900/60 text-orange-300" />
          <Badge label="Lambda (Python 3.12)" color="bg-yellow-900/60 text-yellow-300" />
          <Badge label="API Gateway" color="bg-amber-900/60 text-amber-300" />
          <Badge label="RDS PostgreSQL 16" color="bg-blue-900/60 text-blue-300" />
          <Badge label="S3" color="bg-green-900/60 text-green-300" />
          <Badge label="Claude Opus 4.6" color="bg-pink-900/60 text-pink-300" />
          <Badge label="GitHub Actions" color="bg-purple-900/60 text-purple-300" />
        </div>
        <div className="flex justify-center gap-4 mt-8">
          <a href="https://github.com/jizhaoganye-dev/aws-customer-support-api" target="_blank"
            className="px-6 py-2.5 bg-gray-800 hover:bg-gray-700 border border-gray-600 rounded-xl text-sm font-semibold transition-colors">
            GitHub Repository
          </a>
          <Link href="/demo"
            className="px-6 py-2.5 bg-gradient-to-r from-orange-600 to-amber-500 hover:from-orange-500 hover:to-amber-400 rounded-xl text-sm font-bold text-white transition-all shadow-lg">
            Live Demo
          </Link>
        </div>
      </section>

      {/* Architecture */}
      <section className="mt-16 animate-slide-up">
        <h2 className="text-2xl font-bold text-center mb-2">System Architecture</h2>
        <p className="text-center text-gray-500 text-sm mb-6">AWS SAM (CloudFormation) で全リソースをIaC管理</p>
        <div className="card-glass p-6 glow-orange">
          <ArchitectureDiagram />
        </div>
      </section>

      {/* API Endpoints */}
      <section className="mt-16">
        <h2 className="text-2xl font-bold text-center mb-8">API Endpoints</h2>
        <div className="grid gap-4 md:grid-cols-3">
          <EndpointCard
            method="POST" path="/api/chat"
            desc="AI チャット応答 + カスハラ検知 + 感情分析 + 引き継ぎ判定"
            example={`{
  "conversation_id": "uuid",
  "response": "ご注文の配送状況を確認いたします...",
  "sentiment": {
    "sentiment": "negative",
    "confidence": 0.7,
    "trigger_alert": false
  },
  "harassment": {
    "is_harassment": false,
    "severity": "none"
  },
  "needs_handoff": false
}`}
          />
          <EndpointCard
            method="POST" path="/api/analyze"
            desc="独立分析エンドポイント（リアルタイムダッシュボード監視用）"
            example={`{
  "harassment": {
    "is_harassment": true,
    "severity": "high"
  },
  "sentiment": {
    "sentiment": "anger",
    "trigger_alert": true
  },
  "combined_risk": "critical",
  "alert": {
    "type": "harassment_detected",
    "severity": "high"
  }
}`}
          />
          <EndpointCard
            method="GET" path="/api/health"
            desc="システムヘルスチェック（DB + AI API + ランタイム情報）"
            example={`{
  "status": "healthy",
  "services": {
    "database": { "status": "healthy" },
    "ai_api": { "status": "healthy", "provider": "anthropic" }
  },
  "runtime": {
    "function_name": "chat",
    "memory_limit_mb": 256,
    "environment": "production"
  }
}`}
          />
        </div>
      </section>

      {/* AWS Skills Matrix */}
      <section className="mt-16">
        <h2 className="text-2xl font-bold text-center mb-2">Required AWS Skills</h2>
        <p className="text-center text-gray-500 text-sm mb-6">エイジレス案件の必須要件との対応表</p>
        <div className="card-glass overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-800/50">
                <th className="py-3 px-4 text-left text-xs text-gray-400 font-semibold">Required Skill</th>
                <th className="py-3 px-4 text-left text-xs text-gray-400 font-semibold">Implementation</th>
              </tr>
            </thead>
            <tbody>
              <SkillRow skill="AWS SAM / CloudFormation" impl="template.yaml — VPC, Subnets, NAT GW, RDS, Lambda, API GW, S3 を1ファイルでIaC管理" />
              <SkillRow skill="AWS Lambda" impl="Python 3.12 フレームワーク不使用の純粋Lambda handler × 3本 (chat, analyze, health)" />
              <SkillRow skill="API Gateway" impl="REST API + CORS + Throttling (100 req/s, burst 50) + Stage管理" />
              <SkillRow skill="Amazon RDS" impl="PostgreSQL 16.1 — Private Subnet配置、Security Group制限、自動バックアップ" />
              <SkillRow skill="Amazon S3" impl="静的アセットバケット + CORS設定 + ログ保存" />
              <SkillRow skill="IAM" impl="最小権限ポリシー（VPC, S3, RDS, CloudWatch Logs, SSM）" />
              <SkillRow skill="VPC Networking" impl="Public/Private Subnets, NAT Gateway, Route Tables, Security Groups" />
              <SkillRow skill="GitHub CI/CD" impl="GitHub Actions: pytest → SAM build → SAM deploy (OIDC認証)" />
              <SkillRow skill="Python (Lambda)" impl="接続プール, カスハラ検知, 感情分析, 引き継ぎ構築 — 全てフレームワーク不使用" />
              <SkillRow skill="Claude Code / Cursor" impl="プロジェクト全体がAI駆動開発 (Cursor + Claude Opus 4.6)" />
            </tbody>
          </table>
        </div>
      </section>

      {/* Database Schema */}
      <section className="mt-16">
        <h2 className="text-2xl font-bold text-center mb-2">Database Schema</h2>
        <p className="text-center text-gray-500 text-sm mb-6">PostgreSQL 16.1 — 5テーブル + マテリアライズドビュー</p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <DBTable name="conversations" desc="会話セッション管理" cols={['id (UUID)', 'customer_name', 'status', 'priority', 'tags (JSONB)']} />
          <DBTable name="messages" desc="全メッセージ（分析結果付き）" cols={['id (UUID)', 'conversation_id (FK)', 'role', 'content', 'sentiment', 'harassment_severity']} />
          <DBTable name="harassment_events" desc="カスハラ検知ログ" cols={['id (UUID)', 'severity', 'categories (JSONB)', 'matched_patterns', 'action_taken', 'resolved']} />
          <DBTable name="analysis_logs" desc="リアルタイム分析ログ" cols={['id (UUID)', 'combined_risk', 'sentiment', 'ai_enhanced', 'processing_time_ms']} />
          <DBTable name="handoffs" desc="AI→人間引き継ぎレコード" cols={['id (UUID)', 'priority', 'summary', 'detected_issues (JSONB)', 'order_numbers', 'status']} />
          <DBTable name="daily_metrics" desc="日次KPI集計 (MView)" cols={['metric_date', 'total_messages', 'anger_count', 'harassment_count', 'csat_score']} />
        </div>
      </section>

      {/* Test Results */}
      <section className="mt-16">
        <h2 className="text-2xl font-bold text-center mb-6">Test Suite</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="card-glass p-6 text-center glow-green">
            <div className="text-4xl font-black text-green-400">28</div>
            <div className="text-gray-400 text-sm mt-1">Harassment Detection</div>
            <div className="text-green-500 text-xs mt-2 font-mono">ALL PASSED</div>
          </div>
          <div className="card-glass p-6 text-center glow-green">
            <div className="text-4xl font-black text-green-400">18</div>
            <div className="text-gray-400 text-sm mt-1">Sentiment Analysis</div>
            <div className="text-green-500 text-xs mt-2 font-mono">ALL PASSED</div>
          </div>
          <div className="card-glass p-6 text-center glow-green">
            <div className="text-4xl font-black text-green-400">12</div>
            <div className="text-gray-400 text-sm mt-1">Handoff Context</div>
            <div className="text-green-500 text-xs mt-2 font-mono">ALL PASSED</div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-20 text-center text-gray-600 text-sm pb-8">
        <p>Built with Cursor + Claude Opus 4.6 / Gemini 3</p>
        <p className="mt-1">AWS Serverless Architecture | 2026</p>
      </footer>
    </main>
  )
}
