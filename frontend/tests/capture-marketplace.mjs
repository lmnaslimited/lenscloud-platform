import { chromium } from 'playwright'
import { existsSync, readFileSync, mkdirSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

const baseURL = process.env.LENSCLOUD_BASE_URL || 'http://test.localhost:8000'
const credentials = process.env.LENSCLOUD_CREDENTIAL_FILE
	? JSON.parse(readFileSync(process.env.LENSCLOUD_CREDENTIAL_FILE, 'utf8'))
	: process.env
const outputDir = resolve(process.cwd(), 'docs/evidence/customer-launch/screenshots/20260715-marketplace')
mkdirSync(outputDir, { recursive: true })

// Optional design references. Marketplace has no Stitch mock at the time
// this script was written, so these are opt-in via env var rather than
// hardcoded paths like the dashboard script uses. If unset or missing on
// disk, the report simply omits the side-by-side comparison for that state.
const references = {
	desktop: process.env.LENSCLOUD_MARKETPLACE_DESKTOP_REFERENCE || '',
	mobile: process.env.LENSCLOUD_MARKETPLACE_MOBILE_REFERENCE || '',
}

async function login(page, user, password) {
	if (!user || !password) throw new Error('Customer credentials are required for visual marketplace capture.')
	await page.goto(`${baseURL}/login`)
	await page.locator('#login_email').fill(user)
	await page.locator('#login_password').fill(password)
	await page.locator('button.btn-login').click()
	await page.waitForFunction(() => !window.location.pathname.startsWith('/login'))
}

async function capture(browser, name, viewport, referencePath) {
	const context = await browser.newContext({ viewport })
	let page = await context.newPage()
	await login(page, credentials.customer_user || credentials.LENSCLOUD_CUSTOMER_USER, credentials.customer_password || credentials.LENSCLOUD_CUSTOMER_PASSWORD)
	await page.close()

	page = await context.newPage()
	const errors = []
	page.on('pageerror', (error) => errors.push(error.message))
	page.on('console', (message) => {
		if (message.type() === 'error' && !message.text().startsWith('Failed to load resource:')) errors.push(message.text())
	})

	await page.goto(`${baseURL}/lenscloud/customer/marketplace`)
	await page.getByRole('heading', { name: 'Marketplace',level: 1, exact: true }).waitFor()
	await page.waitForTimeout(1200)

	const cardCount = await page.locator('article').count()
	const bodyText = await page.locator('body').innerText()
	const emptyState = bodyText.includes('No Capabilities Available')

	// Functional check: toggle the first self-service opt-in switch and
	// confirm the UI reflects the change after the API round-trip. Only
	// meaningful on the first capture (desktop) to avoid double-toggling
	// the same customer's state across both viewport passes.
	let toggleResult = 'skipped'
	if (name === 'desktop' && cardCount > 0) {
		const firstToggle = page.locator('article button[aria-pressed]').first()
		if (await firstToggle.count()) {
			const before = await firstToggle.getAttribute('aria-pressed')
			await firstToggle.click()
			await page.waitForTimeout(800) // allow the optimistic update + API round-trip to settle
			const after = await firstToggle.getAttribute('aria-pressed')
			toggleResult = before !== after ? `changed (${before} -> ${after})` : `unchanged (stayed ${before})`
			// Revert so the demo account's opt-in state isn't left mutated by the test run.
			await firstToggle.click()
			await page.waitForTimeout(800)
		} else {
			toggleResult = 'no toggle found'
		}
	}

	const screenshot = resolve(outputDir, `${name}.png`)
	await page.screenshot({ path: screenshot, fullPage: true })
	await context.close()

	const resolvedReference = referencePath && existsSync(referencePath) ? referencePath : null

	return { name, viewport, referencePath: resolvedReference, screenshot, cardCount, emptyState, toggleResult, errors }
}

const browser = await chromium.launch({ headless: true })
try {
	const results = []
	results.push(await capture(browser, 'desktop', { width: 1440, height: 900 }, references.desktop))
	results.push(await capture(browser, 'mobile', { width: 390, height: 844 }, references.mobile))

	const reportPath = resolve(outputDir, 'report.html')
	const mdPath = resolve(outputDir, 'report.md')

	const rows = results.map((item) => `
		<section style="margin:24px 0;padding:16px;border:1px solid #EDEDED;border-radius:12px;background:white">
			<h2>${item.name}</h2>
			<p><strong>Viewport:</strong> ${item.viewport.width}x${item.viewport.height}</p>
			<p><strong>Capability cards found:</strong> ${item.cardCount}${item.emptyState ? ' (empty state shown)' : ''}</p>
			<p><strong>Opt-in toggle check:</strong> ${item.toggleResult}</p>
			<p><strong>Browser errors:</strong> ${item.errors.length ? item.errors.join('; ') : 'none'}</p>
			<div style="display:grid;grid-template-columns:${item.referencePath ? '1fr 1fr' : '1fr'};gap:16px;align-items:start">
				${item.referencePath ? `<div><h3>Design reference</h3><img src="file://${item.referencePath}" style="max-width:100%;border:1px solid #EDEDED" /></div>` : ''}
				<div><h3>Current Platform</h3><img src="file://${item.screenshot}" style="max-width:100%;border:1px solid #EDEDED" /></div>
			</div>
		</section>`).join('\n')

	writeFileSync(reportPath, `<!doctype html><html><head><meta charset="utf-8"><title>LensCloud Marketplace Visual Comparison</title></head><body style="font-family:Inter,Arial,sans-serif;background:#f7f9fb;color:#191c1e;padding:24px"><h1>LensCloud Customer Marketplace Visual Comparison</h1><p>Design reference is only shown if provided via LENSCLOUD_MARKETPLACE_DESKTOP_REFERENCE / LENSCLOUD_MARKETPLACE_MOBILE_REFERENCE and found on disk.</p>${rows}</body></html>`)

	writeFileSync(mdPath, `# Customer Marketplace Visual Comparison\n\n${results.map((item) => `## ${item.name}\n\n- Viewport: ${item.viewport.width}x${item.viewport.height}\n- Capability cards found: ${item.cardCount}${item.emptyState ? ' (empty state shown)' : ''}\n- Reference: ${item.referencePath || 'not provided'}\n- Screenshot: ${item.screenshot}\n- Opt-in toggle check: ${item.toggleResult}\n- Browser errors: ${item.errors.length ? item.errors.join('; ') : 'none'}\n`).join('\n')}\nHTML report: ${reportPath}\n`)

	console.log(`Visual comparison report: ${reportPath}`)
	console.log(`Visual comparison markdown: ${mdPath}`)
	for (const item of results) console.log(`${item.name}: cards=${item.cardCount} toggle=${item.toggleResult} errors=${item.errors.length}`)
} finally {
	await browser.close()
}