import { chromium } from 'playwright'
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

const baseURL = process.env.LENSCLOUD_BASE_URL || 'http://dev.localhost:8000'
const credentials = process.env.LENSCLOUD_CREDENTIAL_FILE
	? JSON.parse(readFileSync(process.env.LENSCLOUD_CREDENTIAL_FILE, 'utf8'))
	: process.env
const outputDir = resolve(process.cwd(), 'docs/evidence/customer-launch/screenshots/20260630-dashboard')
const referenceRoot = resolve(process.cwd(), 'docs/design/stitch_lenscloud_designs')
mkdirSync(outputDir, { recursive: true })

const references = {
	welcome: resolve(referenceRoot, 'welcome_to_lenscloud/screen.png'),
	desktopSubscribed: resolve(referenceRoot, 'customer_dashboard/screen.png'),
	mobileSubscribed: resolve(referenceRoot, 'dashboard_ready_mobile/screen.png'),
}

async function imageSize(browser, path) {
	const page = await browser.newPage()
	await page.goto(`file://${path}`)
	const size = await page.locator('img').evaluate((img) => ({ width: img.naturalWidth, height: img.naturalHeight }))
	await page.close()
	return size
}

async function login(page, user, password) {
	if (!user || !password) throw new Error('Customer credentials are required for visual dashboard capture.')
	await page.goto(`${baseURL}/login`)
	await page.locator('#login_email').fill(user)
	await page.locator('#login_password').fill(password)
	await page.locator('button.btn-login').click()
	await page.waitForFunction(() => !window.location.pathname.startsWith('/login'))
}

async function capture(browser, name, viewport, referencesByState) {
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
	await page.goto(`${baseURL}/lenscloud/customer/dashboard`)
	await page.getByRole('heading', { name: 'Dashboard', exact: true }).waitFor()
	await page.waitForTimeout(1200)
	const bodyText = await page.locator('body').innerText()
	const state = bodyText.includes('Launch your first LensCloud Site') ? 'welcome' : 'subscribed'
	const primaryButtonText = await page.getByRole('link', { name: /Choose a Plan|Open Site|View progress|Continue setup/ }).first().innerText().catch(() => '')
	const referencePath = state === 'welcome' ? referencesByState.welcome : referencesByState.subscribed
	const screenshot = resolve(outputDir, `${name}-${state}.png`)
	await page.screenshot({ path: screenshot, fullPage: true })
	await context.close()
	return { name, viewport, referencePath, screenshot, state, primaryButtonText: primaryButtonText.trim(), errors }
}

const browser = await chromium.launch({ headless: true })
try {
	const sizes = {
		welcome: await imageSize(browser, references.welcome),
		desktopSubscribed: await imageSize(browser, references.desktopSubscribed),
		mobileSubscribed: await imageSize(browser, references.mobileSubscribed),
	}
	console.log(`Reference sizes: welcome=${sizes.welcome.width}x${sizes.welcome.height}, desktopSubscribed=${sizes.desktopSubscribed.width}x${sizes.desktopSubscribed.height}, mobileSubscribed=${sizes.mobileSubscribed.width}x${sizes.mobileSubscribed.height}`)
	const results = []
	results.push(await capture(browser, 'desktop', { width: sizes.welcome.width, height: Math.min(sizes.welcome.height, 1000) }, { welcome: references.welcome, subscribed: references.desktopSubscribed }))
	results.push(await capture(browser, 'mobile', { width: sizes.mobileSubscribed.width, height: Math.min(sizes.mobileSubscribed.height, 1000) }, { welcome: references.welcome, subscribed: references.mobileSubscribed }))
	const reportPath = resolve(outputDir, 'report.html')
	const mdPath = resolve(outputDir, 'report.md')
	const rows = results.map((item) => `
		<section style="margin:24px 0;padding:16px;border:1px solid #EDEDED;border-radius:12px;background:white">
			<h2>${item.name} - ${item.state}</h2>
			<p><strong>Viewport:</strong> ${item.viewport.width}x${item.viewport.height}</p>
			<p><strong>Primary CTA:</strong> ${item.primaryButtonText || 'not found'}</p>
			<p><strong>Browser errors:</strong> ${item.errors.length ? item.errors.join('; ') : 'none'}</p>
			<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start">
				<div><h3>Stitch reference</h3><img src="file://${item.referencePath}" style="max-width:100%;border:1px solid #EDEDED" /></div>
				<div><h3>Current Platform</h3><img src="file://${item.screenshot}" style="max-width:100%;border:1px solid #EDEDED" /></div>
			</div>
		</section>`).join('\n')
	writeFileSync(reportPath, `<!doctype html><html><head><meta charset="utf-8"><title>LensCloud Dashboard Visual Comparison</title></head><body style="font-family:Inter,Arial,sans-serif;background:#f7f9fb;color:#191c1e;padding:24px"><h1>LensCloud Customer Dashboard Visual Comparison</h1><p>References are non-legacy Stitch artifacts. Review side by side before claiming visual parity.</p>${rows}</body></html>`)
	writeFileSync(mdPath, `# Customer Dashboard Visual Comparison - 2026-06-30\n\n${results.map((item) => `## ${item.name}\n\n- State detected: ${item.state}\n- Viewport: ${item.viewport.width}x${item.viewport.height}\n- Reference: ${item.referencePath}\n- Screenshot: ${item.screenshot}\n- Primary CTA: ${item.primaryButtonText || 'not found'}\n- Browser errors: ${item.errors.length ? item.errors.join('; ') : 'none'}\n`).join('\n')}\nHTML report: ${reportPath}\n`)
	console.log(`Visual comparison report: ${reportPath}`)
	console.log(`Visual comparison markdown: ${mdPath}`)
	for (const item of results) console.log(`${item.name}: state=${item.state} viewport=${item.viewport.width}x${item.viewport.height} cta=${item.primaryButtonText || 'not found'} errors=${item.errors.length}`)
} finally {
	await browser.close()
}
