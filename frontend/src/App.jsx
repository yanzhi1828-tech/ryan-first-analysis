import { useState } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import './App.css'

function App() {
  const [query, setQuery] = useState('')
  const [data, setData] = useState(null)
  const [analysis, setAnalysis] = useState('')
  const [loading, setLoading] = useState(false)
  const [aiLoading, setAiLoading] = useState(false)
  const [error, setError] = useState('')

  // 搜索功能
  const handleSearch = async () => {
    if (!query) return
    setLoading(true)
    setError('')
    setData(null)
    setAnalysis('')

    try {
      // 后端会自动处理你是输的名字还是代码
      const response = await axios.get(`https://ryan-first-analysis.onrender.com/api/stock/${query}`)
      
      if (response.data.error) {
        setError(response.data.error)
      } else {
        setData(response.data)
      }
    } catch (err) {
      setError("无法连接后端服务")
    }
    setLoading(false)
  }

  // AI 分析功能
  const handleAnalyze = async () => {
    if (!data) return
    setAiLoading(true)
    try {
      const response = await axios.post(`https://ryan-first-analysis.onrender.com/api/analyze`, {
        symbol: data.symbol,
        name: data.name,
        price: data.price,
        change: data.percent_change
      })
      setAnalysis(response.data.analysis)
    } catch (err) {
      alert("AI分析失败")
    }
    setAiLoading(false)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') handleSearch()
  }

  return (
    <div className="app-layout">
      {/* === 左侧：Sidebar (搜索 + 核心数据) === */}
      <div className="sidebar">
        <div className="brand">
          <h2>Ryan's Analysis</h2>
          <span className="version-tag">FIRST EDITION</span>
        </div>

        <div className="search-container">
          <input 
            type="text" 
            placeholder="Search (e.g. Apple, NVDA)" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button onClick={handleSearch} disabled={loading}>
            {loading ? "SEARCHING..." : "GO"}
          </button>
        </div>
        
        {error && <div className="error-box">{error}</div>}

        {/* 如果有数据，显示在左侧边栏 */}
        {data && (
          <div className="mini-dashboard fade-in">
            <div className="stock-header">
              <h1>{data.symbol}</h1>
              <p>{data.name}</p>
            </div>
            
            <div className="price-display">
              <span className="big-price">${data.price.toFixed(2)}</span>
              <span className={`change-tag ${data.change >= 0 ? 'green' : 'red'}`}>
                {data.change > 0 ? '+' : ''}{data.change.toFixed(2)} ({data.percent_change.toFixed(2)}%)
              </span>
            </div>

            <button 
              className="ai-trigger-btn" 
              onClick={handleAnalyze} 
              disabled={aiLoading}
            >
              {aiLoading ? "Ryan is thinking ing..." : "⚡️ 生成深度研报"}
            </button>
          </div>
        )}
      </div>

      {/* === 右侧：Main Content (图表 + AI 分析) === */}
      <div className="main-content">
        {!data && (
          <div className="empty-state">
            <h1>Welcome to Ryan's Terminal</h1>
            <p>Enter a company name or ticker on the left to start.</p>
          </div>
        )}

        {data && (
          <div className="content-scroll fade-in">
            {/* 1. 走势图模块 */}
            <div className="chart-card">
              <h3>📉 30-Day Trend ({data.symbol})</h3>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.history}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="date" hide />
                    <YAxis domain={['auto', 'auto']} orientation="right" tick={{fill: '#888'}} />
                    <Tooltip 
                      contentStyle={{backgroundColor: '#111', border: '1px solid #444'}}
                      itemStyle={{color: '#fff'}}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="price" 
                      stroke="#00C805" 
                      strokeWidth={2} 
                      dot={false} 
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* 2. AI 分析报告模块 */}
            {analysis && (
              <div className="analysis-card fade-in">
                <div className="markdown-body">
                  <ReactMarkdown>{analysis}</ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App