import { useEffect, Fragment, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectSeparator, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import './App.css'

type Tool = 'green-dot' | 'midori-grid'
type LayoutMode = 'center' | 'spread'
type Dimension = 'width' | 'height'
type Margin = 'top' | 'right' | 'bottom' | 'left'
type BindingSide = 'left' | 'right' | 'top' | 'bottom'
type PunchSide = '长边打孔' | '短边打孔'

const PRESETS = {
  // ── TN ──
  tn: { label: 'TN', note: '110 × 210 mm', width: 110, height: 210 },
  tnp: { label: 'TN-P', note: '88 × 125 mm', width: 88, height: 125 },
  // ── A5 ──
  a5: { label: 'A5', note: '148 × 210 mm', width: 148, height: 210 },
  a5fc: { label: 'A5 FC', note: '107 × 172 mm', width: 107, height: 172 },
  a5s: { label: 'A5 Slim', note: '110 × 210 mm', width: 110, height: 210 },
  // ── A6 ──
  a6per: { label: 'A6 Personal', note: '95 × 172 mm', width: 95, height: 172 },
  a6s: { label: 'A6 Slim', note: '80 × 172 mm', width: 80, height: 172 },
  a6standard: { label: 'A6 Standard', note: '105 × 148 mm', width: 105, height: 148 },
  // ── A7 ──
  '120a7': { label: '120A7', note: '80 × 120 mm', width: 80, height: 120 },
  '127a7': { label: '127A7', note: '80 × 127 mm', width: 80, height: 127 },
  // ── M5 ──
  '62m5': { label: '62M5', note: '62 × 105 mm', width: 62, height: 105 },
  '67m5': { label: '67M5', note: '67 × 105 mm', width: 67, height: 105 },
  '67m5l': { label: '67M5L', note: '105 × 67 mm', width: 105, height: 67 },
  '74m5': { label: '74M5', note: '74 × 105 mm', width: 74, height: 105 },
  // ── 其他 ──
  a4: { label: 'A4', note: '210 × 297 mm', width: 210, height: 297 },
  b5: { label: 'B5', note: '176 × 250 mm', width: 176, height: 250 },
} as const

const PRESET_GROUPS = [
  { label: 'TN', keys: ['tn', 'tnp'] as const },
  { label: 'A5', keys: ['a5', 'a5fc', 'a5s'] as const },
  { label: 'A6', keys: ['a6per', 'a6s', 'a6standard'] as const },
  { label: 'A7', keys: ['120a7', '127a7'] as const },
  { label: 'M5', keys: ['62m5', '67m5', '67m5l', '74m5'] as const },
  { label: '其他', keys: ['a4', 'b5'] as const },
] as const

const PRESET_ITEMS = Object.entries(PRESETS).map(([key, option]) => ({
  value: key,
  label: `${option.label} · ${option.note}`,
}))

type Preset = keyof typeof PRESETS

interface PageSettings {
  width: number
  height: number
  top: number
  right: number
  bottom: number
  left: number
  gridStep: number
  gridColor: string
  dotColor: string
  centerDotColor: string
  showPunchHoles: boolean
  holeDiameter: 4 | 5
  punchSide: PunchSide
  layout: LayoutMode
}

interface XhsMiniTool {
  saveImageToPhotosAlbum: (options: { filePath: string }) => Promise<unknown>
}

declare global {
  interface Window {
    xhs?: { miniTool?: XhsMiniTool }
  }
}

const PRINT_DPI = 300
const PIXELS_PER_MM = PRINT_DPI / 25.4
const TEX_GRID_LINE_WIDTH_MM = (0.7 * 25.4) / 72
const MAX_EXPORT_DIMENSION = 16384

const DEFAULT_SETTINGS: PageSettings = {
  width: 148,
  height: 210,
  top: 10,
  right: 5,
  bottom: 10,
  left: 15,
  gridStep: 3,
  gridColor: '#99def9',
  dotColor: '#39ff14',
  centerDotColor: '#960018',
  showPunchHoles: true,
  holeDiameter: 4,
  punchSide: '长边打孔',
  layout: 'center',
}

function isMarker(index: number, count: number) {
  const middle = Math.floor(count / 2)
  return index > 0 && index < count && (index - middle) % 10 === 0
}

function parseMillimeters(value: string | null): number {
  const n = parseFloat(value ?? '')
  return Number.isFinite(n) ? n : 0
}

// ── Green Dot rendering ──

function drawDotGrid(
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

  // Range from center outward, constrained by margins.
  // x 方向偏移 0.5、y 方向偏移 1.5 —— 与 src/techo/dot-grid.tex 保持一致，勿随意改动。
  const nMin = Math.ceil((settings.left + 0.5 - settings.width / 2) / step)
  const nMax = Math.floor((settings.width - settings.right - 0.5 - settings.width / 2) / step)
  const mMin = Math.ceil((-settings.height + settings.bottom + 1.5 - (-settings.height / 2)) / step)
  const mMax = Math.floor((-settings.top - 1.5 - (-settings.height / 2)) / step)

  // Center point first — drawn exactly once; the grid snaps to it
  context.save()
  context.fillStyle = settings.centerDotColor
  context.beginPath()
  context.arc(cx, cy, dotRadius, 0, Math.PI * 2)
  context.fill()
  context.restore()

  // Spread dots outward from the center (center already drawn → skip it)
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

// ── Midori Grid rendering ──

function drawPunchHoles(
  context: CanvasRenderingContext2D,
  x: number,
  y: number,
  settings: PageSettings,
  scale: number,
  bindingSide: BindingSide,
  punchSide: PunchSide,
) {
  const pitch = 20
  const isPortrait = settings.height >= settings.width
  // Determine which dimension to punch along
  // long edge = max(width, height), short edge = min(width, height)
  const punchAlongHeight = (punchSide === '长边打孔' && isPortrait) || (punchSide === '短边打孔' && !isPortrait)
  const punchLength = punchAlongHeight ? settings.height : settings.width
  const count = Math.max(1, Math.floor((punchLength - 20) / pitch) + 1)
  const firstHole = (punchLength - (count - 1) * pitch) / 2
  const radius = (settings.holeDiameter / 2) * scale

  context.save()
  context.fillStyle = '#fffefd'
  context.strokeStyle = '#5f9f9a'
  context.lineWidth = Math.max(0.35 * scale, 0.45)

  if (punchAlongHeight) {
    // Holes along vertical edge (left or right)
    const holeX = x + (bindingSide === 'left' ? 5 : settings.width - 5) * scale
    for (let index = 0; index < count; index += 1) {
      context.beginPath()
      context.arc(holeX, y + (firstHole + index * pitch) * scale, radius, 0, Math.PI * 2)
      context.fill()
      context.stroke()
    }
  } else {
    // Holes along horizontal edge (top or bottom)
    const holeY = y + (bindingSide === 'top' ? 5 : settings.height - 5) * scale
    for (let index = 0; index < count; index += 1) {
      context.beginPath()
      context.arc(x + (firstHole + index * pitch) * scale, holeY, radius, 0, Math.PI * 2)
      context.fill()
      context.stroke()
    }
  }

  context.restore()
}

function drawMidoriGrid(
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
  context.lineWidth = Math.max(TEX_GRID_LINE_WIDTH_MM * scale, 0.55)
  context.lineCap = 'round'

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

function drawPreviewPage(
  context: CanvasRenderingContext2D,
  tool: Tool,
  x: number,
  y: number,
  settings: PageSettings,
  scale: number,
  bindingSide: BindingSide,
  includePunchHoles = true,
) {
  if (tool === 'green-dot') {
    drawDotGrid(context, x, y, settings, scale)
  } else {
    drawMidoriGrid(context, x, y, settings, scale)
  }
  // 打孔仅在预览中绘制，PNG 导出时不显示（createPrintCanvas 传入 false）
  if (includePunchHoles && settings.showPunchHoles) {
    drawPunchHoles(context, x, y, settings, scale, bindingSide, settings.punchSide)
  }
}

function createPrintCanvas(tool: Tool, settings: PageSettings, page = 0) {
  const width = Math.round(settings.width * PIXELS_PER_MM)
  const height = Math.round(settings.height * PIXELS_PER_MM)
  if (width > MAX_EXPORT_DIMENSION || height > MAX_EXPORT_DIMENSION) {
    throw new Error('尺寸过大，无法生成 PNG。请缩小纸张尺寸后重试。')
  }

  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const context = canvas.getContext('2d')
  if (!context) throw new Error('当前设备不支持 PNG 导出。')

  const pageSettings = settings.layout === 'spread' && page === 0
    ? { ...settings, left: settings.right, right: settings.left }
    : settings
  context.fillStyle = '#fffefd'
  context.fillRect(0, 0, width, height)
  const exportBindingSide: BindingSide = settings.punchSide === '长边打孔'
    ? (settings.layout === 'spread' && page === 0 ? 'right' : 'left')
    : (settings.layout === 'spread' && page === 0 ? 'bottom' : 'top')
  drawPreviewPage(context, tool, 0, 0, pageSettings, PIXELS_PER_MM, exportBindingSide, false)
  return canvas
}

// ── Shared preview canvas ──

function PreviewCanvas({ tool, settings }: { tool: Tool; settings: PageSettings }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const render = () => {
      const bounds = canvas.getBoundingClientRect()
      const ratio = window.devicePixelRatio || 1
      canvas.width = Math.max(1, Math.floor(bounds.width * ratio))
      canvas.height = Math.max(1, Math.floor(bounds.height * ratio))

      const context = canvas.getContext('2d')
      if (!context) return

      context.setTransform(ratio, 0, 0, ratio, 0, 0)
      context.clearRect(0, 0, bounds.width, bounds.height)
      context.fillStyle = '#eef0ed'
      context.fillRect(0, 0, bounds.width, bounds.height)

      const pageCount = settings.layout === 'center' ? 1 : 2
      const gap = pageCount === 2 ? 18 : 0
      const scale = Math.min(
        Math.max(bounds.width - 64, 1) / (settings.width * pageCount + gap),
        Math.max(bounds.height - 76, 1) / settings.height,
      )
      const pageWidth = settings.width * scale
      const pageHeight = settings.height * scale
      const startX = (bounds.width - (pageWidth * pageCount + gap * scale)) / 2
      const startY = (bounds.height - pageHeight) / 2 + 8

      for (let page = 0; page < pageCount; page += 1) {
        const pageX = startX + page * (pageWidth + gap * scale)
        const pageSettings = settings.layout === 'spread' && page === 0
          ? { ...settings, left: settings.right, right: settings.left }
          : settings
        const bindingSide: BindingSide = settings.punchSide === '长边打孔'
          ? (settings.layout === 'spread' && page === 0 ? 'right' : 'left')
          : (settings.layout === 'spread' && page === 0 ? 'bottom' : 'top')

        context.save()
        context.shadowColor = 'rgba(25, 37, 35, 0.17)'
        context.shadowBlur = 14
        context.shadowOffsetY = 5
        context.fillStyle = '#fffefd'
        context.fillRect(pageX, startY, pageWidth, pageHeight)
        context.restore()

        context.strokeStyle = '#d9ddda'
        context.lineWidth = 1
        context.strokeRect(pageX, startY, pageWidth, pageHeight)
        drawPreviewPage(context, tool, pageX, startY, pageSettings, scale, bindingSide)

        context.fillStyle = '#87908c'
        context.font = '500 10px sans-serif'
        context.textAlign = 'center'
        const pageLabel = pageCount === 1 ? '单页' : page === 0 ? '左 · 偶数页' : '右 · 奇数页'
        context.fillText(pageLabel, pageX + pageWidth / 2, startY + pageHeight + 25)
      }

      context.fillStyle = '#67716b'
      context.font = '500 11px sans-serif'
      context.textAlign = 'left'
      context.fillText(`${settings.width} × ${settings.height} mm`, 24, 26)
      context.textAlign = 'right'
      context.fillText(pageCount === 1 ? '居中 · 1 页' : '左右排版 · 2 页', bounds.width - 24, 26)
    }

    const observer = new ResizeObserver(render)
    observer.observe(canvas)
    render()
    return () => observer.disconnect()
  }, [tool, settings])

  const toolLabel = tool === 'green-dot' ? '绿点' : '余白方格'
  return <canvas ref={canvasRef} className="preview-canvas" aria-label={`${toolLabel} 页面预览`} />
}

// ── Shared UI components ──

function NumberField({ id, label, value, onChange }: { id: string; label: string; value: number; onChange: (value: string) => void }) {
  return (
    <div className="number-field">
      <Label htmlFor={id}>{label}</Label>
      <div className="input-with-unit">
        <Input id={id} type="number" min="0" step="1" value={value} onChange={(event) => onChange(event.target.value)} />
        <span>mm</span>
      </div>
    </div>
  )
}

// ── App ──

function App() {
  const [tool, setTool] = useState<Tool>('green-dot')
  const [settings, setSettings] = useState<PageSettings>(DEFAULT_SETTINGS)
  const [preset, setPreset] = useState<Preset>('a5')
  const [exportState, setExportState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [exportMessage, setExportMessage] = useState('')

  const updateDimension = (field: Dimension, raw: string) => {
    const value = Number(raw)
    setSettings((current) => ({ ...current, [field]: Number.isFinite(value) ? Math.max(1, value) : 1 }))
  }

  const updateMargin = (field: Margin, raw: string) => {
    const value = Number(raw)
    setSettings((current) => ({ ...current, [field]: Number.isFinite(value) ? Math.max(0, value) : 0 }))
  }

  const applyPreset = (key: Preset) => {
    const next = PRESETS[key]
    setPreset(key)
    setSettings((current) => ({
      ...DEFAULT_SETTINGS,
      width: next.width,
      height: next.height,
      // 保留用户对网格/颜色的偏好
      gridStep: current.gridStep,
      gridColor: current.gridColor,
      dotColor: current.dotColor,
      centerDotColor: current.centerDotColor,
    }))
  }

  const savePng = async () => {
    const miniTool = window.xhs?.miniTool
    if (!miniTool) {
      setExportState('error')
      setExportMessage('请在小红书小工具内打开，以保存 PNG 到相册。')
      return
    }

    setExportState('saving')
    setExportMessage('正在生成 300 DPI PNG…')
    try {
      const pageCount = settings.layout === 'center' ? 1 : 2
      for (let page = 0; page < pageCount; page += 1) {
        if (pageCount === 2) {
          setExportMessage(page === 0 ? '正在保存左页（偶数页）…' : '正在保存右页（奇数页）…')
        }
        const dataUrl = createPrintCanvas(tool, settings, page).toDataURL('image/png')
        await miniTool.saveImageToPhotosAlbum({ filePath: dataUrl })
      }
      setExportState('saved')
      setExportMessage(pageCount === 1 ? 'PNG 已保存到系统相册。' : '左右两页 PNG 已分别保存到系统相册。')
    } catch (error) {
      setExportState('error')
      setExportMessage(error instanceof Error ? error.message : '保存失败，请检查相册权限后重试。')
    }
  }

  const resetSettings = () => {
    const selectedPreset = PRESETS[preset]
    setSettings({ ...DEFAULT_SETTINGS, width: selectedPreset.width, height: selectedPreset.height })
  }

  const pageCount = settings.layout === 'center' ? 1 : 2


  const toolLabel = tool === 'green-dot' ? '绿点' : '余白方格'


  return (
    <main className="tool-shell">
      <header className="app-header">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">✦</div>
          <div><p className="eyebrow">TECHO 小工具</p><h1>{toolLabel}</h1></div>
        </div>
      </header>

      <div className="workspace">
        <aside className="control-panel" aria-label="页面布局控制">
          {/* ── Tool selector ── */}
          <div className="panel-intro">
            <p className="eyebrow">版本</p>
            <h2>版式选择</h2>
            <p>选择要预览和导出的版式类型。</p>
          </div>

          <Tabs value={tool} onValueChange={(value) => setTool(value as Tool)} className="tool-tabs">
            <TabsList className="tool-tabs-list">
              <TabsTrigger value="green-dot">绿点</TabsTrigger>
              <TabsTrigger value="midori-grid">余白方格</TabsTrigger>
            </TabsList>
          </Tabs>

          {/* ── Shared: paper size ── */}
          <Card className="settings-card">
            <CardHeader><CardTitle>纸张尺寸</CardTitle><CardDescription>可先选择常用规格，再微调数值。</CardDescription></CardHeader>
            <CardContent className="space-y-4">
              <div className="preset-select">
                <Label htmlFor="paper-preset">预制纸张尺寸</Label>
                <Select value={preset} onValueChange={(value) => applyPreset(value as Preset)} items={PRESET_ITEMS}>
                  <SelectTrigger id="paper-preset" className="w-full">
                    <SelectValue placeholder="选择纸张尺寸" />
                  </SelectTrigger>
                  <SelectContent align="start">
                    {PRESET_GROUPS.map((group, gi) => (
                      <Fragment key={group.label}>
                        {gi > 0 && <SelectSeparator />}
                        <SelectGroup>
                          <SelectLabel>{group.label}</SelectLabel>
                          {group.keys.map((key) => {
                            const option = PRESETS[key]
                            return (
                              <SelectItem key={key} value={key}>{option.label} · {option.note}</SelectItem>
                            )
                          })}
                        </SelectGroup>
                      </Fragment>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="dimension-fields">
                <NumberField id="page-width" label="宽度" value={settings.width} onChange={(value) => updateDimension('width', value)} />
                <NumberField id="page-height" label="高度" value={settings.height} onChange={(value) => updateDimension('height', value)} />
              </div>
            </CardContent>
          </Card>

          <Button className="reset-button" variant="outline" type="button" onClick={resetSettings}>↻&nbsp; 恢复 {PRESETS[preset].label} 默认设置</Button>

          {/* ── Shared: margins ── */}
          <Card className="settings-card">
            <CardHeader><CardTitle>边距</CardTitle><CardDescription>左右排版会将“左 / 装订”自动镜像至两个页面的中缝。</CardDescription></CardHeader>
            <CardContent className="margin-fields">
              <NumberField id="margin-top" label="上" value={settings.top} onChange={(value) => updateMargin('top', value)} />
              <NumberField id="margin-right" label="右 / 外侧" value={settings.right} onChange={(value) => updateMargin('right', value)} />
              <NumberField id="margin-bottom" label="下" value={settings.bottom} onChange={(value) => updateMargin('bottom', value)} />
              <NumberField id="margin-left" label="左 / 装订" value={settings.left} onChange={(value) => updateMargin('left', value)} />
            </CardContent>
          </Card>

          {/* ── Tool-specific: grid settings (Midori only) ── */}
          {tool === 'midori-grid' && (
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
                      <Input className="color-hex" value={settings.gridColor.toUpperCase()} maxLength={7} spellCheck={false} onChange={(event) => { const value = event.target.value; if (/^#[0-9a-fA-F]{0,6}$/.test(value)) setSettings((current) => ({ ...current, gridColor: value })) }} onBlur={() => { if (!/^#[0-9a-fA-F]{6}$/.test(settings.gridColor)) setSettings((current) => ({ ...current, gridColor: DEFAULT_SETTINGS.gridColor })) }} aria-label="网格颜色 HEX 值" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* ── Tool-specific: grid settings (Green Dot) ── */}
          {tool === 'green-dot' && (
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
                      <Input className="color-hex" value={settings.dotColor.toUpperCase()} maxLength={7} spellCheck={false} onChange={(event) => { const value = event.target.value; if (/^#[0-9a-fA-F]{0,6}$/.test(value)) setSettings((current) => ({ ...current, dotColor: value })) }} onBlur={() => { if (!/^#[0-9a-fA-F]{6}$/.test(settings.dotColor)) setSettings((current) => ({ ...current, dotColor: DEFAULT_SETTINGS.dotColor })) }} aria-label="点颜色 HEX 值" />
                    </div>
                  </div>
                  <div className="grid-color-control">
                    <Label htmlFor="center-dot-color">中心点颜色</Label>
                    <div className="color-inputs">
                      <Input id="center-dot-color" className="color-picker" type="color" value={settings.centerDotColor} onChange={(event) => setSettings((current) => ({ ...current, centerDotColor: event.target.value }))} aria-label="选择中心点颜色" />
                      <Input className="color-hex" value={settings.centerDotColor.toUpperCase()} maxLength={7} spellCheck={false} onChange={(event) => { const value = event.target.value; if (/^#[0-9a-fA-F]{0,6}$/.test(value)) setSettings((current) => ({ ...current, centerDotColor: value })) }} onBlur={() => { if (!/^#[0-9a-fA-F]{6}$/.test(settings.centerDotColor)) setSettings((current) => ({ ...current, centerDotColor: DEFAULT_SETTINGS.centerDotColor })) }} aria-label="中心点颜色 HEX 值" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* ── Shared: punch hole preview ── */}
          <Card className="settings-card">
            <CardHeader><CardTitle>打孔预览</CardTitle><CardDescription>仅在右侧 Canvas 辅助定位，不会绘制进最终 PNG；孔中心距装订边 5 mm。</CardDescription></CardHeader>
            <CardContent>
              <div className="hole-control">
                <Label htmlFor="punch-preview">显示打孔</Label>
                <Select value={settings.showPunchHoles ? '打孔预览' : '不打孔预览'} onValueChange={(value) => setSettings((current) => ({ ...current, showPunchHoles: value === '打孔预览' }))}>
                  <SelectTrigger id="punch-preview" className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent align="start">
                    <SelectItem value="打孔预览">打孔预览</SelectItem>
                    <SelectItem value="不打孔预览">不打孔预览</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {settings.showPunchHoles && <div className="hole-control hole-diameter-control">
                <Label htmlFor="hole-diameter">孔径</Label>
                <Select value={`${settings.holeDiameter} mm`} onValueChange={(value) => {
                    const parsed = parseMillimeters(value)
                    const valid = parsed === 4 ? 4 : parsed === 5 ? 5 : 4
                    setSettings((current) => ({ ...current, holeDiameter: valid }))
                  }}>
                  <SelectTrigger id="hole-diameter" className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent align="start">
                    <SelectItem value="4 mm">4 mm</SelectItem>
                    <SelectItem value="5 mm">5 mm</SelectItem>
                  </SelectContent>
                </Select>
              </div>}
              {settings.showPunchHoles && <div className="hole-control punch-side-control">
                <Label htmlFor="punch-side">打孔边</Label>
                <Select value={settings.punchSide} onValueChange={(value) => setSettings((current) => ({ ...current, punchSide: value as PunchSide }))}>
                  <SelectTrigger id="punch-side" className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent align="start">
                    <SelectItem value="长边打孔">长边打孔</SelectItem>
                    <SelectItem value="短边打孔">短边打孔</SelectItem>
                  </SelectContent>
                </Select>
              </div>}
            </CardContent>
          </Card>

          {/* ── Shared: layout mode ── */}
          <Card className="settings-card">
            <CardHeader><CardTitle>排版方式</CardTitle><CardDescription>左右排版将输出装订方向相对的偶数页与奇数页。</CardDescription></CardHeader>
            <CardContent>
              <div className="layout-options" role="radiogroup" aria-label="排版方式">
                <Button className={`layout-option ${settings.layout === 'center' ? 'is-selected' : ''}`} variant="outline" type="button" role="radio" aria-checked={settings.layout === 'center'} onClick={() => setSettings((current) => ({ ...current, layout: 'center' }))}>
                  <span className="layout-diagram one-page" aria-hidden="true"><i /></span><span><strong>居中</strong><small>生成 1 页</small></span>
                </Button>
                <Button className={`layout-option ${settings.layout === 'spread' ? 'is-selected' : ''}`} variant="outline" type="button" role="radio" aria-checked={settings.layout === 'spread'} onClick={() => setSettings((current) => ({ ...current, layout: 'spread' }))}>
                  <span className="layout-diagram two-pages" aria-hidden="true"><i /><i /></span><span><strong>左右排版</strong><small>镜像生成 2 页</small></span>
                </Button>
              </div>
            </CardContent>
          </Card>

          <div className="export-controls">
            <Button className="save-button" type="button" disabled={exportState === 'saving'} onClick={savePng}>
              {exportState === 'saving' ? '正在保存 PNG…' : settings.layout === 'spread' ? '分别保存左右页 PNG' : '保存 PNG 到相册'}
            </Button>
            <p className={`export-message ${exportState}`} aria-live="polite">
              {exportMessage || (settings.layout === 'spread' ? '输出为两张 300 DPI PNG，左右页会分别保存到相册。' : '输出为一张 300 DPI PNG。')}
            </p>
          </div>
        </aside>

        <section className="preview-area" aria-label="画布预览">
          <div className="preview-toolbar">
            <div>
              <p className="eyebrow">实时预览</p>
              <h2>{toolLabel}</h2>
            </div>
            <div className="page-count">输出&nbsp; {pageCount} 页</div>
          </div>
          <div className="canvas-frame"><PreviewCanvas tool={tool} settings={settings} /></div>
          </section>
      </div>
    </main>
  )
}

export default App