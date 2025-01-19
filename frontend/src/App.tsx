// import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Layout } from './components/layout/Layout'
import { MapViewer } from './components/map/MapViewer'
import { LandingPage } from './components/landing/LandingPage'
import { LoginPage } from './components/login/LoginPage'
import SignupPage from './components/login/SignupPage'

// Create a client
const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route element={<Layout />}>
            <Route path="/map" element={<MapViewer />} />
            {/* Add other routes as we implement them */}
            {/* ETC 18 Jan 2025 adding login and signup pages */}
            
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App