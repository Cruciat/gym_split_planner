/**
 * Insieme chiuso dei simboli delle etichette (wireframe, § 4.4; modello dati, § 3.9).
 * Il valore di `tag.symbol` è il nome di un'icona di Lucide: il PDF usa lo stesso
 * nome per il file SVG in `backend/.../pdf/icons/`.
 */

import { Ban, EyeOff, Flag, Heart, Info, Star, TriangleAlert, Zap } from 'lucide-vue-next'
import type { Component } from 'vue'

import type { TagColor } from '@/api/client'
import { texts } from '@/texts'

export const SYMBOLS = {
  warning: TriangleAlert,
  ban: Ban,
  info: Info,
  star: Star,
  heart: Heart,
  zap: Zap,
  flag: Flag,
  'eye-off': EyeOff,
} as const satisfies Record<keyof typeof texts.symbols, Component>

export type SymbolName = keyof typeof SYMBOLS

export function isSymbol(name: string): name is SymbolName {
  return Object.hasOwn(SYMBOLS, name)
}

/** Icona di un simbolo; un nome sconosciuto (dati vecchi) mostra l'icona informazione. */
export function symbolIcon(name: string): Component {
  return isSymbol(name) ? SYMBOLS[name] : SYMBOLS.info
}

/** Variabili di colore del tema di Naive UI per i colori semantici delle etichette. */
export const COLOR_VARS = {
  neutral: 'textColor3',
  info: 'infoColor',
  success: 'successColor',
  warning: 'warningColor',
  danger: 'errorColor',
} as const satisfies Record<TagColor, string>
