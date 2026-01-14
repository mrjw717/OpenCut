import { describe, it, expect, beforeEach, afterEach, mock } from "bun:test";
import { useTimelineStore } from "./timeline-store";
import { useProjectStore } from "./project-store";
import { useSceneStore } from "./scene-store";

// Mock storage service to avoid side effects
mock.module("@/lib/storage/storage-service", () => ({
  storageService: {
    saveTimeline: mock(() => Promise.resolve()),
    loadTimeline: mock(() => Promise.resolve([])),
  },
}));

describe("TimelineStore Ripple Logic", () => {
  beforeEach(() => {
    useTimelineStore.setState({
      _tracks: [],
      tracks: [],
      rippleEditingEnabled: false,
    });
  });

  it("should close gap on source track when moving element with ripple enabled", () => {
    const store = useTimelineStore.getState();

    // Create Track 1
    const track1Id = store.addTrack("media");

    // Add Element 1 (0-5s)
    const el1 = {
      type: "media" as const,
      mediaId: "test1",
      name: "Clip 1",
      duration: 5,
      startTime: 0,
      trimStart: 0,
      trimEnd: 0,
    };
    store.addElementToTrack(track1Id, el1);

    // Add Element 2 (5-10s)
    const el2 = {
      type: "media" as const,
      mediaId: "test2",
      name: "Clip 2",
      duration: 5,
      startTime: 5,
      trimStart: 0,
      trimEnd: 0,
    };
    store.addElementToTrack(track1Id, el2);

    // Verify initial state
    let tracks = useTimelineStore.getState().tracks;
    let t1 = tracks.find(t => t.id === track1Id)!;
    expect(t1.elements.length).toBe(2);
    expect(t1.elements[1].startTime).toBe(5);

    // Create Track 2
    const track2Id = store.addTrack("media");

    // Enable Ripple
    useTimelineStore.setState({ rippleEditingEnabled: true });

    // Move Clip 1 to Track 2
    const clip1Id = t1.elements[0].id;
    store.moveElementToTrack(track1Id, track2Id, clip1Id);

    // Verify result
    tracks = useTimelineStore.getState().tracks;
    t1 = tracks.find(t => t.id === track1Id)!;
    const t2 = tracks.find(t => t.id === track2Id)!;

    // Track 1 should have Clip 2 shifted to 0
    expect(t1.elements.length).toBe(1);
    expect(t1.elements[0].startTime).toBe(0); // Ripple worked!

    // Track 2 should have Clip 1
    expect(t2.elements.length).toBe(1);
    expect(t2.elements[0].id).toBe(clip1Id);
  });

  it("should NOT close gap on source track when ripple is disabled", () => {
    const store = useTimelineStore.getState();
    const track1Id = store.addTrack("media");

    store.addElementToTrack(track1Id, {
      type: "media",
      mediaId: "test1",
      name: "Clip 1",
      duration: 5,
      startTime: 0,
      trimStart: 0,
      trimEnd: 0,
    });

    store.addElementToTrack(track1Id, {
      type: "media",
      mediaId: "test2",
      name: "Clip 2",
      duration: 5,
      startTime: 5,
      trimStart: 0,
      trimEnd: 0,
    });

    const track2Id = store.addTrack("media");

    // Ripple Disabled (default)
    expect(store.rippleEditingEnabled).toBe(false);

    const tracks = useTimelineStore.getState().tracks;
    const t1 = tracks.find(t => t.id === track1Id)!;
    const clip1Id = t1.elements[0].id;

    store.moveElementToTrack(track1Id, track2Id, clip1Id);

    const updatedTracks = useTimelineStore.getState().tracks;
    const updatedT1 = updatedTracks.find(t => t.id === track1Id)!;

    expect(updatedT1.elements.length).toBe(1);
    expect(updatedT1.elements[0].startTime).toBe(5); // No shift
  });
});
