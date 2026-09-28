"use client";

import { useSyncExternalStore } from "react";

const noopSubscribe = () => () => {};

/** A value that only exists in the browser (false/default during SSR and hydration). */
export function useBrowserValue<T>(read: () => T, serverValue: T): T {
  return useSyncExternalStore(noopSubscribe, read, () => serverValue);
}

/** localStorage-backed string with change notifications inside the tab. */
export function createLocalStore(key: string, fallback: string) {
  const listeners = new Set<() => void>();
  const read = () => {
    try {
      return localStorage.getItem(key) ?? fallback;
    } catch {
      return fallback;
    }
  };
  const subscribe = (callback: () => void) => {
    listeners.add(callback);
    window.addEventListener("storage", callback);
    return () => {
      listeners.delete(callback);
      window.removeEventListener("storage", callback);
    };
  };
  const write = (value: string) => {
    try {
      localStorage.setItem(key, value);
    } catch {
      // storage unavailable
    }
    listeners.forEach((listener) => listener());
  };
  const useValue = () => useSyncExternalStore(subscribe, read, () => fallback);
  return { useValue, write };
}

/** Tracks the `dark` class on <html>. */
export function useDarkMode(): boolean {
  return useSyncExternalStore(
    (callback) => {
      const observer = new MutationObserver(callback);
      observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
      return () => observer.disconnect();
    },
    () => document.documentElement.classList.contains("dark"),
    () => false,
  );
}
