import { useEffect, useRef, useState } from 'react'
import { API_BASE, RECEIPT_MESSAGE, SAMPLE_MESSAGE, postJson } from './api'

const phases = {
  idle: 'idle',
  sampled: 'sampled',
  parsed: 'parsed',
  executing: 'executing',
  awaiting_confirmation: 'awaiting_confirmation',
  submitted: 'submitted',
  failed: 'failed',
}

function ChatBubble({ role, children }) {
  return <div className={`chat-bubble ${role}`}>{children}</div>
}

function FieldInput({ label, value, name, onChange }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input name={name} value={value} onChange={onChange} />
    </label>
  )
}

function ReceiptCard({ receipt }) {
  if (!receipt) return null
  return (
    <section className="panel receipt-card" data-testid="receipt-card">
      <div className="panel-title">Receipt</div>
      <div className="receipt-pill success">提交成功</div>
      <dl className="receipt-grid">
        <div>
          <dt>报销单号</dt>
          <dd>{receipt.expense_id}</dd>
        </div>
        <div>
          <dt>状态</dt>
          <dd>{receipt.status}</dd>
        </div>
        <div>
          <dt>金额</dt>
          <dd>¥{receipt.amount}</dd>
        </div>
        <div>
          <dt>详情页</dt>
          <dd>{receipt.detail_url}</dd>
        </div>
      </dl>
    </section>
  )
}

function PhaseBadge({ label, active, complete, tone = 'default' }) {
  const classes = ['phase-pill']
  if (active) classes.push('active')
  if (complete) classes.push('complete')
  if (tone !== 'default') classes.push(tone)

  return <span className={classes.join(' ')}>{label}</span>
}

export default function App() {
  const [phase, setPhase] = useState(phases.idle)
  const [message, setMessage] = useState('')
  const [attachmentPath, setAttachmentPath] = useState('')
  const [attachmentPreview, setAttachmentPreview] = useState('')
  const [fields, setFields] = useState(null)
  const [checklist, setChecklist] = useState([])
  const [activeStep, setActiveStep] = useState(-1)
  const [logs, setLogs] = useState([])
  const [sessionId, setSessionId] = useState('')
  const [confirmationMessage, setConfirmationMessage] = useState('')
  const [receipt, setReceipt] = useState(null)
  const [writeBackMessages, setWriteBackMessages] = useState([])
  const [error, setError] = useState('')
  const eventSourceRef = useRef(null)
  const logStreamRef = useRef(null)

  useEffect(() => {
    return () => {
      eventSourceRef.current?.close()
    }
  }, [])

  useEffect(() => {
    if (logStreamRef.current) {
      logStreamRef.current.scrollTop = logStreamRef.current.scrollHeight
    }
  }, [logs])

  const isExecuting = phase === phases.executing || phase === phases.awaiting_confirmation
  const isComplete = phase === phases.submitted
  const sandboxUrl = receipt ? `${API_BASE}${receipt.detail_url}` : `${API_BASE}/expense/new`
  const sandboxLabel = receipt ? 'Sandbox Success Page' : 'Sandbox Expense Form'
  const progressCount = checklist.length > 0 ? Math.min(checklist.length, activeStep + 1) : 0
  const hasParsed = Boolean(fields)
  const hasPlanned = checklist.length > 0
  const currentStatusLabel =
    phase === phases.awaiting_confirmation
      ? 'Waiting Confirmation'
      : phase === phases.executing
        ? 'Executing'
        : phase === phases.submitted
          ? 'Submitted'
          : hasPlanned
            ? 'Planned'
            : hasParsed
              ? 'Parsed'
              : 'Idle'

  const appendLog = (entry) => {
    setLogs((current) => [...current, entry])
  }

  const handleUseSample = () => {
    setMessage(SAMPLE_MESSAGE)
    setAttachmentPath('/samples/invoice.jpg')
    setAttachmentPreview(`${API_BASE}/samples/invoice.jpg`)
    setWriteBackMessages([])
    setReceipt(null)
    setFields(null)
    setChecklist([])
    setLogs(['Demo sample ready'])
    setActiveStep(-1)
    setConfirmationMessage('')
    setError('')
    setPhase(phases.sampled)
  }

  const handleAttachmentChange = (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    const previewUrl = URL.createObjectURL(file)
    setAttachmentPreview(previewUrl)
    setAttachmentPath(file.name)
  }

  const handleParse = async () => {
    try {
      setError('')
      const parsed = await postJson('/parse', {
        message,
        attachment_path: attachmentPath || null,
      })
      setFields(parsed)
      setAttachmentPath(parsed.attachment_path)
      setAttachmentPreview(`${API_BASE}${parsed.attachment_path}`)
      const plan = await postJson('/plan', { fields: parsed })
      setChecklist(plan.checklist)
      setLogs(['Fixed parse result ready', 'Fixed execution plan ready'])
      setPhase(phases.parsed)
    } catch (nextError) {
      setError(nextError.message)
      setPhase(phases.failed)
    }
  }

  const updateField = (event) => {
    const { name, value } = event.target
    setFields((current) => ({ ...current, [name]: value }))
  }

  const handleApplySuggestion = () => {
    if (!fields) return
    setFields({ ...fields, summary: fields.summary_suggestion })
  }

  const connectEvents = (nextSessionId) => {
    eventSourceRef.current?.close()
    const eventSource = new EventSource(`${API_BASE}/events/${nextSessionId}`)
    eventSourceRef.current = eventSource

    eventSource.addEventListener('log', (event) => {
      const payload = JSON.parse(event.data)
      appendLog(payload.message)
    })

    eventSource.addEventListener('step', (event) => {
      const payload = JSON.parse(event.data)
      setActiveStep(payload.step_index)
    })

    eventSource.addEventListener('state', (event) => {
      const payload = JSON.parse(event.data)
      setPhase(payload.state)
    })

    eventSource.addEventListener('confirmation_requested', (event) => {
      const payload = JSON.parse(event.data)
      setConfirmationMessage(payload.message)
      setPhase(phases.awaiting_confirmation)
    })

    eventSource.addEventListener('completed', (event) => {
      const payload = JSON.parse(event.data)
      setReceipt(payload)
      setWriteBackMessages((current) => [...current, RECEIPT_MESSAGE])
      setActiveStep(checklist.length)
      setPhase(phases.submitted)
      eventSource.close()
    })

    eventSource.addEventListener('failed', (event) => {
      const payload = JSON.parse(event.data)
      setError(payload.error)
      setPhase(phases.failed)
      eventSource.close()
    })
  }

  const handleRunAgent = async () => {
    if (!fields) return
    try {
      setError('')
      setLogs(['Starting deterministic ClawSubmit demo flow'])
      setReceipt(null)
      setWriteBackMessages([])
      setActiveStep(-1)
      setConfirmationMessage('')
      const execution = await postJson('/execute', { fields })
      setSessionId(execution.session_id)
      setPhase(phases.executing)
      connectEvents(execution.session_id)
    } catch (nextError) {
      setError(nextError.message)
      setPhase(phases.failed)
    }
  }

  const handleConfirmSubmit = async () => {
    if (!sessionId) return
    try {
      await postJson(`/execute/${sessionId}/confirm`, {})
    } catch (nextError) {
      setError(nextError.message)
      setPhase(phases.failed)
    }
  }

  const canParse = Boolean(message.trim())
  const canRun = Boolean(fields) && !isExecuting

  return (
    <main className="app-shell">
      <header className="hero">
        <div className="hero-copy">
          <div className="eyebrow">Execution-Native Agent Demo</div>
          <h1>ClawSubmit</h1>
          <p>Turn chat plus invoice into a submitted expense, with a real execution plan and human confirmation before commit.</p>
          <div className="phase-rail">
            <PhaseBadge label="Parsed" active={hasParsed && !hasPlanned} complete={hasPlanned || isExecuting || isComplete} />
            <PhaseBadge label="Planned" active={hasPlanned && !isExecuting && !isComplete} complete={isExecuting || isComplete} />
            <PhaseBadge label="Executing" active={phase === phases.executing} complete={phase === phases.awaiting_confirmation || isComplete} tone="info" />
            <PhaseBadge label="Waiting Confirmation" active={phase === phases.awaiting_confirmation} complete={isComplete} tone="warning" />
            <PhaseBadge label="Submitted" active={isComplete} complete={isComplete} tone="success" />
          </div>
        </div>
        <div className="hero-status">
          <div className={`status-badge ${phase}`}>{currentStatusLabel}</div>
          <div className="hero-note">Local-only sandbox demo. Deterministic parse, plan, receipt, and write-back.</div>
        </div>
      </header>

      <section className="grid">
        <div className="panel column left-panel">
          <div className="panel-title">Task Entry</div>
          <div className="panel-kicker">Chat-driven request intake</div>
          <div className="chat-thread" data-testid="chat-thread">
            {message ? <ChatBubble role="user">{message}</ChatBubble> : <div className="placeholder">等待输入报销请求…</div>}
            {writeBackMessages.map((entry) => (
              <ChatBubble key={entry} role="system">
                {entry}
              </ChatBubble>
            ))}
          </div>
          <textarea
            className="composer"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="输入一条聊天式任务请求，比如请帮我报销昨晚打车…"
          />
          <div className="actions">
            <label className={`upload ${isExecuting ? 'disabled' : ''}`}>
              <span>上传发票</span>
              <input type="file" accept=".jpg,.jpeg,.png" onChange={handleAttachmentChange} disabled={isExecuting} />
            </label>
            <button type="button" onClick={handleUseSample} disabled={isExecuting}>
              Use Sample
            </button>
            <button type="button" onClick={handleParse} disabled={!canParse || isExecuting}>
              {phase === phases.parsed ? 'Parsed' : 'Parse'}
            </button>
          </div>
          {attachmentPreview ? (
            <div className="attachment-preview">
              <img src={attachmentPreview} alt="Invoice Preview" />
              <div className="attachment-meta">
                <span>Sample Invoice Ready</span>
                <span>{attachmentPath}</span>
              </div>
            </div>
          ) : null}
        </div>

        <div className="panel column middle-panel">
          <div className="panel-title">Structured Extraction</div>
          <div className="panel-kicker">Normalized expense payload ready for execution</div>
          {fields ? (
            <div className="fields-card">
              <FieldInput label="费用类型" name="expense_type" value={fields.expense_type} onChange={updateField} />
              <FieldInput label="金额" name="amount" value={fields.amount} onChange={updateField} />
              <FieldInput label="时间" name="date_time" value={fields.date_time} onChange={updateField} />
              <FieldInput label="出发地/目的地" name="from_to" value={fields.from_to} onChange={updateField} />
              <FieldInput label="项目" name="project" value={fields.project} onChange={updateField} />
              <FieldInput label="成本中心" name="cost_center" value={fields.cost_center} onChange={updateField} />
              <FieldInput label="报销摘要" name="summary" value={fields.summary} onChange={updateField} />
              <FieldInput
                label="摘要建议"
                name="summary_suggestion"
                value={fields.summary_suggestion}
                onChange={updateField}
              />
              <FieldInput
                label="附件路径"
                name="attachment_path"
                value={fields.attachment_path}
                onChange={updateField}
              />
              {!fields.summary ? (
                <button type="button" className="ghost" onClick={handleApplySuggestion} disabled={isExecuting}>
                  Apply Suggestion
                </button>
              ) : null}
              <button type="button" onClick={handleRunAgent} disabled={!canRun}>
                {isExecuting ? 'Agent Running...' : isComplete ? 'Run Again' : 'Run Agent'}
              </button>
            </div>
          ) : (
            <div className="placeholder">先解析输入，提取结构化字段。</div>
          )}
        </div>

        <div className="column right-column">
          <section className={`panel execution-hub ${isComplete ? 'success-shell' : ''}`}>
            <div className="panel-title">Execution Center</div>
            <div className="panel-kicker">Live plan, automation progress, confirmation gate, and outcome</div>
            <div className="execution-summary">
              <div>
                <strong>{progressCount}</strong> / {checklist.length || 7}
              </div>
              <span>{isComplete ? 'All steps completed' : isExecuting ? 'Automation in progress' : 'Ready to execute'}</span>
            </div>
            <ol className="checklist" data-testid="checklist">
              {checklist.map((item, index) => {
                const state =
                  index < activeStep ? 'done' : index === activeStep ? 'active' : 'pending'
                return (
                  <li key={item} className={`checklist-item ${state}`}>
                    <span className="step-dot" />
                    <span>{item}</span>
                  </li>
                )
              })}
            </ol>
          </section>

          <section className={`panel sandbox-panel ${isExecuting || isComplete ? 'focus-shell' : ''}`}>
            <div className="panel-title">Live Sandbox View</div>
            <div className="sandbox-meta">
              <span className={`sandbox-chip ${receipt ? 'success' : isExecuting ? 'active' : ''}`}>{sandboxLabel}</span>
              <span className="sandbox-url">{receipt ? receipt.detail_url : '/expense/new'}</span>
            </div>
            <iframe title="Local Expense Sandbox" src={sandboxUrl} className="sandbox-frame" />
          </section>

          <section className={`panel logs-panel ${isExecuting ? 'focus-shell' : ''}`}>
            <div className="panel-title">Execution Logs</div>
            <div className="log-stream" ref={logStreamRef}>
              {logs.length ? logs.map((entry, index) => <div key={`${entry}-${index}`} className="log-line">{entry}</div>) : <div className="placeholder">日志将实时显示在这里。</div>}
            </div>
          </section>

          {phase === phases.awaiting_confirmation ? (
            <section className="panel confirmation-card focus-shell" data-testid="confirmation-card">
              <div className="panel-title">Human Confirmation</div>
              <p>{confirmationMessage}</p>
              <button type="button" onClick={handleConfirmSubmit}>
                Confirm Submit
              </button>
            </section>
          ) : null}

          <ReceiptCard receipt={receipt} />

          {error ? (
            <section className="panel error-card">
              <div className="panel-title">Error</div>
              <p>{error}</p>
            </section>
          ) : null}
        </div>
      </section>
    </main>
  )
}
