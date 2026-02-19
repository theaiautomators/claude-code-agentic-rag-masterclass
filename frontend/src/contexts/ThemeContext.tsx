import { createContext, useEffect, useState, type ReactNode } from "react"

export type Theme = "light" | "dark" | "ocean" | "sunset"

interface ThemeContextType {
  theme: Theme
  setTheme: (theme: Theme) => void
}

export const ThemeContext = createContext<ThemeContextType | null>(null)

const STORAGE_KEY = "app-theme"

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored && ["light", "dark", "ocean", "sunset"].includes(stored)) {
      return stored as Theme
    }
    return "light"
  })

  useEffect(() => {
    const root = document.documentElement
    root.classList.remove("dark", "ocean", "sunset")

    if (theme === "dark") {
      root.classList.add("dark")
    } else if (theme === "ocean") {
      root.classList.add("dark", "ocean")
    } else if (theme === "sunset") {
      root.classList.add("dark", "sunset")
    }

    localStorage.setItem(STORAGE_KEY, theme)
  }, [theme])

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme)
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}
