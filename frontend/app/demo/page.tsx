'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'

// ── Local implementations (mirrors Lambda layer logic) ───────────────────────

type Severity = 'critical' | 'high' | 'medium' | 'low' | 'none'
type SentimentType = 'positive' | 'neutral' | 'negative' | 'anger'

interface HarassmentResult {
  is_harassment: boolean
  severity: Severity
  confidence: number
  categories: string[]
  recommendation: string
}

interface SentimentResult {
  sentiment: SentimentType
  confidence: number
  trigger_alert: boolean
  scores: Record<string, number>
}

interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  harassment?: HarassmentResult
  sentiment?: SentimentResult
  timestamp: string
}

const CRITICAL_PATTERNS: [RegExp, string][] = [
  [/殺す|ころす|コロス/, 'death_threat'],
  [/死ね|しね|シネ/, 'death_wish'],
  [/爆破|放火|刺す/, 'violence_threat'],
  [/訴え(る|てやる)|裁判/, 'legal_threat'],
]

const HIGH_PATTERNS: [RegExp, string][] = [
  [/バカ|ばか|馬鹿/, 'insult_baka'],
  [/アホ|あほ|阿呆/, 'insult_aho'],
  [/カス|かす|クズ|くず/, 'insult_kasu'],
  [/ゴミ|ごみ/, 'insult_gomi'],
  [/ふざけるな|ふざけんな|ナメてる|舐めてる/, 'contempt'],
  [/能無し|無能|役立たず|使えない/, 'incompetence'],
  [/クソ|くそ|糞/, 'insult_kuso'],
  [/ボケ|ぼけ/, 'insult_boke'],
]

const MEDIUM_PATTERNS: [RegExp, string][] = [
  [/今すぐ|すぐに|直ちに/, 'urgency'],
  [/責任.*取れ|責任者.*出せ/, 'escalation'],
  [/金.*返せ|弁償しろ/, 'compensation'],
  [/SNS.*晒す|Twitter.*晒す|拡散/, 'social_threat'],
]

function detectHarassment(text: string): HarassmentResult {
  if (!text.trim()) return { is_harassment: false, severity: 'none', confidence: 1, categories: [], recommendation: '' }
  const categories: string[] = []
  let maxSeverity: Severity = 'none'
  const severityOrder: Severity[] = ['none', 'low', 'medium', 'high', 'critical']
  for (const [pattern, cat] of CRITICAL_PATTERNS) {
    if (pattern.test(text)) { categories.push(cat); if (severityOrder.indexOf('critical') > severityOrder.indexOf(maxSeverity)) maxSeverity = 'critical' }
  }
  for (const [pattern, cat] of HIGH_PATTERNS) {
    if (pattern.test(text)) { categories.push(cat); if (severityOrder.indexOf('high') > severityOrder.indexOf(maxSeverity)) maxSeverity = 'high' }
  }
  for (const [pattern, cat] of MEDIUM_PATTERNS) {
    if (pattern.test(text)) { categories.push(cat); if (severityOrder.indexOf('medium') > severityOrder.indexOf(maxSeverity)) maxSeverity = 'medium' }
  }
  const recommendations: Record<Severity, string> = {
    critical: '即座に上席者へエスカレーション。通話録音を保存し、法務部門に報告。',
    high: '冷静に対応し、上席者への引き継ぎを準備。',
    medium: '落ち着いたトーンで対応を継続。事実ベースで回答。',
    low: '通常対応を継続。お客様の不満に寄り添う。',
    none: '通常対応を継続。',
  }
  return {
    is_harassment: ['critical', 'high', 'medium'].includes(maxSeverity),
    severity: maxSeverity,
    confidence: Math.min(0.95, 0.6 + categories.length * 0.1),
    categories,
    recommendation: recommendations[maxSeverity],
  }
}

const POS_KW = ['ありがとう','助かり','感謝','嬉しい','素晴らしい','最高','完璧','良い','丁寧','親切','迅速','満足','解決']
const NEG_KW = ['不満','不便','残念','がっかり','困る','困って','不安','面倒','嫌','ダメ','問題','エラー','バグ','遅い','苦情']
const ANG_KW = ['怒り','激怒','ふざけるな','許さない','ありえない','最悪','最低','酷い','ひどい','クソ','バカ','死ね','殺す','腹が立つ','むかつく','ムカつく','イライラ','ナメてる','ゴミ','カス']

function analyzeSentiment(text: string): SentimentResult {
  if (!text.trim()) return { sentiment: 'neutral', confidence: 1, trigger_alert: false, scores: { positive: 0, neutral: 1, negative: 0, anger: 0 } }
  const posC = POS_KW.filter(k => text.includes(k)).length
  const negC = NEG_KW.filter(k => text.includes(k)).length
  const angC = ANG_KW.filter(k => text.includes(k)).length
  let sentiment: SentimentType = 'neutral'
  let confidence = 0.8
  if (angC >= 1) { sentiment = 'anger'; confidence = Math.min(0.95, 0.6 + angC * 0.1) }
  else if (negC > posC) { sentiment = 'negative'; confidence = Math.min(0.9, 0.5 + negC * 0.1) }
  else if (posC > 0) { sentiment = 'positive'; confidence = Math.min(0.9, 0.5 + posC * 0.1) }
  const total = posC + negC + angC + 1
  return {
    sentiment, confidence, trigger_alert: sentiment === 'anger',
    scores: { positive: +(posC / total).toFixed(3), neutral: +(1 / total).toFixed(3), negative: +(negC / total).toFixed(3), anger: +(angC / total).toFixed(3) },
  }
}

const RESPONSE_RULES: [string[], string][] = [
  [['届かない', '配送', '配達', '発送'], 'ご注文の配送状況を確認いたします。注文番号をお教えいただけますか？通常、出荷後2〜5営業日でのお届けとなります。'],
  [['返品', '返金', 'キャンセル'], '返品・返金のご希望を承ります。ご注文日から30日以内の未使用品に限り全額返金いたします。注文番号をお知らせください。'],
  [['壊れ', '不良', '破損', '故障'], '商品の不具合について、大変申し訳ございません。不具合の状態がわかるお写真をお送りいただけますか？確認後、交換または返金にて対応いたします。'],
  [['ログイン', 'パスワード', 'アカウント'], 'パスワードリセットはログイン画面の「パスワードを忘れた方」から行えます。それでも解決しない場合は、ご登録のメールアドレスをお知らせください。'],
  [['請求', '課金', '料金', '支払い'], '請求内容の詳細を確認いたしますので、対象の注文番号または請求日をお知らせください。'],
  [['こんにちは', 'はじめまして', 'よろしく'], 'こんにちは！カスタマーサポートへようこそ。お問い合わせ内容をお聞かせください。'],
  [['ありがとう', '感謝', '助かり'], 'お役に立てて嬉しいです！他にお困りのことがあればいつでもお声がけください。'],
]

function generateResponse(msg: string, harassment: HarassmentResult): string {
  if (harassment.is_harassment && ['critical', 'high'].includes(harassment.severity)) {
    return 'お気持ちは理解いたします。適切にお答えするため、担当者にお繋ぎいたします。少々お待ちください。'
  }
  for (const [keywords, response] of RESPONSE_RULES) {
    if (keywords.some(kw => msg.includes(kw))) return response
  }
  return 'お問い合わせありがとうございます。もう少し詳しくお聞かせいただけますか？具体的な注文番号やサービス名をお知らせいただけるとスムーズにご対応できます。'
}

// ── Severity Badge ───────────────────────────────────────────────────────────
function SeverityBadge({ severity }: { severity: Severity }) {
  const colors: Record<Severity, string> = {
    critical: 'bg-red-600 text-white animate-pulse',
    high: 'bg-red-500/80 text-white',
    medium: 'bg-orange-500/80 text-white',
    low: 'bg-yellow-600/80 text-white',
    none: 'bg-green-700/80 text-white',
  }
  return <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${colors[severity]}`}>{severity.toUpperCase()}</span>
}

function SentimentBadge({ sentiment }: { sentiment: SentimentType }) {
  const colors: Record<SentimentType, string> = {
    positive: 'bg-emerald-700/80 text-emerald-200',
    neutral: 'bg-gray-700/80 text-gray-300',
    negative: 'bg-orange-700/80 text-orange-200',
    anger: 'bg-red-700/80 text-red-200 animate-pulse',
  }
  const icons: Record<SentimentType, string> = { positive: '+', neutral: '=', negative: '-', anger: '!!'}
  return <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${colors[sentiment]}`}>{icons[sentiment]} {sentiment}</span>
}

// ── Main Demo Page ───────────────────────────────────────────────────────────
export default function DemoPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'system', content: 'AWS Lambda カスタマーサポートAPIのライブデモです。メッセージを送信すると、カスハラ検知・感情分析・AI応答がリアルタイムで実行されます。', timestamp: new Date().toISOString() },
  ])
  const [input, setInput] = useState('')
  const [stats, setStats] = useState({ total: 0, harassment: 0, anger: 0, positive: 0 })
  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const handleSend = () => {
    if (!input.trim()) return
    const text = input.trim()
    setInput('')

    const harassment = detectHarassment(text)
    const sentiment = analyzeSentiment(text)
    const userMsg: ChatMessage = { role: 'user', content: text, harassment, sentiment, timestamp: new Date().toISOString() }

    const aiResponse = generateResponse(text, harassment)
    const aiMsg: ChatMessage = { role: 'assistant', content: aiResponse, timestamp: new Date().toISOString() }

    setMessages(prev => [...prev, userMsg, aiMsg])
    setStats(prev => ({
      total: prev.total + 1,
      harassment: prev.harassment + (harassment.is_harassment ? 1 : 0),
      anger: prev.anger + (sentiment.trigger_alert ? 1 : 0),
      positive: prev.positive + (sentiment.sentiment === 'positive' ? 1 : 0),
    }))
  }

  const sampleMessages = [
    '商品が届きません。注文番号 ORD-12345 です。',
    'ふざけるな！3回も問い合わせてるのに解決しない！バカ！',
    'ありがとうございます。とても助かりました！',
    '殺すぞ！責任者出せ！',
    '返品したいのですが手続きを教えてください',
  ]

  return (
    <main className="max-w-6xl mx-auto px-4 sm:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold gradient-text">Live API Demo</h1>
          <p className="text-gray-500 text-sm mt-1">Lambda関数のロジックをブラウザ上で再現</p>
        </div>
        <Link href="/" className="text-sm text-gray-400 hover:text-white border border-gray-700 px-4 py-2 rounded-xl transition-colors">
          Architecture
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Panel */}
        <div className="lg:col-span-2 card-glass flex flex-col" style={{ height: '70vh' }}>
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] ${msg.role === 'user' ? 'bg-blue-600/30 border-blue-700/50' : msg.role === 'system' ? 'bg-gray-800/50 border-gray-700/50' : 'bg-gray-800/70 border-gray-700/50'} border rounded-2xl p-3`}>
                  {msg.role === 'system' && <p className="text-xs text-gray-500 mb-1">SYSTEM</p>}
                  <p className="text-sm text-gray-200">{msg.content}</p>
                  {msg.harassment && msg.sentiment && (
                    <div className="flex flex-wrap gap-1.5 mt-2 pt-2 border-t border-gray-700/50">
                      <SeverityBadge severity={msg.harassment.severity} />
                      <SentimentBadge sentiment={msg.sentiment.sentiment} />
                      {msg.harassment.is_harassment && (
                        <span className="text-[10px] text-red-400 font-mono">ALERT</span>
                      )}
                    </div>
                  )}
                  {msg.harassment && msg.harassment.is_harassment && (
                    <p className="text-[10px] text-orange-400 mt-1.5">{msg.harassment.recommendation}</p>
                  )}
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          {/* Sample Messages */}
          <div className="px-4 py-2 border-t border-gray-800/50">
            <p className="text-[10px] text-gray-600 mb-1">Sample Messages:</p>
            <div className="flex flex-wrap gap-1.5">
              {sampleMessages.map((s, i) => (
                <button key={i} onClick={() => setInput(s)}
                  className="text-[10px] bg-gray-800/50 hover:bg-gray-700 text-gray-400 px-2 py-1 rounded-lg transition-colors truncate max-w-[200px]">
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-800/50">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSend()}
                placeholder="メッセージを入力..."
                className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-orange-500 transition-colors"
              />
              <button onClick={handleSend}
                className="px-5 py-2.5 bg-gradient-to-r from-orange-600 to-amber-500 hover:from-orange-500 hover:to-amber-400 rounded-xl text-sm font-bold text-white transition-all">
                Send
              </button>
            </div>
          </div>
        </div>

        {/* Stats Panel */}
        <div className="space-y-4">
          <div className="card-glass p-5">
            <h3 className="text-sm font-bold text-gray-300 mb-4">Real-time Analytics</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">Total Messages</span>
                <span className="text-lg font-bold text-white">{stats.total}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">Harassment Detected</span>
                <span className={`text-lg font-bold ${stats.harassment > 0 ? 'text-red-400' : 'text-green-400'}`}>{stats.harassment}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">Anger Alerts</span>
                <span className={`text-lg font-bold ${stats.anger > 0 ? 'text-orange-400' : 'text-green-400'}`}>{stats.anger}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">Positive Sentiment</span>
                <span className="text-lg font-bold text-emerald-400">{stats.positive}</span>
              </div>
            </div>
          </div>

          <div className="card-glass p-5">
            <h3 className="text-sm font-bold text-gray-300 mb-3">Lambda Processing Flow</h3>
            <div className="space-y-2 text-xs text-gray-400">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 bg-blue-600/30 rounded-full flex items-center justify-center text-[10px] text-blue-400 font-bold">1</span>
                <span>API Gateway: Parse &amp; validate</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 bg-orange-600/30 rounded-full flex items-center justify-center text-[10px] text-orange-400 font-bold">2</span>
                <span>Lambda Layer: Harassment detection</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 bg-purple-600/30 rounded-full flex items-center justify-center text-[10px] text-purple-400 font-bold">3</span>
                <span>Lambda Layer: Sentiment analysis</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 bg-pink-600/30 rounded-full flex items-center justify-center text-[10px] text-pink-400 font-bold">4</span>
                <span>Claude Opus 4.6 / Rule-based response</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 bg-cyan-600/30 rounded-full flex items-center justify-center text-[10px] text-cyan-400 font-bold">5</span>
                <span>RDS: Persist conversation + events</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 bg-green-600/30 rounded-full flex items-center justify-center text-[10px] text-green-400 font-bold">6</span>
                <span>Handoff check → Return response</span>
              </div>
            </div>
          </div>

          <div className="card-glass p-5">
            <h3 className="text-sm font-bold text-gray-300 mb-3">Severity Matrix</h3>
            <div className="space-y-1.5 text-[11px]">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-red-600 animate-pulse"></span>
                <span className="text-red-400">CRITICAL</span>
                <span className="text-gray-600">— 脅迫、暴力的発言</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-red-500"></span>
                <span className="text-red-400">HIGH</span>
                <span className="text-gray-600">— 直接的な侮辱</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-orange-500"></span>
                <span className="text-orange-400">MEDIUM</span>
                <span className="text-gray-600">— 威圧的な要求</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-yellow-600"></span>
                <span className="text-yellow-400">LOW</span>
                <span className="text-gray-600">— 軽度の不満</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-green-600"></span>
                <span className="text-green-400">NONE</span>
                <span className="text-gray-600">— 通常の問い合わせ</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
