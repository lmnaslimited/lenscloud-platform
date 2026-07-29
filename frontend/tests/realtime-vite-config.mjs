import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const config = readFileSync(new URL('../vite.config.js', import.meta.url), 'utf8')
const packageJson = JSON.parse(
	readFileSync(new URL('../package.json', import.meta.url), 'utf8'),
)

assert.match(config, /frappeProxy:\s*true/, 'frappe-ui must own proxying')
assert.match(
	config,
	/optimizeDeps:[\s\S]*include:\s*\[['"]feather-icons['"]\]/,
	'feather-icons must be prebundled',
)
assert.doesNotMatch(config, /server:\s*\{[\s\S]*proxy:/, 'manual proxies conflict')
assert.match(packageJson.scripts.dev, /--host\s+0\.0\.0\.0/, 'Vite must be exposed')

console.log('Vite realtime configuration checks passed')
