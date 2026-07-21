import { chromium } from 'playwright'
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

const baseURL = process.env.LENSCLOUD_BASE_URL || 'http://dev.localhost:8000'
const credentialFile = process.env.LENSCLOUD_CREDENTIAL_FILE
if (!credentialFile) throw new Error('LENSCLOUD_CREDENTIAL_FILE is required.')
const credentials = JSON.parse(readFileSync(credentialFile, 'utf8'))
const user = credentials.customer_user || credentials.LENSCLOUD_CUSTOMER_USER
const password = credentials.customer_password || credentials.LENSCLOUD_CUSTOMER_PASSWORD
if (user !== 'iron_monkey_private@example.com') throw new Error(`Unexpected acceptance customer: ${user || 'missing'}`)

const runId = `iron-monkey-${new Date().toISOString().replace(/\D/g, '').slice(4, 14)}`
const outputDir = resolve(process.cwd(), '../docs/evidence/customer-launch/provisioning-under5-20260721')
mkdirSync(outputDir, { recursive: true })

async function login(page) {
	await page.goto(`${baseURL}/login`)
	await page.locator('#login_email').fill(user)
	await page.locator('#login_password').fill(password)
	await page.locator('button.btn-login').click()
	await page.waitForFunction(() => !window.location.pathname.startsWith('/login'))
}

async function fillSetupDefaults(page) {
	const form = page.locator('form').filter({ hasText: 'Setup defaults' })
	if (!(await form.isVisible().catch(() => false))) return
	for (let pass = 0; pass < 3; pass += 1) {
		const selects = form.locator('select')
		for (let index = 0; index < await selects.count(); index += 1) {
			const select = selects.nth(index)
			if (!(await select.inputValue())) {
				const options = await select.locator('option').evaluateAll((rows) => rows.map((row) => row.value).filter(Boolean))
				if (options.length) await select.selectOption(options[0])
			}
		}
		await page.waitForTimeout(500)
		const inputs = form.locator('input[required]')
		for (let index = 0; index < await inputs.count(); index += 1) {
			const input = inputs.nth(index)
			if (await input.inputValue()) continue
			const label = (await input.locator('xpath=ancestor::label[1]').innerText().catch(() => '')).toLowerCase()
			let value = 'Iron Monkey Private'
			if (label.includes('date')) value = '2026-04-01'
			else if (label.includes('email')) value = user
			else if (label.includes('name')) value = 'Iron Monkey'
			await input.fill(value)
		}
	}
	const save = form.getByRole('button', { name: 'Save defaults' })
	await save.waitFor()
	if (await save.isDisabled()) throw new Error('Setup defaults remained incomplete.')
	await save.click()
	await form.waitFor({ state: 'hidden' })
}

async function progressSnapshot(page, site) {
	return page.evaluate(async (siteName) => {
		const query = new URLSearchParams({ site: siteName })
		const response = await fetch(`/api/method/lenscloud.api.provisioning_progress.get_customer_site_progress?${query}`)
		const body = await response.json()
		if (!response.ok || body.exc) throw new Error(body.message || body.exc || `Progress HTTP ${response.status}`)
		return body.message
	}, site)
}

const browser = await chromium.launch({ headless: true })
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } })
const page = await context.newPage()
const browserErrors = []
const network = []
page.on('pageerror', (error) => browserErrors.push(error.message))
page.on('console', (message) => {
	if (message.type() === 'error' && !message.text().startsWith('Failed to load resource:')) browserErrors.push(message.text())
})
page.on('response', (response) => {
	const path = new URL(response.url()).pathname
	if (path.includes('provisioning_progress')) network.push({ at: Date.now(), path, status: response.status() })
})

try {
	await login(page)
	await page.goto(`${baseURL}/lenscloud/customer/plans`)
	await page.getByRole('heading', { name: 'Plans', exact: true }).waitFor()
	const startFree = page.getByRole('button', { name: 'Start Free Plan' })
	await startFree.waitFor()
	await startFree.click()
	await page.getByRole('heading', { name: 'Setup Your Site', exact: true }).waitFor()
	const setupForm = page.locator('form').filter({ hasText: 'Setup defaults' })
	if (!(await setupForm.isVisible().catch(() => false))) {
		const defaultsButton = page.getByRole('button', { name: /Complete setup defaults|Edit setup defaults/ })
		await defaultsButton.waitFor()
		await defaultsButton.click()
		await setupForm.waitFor()
	}
	await fillSetupDefaults(page)
	await page.getByRole('textbox', { name: 'Subdomain' }).fill(runId)
	await page.getByRole('textbox', { name: 'Site Name' }).fill(`Iron Monkey ${runId}`)
	await page.getByRole('button', { name: 'Continue to Review' }).click()
	await page.getByRole('heading', { name: 'Review Subscription', exact: true }).waitFor()
	const submit = page.getByRole('button', { name: 'Start Free Subscription' })
	await submit.waitFor()
	const startedAt = Date.now()
	await submit.click()
	await page.waitForURL(/site=/, { timeout: 30000 })
	const site = new URL(page.url()).searchParams.get('site')
	if (!site) throw new Error('Provisioning route did not include the Site.')

	const transitions = []
	let lastStage = ''
	let refreshEvidence = null
	let finalSnapshot = null
	while (Date.now() - startedAt < 300000) {
		const snapshot = await progressSnapshot(page, site)
		finalSnapshot = snapshot
		if (snapshot.stage !== lastStage) {
			transitions.push({ elapsed_ms: Date.now() - startedAt, ...snapshot })
			lastStage = snapshot.stage
		}
		if (!refreshEvidence && transitions.length >= 2 && !['ready', 'failed'].includes(snapshot.stage)) {
			const before = snapshot.stage
			await page.reload()
			await page.getByRole('heading', { name: 'Plans', exact: true }).waitFor()
			const afterSnapshot = await progressSnapshot(page, site)
			refreshEvidence = { elapsed_ms: Date.now() - startedAt, before, after: afterSnapshot.stage }
		}
		if (snapshot.stage === 'ready') break
		if (snapshot.stage_status === 'failed' || snapshot.stage_status === 'blocked') {
			throw new Error(`Provisioning stopped at ${snapshot.stage}: ${snapshot.message_id || snapshot.customer_message || 'unknown failure'}`)
		}
		await page.waitForTimeout(1000)
	}

	const elapsedMs = Date.now() - startedAt
	if (finalSnapshot?.stage !== 'ready') throw new Error(`Provisioning exceeded 300 seconds at ${finalSnapshot?.stage || 'unknown'}.`)
	if (elapsedMs >= 300000) throw new Error(`Provisioning elapsed ${elapsedMs}ms.`)
	await page.screenshot({ path: resolve(outputDir, `${runId}-ready.png`), fullPage: true })
	const evidence = {
		run_id: runId,
		customer: user,
		site,
		started_at: new Date(startedAt).toISOString(),
		completed_at: new Date().toISOString(),
		elapsed_ms: elapsedMs,
		under_5_minutes: true,
		transitions,
		refresh: refreshEvidence,
		progress_api_calls: network,
		browser_errors: browserErrors,
	}
	writeFileSync(resolve(outputDir, `${runId}.json`), JSON.stringify(evidence, null, 2))
	console.log(JSON.stringify({ site, elapsed_ms: elapsedMs, transitions: transitions.map((row) => [row.stage, row.elapsed_ms]), refresh: refreshEvidence, browser_errors: browserErrors }))
} finally {
	await context.close()
	await browser.close()
}
