import Link from 'next/link';
import Header from '@/components/Header';

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-white">
      <Header />

      <div className="container mx-auto px-6 py-20">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-16">
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              Simple, transparent pricing
            </h1>
            <p className="text-xl text-gray-600 mb-4">
              Choose the plan that works for you
            </p>
            <p className="text-lg text-blue-600 font-semibold">
              🎉 2-20x cheaper than competitors like Alpha Vantage, Polygon, and Finnhub
            </p>
          </div>

          {/* Pricing Cards */}
          <div className="grid md:grid-cols-4 gap-6 max-w-7xl mx-auto mb-16">
            {/* Free Tier */}
            <PricingCard
              name="Free"
              price="$0"
              description="For trying out the API"
              features={[
                '10,000 calls/month',
                '10 calls/minute',
                '150 curated stocks',
                '1 year history',
                'EOD prices only',
                'Community support'
              ]}
              cta="Get Started"
              ctaLink="/api"
            />

            {/* Starter Tier */}
            <PricingCard
              name="Starter"
              price="$9"
              priceDetail="/month"
              description="For individual investors"
              features={[
                '50,000 calls/month',
                '30 calls/minute',
                '3,000 US stocks',
                '5 years history',
                'Hourly + EOD prices',
                'Email support',
                'Bulk: 50 symbols'
              ]}
              cta="Start Free Trial"
              ctaLink="/api"
              badge="5x cheaper than Alpha Vantage"
            />

            {/* Premium Tier */}
            <PricingCard
              name="Premium"
              price="$29"
              priceDetail="/month"
              description="For active traders & apps"
              features={[
                '250,000 calls/month',
                '100 calls/minute',
                '4,600 international stocks',
                '30+ years history',
                '15-min + EOD prices',
                'Priority support',
                'Bulk: 200 symbols',
                'Webhooks'
              ]}
              cta="Start Free Trial"
              ctaLink="/api"
              highlighted
              badge="40% cheaper than Finnhub"
            />

            {/* Professional Tier */}
            <PricingCard
              name="Professional"
              price="$79"
              priceDetail="/month"
              description="For platforms & institutions"
              features={[
                '1M calls/month',
                '300 calls/minute',
                '8,000+ global stocks',
                'Full history',
                '1-min + EOD prices',
                'Dedicated support (4hr SLA)',
                'Bulk: 1,000 symbols',
                'Custom screeners',
                'White-label API'
              ]}
              cta="Start Free Trial"
              ctaLink="/api"
              badge="60% cheaper than Polygon"
            />
          </div>

          {/* Enterprise Section */}
          <div className="max-w-5xl mx-auto mb-24">
            <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-12 text-center">
              <h2 className="text-3xl font-bold text-white mb-4">Enterprise</h2>
              <p className="text-xl text-gray-300 mb-8">
                Custom solutions for large-scale applications
              </p>
              <div className="grid md:grid-cols-3 gap-8 mb-8">
                <div className="text-left">
                  <h3 className="text-white font-semibold mb-2">Unlimited Scale</h3>
                  <p className="text-gray-400 text-sm">Custom rate limits (10,000+ calls/min), unlimited monthly calls</p>
                </div>
                <div className="text-left">
                  <h3 className="text-white font-semibold mb-2">Premium Support</h3>
                  <p className="text-gray-400 text-sm">Dedicated account manager, 99.9% uptime SLA, priority feature development</p>
                </div>
                <div className="text-left">
                  <h3 className="text-white font-semibold mb-2">Custom Integration</h3>
                  <p className="text-gray-400 text-sm">On-premise deployment, direct database access, custom endpoints</p>
                </div>
              </div>
              <Link
                href="/api"
                className="inline-block px-8 py-3 bg-white text-gray-900 rounded-lg font-medium hover:bg-gray-100 transition-all"
              >
                Contact Sales
              </Link>
            </div>
          </div>

          {/* Comparison Table */}
          <div className="max-w-5xl mx-auto mb-24">
            <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">
              How We Compare
            </h2>
            <div className="overflow-x-auto rounded-lg border border-gray-300 shadow-sm">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-900 border-b border-gray-300">
                    <th className="text-left py-4 px-6 text-gray-900 font-semibold border-r border-gray-300 bg-gray-100">Provider</th>
                    <th className="text-left py-4 px-6 text-gray-900 font-semibold border-r border-gray-300 bg-gray-100">Entry Price</th>
                    <th className="text-left py-4 px-6 text-gray-900 font-semibold border-r border-gray-300 bg-gray-100">Free Tier</th>
                    <th className="text-left py-4 px-6 text-gray-900 font-semibold bg-gray-100">Dividend Quality</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-gray-300 bg-blue-50">
                    <td className="py-4 px-4 font-semibold text-gray-900 border-r border-gray-300">Divv API</td>
                    <td className="py-4 px-4 font-semibold text-blue-600 border-r border-gray-300">$9/mo</td>
                    <td className="py-4 px-4 font-semibold text-blue-600 border-r border-gray-300">10,000/mo</td>
                    <td className="py-4 px-4 font-semibold text-blue-600">Specialized & Comprehensive</td>
                  </tr>
                  <tr className="border-b border-gray-300 bg-white hover:bg-gray-50 transition-colors">
                    <td className="py-4 px-4 border-r border-gray-300">Alpha Vantage</td>
                    <td className="py-4 px-4 border-r border-gray-300">$49.99/mo</td>
                    <td className="py-4 px-4 border-r border-gray-300">25/day</td>
                    <td className="py-4 px-4">Generic</td>
                  </tr>
                  <tr className="border-b border-gray-300 bg-white hover:bg-gray-50 transition-colors">
                    <td className="py-4 px-4 border-r border-gray-300">Polygon (Massive)</td>
                    <td className="py-4 px-4 border-r border-gray-300">$199/mo</td>
                    <td className="py-4 px-4 border-r border-gray-300">5/min</td>
                    <td className="py-4 px-4">Limited, unreliable</td>
                  </tr>
                  <tr className="border-b border-gray-300 bg-white hover:bg-gray-50 transition-colors">
                    <td className="py-4 px-4 border-r border-gray-300">Finnhub</td>
                    <td className="py-4 px-4 border-r border-gray-300">$50/mo</td>
                    <td className="py-4 px-4 border-r border-gray-300">60/min (no dividends)</td>
                    <td className="py-4 px-4">Requires paid plan</td>
                  </tr>
                  <tr className="bg-white hover:bg-gray-50 transition-colors">
                    <td className="py-4 px-4 border-r border-gray-300">FMP</td>
                    <td className="py-4 px-4 border-r border-gray-300">$22/mo</td>
                    <td className="py-4 px-4 border-r border-gray-300">250/day</td>
                    <td className="py-4 px-4">Generic</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="text-center mt-6 text-gray-600 font-semibold">
              Result: We're 2-20x cheaper with better dividend data!
            </p>
          </div>

          {/* FAQ Section */}
          <div className="max-w-3xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">
              Frequently Asked Questions
            </h2>
            <div className="space-y-6">
              <FAQItem
                question="Can I change plans later?"
                answer="Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately."
              />
              <FAQItem
                question="What happens if I exceed my rate limit?"
                answer="Requests beyond your rate limit will receive a 429 status code. You can upgrade your plan for higher limits."
              />
              <FAQItem
                question="Do you offer refunds?"
                answer="Yes, we offer a 30-day money-back guarantee for all paid plans."
              />
              <FAQItem
                question="Why are your prices so much lower than competitors?"
                answer="We focus specifically on dividend data, which changes slowly (quarterly/monthly). Unlike real-time APIs, users need far fewer API calls, allowing us to offer better pricing while maintaining quality."
              />
              <FAQItem
                question="What makes your dividend data better?"
                answer="We specialize in dividends with features like Dividend Aristocrat/King identification, dividend sustainability scores, tax withholding rates, and AI-powered forecasts - features not available in generic financial APIs."
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function PricingCard({
  name,
  price,
  priceDetail,
  description,
  features,
  cta,
  ctaLink,
  highlighted = false,
  badge
}: {
  name: string;
  price: string;
  priceDetail?: string;
  description: string;
  features: string[];
  cta: string;
  ctaLink: string;
  highlighted?: boolean;
  badge?: string;
}) {
  return (
    <div className={`p-6 rounded-2xl border-2 ${
      highlighted
        ? 'border-blue-600 shadow-xl relative'
        : 'border-gray-200'
    }`}>
      {highlighted && (
        <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 px-4 py-1 bg-blue-600 text-white text-xs font-medium rounded-full">
          MOST POPULAR
        </div>
      )}
      {badge && !highlighted && (
        <div className="mb-3 inline-block px-3 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
          {badge}
        </div>
      )}
      <h3 className="text-2xl font-bold text-gray-900 mb-2">{name}</h3>
      <div className="mb-4">
        <span className="text-4xl font-bold text-gray-900">{price}</span>
        {priceDetail && <span className="text-gray-600">{priceDetail}</span>}
      </div>
      <p className="text-gray-600 mb-6 text-sm">{description}</p>

      <Link
        href={ctaLink}
        className={`block w-full py-3 px-6 rounded-lg font-medium text-center transition-all text-sm ${
          highlighted
            ? 'bg-blue-600 text-white hover:bg-blue-700'
            : 'bg-white border-2 border-gray-200 text-gray-900 hover:border-gray-300'
        }`}
      >
        {cta}
      </Link>

      <div className="mt-6 pt-6 border-t border-gray-200">
        <ul className="space-y-2">
          {features.map((feature, index) => (
            <li key={index} className="flex items-start">
              <svg className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              <span className="text-gray-600 text-xs">{feature}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function FAQItem({ question, answer }: { question: string; answer: string }) {
  return (
    <div className="border-b border-gray-200 pb-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{question}</h3>
      <p className="text-gray-600">{answer}</p>
    </div>
  );
}
