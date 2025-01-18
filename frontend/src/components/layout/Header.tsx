import React from 'react'
import { Link } from 'react-router-dom'
import { Satellite, Menu } from 'lucide-react'
import { cn } from '../../lib/utils'

interface HeaderProps {
  toggleSidebar: () => void
  isSidebarOpen: boolean
}

export function Header({ toggleSidebar, isSidebarOpen }: HeaderProps) {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200">
      <div className="px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={toggleSidebar}
            className="p-2 hover:bg-gray-100 rounded-lg lg:hidden"
            aria-label={isSidebarOpen ? 'Close sidebar' : 'Open sidebar'}
          >
            <Menu className="w-6 h-6" />
          </button>
          <Link to="/" className="flex items-center gap-2">
            <Satellite className="w-8 h-8 text-blue-600" />
            <span className="text-xl font-semibold text-gray-900">SatelliteAI</span>
          </Link>
        </div>
        
        <div className="flex items-center gap-4">
          <nav className="hidden md:flex items-center gap-1">
            <NavLink to="/docs">Documentation</NavLink>
            <NavLink to="/support">Support</NavLink>
          </nav>
          
          <div className="h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center">
            <span className="text-sm font-medium text-gray-600">JD</span>
          </div>
        </div>
      </div>
    </header>
  )
}

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      className={cn(
        "px-3 py-2 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-100",
        "transition-colors duration-150"
      )}
    >
      {children}
    </Link>
  )
}