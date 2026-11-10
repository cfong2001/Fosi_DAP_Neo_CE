import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import type { Theme } from './kit/looks'
import Hero from './hero/Hero'
import Features from './features/Features'

// Mounts the site's Stageshow pictures into docs/index.html: the hero demo
// into #ce-hero-stage and the feature grid's pictures into its
// [data-picture] slots. The stages follow the page's color scheme.

const query = window.matchMedia('(prefers-color-scheme: dark)')
const current = (): Theme => (query.matches ? 'dark' : 'light')

function useTheme() {
  const [theme, setTheme] = useState<Theme>(current)
  useEffect(() => {
    const update = () => setTheme(current())
    query.addEventListener('change', update)
    return () => query.removeEventListener('change', update)
  }, [])
  return theme
}

function HeroRoot() {
  return <Hero theme={useTheme()} />
}

function FeaturesRoot({ root }: { root: HTMLElement }) {
  return <Features theme={useTheme()} root={root} />
}

const hero = document.getElementById('ce-hero-stage')
if (hero) createRoot(hero).render(<StrictMode><HeroRoot /></StrictMode>)

const grid = document.getElementById('features')
if (grid) {
  // The stat's static fallback (for no script) gives way to the counting one.
  grid.querySelector('[data-stat]')?.replaceChildren()
  const host = document.createElement('div')
  host.hidden = true
  grid.append(host)
  createRoot(host).render(<StrictMode><FeaturesRoot root={grid} /></StrictMode>)
}
