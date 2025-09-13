import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Star, Shield, Award, CheckCircle, Quote } from 'lucide-react';

export const TrustSection = () => {
  return (
    <section className="py-20 bg-muted/30">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-primary mb-4">
            Trusted by NYC Homeowners
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Join thousands of satisfied customers who've made the switch to solar 
            with confidence through our vetted installer network.
          </p>
        </div>

        <div className="max-w-6xl mx-auto">
          {/* Trust Badges */}
          <div className="grid md:grid-cols-4 gap-6 mb-12">
            <Card className="trust-badge transition-all duration-300 border-2 border-trust/20">
              <CardContent className="p-6 text-center">
                <Shield className="h-12 w-12 text-trust mx-auto mb-3" />
                <h3 className="font-semibold mb-2">NYC Licensed</h3>
                <p className="text-sm text-muted-foreground">
                  All installers verified & insured
                </p>
              </CardContent>
            </Card>

            <Card className="trust-badge transition-all duration-300 border-2 border-secondary/20">
              <CardContent className="p-6 text-center">
                <Award className="h-12 w-12 text-secondary mx-auto mb-3" />
                <h3 className="font-semibold mb-2">A+ Rated</h3>
                <p className="text-sm text-muted-foreground">
                  Better Business Bureau
                </p>
              </CardContent>
            </Card>

            <Card className="trust-badge transition-all duration-300 border-2 border-accent/20">
              <CardContent className="p-6 text-center">
                <CheckCircle className="h-12 w-12 text-accent mx-auto mb-3" />
                <h3 className="font-semibold mb-2">25-Year Warranty</h3>
                <p className="text-sm text-muted-foreground">
                  Equipment & workmanship
                </p>
              </CardContent>
            </Card>

            <Card className="trust-badge transition-all duration-300 border-2 border-primary/20">
              <CardContent className="p-6 text-center">
                <div className="flex justify-center mb-3">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="h-5 w-5 text-secondary fill-current" />
                  ))}
                </div>
                <h3 className="font-semibold mb-2">4.8/5 Rating</h3>
                <p className="text-sm text-muted-foreground">
                  2,400+ verified reviews
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Customer Testimonials */}
          <div className="grid md:grid-cols-3 gap-6 mb-12">
            <Card className="shadow-lg">
              <CardContent className="p-6">
                <Quote className="h-8 w-8 text-primary/30 mb-4" />
                <p className="mb-4 text-muted-foreground italic">
                  "Saved $240 last month alone. The process was seamless and the 
                  installer was incredibly professional."
                </p>
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-secondary rounded-full mr-3"></div>
                  <div>
                    <div className="font-semibold">Sarah M.</div>
                    <div className="text-sm text-muted-foreground">Brooklyn Heights</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-lg">
              <CardContent className="p-6">
                <Quote className="h-8 w-8 text-primary/30 mb-4" />
                <p className="mb-4 text-muted-foreground italic">
                  "Best investment we've made. Already seeing 85% reduction in our 
                  electric bill after 6 months."
                </p>
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-accent rounded-full mr-3"></div>
                  <div>
                    <div className="font-semibold">Michael R.</div>
                    <div className="text-sm text-muted-foreground">Queens</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-lg">
              <CardContent className="p-6">
                <Quote className="h-8 w-8 text-primary/30 mb-4" />
                <p className="mb-4 text-muted-foreground italic">
                  "The chat helped me understand everything upfront. No surprises, 
                  just exactly what they promised."
                </p>
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-trust rounded-full mr-3"></div>
                  <div>
                    <div className="font-semibold">Jessica L.</div>
                    <div className="text-sm text-muted-foreground">Upper East Side</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Final CTA */}
          <div className="text-center">
            <Card className="shadow-xl gradient-solar text-white">
              <CardContent className="p-8">
                <h3 className="text-2xl font-bold mb-4">
                  Ready to Join 2,400+ NYC Solar Homes?
                </h3>
                <p className="mb-6 text-lg opacity-90">
                  Get your personalized solar analysis in under 3 minutes. 
                  No obligations, just real numbers for your home.
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <Button size="lg" variant="secondary" className="text-lg px-8 py-4">
                    Start My Solar Analysis
                  </Button>
                  <Button 
                    size="lg" 
                    variant="outline" 
                    className="text-lg px-8 py-4 border-white text-white hover:bg-white hover:text-primary"
                  >
                    Speak with Expert
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
};