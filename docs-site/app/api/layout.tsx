'use client';

import { useState } from 'react';
import Navigation from '@/components/Navigation';
import CodePanel from '@/components/CodePanel';
import Header from '@/components/Header';

export default function APILayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [selectedLanguage, setSelectedLanguage] = useState<'python' | 'javascript' | 'curl'>('python');
  const [currentEndpoint, setCurrentEndpoint] = useState<string>('/api/stocks');

  return (
    <div className="min-h-screen bg-white">
      <Header />

      <div className="flex">
        {/* Left Sidebar - Navigation (wider for better readability) */}
        <aside className="hidden lg:block w-80 border-r border-gray-200 h-[calc(100vh-56px)] sticky top-14 overflow-y-auto bg-white">
          <Navigation onEndpointChange={setCurrentEndpoint} />
        </aside>

        {/* Main Content */}
        <main className="flex-1 min-w-0">
          <div className="max-w-4xl mx-auto px-8 py-6">
            {children}
          </div>
        </main>

        {/* Right Sidebar - Code Examples (wider for better code readability) */}
        <aside className="hidden xl:block w-[800px] border-l border-gray-200 h-[calc(100vh-56px)] sticky top-14 overflow-y-auto bg-white">
          <CodePanel
            endpoint={currentEndpoint}
            language={selectedLanguage}
            onLanguageChange={setSelectedLanguage}
          />
        </aside>
      </div>
    </div>
  );
}
