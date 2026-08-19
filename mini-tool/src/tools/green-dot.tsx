import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { PageSettings } from '@/types'

export const label = '绿点'

export function drawGreenDot(
  context: CanvasRenderingContext2D,
  x: number,
  y: number,
  settings: PageSettings,
  scale: number,
) {
  const step = settings.gridStep
  const cx = x + (settings.width / 2) * scale
  const cy = y + (settings.height / 2) * scale
  const cell = step * scale
  const dotRadius = Math.max(0.35 * scale, 0.4)

  const nMin = Math.ceil((settings.left + 0.5 - settings.width / 2) / step)
  const nMax = Math.floor((settings.width - settings.right - 0.5 - settings.width / 2) / step)
  const mMin = Math.ceil((-settings.height + settings.bottom + 1.5 - (-settings.height / 2)) / step)
  const mMax = Math.floor((-settings.top - 1.5 - (-settings.height / 2)) / step)

  context.save()
  context.fillStyle = settings.centerDotColor
  context.beginPath()
  context.arc(cx, cy, dotRadius, 0, Math.PI * 2)
  context.fill()
  context.restore()

  context.save()
  context.fillStyle = settings.dotColor
  for (let n = nMin; n <= nMax; n += 1) {
    for (let m = mMin; m <= mMax; m += 1) {
      if (n === 0 && m === 0) continue
      const dotX = cx + n * cell
      const dotY = cy + m * cell
      context.beginPath()
      context.arc(dotX, dotY, dotRadius, 0, Math.PI * 2)
      context.fill()
    }
  }
  context.restore()
}

function parseMillimeters(value: string | null): number {
  const n = parseFloat(value ?? '')
  return Number.isFinite(n) ? n : 0
}

interface GreenDotSettingsProps {
  settings: PageSettings
  setSettings: React.Dispatch<React.SetStateAction<PageSettings>>
}

export function GreenDotSettings({ settings, setSettings }: GreenDotSettingsProps) {
  return (
    <Card className="settings-card">
      <CardHeader><CardTitle>网格设置</CardTitle><CardDescription>网格间距与点颜色会同步应用于预览与 PNG 导出。</CardDescription></CardHeader>
      <CardContent>
        <div className="grid-settings-fields">
          <div className="grid-control">
            <Label htmlFor="grid-step">网格大小</Label>
            <Select value={`${settings.gridStep} mm`} onValueChange={(value) => setSettings((current) => ({ ...current, gridStep: parseMillimeters(value) }))}>
              <SelectTrigger id="grid-step" className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent align="start">
                <SelectItem value="2 mm">2 mm</SelectItem>
                <SelectItem value="3 mm">3 mm</SelectItem>
                <SelectItem value="4 mm">4 mm</SelectItem>
                <SelectItem value="5 mm">5 mm</SelectItem>
                <SelectItem value="6 mm">6 mm</SelectItem>
                <SelectItem value="7 mm">7 mm</SelectItem>
                <SelectItem value="8 mm">8 mm</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid-color-control">
            <Label htmlFor="dot-color">点颜色</Label>
            <div className="color-inputs">
              <Input id="dot-color" className="color-picker" type="color" value={settings.dotColor} onChange={(event) => setSettings((current) => ({ ...current, dotColor: event.target.value }))} aria-label="选择点颜色" />
              <Input className="color-hex" value={settings.dotColor.toUpperCase()} maxLength={7} spellCheck={false} onChange={(event) => { const value = event.target.value; if (/^#[0-9a-fA-F]{0,6}$/.test(value)) setSettings((current) => ({ ...current, dotColor: value })) }} onBlur={() => { if (!/^#[0-9a-fA-F]{6}$/.test(settings.dotColor)) setSettings((current) => ({ ...current, dotColor: '#39ff14' })) }} aria-label="点颜色 HEX 值" />
            </div>
          </div>
          <div className="grid-color-control">
            <Label htmlFor="center-dot-color">中心点颜色</Label>
            <div className="color-inputs">
              <Input id="center-dot-color" className="color-picker" type="color" value={settings.centerDotColor} onChange={(event) => setSettings((current) => ({ ...current, centerDotColor: event.target.value }))} aria-label="选择中心点颜色" />
              <Input className="color-hex" value={settings.centerDotColor.toUpperCase()} maxLength={7} spellCheck={false} onChange={(event) => { const value = event.target.value; if (/^#[0-9a-fA-F]{0,6}$/.test(value)) setSettings((current) => ({ ...current, centerDotColor: value })) }} onBlur={() => { if (!/^#[0-9a-fA-F]{6}$/.test(settings.centerDotColor)) setSettings((current) => ({ ...current, centerDotColor: '#960018' })) }} aria-label="中心点颜色 HEX 值" />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}