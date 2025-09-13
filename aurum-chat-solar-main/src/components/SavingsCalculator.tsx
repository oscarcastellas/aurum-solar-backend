import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Calculator, Zap, DollarSign, Home } from 'lucide-react';
import { useSavingsCalculator } from '@/hooks/useSavingsCalculator';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

export const SavingsCalculator = () => {
  const {
    input,
    updateInput,
    isInputValid,
    calculateSavings,
    results,
    isLoading,
    error,
    incentives,
    electricityRates,
    incentivesLoading
  } = useSavingsCalculator();

  const handleCalculateSavings = () => {
    if (!isInputValid) return;
    
    calculateSavings({
      zipCode: input.zipCode,
      monthlyBill: input.monthlyBill,
      homeType: input.homeType,
      roofSize: input.roofSize,
      roofType: input.roofType,
      shading: input.shading,
    });
  };

  return (
    <section className="py-20 bg-muted/30">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-primary mb-4">
            Calculate Your Solar Savings
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            See how much you could save with solar panels on your NYC home. 
            Get personalized estimates in seconds.
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          <Card className="shadow-xl">
            <CardHeader className="gradient-solar text-white">
              <CardTitle className="flex items-center text-2xl">
                <Calculator className="mr-3 h-6 w-6" />
                NYC Solar Savings Calculator
              </CardTitle>
            </CardHeader>
            <CardContent className="p-8">
              <div className="grid md:grid-cols-2 gap-8">
                {/* Input Form */}
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-semibold mb-2">
                      NYC ZIP Code
                    </label>
                    <Input
                      placeholder="e.g. 10001"
                      value={input.zipCode}
                      onChange={(e) => updateInput({ zipCode: e.target.value })}
                      className="text-lg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold mb-2">
                      Monthly Electric Bill
                    </label>
                    <div className="relative">
                      <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        type="number"
                        placeholder="180"
                        value={input.monthlyBill || ''}
                        onChange={(e) => updateInput({ monthlyBill: parseFloat(e.target.value) || 0 })}
                        className="pl-10 text-lg"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold mb-2">
                      Home Type
                    </label>
                    <Select value={input.homeType} onValueChange={(value) => updateInput({ homeType: value })}>
                      <SelectTrigger className="text-lg">
                        <SelectValue placeholder="Select your home type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="single-family">Single Family House</SelectItem>
                        <SelectItem value="townhouse">Townhouse</SelectItem>
                        <SelectItem value="condo">Condo/Co-op</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Button 
                    onClick={handleCalculateSavings}
                    className="w-full text-lg py-3"
                    disabled={!isInputValid || isLoading}
                  >
                    {isLoading ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      <>
                        <Zap className="mr-2 h-5 w-5" />
                        Calculate My Savings
                      </>
                    )}
                  </Button>
                </div>

                {/* Results */}
                <div className="space-y-4">
                  {error && (
                    <ErrorMessage 
                      error={error} 
                      onRetry={handleCalculateSavings}
                      title="Calculation Error"
                    />
                  )}
                  
                  {results ? (
                    <div className="space-y-4">
                      <h3 className="text-xl font-semibold text-primary mb-4">
                        Your Solar Estimate
                      </h3>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-accent/10 p-4 rounded-lg text-center">
                          <div className="text-2xl font-bold text-accent">
                            ${Math.round(results.monthlySavings)}
                          </div>
                          <div className="text-sm text-muted-foreground">Monthly Savings</div>
                        </div>
                        
                        <div className="bg-secondary/10 p-4 rounded-lg text-center">
                          <div className="text-2xl font-bold text-secondary-foreground">
                            {results.paybackYears} years
                          </div>
                          <div className="text-sm text-muted-foreground">Payback Period</div>
                        </div>
                      </div>

                      <div className="bg-primary/5 p-6 rounded-lg border border-primary/20">
                        <div className="text-center">
                          <div className="text-3xl font-bold text-primary mb-2">
                            ${Math.round(results.lifetimeSavings).toLocaleString()}
                          </div>
                          <div className="text-sm text-muted-foreground mb-4">
                            25-Year Lifetime Savings
                          </div>
                          <Button variant="default" className="w-full">
                            Get Detailed Quote
                          </Button>
                        </div>
                      </div>

                      {/* Incentives Display */}
                      {incentives.length > 0 && (
                        <div className="bg-muted/50 p-4 rounded-lg">
                          <h4 className="font-semibold mb-2">Available Incentives</h4>
                          <div className="space-y-2">
                            {incentives.map((incentive, index) => (
                              <div key={index} className="flex justify-between text-sm">
                                <span>{incentive.name}</span>
                                <span className="font-medium">${incentive.amount.toLocaleString()}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="text-xs text-muted-foreground text-center">
                        *Estimates based on NYC averages. Actual results may vary.
                      </div>
                    </div>
                  ) : isLoading ? (
                    <div className="flex flex-col items-center justify-center h-full text-center py-12">
                      <LoadingSpinner size="lg" text="Calculating your savings..." />
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-full text-center py-12">
                      <Home className="h-24 w-24 text-muted-foreground/30 mb-4" />
                      <p className="text-muted-foreground">
                        Enter your details to see personalized solar savings
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};