"use client";

import { Moon, Monitor, Sun } from "lucide-react";
import { useTheme } from "@/providers/ThemeProvider";
import { cn } from "@/lib/utils";
import type { ThemeMode } from "@/types";

const themes: { mode: ThemeMode; icon: typeof Moon; label: string }[] = [
  { mode: "dark", icon: Moon, label: "深色" },
  { mode: "system", icon: Monitor, label: "跟随系统" },
  { mode: "light", icon: Sun, label: "浅色" },
];

export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="theme-toggle" role="radiogroup" aria-label="主题">
      {themes.map(({ mode, icon: Icon, label }) => (
        <button
          key={mode}
          type="button"
          onClick={() => setTheme(mode)}
          title={label}
          role="radio"
          aria-checked={theme === mode}
          className={cn(
            "theme-toggle-option",
            theme === mode && "theme-toggle-option-active"
          )}
        >
          <Icon className="h-4 w-4" />
        </button>
      ))}
    </div>
  );
}
