// import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Layout } from './components/layout/Layout'
import { MapViewer } from './components/map/MapViewer'
import { LandingPage } from './components/landing/LandingPage'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Places from './pages/Places'
import Dashboard from './pages/Dashboard'

// Create a client
const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          
          {/* Protected routes - all inside Layout */}
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/places" element={<Places />} />
            <Route path="/reports" element={<div>Reports</div>} />
            <Route path="/map-viewer" element={<MapViewer />} />
            <Route path="/upload" element={<div>Upload Data</div>} />
            <Route path="/queue" element={<div>Processing Queue</div>} />
            <Route path="/settings" element={<div>Settings</div>} />
          </Route>

          {/* Fallback route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App