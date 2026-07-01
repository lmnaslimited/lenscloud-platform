import { chromium } from 'playwright'
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

const baseURL = process.env.LENSCLOUD_BASE_URL || 'http://dev.localhost:8000'
const credentials = process.env.LENSCLOUD_CREDENTIAL_FILE
	? JSON.parse(readFileSync(process.env.LENSCLOUD_CREDENTIAL_FILE, 'utf8'))
	: process.env
const outputDir = resolve(process.cwd(), 'docs/evidence/customer-launch/screenshots/20260630-plans')
const referenceRoot = resolve(process.cwd(), 'docs/design/stitch_lenscloud_designs')
mkdirSync(outputDir, { recursive: true })
const references = {
	desktop: resolve(referenceRoot, 'choose_your_plan/screen.png'),
	mobile: resolve(referenceRoot, 'choose_plan_mobile/screen.png'),
	setup: resolve(referenceRoot, 'setup_your_site/screen.png'),
	review: resolve(referenceRoot, 'review_subscription/screen.png'),
}

async function imageSize(browser, path) {
	const page = await browser.newPage()
	await page.goto(`file://${path}`)
	const size = await page.locator('img').evaluate((img) => ({ width: img.naturalWidth, height: img.naturalHeight }))
	await page.close()
	return size
}

async function login(page, user, password) {
	if (!user || !password) throw new Error('Customer credentials are required for visual Plans capture.')
	await page.goto(`${baseURL}/login`)
	await page.locator('#login_email').fill(user)
	await page.locator('#login_password').fill(password)
	await page.locator('button.btn-login').click()
	await page.waitForFunction(() => !window.location.pathname.startsWith('/login'))
}

async function openPlans(context, viewport, errors) {
	let page = await context.newPage()
	page.on('pageerror', (error) => errors.push(error.message))
	page.on('console', (message) => {
		if (message.type() === 'error' && !message.text().startsWith('Failed to load resource:')) errors.push(message.text())
	})
	await page.goto(`${baseURL}/lenscloud/customer/plans`)
	await page.getByRole('heading', { name: 'Plans', exact: true }).waitFor()
	await page.getByRole('button', { name: /Start Free Plan/ }).waitFor()
	await page.waitForTimeout(1000)
	return page
}

async function captureChoose(browser, name, viewport, referencePath) {
	const context = await browser.newContext({ viewport })
	let page = await context.newPage()
	await login(page, credentials.customer_user || credentials.LENSCLOUD_CUSTOMER_USER, credentials.customer_password || credentials.LENSCLOUD_CUSTOMER_PASSWORD)
	await page.close()
	const errors = []
	page = await openPlans(context, viewport, errors)
	const bodyText = await page.locator('body').innerText()
	const titles = await page.locator('article').evaluateAll((cards) => cards.map((card) => {
		const text = card.innerText || ''
		const rect = card.getBoundingClientRect()
		return {
			title: ['Tier 2 Growth', 'Free', 'Tier 3 Scale', 'Tier 4 Enterprise'].find((title) => text.includes(title)),
			x: rect.x,
			y: rect.y,
		}
	}).filter((item) => item.title).sort((a, b) => (a.y - b.y) || (a.x - b.x)).map((item) => item.title))
	for (const hiddenTitle of ['Tier 4 Enterprise']) {
		if (bodyText.includes(hiddenTitle)) throw new Error(`${hiddenTitle} must not be visible in customer Plans.`)
	}
	for (const removedText of ['Free-first guided launch', 'Choose your LensCloud Plan', 'Start with the Free Plan, or request access to higher tiers when you are ready.']) {
		if (bodyText.includes(removedText)) throw new Error(`${removedText} should not be visible on customer Plans.`)
	}
	const cta = await page.getByRole('button', { name: /Start Free Plan|Request access|Coming soon/ }).last().innerText().catch(() => '')
	const screenshot = resolve(outputDir, `${name}-plans.png`)
	await page.screenshot({ path: screenshot, fullPage: true })
	await context.close()
	return { name, kind: 'Plan selection', viewport, referencePath, screenshot, titles, cta: cta.trim(), errors }
}

async function captureGuidedStage(browser, name, referencePath, stage) {
	const size = await imageSize(browser, referencePath)
	const viewport = { width: size.width, height: Math.min(size.height, 1000) }
	const context = await browser.newContext({ viewport })
	let page = await context.newPage()
	await login(page, credentials.customer_user || credentials.LENSCLOUD_CUSTOMER_USER, credentials.customer_password || credentials.LENSCLOUD_CUSTOMER_PASSWORD)
	await page.close()
	const errors = []
	page = await openPlans(context, viewport, errors)
	await page.getByRole('button', { name: /Start Free Plan/ }).click()
	await page.getByRole('heading', { name: 'Setup Your Site', exact: true }).first().waitFor()
	await page.getByRole('textbox', { name: 'Subdomain' }).fill('playwright-free-site')
	await page.getByRole('textbox', { name: 'Site Name' }).fill('playwright-free-site')
	await page.getByText('Available', { exact: true }).waitFor()
	if (stage === 'review') {
		await page.getByRole('button', { name: /Continue to Review/ }).click()
		await page.getByRole('heading', { name: 'Review Subscription', exact: true }).first().waitFor()
		await page.getByText('Total due today', { exact: true }).waitFor()
		await page.getByText('No payment method required for Free Plan', { exact: false }).first().waitFor()
	}
	const screenshot = resolve(outputDir, `${name}.png`)
	await page.waitForTimeout(800)
	await page.screenshot({ path: screenshot, fullPage: true })
	const bodyText = await page.locator('body').innerText()
	await context.close()
	return { name, kind: stage === 'review' ? 'Review subscription' : 'Setup your Site', viewport, referencePath, screenshot, titles: [], cta: stage === 'review' ? 'Start Free Subscription' : 'Continue to Review', errors, bodyText }
}


const browser = await chromium.launch({ headless: true })
try {
	const desktop = await imageSize(browser, references.desktop)
	const results = []
	results.push(await captureChoose(browser, 'desktop', { width: desktop.width, height: Math.min(desktop.height, 1000) }, references.desktop))
	results.push(await captureChoose(browser, 'mobile', { width: 390, height: 844 }, references.mobile))
	results.push(await captureGuidedStage(browser, 'desktop-setup-site', references.setup, 'setup'))
	results.push(await captureGuidedStage(browser, 'desktop-review-subscription', references.review, 'review'))
	const reportPath = resolve(outputDir, 'report.html')
	const mdPath = resolve(outputDir, 'report.md')
	const rows = results.map((item) => `
		<section style="margin:24px 0;padding:16px;border:1px solid #EDEDED;border-radius:12px;background:white">
			<h2>${item.kind}: ${item.name}</h2>
			<p><strong>Viewport:</strong> ${item.viewport.width}x${item.viewport.height}</p>
			${item.titles?.length ? `<p><strong>Visible Plans:</strong> ${item.titles.join(', ')}</p>` : ''}
			<p><strong>Primary CTA:</strong> ${item.cta || 'not found'}</p>
			<p><strong>Browser errors:</strong> ${item.errors.length ? item.errors.join('; ') : 'none'}</p>
			<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start">
				<div><h3>Stitch reference</h3><img src="file://${item.referencePath}" style="max-width:100%;border:1px solid #EDEDED" /></div>
				<div><h3>Current Platform</h3><img src="file://${item.screenshot}" style="max-width:100%;border:1px solid #EDEDED" /></div>
			</div>
		</section>`).join('\n')
	writeFileSync(reportPath, `<!doctype html><html><head><meta charset="utf-8"><title>LensCloud Customer Guided Flow Visual Comparison</title></head><body style="font-family:Inter,Arial,sans-serif;background:#f7f9fb;color:#191c1e;padding:24px"><h1>LensCloud Customer Guided Flow Visual Comparison</h1><p>References are non-legacy Stitch artifacts. Review side by side before claiming visual parity.</p>${rows}</body></html>`)
	writeFileSync(mdPath, `# Customer Guided Flow Visual Comparison - 2026-06-30\n\n${results.map((item) => `## ${item.kind}: ${item.name}\n\n- Viewport: ${item.viewport.width}x${item.viewport.height}\n- Reference: ${item.referencePath}\n- Screenshot: ${item.screenshot}\n${item.titles?.length ? `- Visible Plans: ${item.titles.join(', ')}\n` : ''}- Primary CTA: ${item.cta || 'not found'}\n- Browser errors: ${item.errors.length ? item.errors.join('; ') : 'none'}\n`).join('\n')}\nHTML report: ${reportPath}\n`)
	console.log(`Plans visual comparison report: ${reportPath}`)
	console.log(`Plans visual comparison markdown: ${mdPath}`)
	for (const item of results) console.log(`${item.name}: stage=${item.kind} viewport=${item.viewport.width}x${item.viewport.height} plans=${item.titles?.join('|') || '-'} cta=${item.cta || 'not found'} errors=${item.errors.length}`)
} finally {
	await browser.close()
}
