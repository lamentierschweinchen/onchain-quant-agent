import { useRoute } from './hooks/useRoute'
import { HomePage } from './pages/HomePage'
import { CodePage } from './pages/CodePage'
import { PumpPage } from './pages/PumpPage'

function App() {
  const { path } = useRoute()

  if (path === '/code' || path.startsWith('/code/')) {
    return <CodePage />
  }

  if (path === '/pump' || path.startsWith('/pump/')) {
    return <PumpPage />
  }

  return <HomePage />
}

export default App
