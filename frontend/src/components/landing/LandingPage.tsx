import React from 'react'
import { Link } from 'react-router-dom'
import { Satellite, Map, BarChart2, Upload, Shield, Zap } from 'lucide-react'

const WHATSAPP_NUMBER = '+5493513273358';

export function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Top Navigation */}
      <nav className="absolute top-0 left-0 w-full flex justify-between items-center px-6 py-4 z-30">
        <div className="text-white text-lg font-semibold">
          <Link to="/" className="hover:text-blue-300 transition-colors">
            Altara Geospatial AI
          </Link>
        </div>
        <div>
          <Link
            to="/login"
            className="rounded-lg px-4 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 transition-colors duration-200"
          >
            Login
          </Link>
          <span className="mx-2"></span> {/* Add a space between the buttons */}
          <Link
            to="/signup"
            className="rounded-lg px-4 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 transition-colors duration-200"
          >
            Sign Up
          </Link>
        </div>
      </nav>
      {/* Hero Section - Now full viewport height */}
      <div className="relative h-screen">
        {/* Background Image */}
        <div 
          className="absolute inset-0 z-0"
          style={{
            backgroundImage: 'url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop")',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            filter: 'brightness(0.7)',
          }}
        />
        {/* Gradient Overlay */}
        <div 
          className="absolute inset-0 z-10 bg-gradient-to-b from-blue-900/70 to-blue-900/90"
          style={{ mixBlendMode: 'multiply' }}
        />
        
        <div className="relative z-20 h-full flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8">
          <h1 className="mx-auto max-w-4xl font-display text-5xl font-medium tracking-tight text-white sm:text-7xl text-center">
            Satellite Image
            <span className="relative whitespace-nowrap text-blue-300">
              <span className="relative"> Analysis</span>
            </span>
            {' '}Platform
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg tracking-tight text-blue-100 text-center">
            Advanced satellite imagery analysis for monitoring land-use changes, deforestation, and urban expansion in Córdoba, Argentina.
          </p>
          {/* Main user interactions */}
          {/* Platform launch */}
          <div className="mt-10 flex justify-center gap-x-6">
            <Link
              to="/map"
              className="rounded-lg px-4 py-2.5 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 transition-colors duration-200"
            >
              Launch Platform
            </Link>
            {/* Link to login page */}
            <Link
              to="/login" // Add the route to the login page
              className="rounded-lg px-4 py-2.5 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 transition-colors duration-200"
            >
              Login
            </Link>
            {/* Reference to features section below */}
            <a
              href="#features"
              className="rounded-lg px-4 py-2.5 text-sm font-semibold text-blue-100 ring-1 ring-blue-100/20 hover:bg-white/10 transition-all duration-200"
            >
              Learn More
            </a>
          </div>
          <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
            <a href="#features" className="text-white/80 hover:text-white">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              </svg>
            </a>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div id="features" className="relative">
        {/* Background Image */}
        <div 
          className="absolute inset-0 z-0"
          style={{
            backgroundImage: 'url("https://images.unsplash.com/photo-1501854140801-50d01698950b?q=80&w=2000&auto=format&fit=crop")',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            filter: 'brightness(0.8)',
          }}
        />
        {/* Gradient Overlay */}
        <div 
          className="absolute inset-0 z-10 bg-gradient-to-b from-black/30 to-black/50"
        />
        
        <div className="relative z-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Powerful Features for Environmental Monitoring
            </h2>
            <p className="mt-4 text-lg text-gray-200">
              Our platform provides comprehensive tools for analyzing and tracking environmental changes over time.
            </p>
          </div>

          <div className="mt-20 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <Feature
              icon={Map}
              title="Interactive Map Viewer"
              description="Compare satellite imagery from different time periods with advanced visualization tools and layer controls."
            />
            <Feature
              icon={BarChart2}
              title="Advanced Analytics"
              description="Track changes in vegetation, urban development, and land use with precise measurements and statistics."
            />
            <Feature
              icon={Upload}
              title="Easy Data Upload"
              description="Upload and process your own satellite imagery with our intuitive interface and automated processing pipeline."
            />
            <Feature
              icon={Zap}
              title="Real-time Processing"
              description="Get quick results with our optimized processing engine, perfect for time-sensitive analysis."
            />
            <Feature
              icon={Shield}
              title="Secure & Reliable"
              description="Your data is protected with enterprise-grade security and regular backups."
            />
            <Feature
              icon={Satellite}
              title="Multiple Data Sources"
              description="Support for various satellite imagery sources and formats, ensuring comprehensive analysis."
            />
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-blue-600">
        <div className="max-w-7xl mx-auto py-16 px-4 sm:px-6 lg:px-8 flex flex-col lg:flex-row items-center justify-between">
          <div className="text-center lg:text-left lg:max-w-xl">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Ready to start monitoring?
            </h2>
            <p className="mt-4 text-lg text-blue-100">
              Join researchers, organizations, and government agencies already using our platform.
            </p>
          </div>
          <div className="mt-8 lg:mt-0 flex flex-col sm:flex-row gap-4">
            <Link
              to="/map"
              className="rounded-lg px-6 py-3 text-sm font-semibold text-blue-600 bg-white hover:bg-blue-50 transition-colors duration-200"
            >
              Get Started
            </Link>
            <Link
              to="/docs"
              className="rounded-lg px-6 py-3 text-sm font-semibold text-white ring-1 ring-white/20 hover:bg-white/10 transition-colors duration-200"
            >
              View Documentation
            </Link>
          </div>
        </div>
      </div>

      {/* WhatsApp Button */}
      <a
        href={`https://wa.me/${WHATSAPP_NUMBER}`}
        target="_blank"
        rel="noopener noreferrer"
        className="fixed bottom-6 right-6 bg-[#25D366] hover:bg-[#20BA5C] text-white p-4 rounded-full shadow-lg transition-all duration-200 z-[1000] group"
        title="Contact us on WhatsApp"
      >
        <svg
          className="w-6 h-6"
          fill="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"
          />
        </svg>
        <span className="fixed bottom-6 right-20 bg-white text-gray-800 px-4 py-2 rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 text-sm font-medium">
          Need help?
        </span>
      </a>
    </div>
  )
}

function Feature({ icon: Icon, title, description }: {
  icon: React.FC<{ className?: string }>,
  title: string,
  description: string
}) {
  return (
    <div className="bg-white rounded-xl shadow-lg p-8 hover:shadow-xl transition-shadow duration-300">
      <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-600 mb-6">
        <Icon className="h-6 w-6 text-white" />
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-3">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}