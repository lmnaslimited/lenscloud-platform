import { chromium } from 'playwright'
import { readFileSync } from 'node:fs'

const baseURL = process.env.LENSCLOUD_BASE_URL || 'http://dev.localhost:8000'
const credentials = JSON.parse(readFileSync(process.env.LENSCLOUD_CREDENTIAL_FILE, 'utf8'))

async function login(context) {
	const page = await context.newPage()
	await page.goto(`${baseURL}/login`)
	await page.locator('#login_email').fill(credentials.platform_user)
	await page.locator('#login_password').fill(credentials.platform_password)
	await page.locator('button.btn-login').click()
	await page.waitForFunction(() => !location.pathname.startsWith('/login'))
	await page.close()
}

const browser = await chromium.launch({ headless: true })
const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } })
await login(context)
const page = await context.newPage()
const errors = []
page.on('pageerror', (error) => errors.push(error.message))
page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()) })

try {
	await page.goto(`${baseURL}/lenscloud/platform/plans/${encodeURIComponent('Free')}`)
	const planEditor = page.getByTestId('center-document-editor')
	await planEditor.waitFor()
	const allowedPrivacy = planEditor.getByText('Allowed Privacy Profiles', { exact: true }).locator('..').locator('..')
	await allowedPrivacy.waitFor()
	if (await allowedPrivacy.getByTestId('child-table-scroll').count()) throw new Error('Plan Table MultiSelect rendered as a regular child table.')
	if (!(await allowedPrivacy.locator('button').count())) throw new Error('Plan Table MultiSelect has no value-help trigger.')

	const siteCustomer = await page.evaluate(async () => {
		const url = new URL('/api/resource/Site', location.origin)
		url.searchParams.set('fields', JSON.stringify(['customer']))
		url.searchParams.set('filters', JSON.stringify([['customer', '!=', '']]))
		url.searchParams.set('limit_page_length', '1')
		const response = await fetch(url, { credentials: 'include', headers: { Accept: 'application/json' } })
		const body = await response.json()
		if (!response.ok) throw new Error(body.message || 'Unable to load a Site customer.')
		return body.data?.[0]?.customer
	})
	if (!siteCustomer) throw new Error('No customer-linked Site exists for connection acceptance.')

	await page.goto(`${baseURL}/lenscloud/platform/customers/${encodeURIComponent(siteCustomer)}`)
	const customerEditor = page.getByTestId('center-document-editor')
	await customerEditor.waitFor()
	await customerEditor.getByRole('button', { name: 'Save', exact: true }).waitFor()
	await page.getByRole('tab', { name: /Related/ }).click()
	const siteConnection = page.getByText('Site', { exact: true }).locator('..').locator('..')
	await siteConnection.waitFor()
	const total = Number(await siteConnection.locator('button').innerText())
	if (total < 1) throw new Error('Customer Site connection count is empty.')
	await siteConnection.locator('button').click()
	await page.getByRole('heading', { name: 'Sites', exact: true }).waitFor()
	if (new URL(page.url()).searchParams.get('filter_field') !== 'customer') throw new Error('Related count did not apply the customer filter.')
	await page.getByText(new RegExp(`Customer = ${siteCustomer.replace(/[.*+?^$()|[\\]\\]/g, '\\$&')}`)).waitFor()

	await page.goto(`${baseURL}/lenscloud/platform/subscriptions`)
	await page.getByRole('heading', { name: 'Subscriptions', exact: true }).waitFor()
	await page.getByRole('button', { name: 'New Subscription', exact: true }).click()
	await page.locator('p').filter({ hasText: /^New Subscription$/ }).waitFor()
	await page.getByLabel('Customer').waitFor()
	await page.getByLabel('Plan').waitFor()
	await page.getByLabel('Region').waitFor()

	if (errors.length) throw new Error(`Metadata framework browser errors: ${errors.join('; ')}`)
	console.log('Authenticated metadata framework passed: Plan Table MultiSelect, Customer edit, Subscription create, and filtered connections.')
} finally {
	await context.close()
	await browser.close()
}
