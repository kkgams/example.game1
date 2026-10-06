import { readFileSync } from 'node:fs'
import { resolve, join } from 'node:path'

// CLI integration has no frontend downloader. Use separately installed/assembled
// files at the deployment paths recorded by this Project's release lock.
export function localPluginPaths(projectRoot, config) {
  const lock = JSON.parse(readFileSync(join(projectRoot, 'release-lock.json'), 'utf8'))
  const pathsBySource = new Map()
  for (const unit of lock.units) {
    if (unit.kind !== 'component') continue
    for (const [name, asset] of Object.entries(unit.assets)) {
      if (name.endsWith('.wasm')) pathsBySource.set(asset.url, unit.files[0])
    }
  }
  const configured = config.plugins.map(source => {
    if (!/^https?:/i.test(source)) return resolve(projectRoot, source)
    const path = pathsBySource.get(source)
    if (!path) throw new Error(`CLI plugin source is not in release-lock.json: ${source}`)
    return resolve(projectRoot, path)
  })
  return [join(projectRoot, 'plugins/fs.comp.wasm'), ...configured]
}
