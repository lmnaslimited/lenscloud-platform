import { chromium } from 'playwright'
import { readFileSync } from 'node:fs'

const credentials = JSON.parse(
	readFileSync(
		process.env.LENSCLOUD_CREDENTIAL_FILE || '/tmp/lenscloud_credential_file.json',
		'utf8',
	),
)
const siteOrigin = 'http://dev.localhost:8000'
const frontendOrigin =
	process.env.LENSCLOUD_FRONTEND_ORIGIN || 'http://dev.localhost:8080'
const issueName = 'ISS-2026-07-0001'
const deniedIssueName = 'ISS-2026-07-0002'

async function login(context, user, password) {
	const response = await context.request.post(`${siteOrigin}/api/method/login`, {
		form: { usr: user, pwd: password },
	})
	if (!response.ok()) throw new Error(`Login failed for ${user}: ${response.status()}`)
}

function collectBrowserErrors(page) {
	const errors = []
	page.on('pageerror', (error) => errors.push(`pageerror: ${error.message}`))
	page.on('console', (message) => {
		if (message.type() === 'error') errors.push(`console: ${message.text()}`)
	})
	return errors
}

async function saveIssue(context, summary) {
	const bootResponse = await context.request.get(
		`${siteOrigin}/api/method/lenscloud.www.lenscloud.get_context_for_dev`,
	)
	if (!bootResponse.ok()) throw new Error(`Boot request failed: ${bootResponse.status()}`)
	const csrfToken = (await bootResponse.json()).message.csrf_token
	const response = await context.request.put(
		`${siteOrigin}/api/resource/Issue/${issueName}`,
		{
			headers: { 'X-Frappe-CSRF-Token': csrfToken },
			data: { summary },
		},
	)
	if (!response.ok()) {
		throw new Error(`Issue save failed: ${response.status()} ${await response.text()}`)
	}
}

const browser = await chromium.launch({ headless: true })
const customerContext = await browser.newContext()
const supportContext = await browser.newContext()

try {
	await login(
		customerContext,
		credentials.customer_nithu,
		credentials.customer_nithu_password,
	)
	await login(supportContext, credentials.platform_user, credentials.platform_password)

	const denied = await customerContext.request.get(
		`${siteOrigin}/api/resource/Issue/${deniedIssueName}`,
	)
	if (denied.status() !== 403) {
		throw new Error(`Unauthorized Issue returned ${denied.status()}, expected 403`)
	}

	const page = await customerContext.newPage()
	const browserErrors = collectBrowserErrors(page)
	await page.goto(
		`${frontendOrigin}/lenscloud/customer/realtime-issue/${issueName}`,
		{ waitUntil: 'domcontentloaded' },
	)
	await page.getByTestId('issue-summary').waitFor()
	const originalSummary = await page.getByTestId('issue-summary').innerText()

	for (let run = 1; run <= 3; run += 1) {
		const summary = `Realtime browser proof ${run} ${Date.now()}`
		const previousCount = Number(
			await page.getByTestId('issue-update-count').innerText(),
		)
		await saveIssue(supportContext, summary)
		await page.getByTestId('issue-summary').getByText(summary, { exact: true }).waitFor()
		await page.getByTestId('issue-update-count').getByText(
			String(previousCount + 1),
			{ exact: true },
		).waitFor()
	}

	await saveIssue(supportContext, originalSummary)
	await page.getByTestId('issue-summary').getByText(originalSummary, { exact: true }).waitFor()
	if (browserErrors.length) throw new Error(browserErrors.join('\n'))

	console.log('realtime Issue browser proof passed 3 consecutive saves')
} finally {
	await customerContext.close()
	await supportContext.close()
	await browser.close()
}
