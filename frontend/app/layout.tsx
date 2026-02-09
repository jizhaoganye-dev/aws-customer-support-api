import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AWS Serverless Customer Support API — Architecture Showcase',
  description: 'Lambda + API Gateway + RDS + S3 — AI-powered harassment detection & sentiment analysis',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja" suppressHydrationWarning>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  )
}
