import { useState } from 'react';
import { HeroSection } from '@/components/HeroSection';
import { SavingsCalculator } from '@/components/SavingsCalculator';
import { NYCStatsPanel } from '@/components/NYCStatsPanel';
import { TrustSection } from '@/components/TrustSection';
import { AdvancedChatInterface } from '@/components/AdvancedChatInterface';
import { RevenueDashboard } from '@/components/RevenueDashboard';
import { RailwayConnectionTest } from '@/components/RailwayConnectionTest';
import { RailwayTestSuite } from '@/components/RailwayTestSuite';

const Index = () => {
  const [isChatOpen, setIsChatOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <HeroSection onOpenChat={() => setIsChatOpen(true)} />
      
      {/* Savings Calculator */}
      <SavingsCalculator />
      
      {/* NYC Statistics Panel */}
      <NYCStatsPanel />
      
      {/* Trust Section */}
      <TrustSection />
      
      {/* Revenue Dashboard */}
      <RevenueDashboard />
      
      {/* Railway Backend Testing */}
      <div className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-8">
            Railway Backend Testing
          </h2>
          <div className="space-y-8">
            <RailwayConnectionTest />
            <RailwayTestSuite />
          </div>
        </div>
      </div>
      
      {/* Advanced Chat Interface */}
      <AdvancedChatInterface 
        isOpen={isChatOpen} 
        onClose={() => setIsChatOpen(false)}
      />
    </div>
  );
};

export default Index;