import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import './index.css'

function App() {
  const [topic, setTopic] = useState('')
  const [folderPath, setFolderPath] = useState('')
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('')
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  const handleSelectFolder = async () => {
    try {
      const response = await fetch('http://localhost:8000/select_folder')
      if (!response.ok) throw new Error('Failed to open folder picker')
      const data = await response.json()
      if (data.folder_path) {
        setFolderPath(data.folder_path)
      }
    } catch (err) {
      console.error(err)
      alert('Error selecting folder: ' + err.message)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!topic || !folderPath) return
    
    setLoading(true)
    setError(null)
    setResults(null)
    setStatus('Initializing agents...')
    
    try {
      const response = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, folder_path: folderPath })
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to start generation')
      }
      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      
      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        
        for (const line of lines) {
          const cleanLine = line.trim()
          if (!cleanLine.startsWith('data: ')) continue
          
          const rawData = cleanLine.substring(6)
          try {
            const data = JSON.parse(rawData)
            if (data.error) {
              throw new Error(data.error)
            }
            if (data.step === 'complete') {
              setResults(data.result)
              setStatus('')
            } else {
              setStatus(data.status)
            }
          } catch (err) {
            console.error('Error parsing JSON from stream:', err)
          }
        }
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
      setStatus('')
    }
  }

  return (
    <div className="container">
      <div className="header">
        <h1>Course Generator</h1>
        <p>Agentic platform that instantly turns raw documents into structured learning modules.</p>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="topic">Topic Name</label>
            <input 
              type="text" 
              id="topic" 
              placeholder="e.g. Introduction to Quantum Computing" 
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              disabled={loading}
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="folderPath">Reference Documents Folder</label>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <input 
                type="text" 
                id="folderPath" 
                placeholder="Click Browse to select folder..." 
                value={folderPath}
                readOnly
                disabled={loading}
                required
                style={{ flex: 1 }}
              />
              <button 
                type="button" 
                className="btn" 
                onClick={handleSelectFolder} 
                disabled={loading}
                style={{ width: 'auto', padding: '0.75rem 1.25rem' }}
              >
                Browse
              </button>
            </div>
          </div>
          
          {error && <div style={{color: '#ef4444', marginBottom: '1rem'}}>{error}</div>}
          
          <button type="submit" className="btn" disabled={loading || !topic || !folderPath}>
            {loading ? (
              <><span className="loader"></span> {status || 'Designing Course...'}</>
            ) : 'Generate Course Content'}
          </button>
        </form>
      </div>

      {results && (
        results.objectives.includes('ERROR: UNRELATED') ? (
          <div className="card" style={{ border: '1px solid #ef4444', color: '#f87171', padding: '1.5rem 2rem' }}>
            <h2 style={{ color: '#ef4444', fontSize: '1.25rem', marginBottom: '0.5rem' }}>Generation Aborted</h2>
            <p style={{ color: '#f3f4f6' }}>
              The provided reference documents do not contain information related to the requested topic.
              No content was generated to prevent hallucination.
            </p>
          </div>
        ) : (
          <div className="results-grid">
            <div className="card result-section">
              <h2>1. Learning Objectives</h2>
              <div className="markdown-body">
                <ReactMarkdown>{results.objectives}</ReactMarkdown>
              </div>
            </div>
            
            <div className="card result-section">
              <h2>2. Content Sections</h2>
              <div className="markdown-body">
                <ReactMarkdown>{results.sections}</ReactMarkdown>
              </div>
            </div>
            
            <div className="card result-section">
              <h2>3. Practice Quizzes</h2>
              <div className="markdown-body">
                <ReactMarkdown>{results.quizzes}</ReactMarkdown>
              </div>
            </div>
            
            <div className="card result-section">
              <h2>4. Course Summary</h2>
              <div className="markdown-body">
                <ReactMarkdown>{results.summary}</ReactMarkdown>
              </div>
            </div>
          </div>
        )
      )}
    </div>
  )
}

export default App
