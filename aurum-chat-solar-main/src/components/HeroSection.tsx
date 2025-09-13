import { Button } from '@/components/ui/button';
import { MessageCircle, Calculator, Phone } from 'lucide-react';
import heroImage from '@/assets/nyc-solar-hero.jpg';

interface HeroSectionProps {
  onOpenChat: () => void;
}

export const HeroSection = ({ onOpenChat }: HeroSectionProps) => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background Image */}
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ 
          backgroundImage: `linear-gradient(rgba(33, 82, 135, 0.8), rgba(33, 82, 135, 0.6)), url(${heroImage})` 
        }}
      />
      
      {/* Content */}
      <div className="relative z-10 container mx-auto px-4 text-center text-white">
        <div className="animate-fade-up">
          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            Solar Power for <br />
            <span className="text-secondary">NYC Homeowners</span>
          </h1>
          
          <p className="text-xl md:text-2xl mb-8 max-w-3xl mx-auto opacity-90">
            Get instant quotes, local incentives, and connect with trusted solar installers. 
            Join 2,400+ NYC homes saving $180+ monthly on energy bills.
          </p>
        </div>
        
        <div className="animate-slide-in flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
          <Button 
            size="lg" 
            variant="secondary" 
            onClick={onOpenChat}
            className="text-lg px-8 py-4 font-semibold"
          >
            <MessageCircle className="mr-2 h-5 w-5" />
            Start Solar Chat
          </Button>
          
          <Button 
            size="lg" 
            variant="outline" 
            className="text-lg px-8 py-4 font-semibold border-white text-white hover:bg-white hover:text-primary"
          >
            <Calculator className="mr-2 h-5 w-5" />
            Quick Calculator
          </Button>
          
          <Button 
            size="lg" 
            variant="ghost" 
            className="text-lg px-8 py-4 font-semibold text-white hover:bg-white/20"
          >
            <Phone className="mr-2 h-5 w-5" />
            Call Expert
          </Button>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          <div className="text-center animate-fade-up" style={{ animationDelay: '0.2s' }}>
            <div className="text-3xl font-bold text-secondary mb-2">$35K+</div>
            <div className="text-sm opacity-80">Average NYC Solar Savings</div>
          </div>
          <div className="text-center animate-fade-up" style={{ animationDelay: '0.4s' }}>
            <div className="text-3xl font-bold text-secondary mb-2">26%</div>
            <div className="text-sm opacity-80">Federal Tax Credit</div>
          </div>
          <div className="text-center animate-fade-up" style={{ animationDelay: '0.6s' }}>
            <div className="text-3xl font-bold text-secondary mb-2">2,400+</div>
            <div className="text-sm opacity-80">NYC Homes Powered</div>
          </div>
        </div>
      </div>
      
      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 text-white animate-bounce">
        <div className="w-6 h-10 border-2 border-white rounded-full flex justify-center">
          <div className="w-1 h-3 bg-white rounded-full mt-2 animate-pulse"></div>
        </div>
      </div>
    </section>
  );
};