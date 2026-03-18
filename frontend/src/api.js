export const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

export const SAMPLE_MESSAGE =
  '“@行政 麻烦报销一下：昨晚 21:30 从虹桥到公司打车 86.50，项目：龙虾黑客松，成本中心：市场部。发票见图。”'

export const RECEIPT_MESSAGE = '✅ 报销单已提交：BX-20260318-0042｜¥86.50｜市场部｜待审批'

export async function postJson(path, body) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const details = await response.json().catch(() => ({}))
    throw new Error(details.detail || `Request failed: ${response.status}`)
  }

  return response.json()
}
