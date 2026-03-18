import { expect, test } from '@playwright/test'

test('happy path submits the expense and writes back the receipt', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Use Sample' }).click()
  await page.getByRole('button', { name: 'Parse' }).click()
  await expect(page.locator('input[name="expense_type"]')).toHaveValue('差旅-打车')
  await page.getByRole('button', { name: 'Apply Suggestion' }).click()
  await page.getByRole('button', { name: 'Run Agent' }).click()

  await expect(page.getByTestId('confirmation-card')).toBeVisible({ timeout: 20_000 })
  await page.getByRole('button', { name: 'Confirm Submit' }).click()

  await expect(page.getByTestId('receipt-card')).toContainText('BX-20260318-0042', { timeout: 20_000 })
  await expect(page.getByTestId('chat-thread')).toContainText('✅ 报销单已提交：BX-20260318-0042')
})
