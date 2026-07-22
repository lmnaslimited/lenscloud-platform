import { chromium } from 'playwright'
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

const baseURL = process.env.LENSCLOUD_BASE_URL || 'http://dev.localhost:8000'
const credentialFile = process.env.LENSCLOUD_CREDENTIAL_FILE
const site = process.env.LENSCLOUD_SITE
const subscription = process.env.LENSCLOUD_SUBSCRIPTION
const originalStartedAt = Date.parse(process.env.LENSCLOUD_STARTED_AT || '')
if (!credentialFile || !site || !subscription || !originalStartedAt) throw new Error('Credential, Site, Subscription, and original start time are required.')
const credentials = JSON.parse(readFileSync(credentialFile, 'utf8'))
const user = credentials.customer_user || credentials.LENSCLOUD_CUSTOMER_USER
const password = credentials.customer_password || credentials.LENSCLOUD_CUSTOMER_PASSWORD
if (user !== 'iron_monkey_private@example.com') throw new Error(`Unexpected acceptance customer: ${user || 'missing'}`)

const runId = site.split('.')[0]
const outputDir = resolve(process.cwd(), '../docs/evidence/customer-launch/provisioning-under5-20260721')
mkdirSync(outputDir, { recursive: true })

async function snapshot(page) {
	return page.evaluate(async (siteName) => {
		const response = await fetch(`/api/method/lenscloud.api.provisioning_progress.get_customer_site_progress?site=${encodeURIComponent(siteName)}`)
		const body = await response.json()
		if (!response.ok || body.exc) throw new Error(body.message || body.exc || `Progress HTTP ${response.status}`)
		return body.message
	}, site)
}

const browser = await chromium.launch({ headless: true })
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } })
const page = await context.newPage()
const browserErrors = []
const progressCalls = []
page.on('pageerror', (error) => browserErrors.push(error.message))
page.on('response', (response) => {
	const path = new URL(response.url()).pathname
	if (path.includes('provisioning_progress')) progressCalls.push({ at: new Date().toISOString(), path, status: response.status() })
})

const recoveredAt = Date.now()
const transitions = []
let lastStage = ''
let finalSnapshot
let refreshEvidence
try {
	await page.goto(`${baseURL}/login`)
	await page.locator('#login_email').fill(user)
	await page.locator('#login_password').fill(password)
	await page.locator('button.btn-login').click()
	await page.waitForFunction(() => !window.location.pathname.startsWith('/login'))
	await page.goto(`${baseURL}/lenscloud/customer/plans?site=${encodeURIComponent(site)}&subscription=${encodeURIComponent(subscription)}`)
	await page.getByRole('heading', { name: 'Plans', exact: true }).waitFor()

	while (Date.now() - recoveredAt < 600000) {
		const current = await snapshot(page)
		finalSnapshot = current
		if (current.stage !== lastStage) {
			transitions.push({ recovered_elapsed_ms: Date.now() - recoveredAt, original_elapsed_ms: Date.now() - originalStartedAt, ...current })
			lastStage = current.stage
		}
		if (!refreshEvidence && transitions.length >= 2 && !['ready', 'failed'].includes(current.stage)) {
			const before = current.stage
			await page.reload()
			await page.getByRole('heading', { name: 'Plans', exact: true }).waitFor()
			const after = await snapshot(page)
			refreshEvidence = { before, after: after.stage, original_elapsed_ms: Date.now() - originalStartedAt }
		}
		if (current.stage === 'ready') break
		if (current.stage_status === 'failed' || current.stage_status === 'blocked') break
		await page.waitForTimeout(1000)
	}

	await page.screenshot({ path: resolve(outputDir, `${runId}-recovery-final.png`), fullPage: true })
	const completedAt = Date.now()
	const evidence = {
		run_id: runId,
		customer: user,
		site,
		subscription,
		original_started_at: new Date(originalStartedAt).toISOString(),
		recovery_started_at: new Date(recoveredAt).toISOString(),
		completed_at: new Date(completedAt).toISOString(),
		original_elapsed_ms: completedAt - originalStartedAt,
		recovery_elapsed_ms: completedAt - recoveredAt,
		under_5_minutes: completedAt - originalStartedAt < 300000 && finalSnapshot?.stage === 'ready',
		classification: 'failed_acceptance_run_recovered_after_read_path_fix',
		final_snapshot: finalSnapshot,
		transitions,
		refresh: refreshEvidence,
		progress_api_calls: progressCalls,
		browser_errors: browserErrors,
	}
	writeFileSync(resolve(outputDir, `${runId}-recovery.json`), JSON.stringify(evidence, null, 2))
	console.log(JSON.stringify({ final_stage: finalSnapshot?.stage, original_elapsed_ms: evidence.original_elapsed_ms, recovery_elapsed_ms: evidence.recovery_elapsed_ms, transitions: transitions.map((row) => [row.stage, row.recovered_elapsed_ms]), message_id: finalSnapshot?.message_id }))
	if (finalSnapshot?.stage !== 'ready') process.exitCode = 2
} finally {
	await context.close()
	await browser.close()
}
