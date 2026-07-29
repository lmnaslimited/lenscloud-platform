import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const [siteName, ...portArguments] = process.argv.slice(2)
const requiredPorts = portArguments.map(Number)

assert(siteName, 'site name argument is required')
assert(
	requiredPorts.length === 3 && requiredPorts.every(Number.isInteger),
	'web, Vite, and Socket.IO ports are required',
)

const devcontainer = JSON.parse(
	readFileSync(new URL('../../.devcontainer/devcontainer.json', import.meta.url)),
)
const forwarded = new Set(devcontainer.forwardPorts || [])
const missingPorts = requiredPorts.filter((port) => !forwarded.has(port))
assert.equal(
	missingPorts.length,
	0,
	`.devcontainer/devcontainer.json must forward ports: ${missingPorts.join(', ')}`,
)

const compose = readFileSync(
	new URL('../../.devcontainer/docker-compose.yml', import.meta.url),
	'utf8',
)
const escapedSite = siteName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
assert.match(
	compose,
	new RegExp(`["']?${escapedSite}:127\\.0\\.0\\.1["']?`),
	`.devcontainer/docker-compose.yml must persist extra_hosts entry "${siteName}:127.0.0.1"; rebuild the container after adding it`,
)

console.log(
	`Devcontainer forwards ${requiredPorts.join('/')} and persists ${siteName}`,
)
