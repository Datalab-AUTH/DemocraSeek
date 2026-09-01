/**
 * Branding is configuration, not code.
 *
 * Final INNOVADE/DemocraSeek logos and colours were not available at build
 * time. Every value here is overridable through Vite environment variables, so
 * dropping in the real assets is a configuration change, not a code change.
 */

export interface Branding {
  appName: string;
  projectName: string;
  tagline: string;
  logoUrl: string | null;
  accentColour: string | null;
}

const env = import.meta.env as unknown as Record<string, string | undefined>;

export const branding: Branding = {
  appName: env.VITE_APP_NAME ?? "DemocraSeek",
  projectName: env.VITE_PROJECT_NAME ?? "INNOVADE",
  tagline:
    env.VITE_APP_TAGLINE ??
    "Explore the approved knowledge base.",
  logoUrl: env.VITE_LOGO_URL ?? null,
  accentColour: env.VITE_ACCENT_COLOUR ?? null,
};
