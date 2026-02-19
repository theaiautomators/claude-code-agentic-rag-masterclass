import { useTheme } from "@/hooks/useTheme"
import type { Theme } from "@/contexts/ThemeContext"
import { Check } from "lucide-react"

interface ThemeOption {
  id: Theme
  name: string
  description: string
  colors: {
    bg: string
    sidebar: string
    primary: string
    accent: string
    text: string
  }
}

const themes: ThemeOption[] = [
  {
    id: "light",
    name: "Light",
    description: "Clean and bright",
    colors: {
      bg: "#ffffff",
      sidebar: "#f5f5f5",
      primary: "#1a1a1a",
      accent: "#f5f5f5",
      text: "#1a1a1a",
    },
  },
  {
    id: "dark",
    name: "Dark",
    description: "Easy on the eyes",
    colors: {
      bg: "#1a1a1a",
      sidebar: "#262626",
      primary: "#e5e5e5",
      accent: "#333333",
      text: "#e5e5e5",
    },
  },
  {
    id: "ocean",
    name: "Ocean",
    description: "Deep & sophisticated",
    colors: {
      bg: "#0f1a2e",
      sidebar: "#142240",
      primary: "#38bdf8",
      accent: "#1e3a5f",
      text: "#c8e0f4",
    },
  },
  {
    id: "sunset",
    name: "Sunset",
    description: "Warm & bold",
    colors: {
      bg: "#1c1210",
      sidebar: "#261a16",
      primary: "#f59e0b",
      accent: "#3d2518",
      text: "#f0d9c0",
    },
  },
]

export function SettingsPage() {
  const { theme, setTheme } = useTheme()

  return (
    <div className="mx-auto max-w-2xl p-8">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Customize your experience
      </p>

      <div className="mt-8">
        <h2 className="text-lg font-medium">Theme</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Choose a color scheme for the interface
        </p>

        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {themes.map((t) => {
            const isActive = theme === t.id
            return (
              <button
                key={t.id}
                onClick={() => setTheme(t.id)}
                className={`group relative overflow-hidden rounded-xl border-2 transition-all hover:scale-[1.02] ${
                  isActive
                    ? "border-primary ring-2 ring-primary/30"
                    : "border-border hover:border-muted-foreground/40"
                }`}
              >
                {/* Theme preview tile */}
                <div
                  className="flex h-28 flex-col"
                  style={{ backgroundColor: t.colors.bg }}
                >
                  {/* Mini sidebar + content preview */}
                  <div className="flex flex-1">
                    <div
                      className="w-1/3 border-r"
                      style={{
                        backgroundColor: t.colors.sidebar,
                        borderColor: t.colors.accent,
                      }}
                    >
                      {/* Mini thread items */}
                      <div className="space-y-1 p-1.5 pt-2">
                        <div
                          className="h-1.5 w-full rounded-sm"
                          style={{ backgroundColor: t.colors.accent }}
                        />
                        <div
                          className="h-1.5 w-3/4 rounded-sm"
                          style={{ backgroundColor: t.colors.primary, opacity: 0.7 }}
                        />
                        <div
                          className="h-1.5 w-full rounded-sm"
                          style={{ backgroundColor: t.colors.accent }}
                        />
                      </div>
                    </div>
                    <div className="flex flex-1 flex-col justify-end p-2">
                      {/* Mini message bubbles */}
                      <div className="space-y-1">
                        <div
                          className="ml-auto h-2 w-3/4 rounded"
                          style={{ backgroundColor: t.colors.primary, opacity: 0.3 }}
                        />
                        <div
                          className="h-2 w-2/3 rounded"
                          style={{ backgroundColor: t.colors.accent }}
                        />
                      </div>
                      {/* Mini input bar */}
                      <div
                        className="mt-2 h-3 w-full rounded"
                        style={{
                          backgroundColor: t.colors.accent,
                          border: `1px solid ${t.colors.primary}30`,
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* Label area */}
                <div className="border-t bg-card px-3 py-2 text-left">
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm font-medium">{t.name}</span>
                    {isActive && (
                      <Check className="h-3.5 w-3.5 text-primary" />
                    )}
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {t.description}
                  </span>
                </div>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
