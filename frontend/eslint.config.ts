import skipFormatting from '@vue/eslint-config-prettier/skip-formatting'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import pluginVue from 'eslint-plugin-vue'

export default defineConfigWithVueTs(
  {
    name: 'app/files',
    files: ['**/*.{ts,mts,vue}'],
  },
  {
    name: 'app/ignores',
    ignores: [
      'dist/**',
      'coverage/**',
      'test-results/**',
      'playwright-report/**',
      'src/api/schema.d.ts',
    ],
  },
  pluginVue.configs['flat/recommended'],
  vueTsConfigs.strictTypeChecked,
  skipFormatting,
)
