import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { PageSettings } from '@/types'

export const label = '余白方格'

function isMarker(index: number, count: number) {
  const middle = Math.floor(count / 2)
  return index > 0 && index < count && (index - middle) % 10 === 0
}

export function drawMidoriGrid(
  context: CanvasRenderingContext2D,
  x: number,
  y: number,
  settings: PageSettings,
  scale: number,
) {
  const usableWidth = settings.width - settings.left - settings.right
  const usableHeight = settings.height - settings.top - settings.bottom
  if (usableWidth <= 0 || usableHeight <= 0) return

  const step = settings.gridStep
  const columns = Math.floor(usableWidth / step)
  const rows = Math.floor(usableHeight / step)
  if (columns < 1 || rows < 1) return

  const gridWidth = columns * step
  const gridHeight = rows * step
  const startX = x + (settings.left + (usableWidth - gridWidth) / 2) * scale
  const startY = y + (settings.top + (usableHeight - gridHeight) / 2) * scale
  const cell = step * scale
  const lineGap = Math.max(0.75 * scale, 0.65)
  const extensionGap = Math.max(scale, 0.8)
  const extension = Math.max(1.2 * scale, 1)

  context.save()
  context.strokeStyle = settings.gridColor
  context.fillStyle = settings.gridColor
  context.lineWidth = Math.max(0.3 * scale, 0.25)
  context.lineCap = 'butt'

  for (let row = 0; row <= rows; row += 1) {
    const lineY = startY + row * cell
    context.beginPath()
    context.moveTo(startX, lineY)
    context.lineTo(startX + gridWidth * scale, lineY)
    context.stroke()

    if (row > 0 && row < rows && row % 2 === 0 && !isMarker(row, rows)) {
      context.beginPath()
      context.moveTo(startX - extensionGap - extension, lineY)
      context.lineTo(startX - extensionGap, lineY)
      context.moveTo(startX + gridWidth * scale + extensionGap, lineY)
      context.lineTo(startX + gridWidth * scale + extensionGap + extension, lineY)
      context.stroke()
    }
  }

  for (let column = 0; column <= columns; column += 1) {
    const lineX = startX + column * cell
    for (let row = 0; row < rows; row += 1) {
      context.beginPath()
      context.moveTo(lineX, startY + row * cell + lineGap)
      context.lineTo(lineX, startY + (row + 1) * cell)
      context.stroke()
    }

    if (column > 0 && column < columns && column % 2 === 0 && !isMarker(column, columns)) {
      context.beginPath()
      context.moveTo(lineX, startY - extensionGap - extension)
      context.lineTo(lineX, startY - extensionGap)
      context.moveTo(lineX, startY + gridHeight * scale + extensionGap)
      context.lineTo(lineX, startY + gridHeight * scale + extensionGap + extension)
      context.stroke()
    }
  }

  for (let column = 1; column < columns; column += 1) {
    if (!isMarker(column, columns)) continue
    const dotX = startX + column * cell
    const radius = Math.max(0.7 * scale, 0.85)
    context.beginPath()
    context.arc(dotX, startY - 1.5 * scale, radius, 0, Math.PI * 2)
    context.arc(dotX, startY + gridHeight * scale + 1.5 * scale, radius, 0, Math.PI * 2)
    context.fill()
  }

  for (let row = 1; row < rows; row += 1) {
    if (!isMarker(row, rows)) continue
    const dotY = startY + row * cell
    const radius = Math.max(0.7 * scale, 0.85)
    context.beginPath()
    context.arc(startX - 1.5 * scale, dotY, radius, 0, Math.PI * 2)
    context.arc(startX + gridWidth * scale + 1.5 * scale, dotY, radius, 0, Math.PI * 2)
    context.fill()
  }

  context.restore()
}

function parseMillimeters(value: string | null): number {
  const n = parseFloat(value ?? '')
  return Number.isFinite(n) ? n : 0
}

interface MidoriGridSettingsProps {
  settings: PageSettings
  setSettings: React.Dispatch<React.SetStateAction<PageSettings>>
}

export function MidoriGridSettings({ settings, setSettings }: MidoriGridSettingsProps) {
  return (
    <Card className="settings-card">
      <CardHeader><CardTitle>网格设置</CardTitle><CardDescription>网格间距会同步应用于预览与 PNG 导出。</CardDescription></CardHeader>
      <CardContent>
        <div className="grid-settings-fields">
          <div className="grid-control">
            <Label htmlFor="grid-step">网格大小</Label>
            <Select value={`${settings.gridStep} mm`} onValueChange={(value) => setSettings((current) => ({ ...current, gridStep: parseMillimeters(value) }))}>
              <SelectTrigger id="grid-step" className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent align="start">
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
            <Label htmlFor="grid-color">网格颜色</Label>
            <div className="color-inputs">
              <Input id="grid-color" className="color-picker" type="color" value={settings.gridColor} onChange={(event) => setSettings((current) => ({ ...current, gridColor: event.target.value }))} aria-label="选择网格颜色" />
              <Input className="color-hex" value={settings.gridColor.toUpperCase()} maxLength={7} spellCheck={false} onChange={(event) => { const value = event.target.value; if (/^#[0-9a-fA-F]{0,6}$/.test(value)) setSettings((current) => ({ ...current, gridColor: value })) }} onBlur={() => { if (!/^#[0-9a-fA-F]{6}$/.test(settings.gridColor)) setSettings((current) => ({ ...current, gridColor: '#99def9' })) }} aria-label="网格颜色 HEX 值" />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}