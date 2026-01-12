"use client";

import { useTimelineStore } from "@/stores/timeline-store";
import { TimelineTrack, TimelineElement as TimelineElementType } from "@/types/timeline";
import { TIMELINE_CONSTANTS, getTrackElementClasses } from "@/constants/timeline-constants";
import { useMediaStore } from "@/stores/media-store";

interface GhostTrackProps {
  track: TimelineTrack;
  zoomLevel: number;
  isTarget: boolean; // Is the mouse currently over this track?
}

export function GhostTrack({ track, zoomLevel, isTarget }: GhostTrackProps) {
  const { dragState, rippleEditingEnabled } = useTimelineStore();
  const { mediaFiles } = useMediaStore();

  if (!dragState.isDragging || !rippleEditingEnabled) return null;

  // We only show ghosts if we are affecting this track
  const isSource = track.id === dragState.trackId;

  if (!isSource && !isTarget) return null;

  // Get the element being dragged
  // We need to know its duration to calculate shifts
  // But we can't easily get the element object from just ID if it's not in this track
  // We can find it in the global store tracks, but we only have `track` prop here.
  // We can assume the parent passes us the duration or we find it.
  // Let's rely on finding it in the store via hook.

  const draggedElementId = dragState.elementId;
  if (!draggedElementId) return null;

  // Find the dragged element details from the store
  const { tracks } = useTimelineStore.getState();
  const sourceTrack = tracks.find(t => t.id === dragState.trackId);
  const draggedElement = sourceTrack?.elements.find(e => e.id === draggedElementId);

  if (!draggedElement) return null;

  const elementDuration = draggedElement.duration - draggedElement.trimStart - draggedElement.trimEnd;
  const elementEndTime = draggedElement.startTime + elementDuration;

  let simulatedElements: TimelineElementType[] = [...track.elements];

  // 1. Simulate Source Removal & Ripple
  if (isSource && !dragState.isCopying) {
     // Remove dragged element
     simulatedElements = simulatedElements.filter(e => e.id !== draggedElementId);

     // Ripple Close (only if ripple enabled)
     if (rippleEditingEnabled) {
         simulatedElements = simulatedElements.map(e => {
            if (e.startTime >= elementEndTime) {
                 return {
                     ...e,
                     startTime: Math.max(0, e.startTime - elementDuration)
                 };
            }
            return e;
         });
     }
  }

  // 2. Simulate Target Insertion & Ripple
  if (isTarget) {
     // If we are moving within the same track, we already removed it in step 1.
     // Now we insert it at the current drag time.

     const insertTime = dragState.currentTime;

     // Shift elements right to make space
     // Logic: Elements starting after insertTime shift right
     // Or elements overlapping insertTime shift right?
     // Ripple Insert usually shifts everything at or after the insert point.

     simulatedElements = simulatedElements.map(e => {
         // Check if this element needs to shift
         // If it starts after insertion point, shift it.
         // Note: If isSource, we strictly use the *adjusted* positions from step 1 for this check?
         // This gets complex. Moving within same track with ripple:
         // 1. Remove (close gap). 2. Insert (open gap).

         if (e.startTime >= insertTime) {
             return {
                 ...e,
                 startTime: e.startTime + elementDuration
             };
         }
         return e;
     });

     // We don't need to render the ghost of the dragged element itself here,
     // because the user is dragging it (it follows mouse).
     // But we CAN render it to show where it will snap.
     // Let's add it to simulatedElements for visualization.

     const ghostElement = {
         ...draggedElement,
         id: "ghost-dragged",
         startTime: insertTime,
         trackId: track.id
     };
     simulatedElements.push(ghostElement as TimelineElementType);
  }

  return (
    <div className="absolute inset-0 pointer-events-none z-0">
      {simulatedElements.map(element => {
         // Skip if it's the real dragged element (though we filtered it out in source)
         if (element.id === draggedElementId && !isTarget) return null;

         // Only render if position CHANGED from real element?
         // Or just render all as faint background?
         // Render all as faint background is easier to understand "this is the new state".

         const elementLeft = element.startTime * TIMELINE_CONSTANTS.PIXELS_PER_SECOND * zoomLevel;
         const elementWidth = (element.duration - element.trimStart - element.trimEnd) * TIMELINE_CONSTANTS.PIXELS_PER_SECOND * zoomLevel;

         // Determine color based on track type
         // use getTrackElementClasses but override opacity
         const baseClasses = getTrackElementClasses(track.type);
         // Strip bg color and use our own? Or use opacity.

         return (
            <div
                key={`ghost-${element.id}`}
                className={`absolute top-1 bottom-1 rounded-md border-2 border-dashed border-primary/50 bg-background/50 backdrop-blur-[1px]`}
                style={{
                    left: `${elementLeft}px`,
                    width: `${elementWidth}px`,
                    transition: "all 0.2s ease-out"
                }}
            >
                {/* Minimal Content */}
                <div className="w-full h-full flex items-center justify-center overflow-hidden opacity-50">
                    <span className="text-[10px] truncate px-1">{element.name}</span>
                </div>
            </div>
         );
      })}
    </div>
  );
}
