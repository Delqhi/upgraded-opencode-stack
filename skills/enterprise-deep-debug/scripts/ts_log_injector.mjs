#!/usr/bin/env node
/**
 * Automatic log injection for TypeScript/JavaScript files.
 *
 * Uses regex-based code transformation (no external deps required) to inject
 * structured console.log/console.error at every function entry/exit with
 * arguments, return values, timing, and exception capture.
 *
 * Usage:
 *   node ts_log_injector.mjs <path> [--dry-run] [--diff] [--min-lines 3]
 *   node ts_log_injector.mjs src/ --diff
 *   node ts_log_injector.mjs app.ts --dry-run
 */
import fs from 'fs';
import path from 'path';

const INJECT_MARKER = '/* __ALI_INJECTED__ */';

const ENTRY_LOG_TEMPLATE = (funcName, argsStr) =>
  `${INJECT_MARKER} const __ali_t0 = performance.now(); console.log(\`[ENTER] ${funcName}(\${JSON.stringify({${argsStr}}).slice(0,500)})\`);`;

const EXIT_LOG_TEMPLATE = (funcName) =>
  `${INJECT_MARKER} console.log(\`[EXIT] ${funcName} | elapsed=\${(performance.now()-__ali_t0).toFixed(2)}ms\`);`;

const ERROR_LOG_TEMPLATE = (funcName) =>
  `${INJECT_MARKER} console.error(\`[EXCEPTION] ${funcName} | \${__ali_err.constructor.name}: \${__ali_err.message} | elapsed=\${(performance.now()-__ali_t0).toFixed(2)}ms\`); throw __ali_err;`;

const FUNC_PATTERNS = [
  // async function name(args) {
  /^(\s*)(export\s+)?(async\s+)?function\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*[^{]+)?\s*\{/gm,
  // const name = async (args) => {
  /^(\s*)(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(async\s+)?\(([^)]*)\)\s*(?::\s*[^{]+)?\s*=>\s*\{/gm,
  // class method: name(args) {
  /^(\s*)(async\s+)?(\w+)\s*\(([^)]*)\)\s*(?::\s*[^{]+)?\s*\{/gm,
];

function extractArgNames(argsStr) {
  if (!argsStr || !argsStr.trim()) return [];
  return argsStr.split(',')
    .map(a => a.trim())
    .map(a => a.replace(/\s*[:=].*$/, ''))  // Remove type annotations and defaults
    .map(a => a.replace(/^\.\.\./, ''))       // Remove spread
    .map(a => a.replace(/[?]$/, ''))          // Remove optional marker
    .filter(a => a && !a.startsWith('{') && !a.startsWith('['))
    .slice(0, 8);
}

function shouldSkip(funcName, lineContent) {
  if (funcName.startsWith('_') && !funcName.startsWith('__')) return true;
  if (['constructor', 'render', 'toString', 'valueOf', 'toJSON'].includes(funcName)) return true;
  if (lineContent.includes(INJECT_MARKER)) return true;
  return false;
}

function injectLogging(source, filepath) {
  const lines = source.split('\n');
  const injected = [];
  let stats = { functions_found: 0, functions_injected: 0, functions_skipped: 0 };

  let i = 0;
  while (i < lines.length) {
    const line = lines[i];

    // Check for function declarations
    let match = null;
    let funcName = null;
    let argsStr = null;
    let indent = '';

    // Pattern 1: function declarations
    const funcMatch = line.match(/^(\s*)(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)/);
    if (funcMatch && line.trimEnd().endsWith('{')) {
      indent = funcMatch[1];
      funcName = funcMatch[2];
      argsStr = funcMatch[3];
      match = funcMatch;
    }

    // Pattern 2: arrow functions assigned to const/let/var
    if (!match) {
      const arrowMatch = line.match(/^(\s*)(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*(?::\s*[^{]+)?\s*=>\s*\{/);
      if (arrowMatch) {
        indent = arrowMatch[1];
        funcName = arrowMatch[2];
        argsStr = arrowMatch[3];
        match = arrowMatch;
      }
    }

    // Pattern 3: class methods
    if (!match) {
      const methodMatch = line.match(/^(\s*)(?:async\s+)?(\w+)\s*\(([^)]*)\)\s*(?::\s*[^{]+)?\s*\{/);
      if (methodMatch && !line.match(/^\s*(if|else|for|while|switch|catch|do)\s*\(/) && !line.match(/^\s*(class|interface|type|enum)\s/)) {
        indent = methodMatch[1];
        funcName = methodMatch[2];
        argsStr = methodMatch[3];
        match = methodMatch;
      }
    }

    if (match && funcName && !shouldSkip(funcName, line)) {
      stats.functions_found++;

      // Check if already injected
      if (i + 1 < lines.length && lines[i + 1].includes(INJECT_MARKER)) {
        stats.functions_skipped++;
        injected.push(line);
        i++;
        continue;
      }

      const argNames = extractArgNames(argsStr);
      const argsObjStr = argNames.map(a => a).join(', ');

      const bodyIndent = indent + '  ';

      injected.push(line);
      injected.push(`${bodyIndent}${ENTRY_LOG_TEMPLATE(funcName, argsObjStr)}`);
      injected.push(`${bodyIndent}try {`);

      // Find matching closing brace
      let braceCount = 1;
      let j = i + 1;
      const innerLines = [];

      while (j < lines.length && braceCount > 0) {
        const l = lines[j];
        for (const ch of l) {
          if (ch === '{') braceCount++;
          if (ch === '}') braceCount--;
        }
        if (braceCount > 0) {
          // Check for return statements to add return logging
          const returnMatch = l.match(/^(\s*)return\s+(.+?)\s*;?\s*$/);
          if (returnMatch && braceCount === 1) {
            const retIndent = returnMatch[1];
            const retVal = returnMatch[2];
            innerLines.push(`${retIndent}const __ali_ret = ${retVal};`);
            innerLines.push(`${retIndent}console.log(\`[EXIT] ${funcName} | return=\${JSON.stringify(__ali_ret).slice(0,200)} | elapsed=\${(performance.now()-__ali_t0).toFixed(2)}ms\`);`);
            innerLines.push(`${retIndent}return __ali_ret;`);
          } else {
            innerLines.push(l);
          }
          j++;
        } else {
          // This is the closing brace
          break;
        }
      }

      for (const il of innerLines) {
        injected.push(`  ${il}`);
      }

      injected.push(`${bodyIndent}} catch (__ali_err) {`);
      injected.push(`${bodyIndent}  ${ERROR_LOG_TEMPLATE(funcName)}`);
      injected.push(`${bodyIndent}} finally {`);
      injected.push(`${bodyIndent}  ${EXIT_LOG_TEMPLATE(funcName)}`);
      injected.push(`${bodyIndent}}`);
      injected.push(lines[j] || `${indent}}`);

      i = j + 1;
      stats.functions_injected++;
      continue;
    }

    injected.push(line);
    i++;
  }

  return { code: injected.join('\n'), stats };
}

function walkDir(dir, extensions = ['.ts', '.tsx', '.js', '.jsx', '.mjs']) {
  const results = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (['node_modules', '.git', 'dist', '.next', 'build', '__pycache__'].includes(entry.name)) continue;
      results.push(...walkDir(fullPath, extensions));
    } else if (extensions.some(ext => entry.name.endsWith(ext))) {
      results.push(fullPath);
    }
  }
  return results;
}

function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.log('Usage: node ts_log_injector.mjs <path> [--dry-run] [--diff]');
    process.exit(1);
  }

  const targetPath = args[0];
  const dryRun = args.includes('--dry-run');
  const showDiff = args.includes('--diff');

  let files = [];
  const stat = fs.statSync(targetPath);
  if (stat.isDirectory()) {
    files = walkDir(targetPath);
  } else {
    files = [targetPath];
  }

  let totalStats = { files: 0, functions_found: 0, functions_injected: 0, functions_skipped: 0 };

  for (const filepath of files) {
    const source = fs.readFileSync(filepath, 'utf-8');
    const { code, stats } = injectLogging(source, filepath);

    totalStats.files++;
    totalStats.functions_found += stats.functions_found;
    totalStats.functions_injected += stats.functions_injected;
    totalStats.functions_skipped += stats.functions_skipped;

    if (source === code) continue;

    if (showDiff) {
      console.log(`--- a/${filepath}`);
      console.log(`+++ b/${filepath}`);
      const srcLines = source.split('\n');
      const newLines = code.split('\n');
      // Simple diff output
      let ctx = 0;
      for (let k = 0; k < Math.max(srcLines.length, newLines.length); k++) {
        if (srcLines[k] !== newLines[k]) {
          if (srcLines[k]) console.log(`-${srcLines[k]}`);
          if (newLines[k]) console.log(`+${newLines[k]}`);
          ctx = 3;
        } else if (ctx > 0) {
          console.log(` ${srcLines[k] || ''}`);
          ctx--;
        }
      }
    } else if (dryRun) {
      console.log(`// === ${filepath} ===`);
      console.log(code);
    } else {
      // Backup
      const backup = filepath + '.pre_inject';
      if (!fs.existsSync(backup)) {
        fs.writeFileSync(backup, source);
      }
      fs.writeFileSync(filepath, code);
      console.log(`INJECTED ${filepath} (${stats.functions_injected} functions)`);
    }
  }

  console.error(`\n=== INJECTION SUMMARY ===`);
  console.error(`Files scanned:       ${totalStats.files}`);
  console.error(`Functions found:     ${totalStats.functions_found}`);
  console.error(`Functions injected:  ${totalStats.functions_injected}`);
  console.error(`Functions skipped:   ${totalStats.functions_skipped}`);
}

main();
