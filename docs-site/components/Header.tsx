'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useState, useEffect } from 'react';

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  async function checkAuth() {
    try {
      const response = await fetch('http://localhost:8000/auth/status', {
        credentials: 'include',
      });
      const data = await response.json();
      if (data.authenticated) {
        setUser(data.user);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    window.location.href = 'http://localhost:8000/auth/logout';
  }

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200">
      <nav className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">D</span>
            </div>
            <span className="text-xl font-bold text-gray-900">Divv</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link href="/api" className="text-gray-600 hover:text-gray-900 transition-colors">
              Documentation
            </Link>
            <Link href="/examples" className="text-gray-600 hover:text-gray-900 transition-colors">
              Examples
            </Link>
            <Link href="/api-reference" className="text-gray-600 hover:text-gray-900 transition-colors">
              API Reference
            </Link>
            <Link href="/pricing" className="text-gray-600 hover:text-gray-900 transition-colors">
              Pricing
            </Link>
            <Link href="/api-keys" className="text-gray-600 hover:text-gray-900 transition-colors">
              API Keys
            </Link>
            <a
              href="http://localhost:8000/health"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-600 hover:text-gray-900 transition-colors"
            >
              Status
            </a>
          </div>

          {/* CTA Button / User Menu */}
          <div className="hidden md:flex items-center space-x-4">
            {loading ? (
              <div className="w-24 h-10 bg-gray-200 rounded-lg animate-pulse"></div>
            ) : user ? (
              <>
                <div className="flex items-center space-x-3">
                  {user.picture_url && (
                    <Image
                      src={user.picture_url}
                      alt={user.name || user.email}
                      width={32}
                      height={32}
                      className="rounded-full border-2 border-blue-600"
                    />
                  )}
                  <span className="text-sm text-gray-700 font-medium">
                    {user.name || user.email}
                  </span>
                </div>
                <a
                  href="http://localhost:8000/dashboard"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-all text-sm"
                >
                  Dashboard
                </a>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-all text-sm"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <a
                  href="http://localhost:8000/login"
                  className="px-6 py-2 text-gray-700 hover:text-gray-900 font-medium transition-all"
                >
                  Login
                </a>
                <Link
                  href="/api"
                  className="px-6 py-2 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-800 transition-all"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <svg
              className="w-6 h-6 text-gray-600"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              {mobileMenuOpen ? (
                <path d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden mt-4 pb-4 border-t border-gray-200 pt-4">
            <div className="flex flex-col space-y-4">
              <Link
                href="/api"
                className="text-gray-600 hover:text-gray-900 transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Documentation
              </Link>
              <Link
                href="/examples"
                className="text-gray-600 hover:text-gray-900 transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Examples
              </Link>
              <Link
                href="/api-reference"
                className="text-gray-600 hover:text-gray-900 transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                API Reference
              </Link>
              <Link
                href="/pricing"
                className="text-gray-600 hover:text-gray-900 transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Pricing
              </Link>
              <Link
                href="/api-keys"
                className="text-gray-600 hover:text-gray-900 transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                API Keys
              </Link>
              <a
                href="http://localhost:8000/health"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                Status
              </a>
              {user ? (
                <>
                  <div className="flex items-center space-x-3 py-2">
                    {user.picture_url && (
                      <Image
                        src={user.picture_url}
                        alt={user.name || user.email}
                        width={32}
                        height={32}
                        className="rounded-full border-2 border-blue-600"
                      />
                    )}
                    <span className="text-sm text-gray-700 font-medium">
                      {user.name || user.email}
                    </span>
                  </div>
                  <a
                    href="http://localhost:8000/dashboard"
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-all text-center"
                  >
                    Dashboard
                  </a>
                  <button
                    onClick={handleLogout}
                    className="px-6 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-all text-center w-full"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <a
                    href="http://localhost:8000/login"
                    className="px-6 py-2 text-gray-700 hover:text-gray-900 font-medium transition-all text-center"
                  >
                    Login
                  </a>
                  <Link
                    href="/api"
                    className="px-6 py-2 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-800 transition-all text-center"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Get Started
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </nav>
    </header>
  );
}
