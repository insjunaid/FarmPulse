import React, { useState, useEffect } from 'react'
import { Users, Plus, Search, Phone, MapPin, Wheat, AlertCircle, CheckCircle, Wifi, WifiOff } from 'lucide-react'
import axios from 'axios'

const DISTRICTS = ['Mysuru', 'Chamarajanagar', 'Bangalore', 'Mangalore', 'Tumkur']
const CROPS = ['Tomato', 'Onion', 'Potato', 'Cabbage', 'Carrot', 'Bean', 'Chilli']
const MANDIS = ['Mysuru', 'Chamarajanagar']

function FarmerManagement() {
  const [farmers, setFarmers] = useState([])
  const [loading, setLoading] = useState(false)
  const [showRegister, setShowRegister] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterDistrict, setFilterDistrict] = useState('')
  const [apiConnected, setApiConnected] = useState(false)
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    phone_number: '',
    district: '',
    primary_crop: 'Tomato',
    preferred_mandi: 'Mysuru',
  })
  const [formError, setFormError] = useState('')
  const [formSuccess, setFormSuccess] = useState('')

  useEffect(() => {
    fetchFarmers()
  }, [])

  const fetchFarmers = async () => {
    setLoading(true)
    try {
      const response = await axios.get('/api/farmers', { timeout: 5000 })
      if (Array.isArray(response.data)) {
        const mapped = response.data.map(f => ({
          id: f.id,
          name: f.name,
          phone: f.phone_number,
          district: f.district,
          primaryCrop: f.primary_crop || 'Tomato',
          preferredMandi: f.preferred_mandi || 'Mysuru',
          isActive: f.is_active !== false,
          signalsSent: 0,
          lastSignal: null,
        }))
        setFarmers(mapped)
        setApiConnected(true)
      }
    } catch (error) {
      console.warn('Farmers API not available:', error.message)
      setApiConnected(false)
      // Keep whatever farmers we have (or empty)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    setFormError('')
    setFormSuccess('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError('')
    setFormSuccess('')
    
    // Validate
    if (!formData.name || !formData.phone_number || !formData.district) {
      setFormError('Please fill all required fields')
      return
    }
    
    // Validate phone
    const phoneRegex = /^\+?[\d\s-]{10,15}$/
    if (!phoneRegex.test(formData.phone_number)) {
      setFormError('Please enter a valid phone number (e.g. +919876543210)')
      return
    }
    
    try {
      // Call real backend API
      const response = await axios.post('/api/register-farmer', formData, { timeout: 10000 })
      
      // Add to local list
      const newFarmer = {
        id: response.data.id || farmers.length + 1,
        name: response.data.name || formData.name,
        phone: response.data.phone_number || formData.phone_number,
        district: response.data.district || formData.district,
        primaryCrop: response.data.primary_crop || formData.primary_crop,
        preferredMandi: response.data.preferred_mandi || formData.preferred_mandi,
        isActive: true,
        signalsSent: 0,
        lastSignal: null,
      }
      setFarmers([newFarmer, ...farmers])
      setApiConnected(true)
      
      setFormSuccess('Farmer registered successfully! ✅')
      setFormData({
        name: '',
        phone_number: '',
        district: '',
        primary_crop: 'Tomato',
        preferred_mandi: 'Mysuru',
      })
      
      setTimeout(() => {
        setShowRegister(false)
        setFormSuccess('')
      }, 2000)
    } catch (error) {
      console.error('Registration error:', error)
      if (error.response?.status === 400) {
        setFormError(error.response.data?.detail || 'Phone number already registered')
      } else if (error.response?.data?.detail) {
        setFormError(error.response.data.detail)
      } else {
        setFormError('Failed to register farmer. Make sure the backend is running.')
      }
    }
  }

  const getSignalBadge = (signal) => {
    if (!signal) return null
    
    if (signal === 'HOLD') {
      return <span className="px-2 py-1 rounded text-xs font-medium bg-signal-green/20 text-signal-green">HOLD</span>
    }
    if (signal === 'WATCH') {
      return <span className="px-2 py-1 rounded text-xs font-medium bg-signal-amber/20 text-signal-amber">WATCH</span>
    }
    if (signal === 'SELL NOW') {
      return <span className="px-2 py-1 rounded text-xs font-medium bg-signal-red/20 text-signal-red">SELL NOW</span>
    }
  }

  const filteredFarmers = farmers.filter(farmer => {
    const matchesSearch = !searchQuery || 
      farmer.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      farmer.phone.includes(searchQuery) ||
      farmer.primaryCrop.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesDistrict = !filterDistrict || farmer.district === filterDistrict
    
    return matchesSearch && matchesDistrict
  })

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center space-x-2">
            <Users className="w-6 h-6 text-accent" />
            <span>Farmer <span className="text-accent">Management</span></span>
          </h1>
          <div className="flex items-center space-x-3 mt-1">
            <p className="text-gray-400">
              Register and manage farmers in your FPO
            </p>
            <div className="flex items-center space-x-1">
              {apiConnected ? (
                <Wifi className="w-3 h-3 text-signal-green" />
              ) : (
                <WifiOff className="w-3 h-3 text-signal-amber" />
              )}
              <span className={`text-xs ${apiConnected ? 'text-signal-green' : 'text-signal-amber'}`}>
                {apiConnected ? 'Live' : 'Offline'}
              </span>
            </div>
          </div>
        </div>
        
        <button
          onClick={() => setShowRegister(!showRegister)}
          className="btn-primary flex items-center space-x-2 mt-4 md:mt-0"
        >
          <Plus className="w-4 h-4" />
          <span>Register Farmer</span>
        </button>
      </div>

      {/* Register Form */}
      {showRegister && (
        <div className="card mb-6 animate-fade-in">
          <h2 className="text-lg font-semibold text-white mb-4">
            Register New Farmer
          </h2>
          
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  Name <span className="text-signal-red">*</span>
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="input w-full"
                  placeholder="Enter farmer's name"
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  Phone Number <span className="text-signal-red">*</span>
                </label>
                <input
                  type="text"
                  name="phone_number"
                  value={formData.phone_number}
                  onChange={handleInputChange}
                  className="input w-full"
                  placeholder="+919876543210"
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  District <span className="text-signal-red">*</span>
                </label>
                <select
                  name="district"
                  value={formData.district}
                  onChange={handleInputChange}
                  className="input w-full"
                >
                  <option value="">Select district</option>
                  {DISTRICTS.map(d => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  Primary Crop
                </label>
                <select
                  name="primary_crop"
                  value={formData.primary_crop}
                  onChange={handleInputChange}
                  className="input w-full"
                >
                  {CROPS.map(crop => (
                    <option key={crop} value={crop}>{crop}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  Preferred Mandi
                </label>
                <select
                  name="preferred_mandi"
                  value={formData.preferred_mandi}
                  onChange={handleInputChange}
                  className="input w-full"
                >
                  {MANDIS.map(mandi => (
                    <option key={mandi} value={mandi}>{mandi}</option>
                  ))}
                </select>
              </div>
            </div>
            
            {formError && (
              <div className="mt-4 p-3 rounded-lg bg-signal-red/20 border border-signal-red flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 text-signal-red" />
                <span className="text-signal-red text-sm">{formError}</span>
              </div>
            )}
            
            {formSuccess && (
              <div className="mt-4 p-3 rounded-lg bg-signal-green/20 border border-signal-green flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-signal-green" />
                <span className="text-signal-green text-sm">{formSuccess}</span>
              </div>
            )}
            
            <div className="flex justify-end space-x-3 mt-4">
              <button
                type="button"
                onClick={() => setShowRegister(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-primary"
              >
                Register
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Filters */}
      <div className="card mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input w-full pl-10"
              placeholder="Search by name, phone, or crop..."
            />
          </div>
          
          <div className="w-full md:w-48">
            <select
              value={filterDistrict}
              onChange={(e) => setFilterDistrict(e.target.value)}
              className="input w-full"
            >
              <option value="">All Districts</option>
              {DISTRICTS.map(d => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="card">
          <p className="text-sm text-gray-400">Total Farmers</p>
          <p className="text-2xl font-bold text-white mt-1">{farmers.length}</p>
        </div>
        
        <div className="card">
          <p className="text-sm text-gray-400">Active Farmers</p>
          <p className="text-2xl font-bold text-accent mt-1">
            {farmers.filter(f => f.isActive).length}
          </p>
        </div>
        
        <div className="card">
          <p className="text-sm text-gray-400">Signals Sent Today</p>
          <p className="text-2xl font-bold text-white mt-1">
            {farmers.reduce((acc, f) => acc + f.signalsSent, 0)}
          </p>
        </div>
        
        <div className="card">
          <p className="text-sm text-gray-400">Districts</p>
          <p className="text-2xl font-bold text-white mt-1">
            {new Set(farmers.map(f => f.district)).size}
          </p>
        </div>
      </div>

      {/* Farmer List */}
      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-border">
                <th className="text-left text-sm font-medium text-gray-400 px-4 py-3">Farmer</th>
                <th className="text-left text-sm font-medium text-gray-400 px-4 py-3">Contact</th>
                <th className="text-left text-sm font-medium text-gray-400 px-4 py-3">District</th>
                <th className="text-left text-sm font-medium text-gray-400 px-4 py-3">Crop</th>
                <th className="text-left text-sm font-medium text-gray-400 px-4 py-3">Mandi</th>
                <th className="text-left text-sm font-medium text-gray-400 px-4 py-3">Status</th>
                <th className="text-left text-sm font-medium text-gray-400 px-4 py-3">Last Signal</th>
              </tr>
            </thead>
            <tbody>
              {filteredFarmers.map(farmer => (
                <tr key={farmer.id} className="border-b border-dark-border hover:bg-dark-border/30">
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center">
                        <span className="text-accent text-sm font-medium">
                          {farmer.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <span className="text-white font-medium">{farmer.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-2 text-gray-400">
                      <Phone className="w-4 h-4" />
                      <span>{farmer.phone}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-2 text-gray-400">
                      <MapPin className="w-4 h-4" />
                      <span>{farmer.district}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-2 text-gray-400">
                      <Wheat className="w-4 h-4" />
                      <span>{farmer.primaryCrop}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {farmer.preferredMandi}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      farmer.isActive 
                        ? 'bg-signal-green/20 text-signal-green' 
                        : 'bg-gray-500/20 text-gray-500'
                    }`}>
                      {farmer.isActive ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {getSignalBadge(farmer.lastSignal)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {filteredFarmers.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="w-12 h-12 text-gray-600 mb-4" />
            <p className="text-gray-400">No farmers found</p>
            <p className="text-gray-500 text-sm mt-1">Register a farmer to get started</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default FarmerManagement
