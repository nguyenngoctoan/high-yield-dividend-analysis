'use client';

import { useState } from 'react';
import Navigation from '@/components/Navigation';
import Header from '@/components/Header';
import CodePanel from '@/components/CodePanel';

export default function APILayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [currentEndpoint, setCurrentEndpoint] = useState<string>('/api/stocks');
  const [language, setLanguage] = useState<'python' | 'javascript' | 'curl'>('python');

  return (
    <div className="min-h-screen bg-white">
      <Header />

      <div className="container mx-auto px-6">
        <div className="flex gap-6">
          {/* Left Sidebar - Navigation */}
          <aside className="hidden lg:block w-56 flex-shrink-0">
            <div className="sticky top-20 h-[calc(100vh-88px)] overflow-y-auto border-r border-gray-200 pr-4">
              <Navigation onEndpointChange={setCurrentEndpoint} />
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1 min-w-0 py-8">
            {children}
          </main>

          {/* Right Sidebar - Code Examples */}
          <aside className="hidden xl:block w-[500px] flex-shrink-0">
            <div className="sticky top-20 h-[calc(100vh-88px)] overflow-y-auto border-l border-gray-200 pl-4">
              <CodePanel
                endpoint={currentEndpoint}
                language={language}
                onLanguageChange={setLanguage}
              />
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
