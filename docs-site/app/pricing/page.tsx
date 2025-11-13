import Link from 'next/link';
import Header from '@/components/Header';

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-white">
      <Header />

      <div className="container mx-auto px-6 py-20">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="text-center mb-16">
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              Simple, transparent pricing
            </h1>
            <p className="text-xl text-gray-600">
              Choose the plan that works for you
            </p>
          </div>

          {/* Pricing Cards */}
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Free Tier */}
            <PricingCard
              name="Free"
              price="$0"
              description="Perfect for trying out the API"
              features={[
                '1,000 requests/month',
                'Basic endpoints',
                'Community support',
                'Rate limit: 10 req/min'
              ]}
              cta="Get Started"
              ctaLink="/api"
            />

            {/* Pro Tier */}
            <PricingCard
              name="Pro"
              price="$49"
              description="For production applications"
              features={[
                '100,000 requests/month',
                'All endpoints',
                'Email support',
                'Rate limit: 100 req/min',
                'Custom webhooks'
              ]}
              cta="Start Free Trial"
              ctaLink="/api"
              highlighted
            />

            {/* Enterprise Tier */}
            <PricingCard
              name="Enterprise"
              price="Custom"
              description="For large-scale applications"
              features={[
                'Unlimited requests',
                'All endpoints',
                'Priority support',
                'Custom rate limits',
                'SLA guarantee',
                'Dedicated account manager'
              ]}
              cta="Contact Sales"
              ctaLink="/api"
            />
          </div>

          {/* FAQ Section */}
          <div className="mt-24 max-w-3xl mx-auto">
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
  description,
  features,
  cta,
  ctaLink,
  highlighted = false
}: {
  name: string;
  price: string;
  description: string;
  features: string[];
  cta: string;
  ctaLink: string;
  highlighted?: boolean;
}) {
  return (
    <div className={`p-8 rounded-2xl border-2 ${
      highlighted
        ? 'border-gray-900 shadow-lg'
        : 'border-gray-200'
    }`}>
      {highlighted && (
        <div className="mb-4 inline-block px-3 py-1 bg-gray-900 text-white text-xs font-medium rounded-full">
          Most Popular
        </div>
      )}
      <h3 className="text-2xl font-bold text-gray-900 mb-2">{name}</h3>
      <div className="mb-4">
        <span className="text-4xl font-bold text-gray-900">{price}</span>
        {price !== 'Custom' && <span className="text-gray-600">/month</span>}
      </div>
      <p className="text-gray-600 mb-6">{description}</p>

      <Link
        href={ctaLink}
        className={`block w-full py-3 px-6 rounded-lg font-medium text-center transition-all ${
          highlighted
            ? 'bg-gray-900 text-white hover:bg-gray-800'
            : 'bg-white border-2 border-gray-200 text-gray-900 hover:border-gray-300'
        }`}
      >
        {cta}
      </Link>

      <div className="mt-8 pt-8 border-t border-gray-200">
        <ul className="space-y-3">
          {features.map((feature, index) => (
            <li key={index} className="flex items-start">
              <svg className="w-5 h-5 text-gray-900 mr-3 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              <span className="text-gray-600 text-sm">{feature}</span>
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
