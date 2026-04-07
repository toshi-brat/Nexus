import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Overview from './pages/Overview'
import Sentiment from './pages/Sentiment'
import Portfolio from './pages/Portfolio'
import PaperTrade from './pages/PaperTrade'
import Analysis from './pages/Analysis'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Overview />} />
          <Route path="sentiment" element={<Sentiment />} />
          <Route path="portfolio" element={<Portfolio />} />
          <Route path="paper" element={<PaperTrade />} />
          <Route path="analysis" element={<Analysis />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
