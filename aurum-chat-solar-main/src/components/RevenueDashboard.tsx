import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  DollarSign, 
  TrendingUp, 
  Users, 
  Zap, 
  Target,
  BarChart3,
  PieChart,
  Activity,
  RefreshCw,
  Download,
  Filter,
  Calendar,
  MapPin,
  Building
} from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { completeApiClient } from '@/services/apiClientComplete';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

export const RevenueDashboard = () => {
  const {
    analytics,
    analyticsLoading,
    analyticsError,
    leads,
    exportHistory,
    b2bPlatforms,
    refreshAnalytics,
    setAnalyticsLoading,
    setAnalyticsError
  } = useAppStore();

  const [selectedPeriod, setSelectedPeriod] = useState<'7d' | '30d' | '90d' | '1y'>('30d');
  const [selectedBorough, setSelectedBorough] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Refresh analytics data
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refreshAnalytics();
    } finally {
      setIsRefreshing(false);
    }
  };

  // Calculate key metrics
  const calculateMetrics = () => {
    if (!analytics) return null;

    const revenue = analytics.revenue;
    const leadsData = analytics.leads;
    const conversations = analytics.conversations;
    const nycMarket = analytics.nyc_market;

    return {
      totalRevenue: revenue.total_revenue,
      monthlyRevenue: revenue.monthly_revenue,
      revenueGrowth: revenue.revenue_growth,
      averageDealSize: revenue.average_deal_size,
      conversionRate: revenue.conversion_rate,
      totalLeads: leadsData.total,
      qualifiedLeads: leadsData.qualified,
      leadQualityScore: leadsData.quality_score,
      totalConversations: conversations.total,
      averageConversationDuration: conversations.average_duration,
      qualificationRate: conversations.qualification_rate,
      performanceScore: conversations.performance_score,
      totalInstalls: nycMarket.total_installs,
      averageSavings: nycMarket.avg_savings,
      marketGrowth: nycMarket.market_growth
    };
  };

  const metrics = calculateMetrics();

  // Calculate B2B export metrics
  const b2bMetrics = {
    totalExports: exportHistory.length,
    successfulExports: exportHistory.filter(e => e.status === 'exported').length,
    totalRevenue: exportHistory.reduce((sum, e) => sum + (e.revenue || 0), 0),
    averageRevenuePerExport: exportHistory.length > 0 
      ? exportHistory.reduce((sum, e) => sum + (e.revenue || 0), 0) / exportHistory.length 
      : 0,
    topPlatform: b2bPlatforms.length > 0 
      ? b2bPlatforms.reduce((prev, current) => 
          (prev.leads_exported > current.leads_exported) ? prev : current
        ).name
      : 'None'
  };

  if (analyticsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" text="Loading revenue dashboard..." />
      </div>
    );
  }

  if (analyticsError) {
    return (
      <div className="space-y-4">
        <ErrorMessage
          error={analyticsError}
          onRetry={handleRefresh}
          title="Failed to load dashboard"
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold">Revenue Dashboard</h2>
          <p className="text-muted-foreground">
            Real-time performance metrics and revenue tracking
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${metrics?.totalRevenue?.toLocaleString() || '0'}
            </div>
            <div className="flex items-center text-xs text-muted-foreground">
              <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
              +{metrics?.revenueGrowth || 0}% from last period
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Revenue</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${metrics?.monthlyRevenue?.toLocaleString() || '0'}
            </div>
            <div className="text-xs text-muted-foreground">
              Average deal: ${metrics?.averageDealSize?.toLocaleString() || '0'}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Qualified Leads</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics?.qualifiedLeads || 0}
            </div>
            <div className="flex items-center text-xs text-muted-foreground">
              <Target className="h-3 w-3 mr-1" />
              {metrics?.conversionRate ? (metrics.conversionRate * 100).toFixed(1) : 0}% conversion rate
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Performance Score</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics?.performanceScore?.toFixed(1) || '0'}/10
            </div>
            <div className="text-xs text-muted-foreground">
              Lead quality: {metrics?.leadQualityScore?.toFixed(1) || '0'}/10
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analytics Tabs */}
      <Tabs defaultValue="revenue" className="space-y-4">
        <TabsList>
          <TabsTrigger value="revenue">Revenue Analytics</TabsTrigger>
          <TabsTrigger value="leads">Lead Management</TabsTrigger>
          <TabsTrigger value="conversations">Conversation Analytics</TabsTrigger>
          <TabsTrigger value="b2b">B2B Exports</TabsTrigger>
          <TabsTrigger value="nyc">NYC Market</TabsTrigger>
        </TabsList>

        {/* Revenue Analytics Tab */}
        <TabsContent value="revenue" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Revenue Growth</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span>Monthly Growth</span>
                    <Badge variant="outline" className="text-green-600">
                      +{metrics?.revenueGrowth || 0}%
                    </Badge>
                  </div>
                  <Progress value={metrics?.revenueGrowth || 0} className="h-2" />
                  
                  <div className="flex justify-between items-center">
                    <span>Conversion Rate</span>
                    <Badge variant="outline">
                      {(metrics?.conversionRate || 0) * 100}%
                    </Badge>
                  </div>
                  <Progress value={(metrics?.conversionRate || 0) * 100} className="h-2" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Revenue Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Total Revenue</span>
                    <span className="font-medium">
                      ${metrics?.totalRevenue?.toLocaleString() || '0'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Monthly Revenue</span>
                    <span className="font-medium">
                      ${metrics?.monthlyRevenue?.toLocaleString() || '0'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Average Deal Size</span>
                    <span className="font-medium">
                      ${metrics?.averageDealSize?.toLocaleString() || '0'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Lead Management Tab */}
        <TabsContent value="leads" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Lead Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Total Leads</span>
                    <span className="font-medium">{metrics?.totalLeads || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Qualified Leads</span>
                    <span className="font-medium text-green-600">
                      {metrics?.qualifiedLeads || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Quality Score</span>
                    <Badge variant="outline">
                      {metrics?.leadQualityScore?.toFixed(1) || '0'}/10
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Lead Status Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {['new', 'qualifying', 'qualified', 'converting', 'converted'].map((status) => {
                    const count = leads.filter(l => l.status === status).length;
                    const percentage = leads.length > 0 ? (count / leads.length) * 100 : 0;
                    
                    return (
                      <div key={status} className="flex justify-between items-center">
                        <span className="capitalize">{status}</span>
                        <div className="flex items-center gap-2">
                          <Progress value={percentage} className="w-16 h-2" />
                          <span className="text-sm">{count}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recent Leads</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {leads.slice(0, 5).map((lead) => (
                    <div key={lead.id} className="flex justify-between items-center p-2 bg-muted rounded">
                      <div>
                        <div className="font-medium text-sm">{lead.name}</div>
                        <div className="text-xs text-muted-foreground">{lead.email}</div>
                      </div>
                      <Badge variant="outline">
                        {lead.qualification_score}/100
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Conversation Analytics Tab */}
        <TabsContent value="conversations" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Conversation Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Total Conversations</span>
                    <span className="font-medium">{metrics?.totalConversations || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Average Duration</span>
                    <span className="font-medium">
                      {metrics?.averageConversationDuration?.toFixed(1) || '0'} min
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Qualification Rate</span>
                    <Badge variant="outline">
                      {(metrics?.qualificationRate || 0) * 100}%
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance Score</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-center">
                    <div className="text-4xl font-bold text-primary">
                      {metrics?.performanceScore?.toFixed(1) || '0'}
                    </div>
                    <div className="text-sm text-muted-foreground">out of 10</div>
                  </div>
                  <Progress value={(metrics?.performanceScore || 0) * 10} className="h-3" />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* B2B Exports Tab */}
        <TabsContent value="b2b" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Export Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Total Exports</span>
                    <span className="font-medium">{b2bMetrics.totalExports}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Successful Exports</span>
                    <span className="font-medium text-green-600">
                      {b2bMetrics.successfulExports}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Export Revenue</span>
                    <span className="font-medium">
                      ${b2bMetrics.totalRevenue.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Avg Revenue/Export</span>
                    <span className="font-medium">
                      ${b2bMetrics.averageRevenuePerExport.toLocaleString()}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Platform Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {b2bPlatforms.map((platform) => (
                    <div key={platform.code} className="flex justify-between items-center p-2 bg-muted rounded">
                      <div>
                        <div className="font-medium">{platform.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {platform.leads_exported} leads exported
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium">
                          ${platform.revenue_generated.toLocaleString()}
                        </div>
                        <Badge variant={platform.status === 'active' ? 'default' : 'secondary'}>
                          {platform.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* NYC Market Tab */}
        <TabsContent value="nyc" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>NYC Market Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Total Installs</span>
                    <span className="font-medium">{metrics?.totalInstalls?.toLocaleString() || '0'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Average Savings</span>
                    <span className="font-medium">
                      ${metrics?.averageSavings?.toLocaleString() || '0'}/year
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Market Growth</span>
                    <Badge variant="outline" className="text-green-600">
                      +{metrics?.marketGrowth || 0}%
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Borough Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {analytics?.nyc_market?.boroughs?.map((borough: any) => (
                    <div key={borough.name} className="flex justify-between items-center p-2 bg-muted rounded">
                      <div>
                        <div className="font-medium">{borough.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {borough.leads} leads
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium">
                          {borough.conversion_rate * 100}%
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {borough.average_system_size}kW avg
                        </div>
                      </div>
                    </div>
                  )) || []}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};
