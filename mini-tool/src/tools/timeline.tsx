import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { PageSettings, TimelineSide, BindingSide } from '@/types'

export const label = '时间轴'

export function drawTimeline(
  context: CanvasRenderingContext2D,
  x: number,
  y: number,
  settings: PageSettings,
  scale: number,
  side: TimelineSide,
  bindingSide: BindingSide,
) {
  const usableHeight = settings.height - settings.top - settings.bottom
  const horizontalBinding = (bindingSide === 'left' || bindingSide === 'right') ? bindingSide : 'left'
  const actualSide: 'left' | 'right' = side === 'binding'
    ? horizontalBinding
    : (horizontalBinding === 'left' ? 'right' : 'left')
  const axisX = actualSide === 'left'
    ? x + settings.left * scale
    : x + (settings.width - settings.right) * scale
  const dir = actualSide === 'left' ? 1 : -1

  const hourHeight = (usableHeight / 24) * scale
  const longTick = 7 * scale
  const shortTick = 3 * scale
  const labelGap = 3 * scale
  const labelSize = Math.max(3.6 * scale, 3)

  context.save()
  context.strokeStyle = settings.timelineColor
  context.fillStyle = settings.timelineColor
  context.lineWidth = Math.max(0.22 * scale, 0.2)
  context.lineCap = 'butt'
  context.font = `400 ${labelSize}px "3270 Nerd Font", sans-serif`
  context.textAlign = actualSide === 'left' ? 'right' : 'left'
  context.textBaseline = 'middle'

  for (let hour = 0; hour <= 24; hour += 1) {
    const posY = y + (settings.top + (hour / 24) * usableHeight) * scale

    context.beginPath()
    context.moveTo(axisX, posY)
    context.lineTo(axisX + dir * longTick, posY)
    context.stroke()

    const label = String(hour).padStart(2, '0')
    const labelX = actualSide === 'left' ? axisX - labelGap : axisX + labelGap
    context.fillText(label, labelX, posY + 0.4 * scale)

    if (hour < 24) {
      const halfY = posY + hourHeight / 2
      context.beginPath()
      context.moveTo(axisX, halfY)
      context.lineTo(axisX + dir * shortTick, halfY)
      context.stroke()
    }
  }

  context.restore()
}

interface TimelineSettingsProps {
  settings: PageSettings
  setSettings: React.Dispatch<React.SetStateAction<PageSettings>>
}

export function TimelineSettings({ settings, setSettings }: TimelineSettingsProps) {
  return (
    <Card className="settings-card">
      <CardHeader><CardTitle>时间轴设置</CardTitle><CardDescription>选择刻度出现在装订边还是外侧。</CardDescription></CardHeader>
      <CardContent>
        <div className="timeline-controls">
          <div className="timeline-side-control">
            <Label htmlFor="timeline-side">刻度位置</Label>
            <Select value={settings.timelineSide} onValueChange={(value) => setSettings((current) => ({ ...current, timelineSide: value as TimelineSide }))}>
              <SelectTrigger id="timeline-side" className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent align="start">
                <SelectItem value="binding">装订边</SelectItem>
                <SelectItem value="outer">外侧</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid-color-control">
            <Label htmlFor="timeline-color">刻度颜色</Label>
            <div className="color-inputs">
              <Input id="timeline-color" className="color-picker" type="color" value={settings.timelineColor} onChange={(event) => setSettings((current) => ({ ...current, timelineColor: event.target.value }))} aria-label="选择刻度颜色" />
              <Input className="color-hex" value={settings.timelineColor.toUpperCase()} maxLength={7} spellCheck={false} onChange={(event) => { const value = event.target.value; if (/^#[0-9a-fA-F]{0,6}$/.test(value)) setSettings((current) => ({ ...current, timelineColor: value })) }} onBlur={() => { if (!/^#[0-9a-fA-F]{6}$/.test(settings.timelineColor)) setSettings((current) => ({ ...current, timelineColor: '#3D4843' })) }} aria-label="刻度颜色 HEX 值" />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}