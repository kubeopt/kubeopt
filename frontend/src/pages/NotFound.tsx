import { Link } from 'react-router-dom'
import Button from '../components/common/Button'

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-dark-950">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-dark-300 dark:text-dark-600">404</h1>
        <p className="mt-2 text-lg text-dark-600 dark:text-dark-400">Page not found</p>
        <Link to="/" className="mt-6 inline-block">
          <Button>Go to Portfolio</Button>
        </Link>
      </div>
    </div>
  )
}
