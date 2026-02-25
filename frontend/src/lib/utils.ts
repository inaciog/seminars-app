import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// China timezone (UTC+8)
export const CHINA_TIMEZONE = 'Asia/Shanghai';

/**
 * Format a date string in China timezone
 */
export function formatDateChina(dateString: string, options?: Intl.DateTimeFormatOptions): string {
  const opts = options || { year: 'numeric', month: 'short', day: 'numeric' };
  return new Date(dateString).toLocaleDateString('en-US', {
    ...opts,
    timeZone: CHINA_TIMEZONE,
  });
}

/**
 * Format a Date object in China timezone
 */
export function formatDateObjChina(date: Date, options?: Intl.DateTimeFormatOptions): string {
  const opts = options || { year: 'numeric', month: 'short', day: 'numeric' };
  return date.toLocaleDateString('en-US', {
    ...opts,
    timeZone: CHINA_TIMEZONE,
  });
}

/**
 * Format a Date as YYYY-MM-DD string in China timezone
 * Use this instead of toISOString().split('T')[0] to avoid UTC conversion issues
 */
export function formatDateToYMDChina(date: Date): string {
  const parts = new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    timeZone: CHINA_TIMEZONE,
  }).formatToParts(date);
  
  const year = parts.find(p => p.type === 'year')?.value;
  const month = parts.find(p => p.type === 'month')?.value;
  const day = parts.find(p => p.type === 'day')?.value;
  
  return `${year}-${month}-${day}`;
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    timeZone: CHINA_TIMEZONE,
  });
}

export function formatTime(timeString: string): string {
  return new Date(`2000-01-01T${timeString}`).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: CHINA_TIMEZONE,
  });
}

export function formatDateTime(dateTimeString: string): string {
  return new Date(dateTimeString).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: CHINA_TIMEZONE,
  });
}

export function getUrgencyColor(daysUntil: number): string {
  if (daysUntil <= 3) return 'text-red-600 bg-red-50';
  if (daysUntil <= 7) return 'text-amber-600 bg-amber-50';
  return 'text-green-600 bg-green-50';
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 9);
}

export function formatDistanceToNow(dateString: string): string {
  // Get current time in China timezone
  const now = new Date();
  const chinaNow = new Date(now.toLocaleString('en-US', { timeZone: CHINA_TIMEZONE }));
  
  // Parse the date and convert to China time
  const date = new Date(dateString);
  const chinaDate = new Date(date.toLocaleString('en-US', { timeZone: CHINA_TIMEZONE }));
  
  const diffMs = chinaNow.getTime() - chinaDate.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return 'yesterday';
  if (diffDays < 7) return `${diffDays}d ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
  return `${Math.floor(diffDays / 30)}mo ago`;
}
