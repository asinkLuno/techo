import { cp, mkdir, readdir, rm, stat } from 'node:fs/promises'
import { execFileSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const dist = path.join(root, 'dist')
const staticDir = path.join(root, 'static')
const artifactDir = path.join(root, 'artifacts')
const artifact = path.join(artifactDir, 'techo-mini-tool.zip')
const rootPreviewFiles = ['index.html', 'assets']
const allowedExtensions = new Set(['.html', '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.woff', '.woff2', '.json'])

async function walk(directory) {
  const entries = await readdir(directory, { withFileTypes: true })
  const files = []
  for (const entry of entries) {
    const entryPath = path.join(directory, entry.name)
    if (entry.isDirectory()) files.push(...await walk(entryPath))
    else files.push(entryPath)
  }
  return files
}

await cp(path.join(staticDir, 'index.html'), path.join(dist, 'index.html'))
for (const item of rootPreviewFiles) {
  await rm(path.join(root, item), { recursive: true, force: true })
  await cp(path.join(dist, item), path.join(root, item), { recursive: true })
}
const files = await walk(dist)
for (const file of files) {
  const relative = path.relative(dist, file)
  const extension = path.extname(file).toLowerCase()
  if (!allowedExtensions.has(extension)) throw new Error(`Unsupported artifact file: ${relative}`)
  if (relative.endsWith('.map') || relative.includes('node_modules') || relative.includes('.DS_Store')) {
    throw new Error(`Forbidden artifact file: ${relative}`)
  }
}

const html = await (await import('node:fs/promises')).readFile(path.join(dist, 'index.html'), 'utf8')
if (!html.includes('<!DOCTYPE html>') || !html.includes('lang="zh-CN"')) throw new Error('Invalid index.html document metadata')
if (!html.includes('viewport-fit=cover')) throw new Error('Missing viewport-fit=cover')
if (html.includes('type="module"') || /<script(?![^>]*\bsrc=)[^>]*>/i.test(html)) throw new Error('Scripts must be external classic scripts')
if (/https?:\/\//.test(html) || /<base\b|<iframe\b|<object\b/i.test(html)) throw new Error('Artifact contains a forbidden external or embedded resource')

await mkdir(artifactDir, { recursive: true })
await rm(artifact, { force: true })
execFileSync('zip', ['-r', artifact, '.', '-x', '*.DS_Store'], { cwd: dist, stdio: 'inherit' })
const bytes = (await stat(artifact)).size
if (bytes > 10 * 1024 * 1024) throw new Error(`Artifact exceeds 10 MB: ${bytes} bytes`)
console.log(`Created ${artifact} (${(bytes / 1024).toFixed(1)} KiB)`)
