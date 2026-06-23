import { chromium } from 'playwright'
import { readFileSync } from 'node:fs'

const baseURL = process.env.LENSCLOUD_BASE_URL || 'http://dev.localhost:8000'
const credentials = JSON.parse(readFileSync(process.env.LENSCLOUD_CREDENTIAL_FILE, 'utf8'))

async function login(page) {
	await page.goto(`${baseURL}/login`)
	await page.locator('#login_email').fill(credentials.platform_user)
	await page.locator('#login_password').fill(credentials.platform_password)
	await page.locator('button.btn-login').click()
	await page.waitForFunction(() => !window.location.pathname.startsWith('/login'))
}


async function saveAndWait(page, editor, expected) {
	const save = editor.getByRole('button', { name: 'Save', exact: true })
	const response = page.waitForResponse((item) => item.request().method() === 'PUT' && item.url().includes('/api/resource/Landscape/'))
	await save.click()
	const result = await response
	const requestPayload = result.request().postDataJSON()
	if (!result.ok()) throw new Error(`Landscape save failed with HTTP ${result.status()}.`)
	for (let attempt = 0; attempt < 50; attempt += 1) {
		if (!(await save.isDisabled()) && await editor.getByLabel('Bench Group').inputValue() === expected) return
		await page.waitForTimeout(100)
	}
	const actual = await editor.getByLabel('Bench Group').inputValue()
	throw new Error(`Bench Group did not reload as ${expected}; payload was ${requestPayload?.environments?.[0]?.bench_group}; actual was ${actual}.`)
}

const browser = await chromium.launch({ headless: true })
const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } })
let page = await context.newPage()
const errors = []

try {
	await login(page)
	await page.close()
	page = await context.newPage()
	page.on('pageerror', (error) => errors.push(error.message))
	page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()) })
	await page.goto(`${baseURL}/lenscloud/platform/landscapes/${encodeURIComponent('Single Tier')}`)
	await page.getByRole('heading', { name: 'Landscapes', exact: true }).waitFor()
	const editor = page.getByTestId('center-document-editor')
	await editor.waitFor()
	await editor.getByText('Environments', { exact: true }).waitFor()
	await page.getByRole('separator', { name: 'Resize document editor' }).waitFor()

	const environment = editor.getByLabel('Environment')
	if (await environment.inputValue() !== 'Prod') throw new Error('Seeded Prod child row did not load.')
	await environment.click()
	await page.getByRole('option', { name: /Prod/ }).first().waitFor()
	await page.keyboard.press('Escape')

	const scroller = editor.getByTestId('child-table-scroll')
	const scrolling = await scroller.evaluate((element) => element.scrollWidth > element.clientWidth)
	if (!scrolling) throw new Error('Wide child table does not provide horizontal scrolling.')
	const rowHeight = await editor.locator('tbody tr').first().evaluate((row) => row.getBoundingClientRect().height)
	if (rowHeight > 64) throw new Error(`Child grid row is too bulky at ${rowHeight}px.`)
	const stickyCells = await editor.locator('tbody tr').first().locator('td').evaluateAll((cells) => [getComputedStyle(cells[0]).position, getComputedStyle(cells[1]).position, getComputedStyle(cells[cells.length - 1]).position])
	if (stickyCells.some((position) => position !== 'sticky')) throw new Error(`Expected fixed child columns, got ${stickyCells.join(', ')}`)
	await page.getByRole('button', { name: 'Expand editor' }).click()
	await page.getByRole('button', { name: 'Restore split editor' }).waitFor()
	await page.getByRole('button', { name: 'Restore split editor' }).click()

	await editor.getByRole('button', { name: 'Add row', exact: true }).click()
	if (await editor.getByLabel('Bench Group').count() !== 2) throw new Error('Add child row did not create editable controls.')
	await editor.getByRole('button', { name: 'Remove row' }).last().click()
	if (await editor.getByLabel('Bench Group').count() !== 1) throw new Error('Remove child row did not update the table.')

	const benchGroup = editor.getByLabel('Bench Group')
	const original = 'prod'
	if (await benchGroup.inputValue() !== original) {
		await benchGroup.fill(original)
		await benchGroup.press('Tab')
		await editor.getByText('Unsaved', { exact: true }).waitFor()
		await saveAndWait(page, editor, original)
	}
	const probe = 'prod-ui-probe-temporary'
	await editor.getByLabel('Bench Group').fill(probe)
	await editor.getByLabel('Bench Group').press('Tab')
	await editor.getByText('Unsaved', { exact: true }).waitFor()
	await saveAndWait(page, editor, probe)

	await editor.getByLabel('Bench Group').fill(original)
	await editor.getByLabel('Bench Group').press('Tab')
	await editor.getByText('Unsaved', { exact: true }).waitFor()
	await saveAndWait(page, editor, original)

	await page.goto(`${baseURL}/lenscloud/platform/release-groups/${encodeURIComponent('lens-pure')}`)
	const releaseEditor = page.getByTestId('center-document-editor')
	await releaseEditor.waitFor()
	await releaseEditor.getByText('Image Family', { exact: true }).waitFor()
	await releaseEditor.getByText('Apps', { exact: true }).waitFor()
	await releaseEditor.getByText('Included Apps', { exact: true }).waitFor()
	if (await releaseEditor.getByLabel('Title', { exact: true }).count()) throw new Error('Autoname Title must not appear in the existing-document editor.')
	await releaseEditor.getByRole('button', { name: 'Rename', exact: true }).click()
	await releaseEditor.getByText('Frappe updates links and the field-based document title through its rename workflow.', { exact: true }).waitFor()
	await releaseEditor.getByRole('button', { name: 'Cancel', exact: true }).click()
	await releaseEditor.getByText('ERPNext', { exact: true }).waitFor()
	const includedApps = releaseEditor.getByText('Included Apps', { exact: true }).locator('..').locator('..')
	await includedApps.locator('button').last().click()
	await page.getByRole('option', { name: /ERPNext/i }).first().waitFor()
	await page.keyboard.press('Escape')
	await releaseEditor.getByRole('button', { name: /Remove ERPNext/i }).click()
	await releaseEditor.getByText('Unsaved', { exact: true }).waitFor()
	await releaseEditor.getByRole('button', { name: 'Discard', exact: true }).click()
	await releaseEditor.getByText('ERPNext', { exact: true }).waitFor()

	if (errors.length) throw new Error(`Browser errors: ${errors.join('; ')}`)
	console.log('Authenticated metadata editor Playwright passed: sections, compact fixed columns, horizontal scroll, child persistence, and Table MultiSelect value help/discard, and rename-only autoname fields.')
} finally {
	await context.close()
	await browser.close()
}
