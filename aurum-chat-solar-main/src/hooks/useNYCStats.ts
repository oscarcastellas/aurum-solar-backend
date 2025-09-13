import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient, type NYCStatsResponse, type BoroughStats } from '@/services/apiClient';

export const useNYCStats = () => {
  const [selectedBorough, setSelectedBorough] = useState<string>('brooklyn');

  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['nyc-borough-stats'],
    queryFn: () => apiClient.getNYCBoroughStats(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 10 * 60 * 1000, // Refetch every 10 minutes
  });

  const currentBoroughData = stats?.boroughs?.[selectedBorough] || null;

  const boroughs = stats?.boroughs ? Object.keys(stats.boroughs) : [];

  const selectBorough = (borough: string) => {
    setSelectedBorough(borough);
  };

  return {
    stats,
    selectedBorough,
    currentBoroughData,
    boroughs,
    selectBorough,
    isLoading,
    error,
  };
};
