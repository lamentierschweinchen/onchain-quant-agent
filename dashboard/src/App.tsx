import { useRoute } from './hooks/useRoute'
import { HomePage } from './pages/HomePage'
import { CodePage } from './pages/CodePage'

function App() {
  const { path } = useRoute()

  if (path === '/code' || path.startsWith('/code/')) {
    return <CodePage />
  }

  return <HomePage />
}

export default App
