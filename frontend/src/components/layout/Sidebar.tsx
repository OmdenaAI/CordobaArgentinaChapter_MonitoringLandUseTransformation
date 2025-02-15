import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Map,
  Upload,
  ListTodo,
  FileText,
  Settings,
  X,
  MapPin
} from 'lucide-react'
import { cn } from '../../lib/utils'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed top-0 left-0 z-50 h-full w-64 bg-white border-r border-gray-200",
          "transform transition-transform duration-200 ease-in-out lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200 lg:hidden">
          <span className="text-lg font-semibold text-gray-900">Menu</span>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg"
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="p-4 space-y-1">
          <NavItem to="/dashboard" icon={LayoutDashboard}>Dashboard</NavItem>
          <NavItem to="/places" icon={MapPin}>My Places</NavItem>
          <NavItem to="/reports" icon={FileText}>Reports</NavItem>
          <NavItem to="/map-viewer" icon={Map}>Map Viewer</NavItem>
          <NavItem to="/upload" icon={Upload}>Upload Data</NavItem>
          <NavItem to="/queue" icon={ListTodo}>Processing Queue</NavItem>
          <NavItem to="/settings" icon={Settings}>Settings</NavItem>
        </nav>
      </aside>
    </>
  )
}

interface NavItemProps {
  to: string
  icon: React.FC<{ className?: string }>
  children: React.ReactNode
}

function NavItem({ to, icon: Icon, children }: NavItemProps) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium",
          "transition-colors duration-150",
          isActive
            ? "bg-blue-50 text-blue-700"
            : "text-gray-700 hover:bg-gray-100"
        )
      }
    >
      <Icon className="w-5 h-5" />
      {children}
    </NavLink>
  )
}