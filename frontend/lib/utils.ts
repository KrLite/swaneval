import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Parse a timestamp string as UTC.
 * Backend sends naive UTC timestamps without 'Z' suffix —
 * JS would misinterpret them as local time. This ensures UTC.
 */
export function utc(ts: string | null | undefined): Date | null {
  if (!ts) return null;
  // If already has timezone info, parse directly
  if (ts.endsWith("Z") || /[+-]\d{2}:\d{2}$/.test(ts)) return new Date(ts);
  // Treat naive timestamp as UTC
  return new Date(ts + "Z");
}
