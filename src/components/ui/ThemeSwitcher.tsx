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
    <div className="flex items-center gap-1 rounded-lg bg-white/5 p-1">
      {themes.map(({ mode, icon: Icon, label }) => (
        <button
          key={mode}
          onClick={() => setTheme(mode)}
          title={label}
          className={cn(
            "flex h-7 w-7 items-center justify-center rounded-md transition-colors",
            theme === mode
              ? "bg-white/15 text-white"
              : "text-gray-400 hover:text-white hover:bg-white/10"
          )}
        >
          <Icon className="h-4 w-4" />
        </button>
      ))}
    </div>
  );
}
