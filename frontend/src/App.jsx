import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import SignalGrid from './pages/SignalGrid'
import ForecastChart from './pages/ForecastChart'
import FarmerManagement from './pages/FarmerManagement'
import SMSSimulator from './pages/SMSSimulator'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-dark-bg">
        {/* Navbar */}
        <Navbar />
        
        {/* Main Content */}
        <main className="container mx-auto px-4 py-6">
          <Routes>
            <Route path="/" element={<Navigate to="/signals" replace />} />
            <Route path="/signals" element={<SignalGrid />} />
            <Route path="/forecast" element={<ForecastChart />} />
            <Route path="/farmers" element={<FarmerManagement />} />
            <Route path="/sms" element={<SMSSimulator />} />
          </Routes>
        </main>
        
        {/* Footer */}
        <footer className="border-t border-dark-border mt-12 py-6">
          <div className="container mx-auto px-4 text-center text-gray-400 text-sm">
            <p>FarmPulse | Predictive Crop Price Intelligence for Karnataka Farmers</p>
            <p className="mt-1">© 2025 FarmPulse. All rights reserved.</p>
          </div>
        </footer>
      </div>
    </Router>
  )
}

export default App
