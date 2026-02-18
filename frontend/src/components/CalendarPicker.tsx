import { useState, useEffect, useCallback } from 'react';
import { ChevronLeft, ChevronRight, X } from 'lucide-react';
import { 
  format, 
  addMonths, 
  subMonths, 
  startOfMonth, 
  endOfMonth, 
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  isSameMonth,
  isSameDay,
  isBefore,
  startOfDay,
  isWithinInterval,
  parseISO
} from 'date-fns';
import { cn } from '@/lib/utils';

interface AvailabilityRange {
  start_date: string;
  end_date: string;
  preference?: string;
}

interface CalendarPickerProps {
  selectedDates: Date[];
  onChange: (dates: Date[]) => void;
  minDate?: Date;
  existingAvailability?: AvailabilityRange[];
}

export function CalendarPicker({ selectedDates, onChange, minDate, existingAvailability }: CalendarPickerProps) {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [isShiftPressed, setIsShiftPressed] = useState(false);
  const [lastSelectedDate, setLastSelectedDate] = useState<Date | null>(null);

  // Track shift key state
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Shift') setIsShiftPressed(true);
    };
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.key === 'Shift') setIsShiftPressed(false);
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, []);

  // Get all days to display in the calendar grid
  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(monthStart);
  const calendarStart = startOfWeek(monthStart);
  const calendarEnd = endOfWeek(monthEnd);
  const days = eachDayOfInterval({ start: calendarStart, end: calendarEnd });

  // Group days by week
  const weeks: Date[][] = [];
  let currentWeek: Date[] = [];
  days.forEach((day, index) => {
    currentWeek.push(day);
    if (currentWeek.length === 7 || index === days.length - 1) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  });

  const toggleDate = useCallback((date: Date) => {
    const isSelected = selectedDates.some(d => isSameDay(d, date));
    
    if (isShiftPressed && lastSelectedDate && !isSelected) {
      // Shift+click: select range from last selected to current
      const start = lastSelectedDate < date ? lastSelectedDate : date;
      const end = lastSelectedDate < date ? date : lastSelectedDate;
      const rangeDates = eachDayOfInterval({ start, end });
      
      // Merge with existing selected dates, avoiding duplicates
      const newDates = [...selectedDates];
      rangeDates.forEach(d => {
        if (!newDates.some(existing => isSameDay(existing, d))) {
          newDates.push(d);
        }
      });
      onChange(newDates.sort((a, b) => a.getTime() - b.getTime()));
      setLastSelectedDate(date);
    } else if (isSelected) {
      // Remove date
      onChange(selectedDates.filter(d => !isSameDay(d, date)));
      setLastSelectedDate(null);
    } else {
      // Add single date
      onChange([...selectedDates, date].sort((a, b) => a.getTime() - b.getTime()));
      setLastSelectedDate(date);
    }
  }, [isShiftPressed, lastSelectedDate, selectedDates, onChange]);

  // Check if a date is within existing availability ranges
  const isInExistingAvailability = useCallback((date: Date): boolean => {
    if (!existingAvailability || existingAvailability.length === 0) return false;
    
    return existingAvailability.some(range => {
      const startDate = parseISO(range.start_date);
      const endDate = parseISO(range.end_date);
      return isWithinInterval(date, { start: startDate, end: endDate }) ||
             isSameDay(date, startDate) ||
             isSameDay(date, endDate);
    });
  }, [existingAvailability]);

  const nextMonth = () => setCurrentMonth(addMonths(currentMonth, 1));
  const prevMonth = () => setCurrentMonth(subMonths(currentMonth, 1));

  const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div className="w-full">
      {/* Calendar Header */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={prevMonth}
          className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <h3 className="font-semibold text-gray-900">
          {format(currentMonth, 'MMMM yyyy')}
        </h3>
        <button
          onClick={nextMonth}
          className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>

      {/* Week Day Headers */}
      <div className="grid grid-cols-7 gap-1 mb-2">
        {weekDays.map(day => (
          <div key={day} className="text-center text-xs font-medium text-gray-500 py-1">
            {day}
          </div>
        ))}
      </div>

      {/* Calendar Grid */}
      <div className="space-y-1">
        {weeks.map((week, weekIndex) => (
          <div key={weekIndex} className="grid grid-cols-7 gap-1">
            {week.map((day, dayIndex) => {
              const isSelected = selectedDates.some(d => isSameDay(d, day));
              const isCurrentMonth = isSameMonth(day, currentMonth);
              const isDisabled = minDate ? isBefore(day, startOfDay(minDate)) : false;
              
              // Check if this date is in existing availability
              const inExistingAvailability = isInExistingAvailability(day);
              
              // Check if this date is in a sequence
              const prevDay = new Date(day);
              prevDay.setDate(prevDay.getDate() - 1);
              const nextDay = new Date(day);
              nextDay.setDate(nextDay.getDate() + 1);
              
              const isPrevSelected = selectedDates.some(d => isSameDay(d, prevDay));
              const isNextSelected = selectedDates.some(d => isSameDay(d, nextDay));
              
              // Determine border radius based on sequence position
              let borderRadius = 'rounded-lg';
              if (isSelected) {
                if (isPrevSelected && isNextSelected) {
                  borderRadius = 'rounded-none';
                } else if (isPrevSelected) {
                  borderRadius = 'rounded-r-lg rounded-l-none';
                } else if (isNextSelected) {
                  borderRadius = 'rounded-l-lg rounded-r-none';
                }
              }

              return (
                <button
                  key={dayIndex}
                  onClick={() => !isDisabled && toggleDate(day)}
                  disabled={isDisabled}
                  className={cn(
                    'h-9 w-full flex items-center justify-center text-sm transition-all relative',
                    borderRadius,
                    isSelected 
                      ? 'bg-primary-600 text-white font-medium hover:bg-primary-700' 
                      : inExistingAvailability 
                        ? 'bg-green-100 text-green-800 hover:bg-green-200' 
                        : 'hover:bg-gray-100',
                    !isCurrentMonth && !isSelected && !inExistingAvailability && 'text-gray-300',
                    isDisabled && 'opacity-30 cursor-not-allowed',
                    !isSelected && isCurrentMonth && !inExistingAvailability && 'text-gray-700'
                  )}
                  title={inExistingAvailability && !isSelected ? 'Already in availability' : undefined}
                >
                  {format(day, 'd')}
                  {inExistingAvailability && !isSelected && (
                    <span className="absolute bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 bg-green-500 rounded-full" />
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {/* Selected Dates Summary */}
      {selectedDates.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Selected Dates ({selectedDates.length})
            </span>
            <button
              onClick={() => onChange([])}
              className="text-xs text-red-600 hover:text-red-700"
            >
              Clear all
            </button>
          </div>
          <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
            {selectedDates.map((date, index) => (
              <span
                key={index}
                className="inline-flex items-center gap-1 px-2 py-1 bg-primary-50 text-primary-700 text-sm rounded-lg"
              >
                {format(date, 'MMM d, yyyy')}
                <button
                  onClick={() => toggleDate(date)}
                  className="hover:bg-primary-200 rounded p-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Shift hint */}
      <div className="mt-3 text-xs text-gray-500 flex items-center gap-1">
        <span className="font-medium">Tip:</span> Hold Shift and click to select date ranges
      </div>

      {/* Quick Actions */}
      <div className="mt-4 flex gap-2">
        <button
          onClick={() => {
            // Select all Tuesdays in current month
            const days = eachDayOfInterval({
              start: startOfMonth(currentMonth),
              end: endOfMonth(currentMonth)
            });
            const tuesdays = days.filter(d => d.getDay() === 2);
            const newDates = [...selectedDates];
            tuesdays.forEach(tue => {
              if (!selectedDates.some(d => isSameDay(d, tue))) {
                newDates.push(tue);
              }
            });
            onChange(newDates.sort((a, b) => a.getTime() - b.getTime()));
            if (newDates.length > 0) {
              setLastSelectedDate(newDates[newDates.length - 1]);
            }
          }}
          className="px-3 py-1.5 text-xs bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
        >
          + All Tuesdays
        </button>
        <button
          onClick={() => {
            // Select biweekly dates
            const days = eachDayOfInterval({
              start: startOfMonth(currentMonth),
              end: endOfMonth(currentMonth)
            });
            const biweekly = days.filter((_, i) => i % 14 < 7);
            const newDates = [...selectedDates];
            biweekly.forEach(date => {
              if (!selectedDates.some(d => isSameDay(d, date))) {
                newDates.push(date);
              }
            });
            onChange(newDates.sort((a, b) => a.getTime() - b.getTime()));
            if (newDates.length > 0) {
              setLastSelectedDate(newDates[newDates.length - 1]);
            }
          }}
          className="px-3 py-1.5 text-xs bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
        >
          + Biweekly
        </button>
      </div>
    </div>
  );
}
