import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'HiringAI — Find your next opportunity with AI',
  description: 'AI-powered job matching, career guidance, and recruitment.',
}

import { AuthProvider } from '@/components/auth/AuthContext'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
