const anyWindow = window as any;

/**
 * Simple heuristic for detecting if user is *probably* using a Mac computer.
 * https://stackoverflow.com/a/11752084
 */
export function isMac(): boolean {
  return anyWindow['navigator']['platform'].includes('Mac');
}

/**
 * Detects if user is using ChromeOS.
 */
export function isChromeOS(): boolean {
  return anyWindow['navigator']['userAgent'].includes('CrOS');
}
