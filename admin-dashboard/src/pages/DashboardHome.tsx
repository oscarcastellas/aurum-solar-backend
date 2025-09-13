import React from 'react'
import { useQuery } from 'react-query'
import { 
  DollarSign, 
  Users, 
  TrendingUp, 
  Target,
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3
} from 'lucide-react'

// Components
import MetricCard from '../components/dashboard/MetricCard'
import RevenueChart from '../components/dashboard/RevenueChart'
import KPIStatus from '../components/dashboard/KPIStatus'
import RecentActivity from '../components/dashboard/RecentActivity'
import PerformanceAlerts from '../components/dashboard/PerformanceAlerts'
import LoadingSpinner from '../components/ui/LoadingSpinner'

// API
import { fetchDashboardMetrics } from '../services/api'

const DashboardHome: React.FC = () => {
  const { data: dashboardData, isLoading, error } = useQuery(
    'dashboard-metrics',
    fetchDashboardMetrics,
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  )

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
          <span className="text-red-800">Failed to load dashboard data</span>
        </div>
      </div>
    )
  }

  const { summary, real_time, kpis } = dashboardData || {}

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Revenue Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Real-time performance monitoring and analytics
          </p>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <Clock className="h-4 w-4" />
          <span>Last updated: {real_time?.timestamp ? new Date(real_time.timestamp).toLocaleTimeString() : 'N/A'}</span>
        </div>
      </div>

      {/* Performance Alerts */}
      <PerformanceAlerts />

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Today's Revenue"
          value={real_time?.today?.revenue || 0}
          format="currency"
          change={real_time?.yesterday_comparison?.revenue_change || 0}
          icon={DollarSign}
          color="green"
        />
        <MetricCard
          title="Today's Leads"
          value={real_time?.today?.leads || 0}
          format="number"
          change={real_time?.yesterday_comparison?.leads_change || 0}
          icon={Users}
          color="blue"
        />
        <MetricCard
          title="Conversion Rate"
          value={real_time?.today?.conversion_rate || 0}
          format="percentage"
          target={0.60}
          icon={Target}
          color="purple"
        />
        <MetricCard
          title="Pipeline Value"
          value={real_time?.pipeline_value?.total_pipeline_value || 0}
          format="currency"
          icon={TrendingUp}
          color="orange"
        />
      </div>

      {/* KPI Status */}
      <KPIStatus kpis={kpis} />

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RevenueChart />
        <RecentActivity />
      </div>

      {/* Summary Metrics */}
      {summary && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Revenue Summary */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue Summary</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Revenue (30d)</span>
                <span className="font-semibold">
                  ${summary.revenue_metrics?.total_revenue?.toLocaleString() || 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Avg Revenue/Lead</span>
                <span className="font-semibold">
                  ${summary.revenue_metrics?.average_revenue_per_lead?.toFixed(2) || 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Growth Rate</span>
                <span className={`font-semibold ${(summary.revenue_metrics?.growth_rate || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {((summary.revenue_metrics?.growth_rate || 0) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          {/* Quality Distribution */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Lead Quality</h3>
            <div className="space-y-3">
              {summary.revenue_metrics?.quality_distribution && Object.entries(summary.revenue_metrics.quality_distribution).map(([tier, count]) => (
                <div key={tier} className="flex justify-between">
                  <span className="text-gray-600 capitalize">{tier}</span>
                  <span className="font-semibold">{count as number} leads</span>
                </div>
              ))}
            </div>
          </div>

          {/* Platform Performance */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Platform Performance</h3>
            <div className="space-y-3">
              {summary.revenue_metrics?.platform_performance && Object.entries(summary.revenue_metrics.platform_performance).map(([platform, revenue]) => (
                <div key={platform} className="flex justify-between">
                  <span className="text-gray-600 capitalize">{platform.replace('_', ' ')}</span>
                  <span className="font-semibold">${(revenue as number).toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DashboardHome
