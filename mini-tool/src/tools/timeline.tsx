import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { PageSettings, BindingSide } from '@/types'

export const label = '时间轴'

export function drawTimeline(
  context: CanvasRenderingContext2D,
  x: number,
  y: number,
  settings: PageSettings,
  scale: number,
  bindingSide: BindingSide,
) {
  const usableHeight = settings.height - settings.top - settings.bottom
  const startHour = Math.max(0, Math.min(26, settings.timelineStart))
  const endHour = Math.max(startHour + 1, Math.min(26, settings.timelineEnd))
  const actualSide: 'left' | 'right' = (bindingSide === 'left' || bindingSide === 'right') ? bindingSide : 'left'
  const axisX = actualSide === 'left'
    ? x + settings.left * scale
    : x + (settings.width - settings.right) * scale
  const dir = actualSide === 'left' ? 1 : -1

  const hourHeight = (usableHeight / (endHour - startHour)) * scale
  const longTick = 7 * scale
  const shortTick = 3 * scale
  const labelGap = 3 * scale
  const labelSize = Math.max(3.6 * scale, 3)
  const lineWidth = Math.max(0.22 * scale, 0.2)
  const extensionEndX = actualSide === 'left'
    ? x + (settings.width * 2 / 3) * scale
    : x + (settings.width / 3) * scale

  context.save()
  context.strokeStyle = settings.timelineColor
  context.fillStyle = settings.timelineColor
  context.lineWidth = lineWidth
  context.lineCap = 'butt'
  context.font = `400 ${labelSize}px "3270 Nerd Font", sans-serif`
  context.textAlign = actualSide === 'left' ? 'right' : 'left'
  context.textBaseline = 'middle'

  for (let hour = startHour; hour <= endHour; hour += 1) {
    const posY = y + (settings.top + ((hour - startHour) / (endHour - startHour)) * usableHeight) * scale

    context.beginPath()
    context.moveTo(axisX, posY)
    context.lineTo(axisX + dir * longTick, posY)
    context.stroke()

    const extensionStartX = axisX + dir * longTick
    const extensionLength = Math.abs(extensionEndX - extensionStartX)
    const dotSpacing = hourHeight / 2
    for (let distance = dotSpacing; distance < extensionLength; distance += dotSpacing) {
      context.beginPath()
      context.arc(extensionStartX + dir * distance, posY, lineWidth / 2, 0, Math.PI * 2)
      context.fill()
    }

    const label = String(hour).padStart(2, '0')
    const labelX = actualSide === 'left' ? axisX - labelGap : axisX + labelGap
    context.fillText(label, labelX, posY + 0.4 * scale)

    if (hour < endHour) {
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
      <CardHeader><CardTitle>时间轴设置</CardTitle><CardDescription>刻度固定显示在装订内侧，可设置起止时间和页数。</CardDescription></CardHeader>
      <CardContent>
        <div className="timeline-controls">
          <div className="timeline-pages-control">
            <Label htmlFor="timeline-pages">时间轴页数</Label>
            <Select value={`${settings.timelinePages} 页`} onValueChange={(value) => setSettings((current) => ({ ...current, timelinePages: value === '2 页' ? 2 : 1 }))}>
              <SelectTrigger id="timeline-pages" className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent align="start">
                <SelectItem value="1 页">单页</SelectItem>
                <SelectItem value="2 页">左右排版 · 2 页</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {settings.timelinePages === 2 && <div className="timeline-pages-control">
            <Label htmlFor="timeline-swap-pages">左右页时间轴</Label>
            <Select value={settings.timelineSwapPages ? '交换' : '默认'} onValueChange={(value) => setSettings((current) => ({ ...current, timelineSwapPages: value === '交换' }))}>
              <SelectTrigger id="timeline-swap-pages" className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent align="start">
                <SelectItem value="默认">默认顺序</SelectItem>
                <SelectItem value="交换">交换左右页</SelectItem>
              </SelectContent>
            </Select>
          </div>}
          <div className="timeline-range-controls">
            <div className="number-field">
              <Label htmlFor="timeline-start">开始时间</Label>
              <div className="input-with-unit">
                <Input id="timeline-start" type="number" min="0" max="25" step="1" value={settings.timelineStart} onChange={(event) => {
                  const value = Math.max(0, Math.min(settings.timelineEnd - 1, Number(event.target.value) || 0))
                  setSettings((current) => ({ ...current, timelineStart: value }))
                }} />
                <span>时</span>
              </div>
            </div>
            <div className="number-field">
              <Label htmlFor="timeline-end">结束时间</Label>
              <div className="input-with-unit">
                <Input id="timeline-end" type="number" min="1" max="26" step="1" value={settings.timelineEnd} onChange={(event) => {
                  const value = Math.max(settings.timelineStart + 1, Math.min(26, Number(event.target.value) || 1))
                  setSettings((current) => ({ ...current, timelineEnd: value }))
                }} />
                <span>时</span>
              </div>
            </div>
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