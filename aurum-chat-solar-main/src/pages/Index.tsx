import { useState } from 'react';
import { HeroSection } from '@/components/HeroSection';
import { SavingsCalculator } from '@/components/SavingsCalculator';
import { NYCStatsPanel } from '@/components/NYCStatsPanel';
import { TrustSection } from '@/components/TrustSection';
import { ChatInterface } from '@/components/ChatInterface';

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
      
      {/* Chat Interface */}
      <ChatInterface 
        isOpen={isChatOpen} 
        onClose={() => setIsChatOpen(false)}
      />
    </div>
  );
};

export default Index;