import { chromium } from 'playwright'
import { readFileSync } from 'node:fs'

const baseURL = process.env.LENSCLOUD_BASE_URL || 'http://dev.localhost:8000'
const credentials = JSON.parse(readFileSync(process.env.LENSCLOUD_CREDENTIAL_FILE, 'utf8'))
const site = process.env.LENSCLOUD_BENCH_COMMAND_SITE || 'run-20260629-free-prod-site.cloud.lmnaslens.com'

function escapeRegExp(value) {
	return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

async function login(context) {
	const page = await context.newPage()
	await page.goto(`${baseURL}/login`)
	await page.locator('#login_email').fill(credentials.platform_user)
	await page.locator('#login_password').fill(credentials.platform_password)
	await page.locator('button.btn-login').click()
	await page.waitForFunction(() => !location.pathname.startsWith('/login'))
	await page.close()
}

async function selectCommand(page, command) {
	await page.getByLabel('Command').click()
	await page.getByRole('option', { name: command, exact: true }).click()
}

const browser = await chromium.launch({ headless: true })
const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } })
await login(context)
const page = await context.newPage()
const errors = []
page.on('pageerror', (error) => errors.push(error.message))
page.on('console', (message) => { if (message.type() === 'error' && !message.text().startsWith('Failed to load resource:')) errors.push(message.text()) })

try {
	await page.goto(`${baseURL}/lenscloud/platform/sites/${encodeURIComponent(site)}`)
	await page.getByText(new RegExp(`Editing Site: ${escapeRegExp(site)}`)).waitFor({ timeout: 20000 })
	await page.getByRole('tab', { name: /Actions/ }).click()
	await page.getByRole('button', { name: 'Run Site Control command', exact: true }).click()

	await selectCommand(page, 'backup.status')
	await page.getByLabel('Args JSON').fill('{}')
	await page.getByLabel('Timeout seconds').fill('120')
	await page.getByLabel('Reason').fill('Authenticated UI verification of backup.status display contract')
	await page.getByRole('button', { name: 'Run action', exact: true }).click()
	const resultCard = page.locator('.bg-emerald-50').filter({ hasText: 'Bench Command result' })
	await resultCard.waitFor({ timeout: 180000 })
	await resultCard.getByText('Backups:', { exact: true }).waitFor()
	await resultCard.getByText(/available/).waitFor()
	if (await resultCard.getByText(/password|secret|token|private key|dump/i).count()) throw new Error('Secret-like text appeared in backup.status result card.')

	await selectCommand(page, 'backup.create')
	await page.getByLabel('Args JSON').fill('{}')
	await page.getByLabel('Reason').fill('Authenticated UI verification that backup.create remains unsupported')
	await page.getByRole('button', { name: 'Run action', exact: true }).click()
	await page.getByText('Unsupported', { exact: false }).waitFor({ timeout: 60000 })
	if (await page.locator('.bg-emerald-50').filter({ hasText: 'Bench Command result' }).count()) throw new Error('Unsupported backup.create displayed a successful Bench Command result card.')
	if (errors.length) throw new Error(`Backup status display browser errors: ${errors.join('; ')}`)
	console.log(`Authenticated backup.status display and backup.create unsupported checks passed for ${site}.`)
} finally {
	await context.close()
	await browser.close()
}
