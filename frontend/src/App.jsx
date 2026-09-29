import { useRef, useState } from 'react'
import {
  ArrowUpRight,
  Check,
  Clipboard,
  FileCheck2,
  FileText,
  FileUp,
  LoaderCircle,
  Scale,
  ShieldCheck,
  Sparkles,
  X,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './App.css'

async function requestJson(path, options = {}) {
  let response

  try {
    response = await fetch(path, options)
  } catch {
    throw new Error(
      'Could not reach the API. Check that the FastAPI service is running and try again.',
    )
  }

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = typeof payload?.detail === 'string' ? payload.detail : null
    throw new Error(detail || `The API returned an error (${response.status}).`)
  }

  return payload
}

function readableSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function App() {
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [contract, setContract] = useState(null)
  const [question, setQuestion] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [phase, setPhase] = useState('idle')
  const [error, setError] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [copied, setCopied] = useState(false)

  const busy = phase !== 'idle'

  function chooseFile(nextFile) {
    if (!nextFile) return
    const extension = nextFile.name.split('.').pop()?.toLowerCase()
    if (!['pdf', 'txt'].includes(extension)) {
      setError('Choose a PDF or TXT file to continue.')
      return
    }

    setFile(nextFile)
    setContract(null)
    setAnalysis(null)
    setError('')
    setCopied(false)
  }

  function clearFile() {
    setFile(null)
    setContract(null)
    setAnalysis(null)
    setError('')
    if (inputRef.current) inputRef.current.value = ''
  }

  async function submitReview(event) {
    event.preventDefault()
    if (!file && !contract) {
      setError('Add a document before starting the review.')
      return
    }

    setError('')
    setCopied(false)

    try {
      let currentContract = contract

      if (!currentContract) {
        setPhase('uploading')
        const formData = new FormData()
        formData.append('file', file)
        currentContract = await requestJson('/contracts/upload', {
          method: 'POST',
          body: formData,
        })
        setContract(currentContract)
      }

      setPhase('analyzing')
      const payload = { question: question.trim() }
      const result = await requestJson(
        `/analysis/analyze/${encodeURIComponent(currentContract.id)}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        },
      )
      setAnalysis(result)
    } catch (submitError) {
      setError(submitError.message || 'The review could not be completed.')
    } finally {
      setPhase('idle')
    }
  }

  async function copyAnalysis() {
    if (!analysis?.analysis) return
    try {
      await navigator.clipboard.writeText(analysis.analysis)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1800)
    } catch {
      setError('Clipboard access is unavailable in this browser.')
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Vakil Vision home">
          <span className="brand-mark"><Scale size={19} strokeWidth={1.8} /></span>
          <span className="brand-copy">
            <strong>vakil<span>vision</span></strong>
            <small>CONTRACT REVIEW</small>
          </span>
        </a>
        <div className="topbar-right">
          <span className="topbar-label"><ShieldCheck size={15} /> Document workspace</span>
          <a className="docs-link" href="/docs" target="_blank" rel="noreferrer">
            API docs <ArrowUpRight size={14} />
          </a>
        </div>
      </header>

      <main className="workspace">
        <div className="page-heading">
          <div>
            <p className="eyebrow">YOUR REVIEW DESK <span> / </span> NEW ANALYSIS</p>
            <h1>Bring the details<br className="desktop-break" /> into focus.</h1>
            <p className="page-intro">
              Upload a contract and get a source-cited summary grounded in the document.
            </p>
          </div>
          <div className="heading-mark" aria-hidden="true">
            <span>V</span><i>V</i>
          </div>
        </div>

        <div className="review-grid">
          <section className="review-card input-card" aria-labelledby="review-title">
            <div className="card-heading">
              <div className="step-label"><span>01</span> DOCUMENT & QUESTION</div>
              <div className="secure-note"><ShieldCheck size={14} /> Source-grounded</div>
            </div>

            <h2 id="review-title">Start a review</h2>
            <p className="card-description">Choose a file, then ask about a specific clause or leave the question blank for a key-terms review.</p>

            <form onSubmit={submitReview}>
              <input
                ref={inputRef}
                className="visually-hidden"
                type="file"
                accept=".pdf,.txt,application/pdf,text/plain"
                onChange={(event) => chooseFile(event.target.files?.[0])}
                aria-label="Choose a PDF or TXT document"
              />

              {file ? (
                <div className="selected-file">
                  <div className="file-type-icon"><FileText size={19} /></div>
                  <div className="selected-file-copy">
                    <strong title={file.name}>{file.name}</strong>
                    <span>{readableSize(file.size)} <span className="dot-separator">·</span> Ready to review</span>
                  </div>
                  <button className="icon-button remove-file" type="button" onClick={clearFile} aria-label="Remove selected document" disabled={busy}>
                    <X size={17} />
                  </button>
                </div>
              ) : (
                <button
                  className={`drop-zone${isDragging ? ' is-dragging' : ''}`}
                  type="button"
                  onClick={() => inputRef.current?.click()}
                  onDragOver={(event) => { event.preventDefault(); setIsDragging(true) }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={(event) => {
                    event.preventDefault()
                    setIsDragging(false)
                    chooseFile(event.dataTransfer.files?.[0])
                  }}
                  disabled={busy}
                >
                  <span className="drop-icon"><FileUp size={21} strokeWidth={1.8} /></span>
                  <span className="drop-copy"><strong>Drop your document here</strong><span>or <u>browse files</u> from your device</span></span>
                  <span className="file-format">PDF <i /> TXT</span>
                </button>
              )}

              <label className="question-label" htmlFor="question">What would you like to know? <span>OPTIONAL</span></label>
              <textarea
                id="question"
                className="question-input"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="e.g. What does the agreement say about termination?"
                maxLength={4000}
                rows={3}
                disabled={busy}
              />
              <div className="question-foot"><span>Answers use only the uploaded document.</span><span>{question.length}/4000</span></div>

              {error && (
                <div className="error-message" role="alert">
                  <span className="error-dot" />
                  <p>{error}</p>
                </div>
              )}

              <button className="submit-button" type="submit" disabled={busy || (!file && !contract)}>
                {busy ? (
                  <><LoaderCircle className="spin" size={17} /> {phase === 'uploading' ? 'Uploading document…' : 'Reading the document…'}</>
                ) : (
                  <>{contract ? 'Ask this document' : 'Upload & analyze'} <Sparkles size={16} /></>
                )}
              </button>
            </form>

            <div className="process-note">
              <div className={`process-step${contract ? ' is-complete' : ''}`}><span>{contract ? <Check size={12} /> : '1'}</span><p>Upload source</p></div>
              <div className="process-line" />
              <div className={`process-step${analysis ? ' is-complete' : ''}${phase === 'analyzing' ? ' is-active' : ''}`}><span>{analysis ? <Check size={12} /> : phase === 'analyzing' ? <LoaderCircle className="spin" size={12} /> : '2'}</span><p>Read analysis</p></div>
            </div>
          </section>

          <section className={`review-card result-card${analysis ? ' has-analysis' : ''}`} aria-labelledby="analysis-title" aria-live="polite">
            <div className="card-heading result-heading">
              <div className="step-label"><span>02</span> FINDINGS</div>
              {analysis ? (
                <button className="copy-button" type="button" onClick={copyAnalysis}>
                  {copied ? <Check size={14} /> : <Clipboard size={14} />}{copied ? 'Copied' : 'Copy summary'}
                </button>
              ) : <span className="pending-label">AWAITING SOURCE</span>}
            </div>

            <div className="result-title-row">
              <div><h2 id="analysis-title">Analysis</h2><p className="card-description">The document’s language, with citations to its source.</p></div>
              {analysis && <span className="ready-badge"><span /> Ready</span>}
            </div>

            {analysis ? (
              <>
                <div className="source-summary">
                  <span className="source-icon"><FileCheck2 size={16} /></span>
                  <div className="source-copy"><strong>{analysis.document_name || contract?.original_filename || 'Uploaded document'}</strong><span>{analysis.question || 'Key-terms review'} <span className="dot-separator">·</span> gpt-6-luna</span></div>
                </div>
                <div className="analysis-body">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{analysis.analysis}</ReactMarkdown>
                </div>
                <div className="analysis-footnote"><ShieldCheck size={14} /> Summary of retrieved text. Verify every citation against the original.</div>
              </>
            ) : (
              <div className="empty-result">
                <div className="empty-document" aria-hidden="true"><FileText size={24} strokeWidth={1.5} /><span><i /><i /><i /></span></div>
                <h3>Your findings will appear here</h3>
                <p>Upload a contract to see a concise answer with page citations and relevant excerpts.</p>
                <div className="empty-tags"><span><Check size={12} /> Precise quotes</span><span><Check size={12} /> Page references</span></div>
              </div>
            )}
          </section>
        </div>

        <footer className="workspace-footer">
          <span><Scale size={15} /> VAKIL VISION</span>
          <p>This is a summary of retrieved documents, not legal advice.</p>
        </footer>
      </main>
    </div>
  )
}

export default App
