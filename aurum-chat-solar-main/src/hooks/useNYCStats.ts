import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient, type NYCStatsResponse, type BoroughStats } from '@/services/apiClient';

export const useNYCStats = () => {
  const [selectedBorough, setSelectedBorough] = useState<string>('brooklyn');

  // Mock data for NYC stats since the endpoint isn't available yet
  const mockStats = {
    boroughs: {
      brooklyn: {
        name: 'Brooklyn',
        installs: 450,
        avgSavings: '$180',
        incentives: '$8,500',
        payback: '7.2 years',
        avgSystemSize: 8.5,
        avgCost: 25500,
        growthRate: 15.2
      },
      manhattan: {
        name: 'Manhattan',
        installs: 320,
        avgSavings: '$220',
        incentives: '$9,200',
        payback: '6.8 years',
        avgSystemSize: 9.2,
        avgCost: 27600,
        growthRate: 18.5
      },
      queens: {
        name: 'Queens',
        installs: 380,
        avgSavings: '$195',
        incentives: '$8,800',
        payback: '7.0 years',
        avgSystemSize: 8.8,
        avgCost: 26400,
        growthRate: 16.8
      },
      bronx: {
        name: 'Bronx',
        installs: 180,
        avgSavings: '$165',
        incentives: '$7,500',
        payback: '7.5 years',
        avgSystemSize: 7.8,
        avgCost: 23400,
        growthRate: 12.3
      },
      staten_island: {
        name: 'Staten Island',
        installs: 95,
        avgSavings: '$175',
        incentives: '$8,000',
        payback: '7.3 years',
        avgSystemSize: 8.2,
        avgCost: 24600,
        growthRate: 14.1
      }
    },
    totalInstalls: 1425,
    avgSavings: 187,
    marketGrowth: 15.4,
    lastUpdated: new Date().toISOString()
  };

  const { data: stats = mockStats, isLoading = false, error = null } = useQuery({
    queryKey: ['nyc-borough-stats'],
    queryFn: () => Promise.resolve(mockStats), // Use mock data for now
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
