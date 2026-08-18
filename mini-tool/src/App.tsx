import { useEffect, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import './App.css'

type LayoutMode = 'center' | 'spread'
type Dimension = 'width' | 'height'
type Margin = 'top' | 'right' | 'bottom' | 'left'

const PRESETS = {
  a5: { label: 'A5', note: '148 × 210 mm', width: 148, height: 210 },
  a6: { label: 'A6', note: '105 × 148 mm', width: 105, height: 148 },
  a6Personal: { label: 'A6 Personal', note: '95 × 170 mm', width: 95, height: 170 },
  a6Fc: { label: 'A6 FC', note: '108 × 170 mm', width: 108, height: 170 },
  a5Slim: { label: 'A5 Slim', note: '110 × 210 mm', width: 110, height: 210 },
  a6Slim: { label: 'A6 Slim', note: '80 × 172 mm', width: 80, height: 172 },
  a7: { label: 'A7', note: '80 × 120 mm', width: 80, height: 120 },
  a7L: { label: 'A7L', note: '80 × 127 mm', width: 80, height: 127 },
  m5_67: { label: '67M5', note: '67 × 105 mm', width: 67, height: 105 },
  m5_74: { label: '74M5', note: '74 × 105 mm', width: 74, height: 105 },
  m5_62: { label: '62M5', note: '62 × 105 mm', width: 62, height: 105 },
  passport: { label: 'Passport', note: '88 × 125 mm', width: 88, height: 125 },
} as const

type Preset = keyof typeof PRESETS

interface PageSettings {
  width: number
  height: number
  top: number
  right: number
  bottom: number
  left: number
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
const MAX_EXPORT_DIMENSION = 16384

const DEFAULT_SETTINGS: PageSettings = {
  width: 148,
  height: 210,
  top: 5,
  right: 5,
  bottom: 10,
  left: 15,
  layout: 'center',
}

function isMarker(index: number, count: number) {
  const middle = Math.floor(count / 2)
  return index > 0 && index < count && (index - middle) % 10 === 0
}

function drawGrid(context: CanvasRenderingContext2D, x: number, y: number, settings: PageSettings, scale: number) {
  const usableWidth = settings.width - settings.left - settings.right
  const usableHeight = settings.height - settings.top - settings.bottom
  if (usableWidth <= 0 || usableHeight <= 0) return

  const step = 5
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
  context.strokeStyle = '#81c5cb'
  context.fillStyle = '#6fb9c1'
  context.lineWidth = Math.max(0.45 * scale, 0.55)
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

function createPrintCanvas(settings: PageSettings, page = 0) {
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
  drawGrid(context, 0, 0, pageSettings, PIXELS_PER_MM)
  return canvas
}

function PreviewCanvas({ settings }: { settings: PageSettings }) {
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
        // Two-page layout mirrors the inner/binding margin at the center seam.
        const pageSettings = settings.layout === 'spread' && page === 0
          ? { ...settings, left: settings.right, right: settings.left }
          : settings

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
        drawGrid(context, pageX, startY, pageSettings, scale)

        context.fillStyle = '#87908c'
        context.font = '500 10px sans-serif'
        context.textAlign = 'center'
        const pageLabel = pageCount === 1 ? 'SINGLE PAGE' : page === 0 ? 'LEFT · EVEN' : 'RIGHT · ODD'
        context.fillText(pageLabel, pageX + pageWidth / 2, startY + pageHeight + 25)
      }

      context.fillStyle = '#67716b'
      context.font = '500 11px sans-serif'
      context.textAlign = 'left'
      context.fillText(`${settings.width} × ${settings.height} mm`, 24, 26)
      context.textAlign = 'right'
      context.fillText(pageCount === 1 ? 'CENTER · 1 PAGE' : 'SPREAD · 2 PAGES', bounds.width - 24, 26)
    }

    const observer = new ResizeObserver(render)
    observer.observe(canvas)
    render()
    return () => observer.disconnect()
  }, [settings])

  return <canvas ref={canvasRef} className="preview-canvas" aria-label="Midori grid page preview" />
}

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

function App() {
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
    setSettings((current) => ({ ...current, width: next.width, height: next.height }))
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
        const dataUrl = createPrintCanvas(settings, page).toDataURL('image/png')
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
  const usableWidth = Math.max(0, settings.width - settings.left - settings.right)
  const usableHeight = Math.max(0, settings.height - settings.top - settings.bottom)

  return (
    <main className="tool-shell">
      <header className="app-header">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">✦</div>
          <div><p className="eyebrow">TECHO MINI TOOL</p><h1>Midori Grid</h1></div>
        </div>
        <p className="header-note">Python + XeLaTeX · layout preview</p>
      </header>

      <div className="workspace">
        <aside className="control-panel" aria-label="Page layout controls">
          <div className="panel-intro">
            <p className="eyebrow">PAGE SETUP</p>
            <h2>纸张与留白</h2>
            <p>设置成品尺寸与网格安全区，右侧实时复刻 Midori 的 5 mm 方格。</p>
          </div>

          <Card className="settings-card">
            <CardHeader><CardTitle>纸张尺寸</CardTitle><CardDescription>可先选择常用规格，再微调数值。</CardDescription></CardHeader>
            <CardContent className="space-y-4">
              <div className="preset-select">
                <Label htmlFor="paper-preset">预制纸张尺寸</Label>
                <Select value={preset} onValueChange={(value) => applyPreset(value as Preset)}>
                  <SelectTrigger id="paper-preset" className="w-full">
                    <SelectValue placeholder="选择纸张尺寸" />
                  </SelectTrigger>
                  <SelectContent align="start">
                    {(Object.entries(PRESETS) as [Preset, (typeof PRESETS)[Preset]][]).map(([key, option]) => (
                      <SelectItem key={key} value={key}>{option.label} · {option.note}</SelectItem>
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

          <Card className="settings-card">
            <CardHeader><CardTitle>边距</CardTitle><CardDescription>左右排版会将“左 / 装订”自动镜像至两个页面的中缝。</CardDescription></CardHeader>
            <CardContent className="margin-fields">
              <NumberField id="margin-top" label="上" value={settings.top} onChange={(value) => updateMargin('top', value)} />
              <NumberField id="margin-right" label="右 / 外侧" value={settings.right} onChange={(value) => updateMargin('right', value)} />
              <NumberField id="margin-bottom" label="下" value={settings.bottom} onChange={(value) => updateMargin('bottom', value)} />
              <NumberField id="margin-left" label="左 / 装订" value={settings.left} onChange={(value) => updateMargin('left', value)} />
            </CardContent>
          </Card>

          <Card className="settings-card">
            <CardHeader><CardTitle>排版方式</CardTitle><CardDescription>左右排版将输出装订方向相对的偶数页与奇数页。</CardDescription></CardHeader>
            <CardContent>
              <div className="layout-options" role="radiogroup" aria-label="Layout mode">
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

        <section className="preview-area" aria-label="Canvas preview">
          <div className="preview-toolbar"><div><p className="eyebrow">LIVE CANVAS</p><h2>网格预览</h2></div><div className="page-count">⌑&nbsp; {pageCount} 页输出</div></div>
          <div className="canvas-frame"><PreviewCanvas settings={settings} /></div>
          <footer className="preview-footer">
            {settings.layout === 'spread' ? <><span>装订边距</span><strong>{settings.left.toFixed(0)} mm</strong><span className="footer-dot" /><span>外侧边距</span><strong>{settings.right.toFixed(0)} mm</strong><span className="footer-dot" /><span>左右页面已镜像</span></> : <><span>可用网格区域</span><strong>{usableWidth.toFixed(0)} × {usableHeight.toFixed(0)} mm</strong><span className="footer-dot" /><span>网格间距 5 mm</span></>}
          </footer>
        </section>
      </div>
    </main>
  )
}

export default App
