import { chromium } from 'playwright'
import { readFileSync } from 'node:fs'

const baseURL = process.env.LENSCLOUD_BASE_URL || 'http://dev.localhost:8000'
const mobile = process.env.LENSCLOUD_VIEWPORT === 'mobile'
const contextOptions = mobile
	? { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true }
	: { viewport: { width: 1440, height: 900 } }
const credentials = process.env.LENSCLOUD_CREDENTIAL_FILE
	? JSON.parse(readFileSync(process.env.LENSCLOUD_CREDENTIAL_FILE, 'utf8'))
	: process.env

async function login(page, user, password) {
	if (!user || !password) throw new Error('Selected authenticated scope has no credentials.')
	await page.goto(`${baseURL}/login`)
	await page.locator('#login_email').fill(user)
	await page.locator('#login_password').fill(password)
	await page.locator('button.btn-login').click()
	await page.waitForFunction(() => !window.location.pathname.startsWith('/login'))
}

function collectErrors(page) {
	const errors = []
	page.on('pageerror', (error) => errors.push(error.message))
	page.on('console', (message) => {
		if (message.type() === 'error' && !message.text().startsWith('Failed to load resource:')) errors.push(message.text())
	})
	page.on('response', (response) => {
		const path = new URL(response.url()).pathname
		if (response.status() >= 400 && path !== '/socket.io/') errors.push('HTTP ' + response.status() + ' ' + path)
	})
	page.on('response', (response) => { if (response.status() >= 400) errors.push() })
	return errors
}

async function assertClean(errors, scope) {
	await new Promise((resolve) => setTimeout(resolve, 300))
	if (errors.length) throw new Error(`${scope} browser errors: ${errors.join('; ')}`)
}

async function assertPage(page, path, heading) {
	const errors = collectErrors(page)
	await page.goto(`${baseURL}${path}`)
	await page.waitForTimeout(1500)
	const headingLocator = page.getByRole('heading', { name: heading, exact: true })
	if (!(await headingLocator.count())) {
		const labels = (await page.locator('body').innerText()).split('\n').filter(Boolean).slice(0, 12).join(' | ')
		throw new Error(`${heading} route did not render. Final URL: ${page.url()}. UI: ${labels}. Errors: ${errors.join('; ')}`)
	}
	await headingLocator.waitFor()
	const count = page.getByText(/\d+ \/ \d+/).first()
	await count.waitFor()
	const text = await count.innerText()
	const total = Number(text.split('/').at(-1).trim())
	if (!total) throw new Error(`${heading} list contains no visible records.`)
	const alert = page.getByText('Unable to load or save this surface', { exact: true })
	if (await alert.count()) throw new Error(`${heading} list reported a load failure.`)
	await assertClean(errors, heading)
}

async function testPlatform(browser) {
	const context = await browser.newContext(contextOptions)
	let page = await context.newPage()
	await login(page, credentials.platform_user || credentials.LENSCLOUD_PLATFORM_USER, credentials.platform_password || credentials.LENSCLOUD_PLATFORM_PASSWORD)
	await page.close()
	page = await context.newPage()
	const errors = collectErrors(page)
	await page.goto(`${baseURL}/lenscloud/platform/dashboard`)
	await page.getByRole('heading', { name: 'Dashboard', exact: true }).waitFor()
	await page.getByRole('heading', { name: 'Customer onboarding gates', exact: true }).waitFor()
	await page.getByRole('heading', { name: 'Action required', exact: true }).waitFor()
	await page.getByRole('heading', { name: 'Regional capacity', exact: true }).waitFor()
	let navigation = page.locator('aside')
	if (mobile) {
		await page.getByRole('button', { name: 'Toggle navigation' }).click()
		navigation = page.getByTestId('mobile-navigation')
	}
	await navigation.getByText('Customers and Commerce', { exact: true }).waitFor()
	await navigation.getByText('Product and Delivery', { exact: true }).waitFor()
	await navigation.getByText('Runtime', { exact: true }).waitFor()
	await assertClean(errors, 'Platform dashboard')
	await assertPage(page, '/lenscloud/platform/customers', 'Customers')
	await assertPage(page, '/lenscloud/platform/sites', 'Sites')
	await context.close()
}

async function testCustomer(browser) {
	const user = credentials.customer_user || credentials.LENSCLOUD_CUSTOMER_USER
	const password = credentials.customer_password || credentials.LENSCLOUD_CUSTOMER_PASSWORD
	if (!user || !password) return false
	const context = await browser.newContext(contextOptions)
	let page = await context.newPage()
	await login(page, user, password)
	await page.close()
	page = await context.newPage()
	const errors = collectErrors(page)
	await page.goto(`${baseURL}/lenscloud/customer/create-site`)
	await page.getByRole('heading', { name: 'Create Site', exact: true }).waitFor()
	await page.getByText('Free Plan', { exact: false }).first().waitFor()
	await assertClean(errors, 'Customer')
	await context.close()
	return true
}

const browser = await chromium.launch({ headless: true })
try {
	await testPlatform(browser)
	const customerRan = await testCustomer(browser)
	console.log(`Authenticated LensCloud Playwright passed: Platform ${mobile ? 'mobile' : 'desktop'}; Customer ${customerRan ? 'passed' : 'skipped (credentials not supplied)'}.`)
} finally {
	await browser.close()
}
