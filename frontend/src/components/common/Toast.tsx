import { useEffect, useState } from 'react'
import { clsx } from 'clsx'
import { X, CheckCircle, AlertTriangle, XCircle, Info } from 'lucide-react'

interface ToastProps {
  message: string
  type?: 'success' | 'error' | 'warning' | 'info'
  duration?: number
  onClose: () => void
}

const icons = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
}

export default function Toast({ message, type = 'info', duration = 4000, onClose }: ToastProps) {
  const [visible, setVisible] = useState(true)
  const Icon = icons[type]

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false)
      setTimeout(onClose, 300)
    }, duration)
    return () => clearTimeout(timer)
  }, [duration, onClose])

  return (
    <div
      className={clsx(
        'fixed bottom-4 right-4 z-50 flex items-center gap-3 rounded-lg px-4 py-3 shadow-lg transition-all',
        visible ? 'translate-y-0 opacity-100' : 'translate-y-2 opacity-0',
        {
          'bg-green-600 text-white': type === 'success',
          'bg-red-600 text-white': type === 'error',
          'bg-yellow-500 text-dark-900': type === 'warning',
          'bg-blue-600 text-white': type === 'info',
        },
      )}
    >
      <Icon className="h-5 w-5 flex-shrink-0" />
      <span className="text-sm">{message}</span>
      <button onClick={onClose} className="ml-2 rounded p-0.5 hover:bg-white/20">
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}
