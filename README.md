# AI Customer Support API — AWS Serverless

[![AWS SAM](https://img.shields.io/badge/AWS_SAM-FF9900?logo=amazonaws&logoColor=white)](https://aws.amazon.com/serverless/sam/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![Lambda](https://img.shields.io/badge/AWS_Lambda-FF9900?logo=awslambda&logoColor=white)](https://aws.amazon.com/lambda/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Claude](https://img.shields.io/badge/Claude_Opus_4.6-Anthropic-191919?logo=anthropic&logoColor=white)](https://anthropic.com)

カスタマーハラスメント対策 + AI チャットボット の **AWS サーバーレス API**。
Lambda + API Gateway + RDS (PostgreSQL) + S3 で構築。Claude Opus 4.6 / Gemini 3 による高度な自然言語処理を実装。

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       API Gateway                           │
│              (REST API + CORS + Throttling)                  │
├──────────┬──────────────┬──────────────┬────────────────────┤
│          │              │              │                    │
│  POST    │    POST      │    GET       │                    │
│ /api/chat│  /api/analyze│  /api/health │                    │
│          │              │              │                    │
├──────────┼──────────────┼──────────────┤                    │
│          │              │              │                    │
│  Lambda  │   Lambda     │   Lambda     │   Lambda Layer     │
│  (chat)  │  (analyze)   │  (health)    │   (common utils)   │
│          │              │              │                    │
│  - AI応答 │  - カスハラ検知│  - DB疎通確認 │  - DB接続プール    │
│  - 会話管理│  - 感情分析   │  - API状態   │  - ハラスメント検知  │
│  - 引き継ぎ│  - リスク判定 │  - ランタイム │  - 感情分析         │
│          │              │              │  - 引き継ぎ構築     │
├──────────┴──────────────┴──────────────┴────────────────────┤
│                                                             │
│                    VPC (10.0.0.0/16)                        │
│  ┌─────────────────────┐  ┌──────────────────────────────┐ │
│  │   Private Subnets    │  │    RDS PostgreSQL 16.1       │ │
│  │   (Lambda + RDS)     │──│    (db.t3.micro)             │ │
│  └─────────────────────┘  │    - conversations            │ │
│  ┌─────────────────────┐  │    - messages                 │ │
│  │   Public Subnet      │  │    - harassment_events        │ │
│  │   (NAT Gateway)      │  │    - analysis_logs            │ │
│  └─────────────────────┘  │    - handoffs                 │ │
│                           │    - daily_metrics (MView)     │ │
│                           └──────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   S3 Bucket (Static Assets / Logs)                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **IaC** | AWS SAM (CloudFormation) | Infrastructure as Code |
| **Compute** | AWS Lambda (Python 3.12) | Serverless functions |
| **API** | Amazon API Gateway | REST API + CORS + Rate limiting |
| **Database** | Amazon RDS (PostgreSQL 16.1) | Persistent data storage |
| **Storage** | Amazon S3 | Static assets & logs |
| **Networking** | VPC + NAT Gateway | Private subnet isolation |
| **AI** | Claude Opus 4.6 (Anthropic API) | NLP / Chat / Analysis |
| **CI/CD** | GitHub Actions + SAM CLI | Automated deployment |

## Project Structure

```
aws-customer-support-api/
├── template.yaml              # SAM template (IaC)
├── samconfig.toml             # SAM CLI deployment config
├── iam-policy.json            # IAM policy document
│
├── functions/
│   ├── chat/
│   │   └── app.py             # Chat Lambda (AI response + handoff)
│   ├── analyze/
│   │   └── app.py             # Analysis Lambda (harassment + sentiment)
│   └── health/
│       └── app.py             # Health check Lambda
│
├── layers/
│   └── common/
│       ├── requirements.txt   # Shared dependencies
│       └── python/
│           ├── db.py                  # RDS connection pool
│           ├── harassment_detector.py # カスハラ検知エンジン
│           ├── sentiment_analyzer.py  # 感情分析エンジン
│           ├── handoff.py             # AI→人間引き継ぎ
│           └── response_helpers.py    # API response utilities
│
├── database/
│   ├── schema.sql             # Full RDS schema + indexes + views
│   └── migrations/
│       └── 001_initial.sql    # Migration tracking
│
├── tests/
│   ├── test_harassment_detector.py  # 28 test cases
│   ├── test_sentiment_analyzer.py   # 18 test cases
│   └── test_handoff.py              # 12 test cases
│
├── .github/
│   └── workflows/
│       └── deploy.yml         # CI/CD pipeline
│
├── .env.example               # Environment template
├── .gitignore
└── README.md
```

## API Endpoints

### POST /api/chat
AI チャット応答 + カスハラ検知 + 感情分析 + 引き継ぎ判定

```json
// Request
{
  "message": "商品が届きません。注文番号 ORD-12345 です。",
  "conversation_id": "uuid-here",
  "customer_name": "山田太郎",
  "history": []
}

// Response
{
  "conversation_id": "uuid",
  "response": "ご注文の配送状況を確認いたします...",
  "sentiment": {
    "sentiment": "negative",
    "confidence": 0.7,
    "scores": { "positive": 0, "neutral": 0.2, "negative": 0.8, "anger": 0 },
    "trigger_alert": false
  },
  "harassment": {
    "is_harassment": false,
    "severity": "none",
    "confidence": 0.9
  },
  "handoff": null,
  "needs_handoff": false
}
```

### POST /api/analyze
独立した分析エンドポイント（ダッシュボードリアルタイム監視用）

```json
// Request
{ "message": "ふざけるな！バカ！", "conversation_id": "uuid" }

// Response
{
  "harassment": { "is_harassment": true, "severity": "high", ... },
  "sentiment": { "sentiment": "anger", "trigger_alert": true, ... },
  "combined_risk": "critical",
  "alert": {
    "type": "harassment_detected",
    "message": "カスハラ検出（high）...",
    "severity": "high"
  }
}
```

### GET /api/health
ヘルスチェック（DB + AI API + ランタイム情報）

## Required AWS Skills Demonstrated

| Skill | Implementation |
|-------|---------------|
| **AWS SAM / CloudFormation** | `template.yaml` — VPC, Subnets, RDS, Lambda, API Gateway, S3 |
| **AWS Lambda** | 3 functions (Python, no framework — pure Lambda handler) |
| **Amazon API Gateway** | REST API with CORS, throttling, stage management |
| **Amazon RDS** | PostgreSQL 16.1, private subnet, security groups |
| **Amazon S3** | Asset bucket with CORS |
| **IAM** | Least-privilege policies for Lambda execution |
| **VPC Networking** | Public/private subnets, NAT Gateway, route tables |
| **GitHub CI/CD** | SAM build → test → deploy pipeline with OIDC |
| **Python (Lambda)** | Framework-free handlers with connection pooling |
| **Claude Code / Cursor** | AI-driven development (this entire project) |

## Local Development

```bash
# 1. Install dependencies
pip install -r layers/common/requirements.txt
pip install pytest

# 2. Run tests
PYTHONPATH=layers/common/python pytest tests/ -v

# 3. Local API (requires Docker + SAM CLI)
sam build --use-container
sam local start-api

# 4. Deploy to AWS
sam deploy --guided
```

## Database Schema

5 tables + 1 materialized view:

- **conversations** — 会話セッション管理（ステータス、優先度、タグ）
- **messages** — 全メッセージ（感情分析・ハラスメント検知結果付き）
- **harassment_events** — カスハラ検知ログ（カテゴリ、対応記録）
- **analysis_logs** — リアルタイム分析ログ（複合リスク判定）
- **handoffs** — AI→人間引き継ぎレコード（コンテキスト、優先度）
- **daily_metrics** — 日次KPI集計（CSAT, ハラスメント件数 etc.）

## Security

- Lambda functions in **private subnets** (no direct internet access)
- RDS accessible **only from Lambda** security group
- API Gateway **rate limiting** (100 req/s, burst 50)
- Secrets via **SSM Parameter Store** (not hardcoded)
- **IAM least-privilege** policies per function

---

**Built with Cursor + Claude Opus 4.6** — AI-driven serverless development
