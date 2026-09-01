/**
 * Theme switch: light, dark, or follow the system.
 *
 * A radio group rather than a cycling button, so the current state is visible
 * without clicking and "system" stays reachable in one step.
 */

import type { ThemeChoice } from "../hooks/useTheme";
import { useUi } from "../i18n";

interface Props {
  theme: ThemeChoice;
  onChange: (choice: ThemeChoice) => void;
}

const OPTIONS: { value: ThemeChoice; icon: JSX.Element }[] = [
  {
    value: "light",
    icon: (
      <>
        <circle cx="8" cy="8" r="3.2" />
        <path d="M8 1v1.8M8 13.2V15M1 8h1.8M13.2 8H15M3.1 3.1l1.3 1.3M11.6 11.6l1.3 1.3M12.9 3.1l-1.3 1.3M4.4 11.6l-1.3 1.3" />
      </>
    ),
  },
  {
    value: "system",
    icon: (
      <>
        <rect x="1.6" y="2.6" width="12.8" height="9" rx="1.4" />
        <path d="M5.5 13.8h5" />
      </>
    ),
  },
  {
    value: "dark",
    icon: <path d="M13 9.4A5.6 5.6 0 0 1 6.6 3a5.8 5.8 0 1 0 6.4 6.4Z" />,
  },
];

export function ThemeToggle({ theme, onChange }: Props): JSX.Element {
  const { ui } = useUi();
  const labels: Record<ThemeChoice, string> = {
    light: ui.theme.light,
    system: ui.theme.system,
    dark: ui.theme.dark,
  };
  return (
    <div className="theme-toggle" role="radiogroup" aria-label={ui.theme.group}>
      {OPTIONS.map((option) => {
        const label = labels[option.value];
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={theme === option.value}
            aria-label={`${label} ${ui.theme.suffix}`}
            title={`${label} ${ui.theme.suffix}`}
            className={
              theme === option.value ? "theme-toggle__item is-active" : "theme-toggle__item"
            }
            onClick={() => onChange(option.value)}
          >
            <svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">
              {option.icon}
            </svg>
          </button>
        );
      })}
    </div>
  );
}
