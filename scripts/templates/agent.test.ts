import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('A2A Agent Security & Structure Tests', () => {
  const agentRoot = path.resolve(__dirname, '..');

  describe('File Structure', () => {
    it('should have agent.json', () => {
      expect(fs.existsSync(path.join(agentRoot, 'agent.json'))).toBe(true);
    });
    it('should have A2A-CARD.md', () => {
      expect(fs.existsSync(path.join(agentRoot, 'A2A-CARD.md'))).toBe(true);
    });
    it('should have src/runtime.ts', () => {
      expect(fs.existsSync(path.join(agentRoot, 'src', 'runtime.ts'))).toBe(true);
    });
    it('should have src/mcp-server.ts', () => {
      expect(fs.existsSync(path.join(agentRoot, 'src', 'mcp-server.ts'))).toBe(true);
    });
  });

  describe('Security', () => {
    it('should have .githooks/pre-commit', () => {
      expect(fs.existsSync(path.join(agentRoot, '.githooks', 'pre-commit'))).toBe(true);
    });
    it('should have .githooks/pre-push', () => {
      expect(fs.existsSync(path.join(agentRoot, '.githooks', 'pre-push'))).toBe(true);
    });
    it('should have .secrets.baseline', () => {
      expect(fs.existsSync(path.join(agentRoot, '.secrets.baseline'))).toBe(true);
    });
    it('should NOT contain external code references', () => {
      const srcDir = path.join(agentRoot, 'src');
      if (fs.existsSync(srcDir)) {
        const files = fs.readdirSync(srcDir, { recursive: true });
        for (const file of files) {
          const content = fs.readFileSync(path.join(srcDir, file), 'utf-8');
          expect(content).not.toMatch(/claude|anthropic|@ant\//);
        }
      }
    });
  });

  describe('Agent Config', () => {
    it('should have marketplace metadata', () => {
      const agentJson = JSON.parse(fs.readFileSync(path.join(agentRoot, 'agent.json'), 'utf-8'));
      expect(agentJson.marketplace).toHaveProperty('pricingModel');
      expect(agentJson.marketplace).toHaveProperty('monthlyPrice');
      expect(agentJson.marketplace).toHaveProperty('purchaseModes');
    });
  });
});
