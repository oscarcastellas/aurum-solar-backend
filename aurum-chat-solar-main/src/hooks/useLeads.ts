import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { completeApiClient, type LeadData, type Lead } from '@/services/apiClient';

export const useLeads = () => {
  const queryClient = useQueryClient();

  const createLead = useMutation({
    mutationFn: (leadData: LeadData) => completeApiClient.createLead(leadData),
    onSuccess: (newLead: Lead) => {
      // Invalidate and refetch leads list
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      
      // Add the new lead to the cache
      queryClient.setQueryData(['leads', newLead.id], newLead);
    },
    onError: (error) => {
      console.error('Lead creation error:', error);
    },
  });

  const updateLead = useMutation({
    mutationFn: ({ leadId, updates }: { leadId: string; updates: Partial<Lead> }) =>
      completeApiClient.updateLead(leadId, updates),
    onSuccess: (updatedLead: Lead) => {
      // Update the specific lead in cache
      queryClient.setQueryData(['leads', updatedLead.id], updatedLead);
      
      // Invalidate leads list to ensure consistency
      queryClient.invalidateQueries({ queryKey: ['leads'] });
    },
    onError: (error) => {
      console.error('Lead update error:', error);
    },
  });

  const getLead = (leadId: string) => {
    return useQuery({
      queryKey: ['leads', leadId],
      queryFn: () => completeApiClient.getLead(leadId),
      enabled: !!leadId,
    });
  };

  const getAllLeads = () => {
    return useQuery({
      queryKey: ['leads'],
      queryFn: async () => {
        // This would need to be implemented in the backend
        // For now, return empty array
        return [];
      },
    });
  };

  return {
    createLead: createLead.mutate,
    updateLead: updateLead.mutate,
    getLead,
    getAllLeads,
    isCreating: createLead.isPending,
    isUpdating: updateLead.isPending,
    createError: createLead.error,
    updateError: updateLead.error,
  };
};
