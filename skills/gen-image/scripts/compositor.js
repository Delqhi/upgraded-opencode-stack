import fs from 'fs';
import path from 'path';

export function buildThumbnail({ 
  mascotPath, 
  bgPath, 
  objectPath, 
  effectsPath, 
  arrowPath, 
  textMain, 
  textHighlight, 
  textSubtitle,
  outputPath 
}) {
  const templatePath = path.join(process.env.SKILL_DIR, 'templates/base.svg');
  let svg = fs.readFileSync(templatePath, 'utf-8');
  const subtitle = (textSubtitle || 'ANTIGRAVITY MODE').toUpperCase();

  const transparentPixel = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+tmY0AAAAASUVORK5CYII=';

  const toDataUri = (filePath) => {
    if (!filePath) return transparentPixel;
    const resolved = path.resolve(filePath);
    if (!fs.existsSync(resolved)) return transparentPixel;
    const ext = path.extname(resolved).toLowerCase();
    const mime = ext === '.png' ? 'image/png' : ext === '.webp' ? 'image/webp' : 'image/jpeg';
    return `data:${mime};base64,${fs.readFileSync(resolved).toString('base64')}`;
  };

  svg = svg
    .replace('{{MASCOT_LAYER}}', toDataUri(mascotPath))
    .replace('{{BG_LAYER}}', toDataUri(bgPath))
    .replace('{{OBJECT_LAYER}}', toDataUri(objectPath))
    .replace('{{EFFECTS_LAYER}}', toDataUri(effectsPath))
    .replace('{{ARROW_LAYER}}', toDataUri(arrowPath));

  svg = svg
    .replace('{{TEXT_SUBTITLE}}', subtitle)
    .replace('{{TEXT_MAIN}}', textMain.toUpperCase())
    .replace('{{TEXT_HIGHLIGHT}}', textHighlight.toUpperCase());

  fs.writeFileSync(outputPath, svg);
  console.log(`[Engine] Rendered Blueprint: ${outputPath}`);
}
