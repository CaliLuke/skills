---
name: alphatab
description: AlphaTab music notation in JS/TS apps. Use for @coderline/alphatab setup, Vite worker integration, fonts/soundfonts, playback controls, track rendering, AlphaTex, drum notation, and React integration.
---

# AlphaTab Skill

Use this skill when working with AlphaTab music notation library in any project.

## Overview

AlphaTab is a JavaScript/TypeScript library for rendering and playing music notation (Guitar Pro files, AlphaTex). It handles sheet music display, audio synthesis, and playback.

## Critical Setup Requirements

### Vite Plugin (REQUIRED for audio)

Audio playback requires Web Workers. You MUST use the official Vite plugin:

```bash
bun add @coderline/alphatab @coderline/alphatab-vite
```

```typescript
// vite.config.ts
import { alphaTab } from "@coderline/alphatab-vite"; // Named export, NOT default!

export default defineConfig({
  plugins: [
    react(),
    alphaTab(), // Handles Web Workers for audio synthesis
  ],
});
```

**Common mistake**: Using `import alphaTab from` instead of `import { alphaTab } from` - it's a named export.

### Required Assets

Copy to your `public/` folder:

- `/fonts/bravura/` - Music notation font
- `/soundfonts/sonivox.sf2` - Audio samples for playback

## Settings Configuration

```typescript
import { AlphaTabApi, Settings } from "@coderline/alphatab";

const settings = new Settings();

// Core settings
settings.core.fontDirectory = "/fonts/bravura/";
settings.core.enableLazyLoading = true;
settings.core.engine = "svg";

// Display
settings.display.layoutMode = 1; // 0=Page, 1=Horizontal

// Player (audio)
settings.player.enablePlayer = true;
settings.player.enableCursor = true;
settings.player.enableUserInteraction = true; // Built-in selection!
settings.player.enableAnimatedBeatCursor = true;
settings.player.enableElementHighlighting = true;
settings.player.soundFont = "/soundfonts/sonivox.sf2";
settings.player.scrollMode = 1; // 0=Off, 1=Continuous, 2=OffScreen
settings.player.scrollSpeed = 300;

const api = new AlphaTabApi(containerElement, settings);
```

## Required CSS

AlphaTab creates elements with these classes - you MUST style them:

```css
/* Playback cursor - highlights current bar */
.at-cursor-bar {
  background: rgba(255, 242, 0, 0.25);
}

/* Playback cursor - vertical line on current beat */
.at-cursor-beat {
  background: rgba(64, 64, 255, 0.75);
  width: 3px;
}

/* Highlights notes being played */
.at-highlight * {
  fill: #0078ff;
  stroke: #0078ff;
}

/* Selection highlight for loop range (drag to select) */
/* NOTE: .at-selection is a container, the actual highlight is on child divs */
.at-selection div {
  background: rgba(64, 64, 255, 0.1);
}
```

## Loading Content

```typescript
// AlphaTex string
api.tex(alphaTexString);

// GP file (ArrayBuffer)
api.load(new Uint8Array(arrayBuffer));
```

## Event Lifecycle

Events fire in this order:

1. `scoreLoaded` - Score parsed, ready to render
2. `renderStarted` - Rendering begun
3. `renderFinished` - Notation visible
4. `soundFontLoad` - Progress loading audio samples
5. `soundFontLoaded` - Audio samples ready
6. `midiLoaded` - MIDI data generated
7. `playerReady` - **NOW you can call play()**

**Common mistake**: Trying to play before `playerReady` fires.

## Playback Controls

```typescript
api.play();
api.pause();
api.stop();
api.playPause();

// Speed (1.0 = normal)
api.playbackSpeed = 0.5; // Half speed

// Seek to position
api.tickPosition = masterBar.start;

// Looping
api.isLooping = true;
api.playbackRange = {
  startTick: startMasterBar.start,
  endTick: endMasterBar.start + endMasterBar.calculateDuration(),
};
```

## Built-in Selection (Don't reinvent this!)

When `enableUserInteraction: true`, AlphaTab handles selection automatically:

- User can click and drag to select a range
- `.at-selection` CSS class shows the highlight
- Listen to `playbackRangeChanged` event for selection changes

```typescript
api.playbackRangeChanged.on((args) => {
  if (args.playbackRange) {
    // User selected a range
    console.log(args.playbackRange.startTick, args.playbackRange.endTick);
  } else {
    // Selection cleared
  }
});
```

**DO NOT** implement your own selection with beatMouseDown/beatMouseUp - use the built-in one.

## Selection Highlight API (for custom UIs)

```typescript
// Show visual highlight without changing playback range
api.highlightPlaybackRange(startBeat, endBeat);

// Apply the highlight as the actual playback range
api.applyPlaybackRangeFromHighlight();

// Clear highlight
api.clearPlaybackRangeHighlight();
```

## Track Selection

```typescript
// After scoreLoaded, render specific track(s)
api.scoreLoaded.on((score) => {
  const drumTrack = score.tracks.find((t) => t.name === "Drums");
  if (drumTrack) {
    api.renderTracks([drumTrack]);
  }
});

// Get track info
score.tracks.map((t) => ({ name: t.name, index: t.index }));
```

## AlphaTex Drum Notation

For percussion, use articulation names with duration AFTER the note:

```tex
\title "Rock Beat"
\tempo 100
.
\track "Drums"
\instrument percussion
\articulation defaults
(KickHit HiHatClosed).8 HiHatClosed.8 (SnareHit HiHatClosed).8 HiHatClosed.8 |
```

**Common articulations**: `KickHit`, `SnareHit`, `HiHatClosed`, `HiHatOpen`, `CrashCymbal`, `RideCymbal`

**Duration syntax**: `NoteName.duration` where duration is: 1=whole, 2=half, 4=quarter, 8=eighth, 16=sixteenth

**Chords**: `(Note1 Note2).duration`

## React Integration Pattern

```tsx
// Use key prop to force remount when content changes
<AlphaTabPlayer
  key={`file-${fileName}-track-${trackIndex}`}
  fileData={fileData}
  trackIndex={trackIndex}
/>
```

## Debugging

Check these if player doesn't work:

1. Is Vite plugin installed? (check for Web Worker errors)
2. Are fonts loading? (check Network tab for /fonts/bravura/)
3. Is soundfont loading? (check for /soundfonts/\*.sf2)
4. Did `playerReady` fire? (add event listener)
5. Are CSS classes styled? (inspect .at-cursor-bar etc.)

## Common Mistakes

1. **Missing Vite plugin** - Audio won't work without Web Workers
2. **Wrong import** - `{ alphaTab }` not `alphaTab` default
3. **Playing too early** - Wait for `playerReady` event
4. **Missing CSS** - Cursor/selection invisible without styles
5. **Custom selection** - Use built-in `enableUserInteraction` instead
6. **Wrong AlphaTex syntax** - Duration goes AFTER note name for drums
