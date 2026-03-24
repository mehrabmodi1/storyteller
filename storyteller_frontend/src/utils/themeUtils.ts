/**
 * Shared theme utilities for graph node components.
 */

export function getRingClass(themeRing?: string | null, fallback = 'ring-amber-500'): string {
  if (!themeRing) return fallback;
  return themeRing.replace('focus:', '');
}
