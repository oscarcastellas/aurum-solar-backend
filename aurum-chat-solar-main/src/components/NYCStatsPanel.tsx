import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { MapPin, Users, Zap, TrendingUp } from 'lucide-react';
import { useNYCStats } from '@/hooks/useNYCStats';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

export const NYCStatsPanel = () => {
  const {
    stats,
    selectedBorough,
    currentBoroughData,
    boroughs,
    selectBorough,
    isLoading,
    error
  } = useNYCStats();

  return (
    <section className="py-20 bg-background">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-primary mb-4">
            Solar Across NYC Boroughs
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            See how your neighbors are saving with solar. Each borough has unique 
            incentives and solar potential.
          </p>
        </div>

        <div className="max-w-6xl mx-auto">
          {error && (
            <div className="mb-8">
              <ErrorMessage 
                error={error} 
                title="Failed to load NYC statistics"
                showDetails={false}
              />
            </div>
          )}
          
          {isLoading ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner size="lg" text="Loading NYC solar statistics..." />
            </div>
          ) : (
            <>
              {/* Borough Selector */}
              <div className="flex flex-wrap justify-center gap-4 mb-8">
                {boroughs.map((borough) => (
                  <Button
                    key={borough}
                    variant={selectedBorough === borough ? "default" : "outline"}
                    onClick={() => selectBorough(borough)}
                    className="borough-card transition-all duration-300"
                  >
                    <MapPin className="mr-2 h-4 w-4" />
                    {borough.charAt(0).toUpperCase() + borough.slice(1)}
                  </Button>
                ))}
              </div>
            </>
          )}

          {/* Selected Borough Stats */}
          {currentBoroughData && (
            <Card className="shadow-lg animate-fade-up">
              <CardHeader className="gradient-energy text-white text-center">
                <CardTitle className="text-3xl">
                  {currentBoroughData.name} Solar Stats
                </CardTitle>
              </CardHeader>
              <CardContent className="p-8">
                <div className="grid md:grid-cols-4 gap-6">
                  <div className="text-center">
                    <Users className="h-8 w-8 text-primary mx-auto mb-3" />
                    <div className="text-3xl font-bold text-primary mb-2">
                      {currentBoroughData.installs.toLocaleString()}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Solar Installations
                    </div>
                  </div>

                  <div className="text-center">
                    <TrendingUp className="h-8 w-8 text-accent mx-auto mb-3" />
                    <div className="text-3xl font-bold text-accent mb-2">
                      ${currentBoroughData.avgSavings.toLocaleString()}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Annual Savings
                    </div>
                  </div>

                  <div className="text-center">
                    <Zap className="h-8 w-8 text-secondary mx-auto mb-3" />
                    <div className="text-3xl font-bold text-secondary-foreground mb-2">
                      ${currentBoroughData.incentives.toLocaleString()}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Local Incentives
                    </div>
                  </div>

                  <div className="text-center">
                    <div className="h-8 w-8 bg-trust rounded-full flex items-center justify-center mx-auto mb-3">
                      <span className="text-white font-bold text-sm">ROI</span>
                    </div>
                    <div className="text-3xl font-bold text-trust mb-2">
                      {currentBoroughData.payback} years
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Payback Period
                    </div>
                  </div>
                </div>

                <div className="mt-8 p-6 bg-muted/50 rounded-lg">
                  <h3 className="font-semibold mb-4 text-center">
                    Why {currentBoroughData.name} Residents Choose Solar
                  </h3>
                  <div className="grid md:grid-cols-3 gap-4 text-sm">
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-accent rounded-full mr-3"></div>
                      High electricity rates
                    </div>
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-secondary rounded-full mr-3"></div>
                      Strong local incentives
                    </div>
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-trust rounded-full mr-3"></div>
                      Proven ROI track record
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </section>
  );
};