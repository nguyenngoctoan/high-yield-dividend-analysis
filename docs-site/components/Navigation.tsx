'use client';

import Link from 'next/link';
import { useState } from 'react';
import { ChevronRight, Home } from 'lucide-react';

interface NavSection {
  title: string;
  items: NavItem[];
}

interface NavItem {
  title: string;
  href: string;
}

const navigationSections: NavSection[] = [
  {
    title: 'Quickstart',
    items: [
      { title: 'About the REST API', href: '/api' },
      { title: 'Using the REST API', href: '/api/quickstart' },
      { title: 'Authentication', href: '/api/authentication' },
    ],
  },
  {
    title: 'Stocks',
    items: [
      { title: 'List stocks', href: '/api/stocks' },
      { title: 'Get stock details', href: '/api/stocks' },
    ],
  },
  {
    title: 'Dividends',
    items: [
      { title: 'Get dividend calendar', href: '/api/dividends' },
      { title: 'Get dividend history', href: '/api/dividends' },
      { title: 'Get stock dividend summary', href: '/api/dividends' },
    ],
  },
  {
    title: 'Screeners',
    items: [
      { title: 'High-yield screener', href: '/api/screeners' },
      { title: 'Monthly dividend payers', href: '/api/screeners' },
    ],
  },
  {
    title: 'Analytics',
    items: [
      { title: 'Analyze portfolio', href: '/api/analytics' },
    ],
  },
  {
    title: 'Prices',
    items: [
      { title: 'Get price history', href: '/api/prices' },
      { title: 'Get latest price', href: '/api/prices' },
    ],
  },
];

export default function Navigation({ onEndpointChange }: { onEndpointChange?: (endpoint: string) => void }) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['Stocks', 'Dividends'])
  );

  const toggleSection = (title: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(title)) {
      newExpanded.delete(title);
    } else {
      newExpanded.add(title);
    }
    setExpandedSections(newExpanded);
  };

  return (
    <nav className="py-4">
      {/* Home Link */}
      <Link
        href="/"
        className="flex items-center gap-2 px-4 py-1.5 text-xs text-gray-600 hover:text-blue-600 mb-4"
      >
        <Home className="w-3.5 h-3.5" />
        Home
      </Link>

      {/* Main Title */}
      <div className="px-4 py-2 text-sm font-semibold text-gray-900 border-b border-gray-200 mb-2">
        REST API
      </div>

      {/* API Version Dropdown */}
      <div className="px-4 py-2 mb-2">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <span>API Version: 2025-11-20 (latest)</span>
        </div>
      </div>

      {/* Navigation Sections */}
      <div className="text-xs">
        {navigationSections.map((section) => (
          <div key={section.title} className="mb-2">
            <button
              onClick={() => toggleSection(section.title)}
              className="flex items-center justify-between w-full text-left px-4 py-1.5 text-gray-900 font-medium hover:bg-gray-100"
            >
              {section.title}
              <ChevronRight
                className={`w-3.5 h-3.5 transform transition-transform ${
                  expandedSections.has(section.title) ? 'rotate-90' : ''
                }`}
              />
            </button>

            {expandedSections.has(section.title) && (
              <ul className="mt-1">
                {section.items.map((item, index) => (
                  <li key={`${section.title}-${item.href}-${index}`}>
                    <Link
                      href={item.href}
                      onClick={() => onEndpointChange?.(item.href)}
                      className="block px-4 py-1.5 pl-8 text-gray-700 hover:bg-gray-100 hover:text-blue-600"
                    >
                      {item.title}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </nav>
  );
}
