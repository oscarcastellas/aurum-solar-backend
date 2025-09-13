import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient, type SavingsInput, type SavingsResult, type IncentiveData } from '@/services/apiClient';

export const useSavingsCalculator = () => {
  const [input, setInput] = useState<SavingsInput>({
    zipCode: '',
    monthlyBill: 0,
    homeType: '',
    roofSize: undefined,
    roofType: 'asphalt',
    shading: 'minimal',
  });

  const calculateSavings = useMutation({
    mutationFn: (data: SavingsInput) => apiClient.calculateSavings(data),
    onSuccess: (data: SavingsResult) => {
      console.log('Savings calculated:', data);
    },
    onError: (error) => {
      console.error('Savings calculation error:', error);
    },
  });

  const { data: incentives, isLoading: incentivesLoading } = useQuery({
    queryKey: ['incentives', input.zipCode],
    queryFn: () => apiClient.getNYCIncentives(input.zipCode),
    enabled: !!input.zipCode && input.zipCode.length === 5,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const { data: electricityRates, isLoading: ratesLoading } = useQuery({
    queryKey: ['electricity-rates', input.zipCode],
    queryFn: () => apiClient.getElectricityRates(input.zipCode),
    enabled: !!input.zipCode && input.zipCode.length === 5,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });

  const updateInput = (updates: Partial<SavingsInput>) => {
    setInput(prev => ({ ...prev, ...updates }));
  };

  const resetInput = () => {
    setInput({
      zipCode: '',
      monthlyBill: 0,
      homeType: '',
      roofSize: undefined,
      roofType: 'asphalt',
      shading: 'minimal',
    });
  };

  const isInputValid = () => {
    return !!(
      input.zipCode &&
      input.zipCode.length === 5 &&
      input.monthlyBill > 0 &&
      input.homeType
    );
  };

  return {
    input,
    updateInput,
    resetInput,
    isInputValid: isInputValid(),
    calculateSavings: calculateSavings.mutate,
    results: calculateSavings.data,
    isLoading: calculateSavings.isPending,
    error: calculateSavings.error,
    incentives: incentives || [],
    electricityRates,
    incentivesLoading,
    ratesLoading,
  };
};
