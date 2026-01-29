import { Link, useLocation } from 'react-router-dom'
import { Menu, X, FileText, MessageSquare, Pill, Activity, Home } from 'lucide-react'
import { useState } from 'react'

export default function Layout({ children }) {
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navItems = [
    { path: '/', label: 'Home', icon: Home },
    { path: '/lab-analyzer', label: 'Lab Analyzer', icon: FileText },
    { path: '/interview', label: 'Patient Interview', icon: MessageSquare },
    { path: '/triage', label: 'Triage Assessment', icon: Activity },
    { path: '/medication-interaction', label: 'Medication Interaction', icon: Pill },
  ]

  // For home page, show minimal layout
  if (location.pathname === '/') {
    return (
      <div className="h-screen bg-white flex flex-col overflow-hidden">
        {/* Minimal Header with Capsule Navbar */}
        <nav className="flex justify-center items-center px-6 py-4 flex-shrink-0">
          <div className="flex items-center gap-2 bg-white border border-[#e2e8f0] rounded-full px-2 py-1.5 shadow-sm">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2 text-sm px-4 py-2 rounded-full transition-all duration-200 font-medium ${
                    isActive
                      ? 'bg-[#4285f4] text-white shadow-sm'
                      : 'text-[#4a5568] hover:text-[#1a1a1a] hover:bg-[#f7fafc]'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </div>
        </nav>
        <main className="flex-1 overflow-hidden">{children}</main>
      </div>
    )
  }

  // For other pages, show full layout
  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b border-[#e2e8f0] bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity cursor-pointer">
              <img src="/logo.svg" alt="MedAI Logo" className="w-8 h-8" />
              <span className="text-xl font-semibold text-[#1a1a1a]">MedAI</span>
            </Link>
            <div className="flex items-center gap-2">
              <div className="hidden md:flex items-center gap-1 bg-white border border-[#e2e8f0] rounded-full px-2 py-1 shadow-sm">
                {navItems.map((item) => {
                  const Icon = item.icon
                  const isActive = location.pathname === item.path
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
                        isActive
                          ? 'bg-[#4285f4] text-white shadow-sm'
                          : 'text-[#4a5568] hover:bg-[#f7fafc] hover:text-[#1a1a1a]'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      <span>{item.label}</span>
                    </Link>
                  )
                })}
              </div>
              <button
                className="md:hidden p-2 rounded-full hover:bg-[#f1f3f4] transition-colors"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? (
                  <X className="w-5 h-5 text-[#4a5568]" />
                ) : (
                  <Menu className="w-5 h-5 text-[#5f6368]" />
                )}
              </button>
            </div>
          </div>
        </div>
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-[#e2e8f0] bg-white">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center px-4 py-3 transition-colors ${
                    isActive
                      ? 'bg-[#e8f0fe] text-[#4285f4] font-medium'
                      : 'text-[#4a5568] hover:bg-[#f7fafc]'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-3" />
                  {item.label}
                </Link>
              )
            })}
          </div>
        )}
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  )
}
