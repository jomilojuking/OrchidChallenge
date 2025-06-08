import './globals.css'

export const metadata = {
  title: 'Orchid Challenge',
  description: 'Clone any website with AI',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-white text-neutral-900 antialiased">
        <div className="min-h-screen flex flex-col items-center justify-center px-6 py-10 bg-gradient-to-br from-white to-neutral-100 font-outfit">
          <div className="w-full max-w-3xl bg-white shadow-lg rounded-3xl p-10 transition-all">
            <header className="mb-6 text-center rounded-xl">
              <h1 className="text-4xl font-semibold tracking-tight">Orchid Challenge</h1>
              <p className="text-neutral-500 mt-2">Clone any website with the help of AI</p>
            </header>

            <main className="rounded-xl">{children}</main>

            <footer className="mt-10 text-center text-sm text-neutral-400 rounded-lg">
              &copy; {new Date().getFullYear()} Website Cloner. All rights reserved.
            </footer>
          </div>
        </div>
      </body>
    </html>
  )
}
