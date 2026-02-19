import { useRef, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { MessageSquare, Trash2 } from "lucide-react"
import type { Thread } from "@/types"

interface ThreadListProps {
  threads: Thread[]
  activeThreadId: string | null
  onSelect: (threadId: string) => void
  onCreate: () => void
  onDelete: (threadId: string) => void
}

const SWIPE_THRESHOLD = 80
const CLICK_TOLERANCE = 5

interface DragState {
  startX: number
  currentX: number
  isDragging: boolean
  pointerId: number | null
}

function SwipeableThread({
  thread,
  isActive,
  onSelect,
  onDelete,
}: {
  thread: Thread
  isActive: boolean
  onSelect: () => void
  onDelete: () => void
}) {
  const foregroundRef = useRef<HTMLDivElement>(null)
  const dragState = useRef<DragState>({
    startX: 0,
    currentX: 0,
    isDragging: false,
    pointerId: null,
  })

  const handlePointerDown = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      const el = foregroundRef.current
      if (!el) return

      el.setPointerCapture(e.pointerId)
      el.style.transition = "none"

      dragState.current = {
        startX: e.clientX,
        currentX: e.clientX,
        isDragging: false,
        pointerId: e.pointerId,
      }
    },
    []
  )

  const handlePointerMove = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      const state = dragState.current
      if (state.pointerId === null) return

      const dx = e.clientX - state.startX
      state.currentX = e.clientX

      if (Math.abs(dx) > CLICK_TOLERANCE) {
        state.isDragging = true
      }

      if (state.isDragging && foregroundRef.current) {
        // Only allow dragging left (negative direction)
        const offset = Math.min(0, dx)
        foregroundRef.current.style.transform = `translateX(${offset}px)`
      }
    },
    []
  )

  const handlePointerUp = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      const el = foregroundRef.current
      const state = dragState.current
      if (!el || state.pointerId === null) return

      el.releasePointerCapture(e.pointerId)
      el.style.transition = "transform 200ms ease-out"

      const dx = e.clientX - state.startX

      if (!state.isDragging) {
        // It was a click, not a drag
        el.style.transform = "translateX(0)"
        state.pointerId = null
        onSelect()
        return
      }

      if (dx < -SWIPE_THRESHOLD) {
        // Swiped past threshold — archive
        el.style.transform = "translateX(-100%)"
        setTimeout(onDelete, 200)
      } else {
        // Snap back
        el.style.transform = "translateX(0)"
      }

      state.pointerId = null
      state.isDragging = false
    },
    [onSelect, onDelete]
  )

  const handlePointerCancel = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      const el = foregroundRef.current
      if (!el) return
      el.releasePointerCapture(e.pointerId)
      el.style.transition = "transform 200ms ease-out"
      el.style.transform = "translateX(0)"
      dragState.current.pointerId = null
      dragState.current.isDragging = false
    },
    []
  )

  return (
    <div className="relative overflow-hidden rounded-lg">
      {/* Background layer — red archive zone */}
      <div className="absolute inset-0 flex items-center justify-end bg-destructive px-4 text-destructive-foreground">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Archive</span>
          <Trash2 className="h-4 w-4" />
        </div>
      </div>

      {/* Foreground layer — the actual thread button */}
      <div
        ref={foregroundRef}
        className={`relative flex cursor-pointer select-none items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors active:scale-[0.98] ${
          isActive
            ? "border-border bg-accent shadow-sm"
            : "border-transparent bg-background hover:bg-accent"
        }`}
        style={{ touchAction: "pan-y" }}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerCancel}
      >
        <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />
        <span className="truncate">{thread.title}</span>
      </div>
    </div>
  )
}

export function ThreadList({
  threads,
  activeThreadId,
  onSelect,
  onCreate,
  onDelete,
}: ThreadListProps) {
  return (
    <div className="flex h-full flex-col">
      <div className="p-3">
        <Button onClick={onCreate} className="w-full" variant="outline">
          + New Chat
        </Button>
      </div>
      <Separator />
      <ScrollArea className="flex-1">
        <div className="space-y-1 p-2">
          {threads.map((thread) => (
            <SwipeableThread
              key={thread.id}
              thread={thread}
              isActive={thread.id === activeThreadId}
              onSelect={() => onSelect(thread.id)}
              onDelete={() => onDelete(thread.id)}
            />
          ))}
          {threads.length === 0 && (
            <p className="px-3 py-2 text-sm text-muted-foreground">
              No conversations yet
            </p>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
