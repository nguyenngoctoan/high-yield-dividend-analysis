'use client';

import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { API_CONFIG } from '@/lib/config';

interface CodePanelProps {
  endpoint: string;
  language: 'python' | 'javascript' | 'curl';
  onLanguageChange: (lang: 'python' | 'javascript' | 'curl') => void;
}

const getCodeExamples = (apiUrl: string): Record<string, Record<string, string>> => ({
  '/api/stocks': {
    python: `import requests

# List stocks with filtering
response = requests.get(
    "${apiUrl}/v1/stocks",
    params={
        "has_dividends": True,
        "min_yield": 5.0,
        "limit": 20
    }
)

stocks = response.json()
for stock in stocks['data']:
    print(f"{stock['symbol']}: {stock['dividend_yield']:.2f}%")`,
    javascript: `// List stocks with filtering
const response = await fetch(
  '${apiUrl}/v1/stocks?' +
  new URLSearchParams({
    has_dividends: 'true',
    min_yield: '5.0',
    limit: '20'
  })
);

const stocks = await response.json();
stocks.data.forEach(stock => {
  console.log(\`\${stock.symbol}: \${stock.dividend_yield}%\`);
});`,
    curl: `curl "${apiUrl}/v1/stocks?has_dividends=true&min_yield=5.0&limit=20"`,
  },
  '/api/dividends': {
    python: `import requests
from datetime import date

# Get dividend calendar
response = requests.get(
    "${apiUrl}/v1/dividends/calendar",
    params={
        "start_date": "2025-11-01",
        "end_date": "2025-12-31"
    }
)

events = response.json()
for event in events['data']:
    print(f"{event['symbol']}: {event['ex_date']} - $\\{event['amount']}")`,
    javascript: `// Get dividend calendar
const response = await fetch(
  '${apiUrl}/v1/dividends/calendar?' +
  new URLSearchParams({
    start_date: '2025-11-01',
    end_date: '2025-12-31'
  })
);

const events = await response.json();
events.data.forEach(event => {
  console.log(\`\${event.symbol}: \${event.ex_date} - $\$\\{event.amount}\`);
});`,
    curl: `curl "${apiUrl}/v1/dividends/calendar?start_date=2025-11-01&end_date=2025-12-31"`,
  },
  '/api/screeners': {
    python: `import requests

# High-yield screener
response = requests.get(
    "${apiUrl}/v1/screeners/high-yield",
    params={
        "min_yield": 6.0,
        "min_market_cap": 1000000000
    }
)

results = response.json()
for stock in results['data'][:10]:
    print(f"{stock['symbol']:6s} {stock['yield']:5.2f}% - {stock['company']}")`,
    javascript: `// High-yield screener
const response = await fetch(
  '${apiUrl}/v1/screeners/high-yield?' +
  new URLSearchParams({
    min_yield: '6.0',
    min_market_cap: '1000000000'
  })
);

const results = await response.json();
results.data.slice(0, 10).forEach(stock => {
  console.log(\`\${stock.symbol} \${stock.yield}% - \${stock.company}\`);
});`,
    curl: `curl "${apiUrl}/v1/screeners/high-yield?min_yield=6.0&min_market_cap=1000000000"`,
  },
  '/api/analytics': {
    python: `import requests

# Analyze portfolio
response = requests.post(
    "${apiUrl}/v1/analytics/portfolio",
    json={
        "positions": [
            {"symbol": "AAPL", "shares": 100},
            {"symbol": "MSFT", "shares": 50}
        ],
        "projection_years": 5,
        "reinvest_dividends": True,
        "annual_contribution": 10000
    }
)

analysis = response.json()
print(f"Current Value: {analysis['current_value']:,.2f}")
print(f"Annual Income: {analysis['annual_dividend_income']:,.2f}")
print(f"Portfolio Yield: {analysis['portfolio_yield']:.2f}%")`,
    javascript: `// Analyze portfolio
const response = await fetch(
  '${apiUrl}/v1/analytics/portfolio',
  {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      positions: [
        {symbol: 'AAPL', shares: 100},
        {symbol: 'MSFT', shares: 50}
      ],
      projection_years: 5,
      reinvest_dividends: true,
      annual_contribution: 10000
    })
  }
);

const analysis = await response.json();
console.log(\`Current Value: $\$\\{analysis.current_value}\`);
console.log(\`Annual Income: $\$\\{analysis.annual_dividend_income}\`);`,
    curl: `curl -X POST "${apiUrl}/v1/analytics/portfolio" \\
  -H "Content-Type: application/json" \\
  -d '{
    "positions": [
      {"symbol": "AAPL", "shares": 100}
    ],
    "projection_years": 5
  }'`,
  },
  '/api/prices': {
    python: `import requests

# Get price history
response = requests.get(
    "${apiUrl}/v1/prices/AAPL",
    params={
        "start_date": "2025-10-01",
        "end_date": "2025-11-01",
        "interval": "daily"
    }
)

prices = response.json()
for bar in prices['data'][:5]:
    print(f"{bar['date']}: {bar['close']:.2f}")`,
    javascript: `// Get price history
const response = await fetch(
  '${apiUrl}/v1/prices/AAPL?' +
  new URLSearchParams({
    start_date: '2025-10-01',
    end_date: '2025-11-01',
    interval: 'daily'
  })
);

const prices = await response.json();
prices.data.slice(0, 5).forEach(bar => {
  console.log(\`\${bar.date}: $\${bar.close}\`);
});`,
    curl: `curl "${apiUrl}/v1/prices/AAPL?start_date=2025-10-01&end_date=2025-11-01"`,
  },
});

export default function CodePanel({ endpoint, language, onLanguageChange }: CodePanelProps) {
  const [copied, setCopied] = useState(false);
  const codeExamples = getCodeExamples(API_CONFIG.baseUrl);

  const code = codeExamples[endpoint]?.[language] || codeExamples['/api/stocks']?.[language] || '';

  const copyToClipboard = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const languages = [
    { id: 'python' as const, label: 'Python' },
    { id: 'javascript' as const, label: 'JavaScript' },
    { id: 'curl' as const, label: 'cURL' },
  ];

  const responseExample = {
    object: "list",
    has_more: false,
    data: [
      {
        id: "stock_aapl",
        symbol: "AAPL",
        company: "Apple Inc.",
        exchange: "NASDAQ",
        price: 185.50,
        dividend_yield: 0.52
      }
    ]
  };

  return (
    <div className="p-6 bg-white">
      {/* Code Examples Header */}
      <h2 className="text-lg font-bold text-gray-900 mb-6">Code Examples</h2>

      {/* Dark Code Block */}
      <div className="relative mb-8 rounded-lg overflow-hidden shadow-sm">
        {/* Language Tabs on Dark Background */}
        <div className="bg-[#2d2d2d] flex items-center justify-between px-4 py-3">
          <div className="flex gap-2">
            {languages.map((lang) => (
              <button
                key={lang.id}
                onClick={() => onLanguageChange(lang.id)}
                className={`px-3 py-1 text-sm font-medium ${
                  language === lang.id
                    ? 'text-white'
                    : 'text-gray-400 hover:text-gray-300'
                }`}
              >
                {lang.label}
              </button>
            ))}
          </div>

          {/* Copy and Fullscreen Icons */}
          <div className="flex gap-2">
            <button
              onClick={copyToClipboard}
              className="p-1 text-gray-400 hover:text-white"
              aria-label="Copy code"
            >
              {copied ? (
                <Check className="w-4 h-4 text-green-400" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        {/* Dark Code Area */}
        <pre className="bg-[#1e1e1e] text-gray-300 p-6 overflow-x-auto text-sm font-mono leading-relaxed">
          <code className="text-gray-300 whitespace-pre">{code}</code>
        </pre>
      </div>

      {/* Subscription Request Section */}
      <div className="mb-8">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Subscription Request</h3>
        <div className="bg-gray-50 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="bg-green-100 text-green-700 text-xs font-semibold px-2 py-1 rounded">
              WS
            </span>
            <code className="text-sm font-mono text-gray-700">
              {`{"action":"subscribe", "params":"T.*"}`}
            </code>
          </div>
          <button className="p-1 text-gray-400 hover:text-gray-600" aria-label="Copy">
            <Copy className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Response Object Section */}
      <div className="mb-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Response Object</h3>
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 flex items-center justify-between border-b border-gray-200">
            <span className="text-sm font-medium text-gray-700">Sample Response</span>
            <div className="flex gap-2">
              <button className="p-1 text-gray-400 hover:text-gray-600" aria-label="Copy">
                <Copy className="w-4 h-4" />
              </button>
            </div>
          </div>
          <pre className="bg-white p-4 overflow-x-auto text-sm font-mono">
            <code className="text-gray-800">{JSON.stringify(responseExample, null, 2)}</code>
          </pre>
        </div>
      </div>
    </div>
  );
}
