export const DICE_OVERLAY_MS = 2500;
export const DICE_SETTLE_START = 0.6;
export const DICE_SETTLE_DURATION = 0.9;

// Presentation follows real time, not the capped delta used by the physics solver.
export function diceElapsedSeconds(startedAt: number, currentFrame: number) {
  return Math.max(0, (currentFrame - startedAt) / 1000);
}
