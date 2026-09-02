/** Store four preference codes and their policy version in localStorage. */

import { useCallback, useEffect, useState } from "react";

import type { Profile } from "../api/types";

export const STORAGE_KEY = "democraseek.profile.v2";
const LEGACY_STORAGE_KEYS = ["democraseek.profile.v1"] as const;

function isProfile(value: unknown): value is Profile {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.role_code === "string" &&
    typeof candidate.intent_code === "string" &&
    typeof candidate.support_code === "string" &&
    typeof candidate.mode_code === "string" &&
    typeof candidate.policy_version === "string"
  );
}

function readStoredProfile(): Profile | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    return isProfile(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

export function useProfile(): {
  profile: Profile | null;
  saveProfile: (profile: Profile) => void;
  resetProfile: () => void;
} {
  const [profile, setProfile] = useState<Profile | null>(() => readStoredProfile());

  useEffect(() => {
    // Remove the incompatible v1 Barrier/B-code profile.
    try {
      for (const key of LEGACY_STORAGE_KEYS) window.localStorage.removeItem(key);
    } catch {
      /* storage may be unavailable; no migration is required for this session */
    }
  }, []);

  useEffect(() => {
    try {
      if (profile) {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
      } else {
        window.localStorage.removeItem(STORAGE_KEY);
      }
    } catch {
      /* storage may be unavailable (private mode); the session still works */
    }
  }, [profile]);

  const saveProfile = useCallback((next: Profile) => setProfile(next), []);
  const resetProfile = useCallback(() => setProfile(null), []);

  return { profile, saveProfile, resetProfile };
}
