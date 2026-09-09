import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Home from './pages/Home'
import Install from './pages/Install'
import Docker from './pages/Docker'
import K8s from './pages/K8s'
import Operations from './pages/Operations'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="navbar">
          <div className="nav-brand">
            <a href="/">DM Database Skills</a>
          </div>
          <div className="nav-links">
            <NavLink to="/" end>首页</NavLink>
            <NavLink to="/install">安装</NavLink>
            <NavLink to="/docker">Docker</NavLink>
            <NavLink to="/k8s">K8s</NavLink>
            <NavLink to="/operations">运维</NavLink>
          </div>
        </nav>
        <main className="main">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/install" element={<Install />} />
            <Route path="/docker" element={<Docker />} />
            <Route path="/k8s" element={<K8s />} />
            <Route path="/operations" element={<Operations />} />
          </Routes>
        </main>
        <footer className="footer">
          <p>达梦数据库操作 SKILLS · 基于 TypeScript + React + Vite 构建</p>
        </footer>
      </div>
    </BrowserRouter>
  )
}

export default App
