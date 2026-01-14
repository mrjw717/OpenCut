"use client";

import { cn } from "@/lib/utils";
import { TIMELINE_CONSTANTS } from "@/constants/timeline-constants";

interface TimelineMarkerProps {
  time: number;
  zoomLevel: number;
  interval: number;
  isMainMarker: boolean;
  level?: 1 | 2 | 3;
}

export function TimelineMarker({
  time,
  zoomLevel,
  interval,
  isMainMarker,
  level = 1,
}: TimelineMarkerProps) {
  return (
    <div
      className={cn(
        "absolute top-0 border-l",
        level === 1 && "h-4 border-muted-foreground/60",
        level === 2 && "h-2 border-muted-foreground/40",
        level === 3 && "h-1 border-muted-foreground/20"
      )}
      style={{
        left: `${time * TIMELINE_CONSTANTS.PIXELS_PER_SECOND * zoomLevel}px`,
      }}
    >
      {isMainMarker && (
        <span
          className={cn(
            "absolute top-1 left-1 text-[0.6rem] text-muted-foreground font-medium select-none"
          )}
        >
          {(() => {
            const formatTime = (seconds: number) => {
              const hours = Math.floor(seconds / 3600);
              const minutes = Math.floor((seconds % 3600) / 60);
              const secs = seconds % 60;

              if (hours > 0) {
                return `${hours}:${minutes
                  .toString()
                  .padStart(2, "0")}:${Math.floor(secs)
                  .toString()
                  .padStart(2, "0")}`;
              }
              if (minutes > 0) {
                return `${minutes}:${Math.floor(secs)
                  .toString()
                  .padStart(2, "0")}`;
              }
              if (interval >= 1) {
                return `${Math.floor(secs)}s`;
              }
              // For sub-second accuracy
              return `${secs.toFixed(1)}s`;
            };
            return formatTime(time);
          })()}
        </span>
      )}
    </div>
  );
}
