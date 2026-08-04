import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const config = readFileSync(new URL('../vite.config.js', import.meta.url), 'utf8')
const main = readFileSync(new URL('../src/main.js', import.meta.url), 'utf8')
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

assert.match(main, /app\.use\(FrappeUI,\s*\{\s*socketio:\s*false\s*\}\)/, 'frappe-ui implicit socket must be disabled')
assert.equal((main.match(/initSocket\(\)/g) || []).length, 1, 'LensCloud must initialize exactly one socket')

console.log('Vite realtime configuration checks passed')
