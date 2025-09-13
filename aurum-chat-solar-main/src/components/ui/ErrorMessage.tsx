import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCw, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ErrorMessageProps {
  error: any;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
  title?: string;
  showDetails?: boolean;
}

export const ErrorMessage = ({ 
  error, 
  onRetry, 
  onDismiss, 
  className,
  title = 'An error occurred',
  showDetails = false
}: ErrorMessageProps) => {
  const getErrorMessage = (error: any): string => {
    if (typeof error === 'string') return error;
    if (error?.message) return error.message;
    if (error?.error) return error.error;
    return 'An unexpected error occurred';
  };

  const getErrorTitle = (error: any): string => {
    if (error?.status === 0) return 'Network Error';
    if (error?.status === 401) return 'Authentication Error';
    if (error?.status === 403) return 'Access Denied';
    if (error?.status === 404) return 'Not Found';
    if (error?.status === 500) return 'Server Error';
    return title;
  };

  return (
    <Alert variant="destructive" className={cn('relative', className)}>
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle>{getErrorTitle(error)}</AlertTitle>
      <AlertDescription className="mt-2">
        {getErrorMessage(error)}
      </AlertDescription>
      
      {showDetails && error?.status && (
        <details className="mt-2">
          <summary className="cursor-pointer text-sm font-medium">
            Technical Details
          </summary>
          <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-auto">
            {JSON.stringify(error, null, 2)}
          </pre>
        </details>
      )}
      
      <div className="flex gap-2 mt-3">
        {onRetry && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="h-8"
          >
            <RefreshCw className="mr-1 h-3 w-3" />
            Try Again
          </Button>
        )}
        {onDismiss && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onDismiss}
            className="h-8"
          >
            <X className="mr-1 h-3 w-3" />
            Dismiss
          </Button>
        )}
      </div>
    </Alert>
  );
};
