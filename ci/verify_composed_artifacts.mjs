// Compare freshly compiled module 31 with the recorded browser payload.
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {FULL_GROWTHS} from '../docs/builder-full.mjs';

const growth = FULL_GROWTHS.find(item => item.module === 31);
if (!growth || FULL_GROWTHS.filter(item => item.module === 31).length !== 1)
  throw new Error('Expected exactly one module 31 browser payload');
if (typeof growth.hex !== 'string' || !/^(?:[0-9a-f]{2})+$/i.test(growth.hex))
  throw new Error('Invalid browser payload hex');
const browser = Buffer.from(growth.hex, 'hex');
const compiled = await readFile(new URL('../patches/full/out/payload31.bin', import.meta.url));
// build_compose.py rewrites the layout report, so CI passes a copy made
// before the build to compare against the committed record.
const layoutPath = process.argv[2] || new URL('../patches/full/out/layout31.json', import.meta.url);
const recorded = JSON.parse(await readFile(layoutPath, 'utf8'));
const digest = createHash('sha256').update(compiled).digest('hex');
if (compiled.length !== growth.length || compiled.length !== recorded.payload_bytes ||
    digest !== growth.sha256 || digest !== recorded.payload_sha256 || !compiled.equals(browser))
  throw new Error('Compiled module 31 does not match the recorded/browser payload');
console.log(`Module 31: ${compiled.length} bytes, SHA-256 ${digest}; source and browser match.`);
