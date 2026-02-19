import { ChevronDown } from "lucide-react"
import { Button } from "@/components/ui/button"

interface ScrollToBottomProps {
  visible: boolean
  onClick: () => void
}

export function ScrollToBottom({ visible, onClick }: ScrollToBottomProps) {
  return (
    <div className="pointer-events-none absolute bottom-4 left-0 right-0 flex justify-center">
      <Button
        variant="secondary"
        size="icon"
        onClick={onClick}
        className={`pointer-events-auto h-8 w-8 rounded-full shadow-md transition-opacity ${
          visible ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
      >
        <ChevronDown className="h-4 w-4" />
      </Button>
    </div>
  )
}
