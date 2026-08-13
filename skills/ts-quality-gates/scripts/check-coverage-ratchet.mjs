#!/usr/bin/env node

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, isAbsolute, relative, resolve, sep } from 'node:path';

const METRICS = ['lines', 'statements', 'functions', 'branches'];

function fail(message) {
  console.error(`Coverage ratchet: ${message}`);
  process.exit(1);
}

function parseArgs(argv) {
  const options = {
    baseline: '.quality/coverage-baseline.json',
    summary: 'coverage/coverage-summary.json',
    root: process.cwd(),
    tolerance: 0.01,
    writeBaseline: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === '--write-baseline') {
      options.writeBaseline = true;
    } else if (argument === '--help') {
      console.log('Usage: check-coverage-ratchet.mjs [--summary FILE] [--baseline FILE] [--root DIR] --new-file-min PERCENT [--tolerance PERCENT] [--write-baseline]');
      process.exit(0);
    } else if (['--summary', '--baseline', '--root', '--new-file-min', '--tolerance'].includes(argument)) {
      const value = argv[index + 1];
      if (value === undefined) fail(`${argument} requires a value`);
      index += 1;
      const key = {
        '--summary': 'summary',
        '--baseline': 'baseline',
        '--root': 'root',
        '--new-file-min': 'newFileMin',
        '--tolerance': 'tolerance',
      }[argument];
      options[key] = value;
    } else {
      fail(`unknown argument: ${argument}`);
    }
  }

  options.root = resolve(options.root);
  options.summary = resolve(options.root, options.summary);
  options.baseline = resolve(options.root, options.baseline);
  options.tolerance = Number(options.tolerance);
  options.newFileMin = Number(options.newFileMin);

  if (!Number.isFinite(options.newFileMin) || options.newFileMin < 0 || options.newFileMin > 100) {
    fail('--new-file-min must be a number from 0 through 100');
  }
  if (!Number.isFinite(options.tolerance) || options.tolerance < 0) {
    fail('--tolerance must be a non-negative number');
  }
  return options;
}

function readJson(path, label) {
  if (!existsSync(path)) fail(`${label} is missing: ${path}`);
  try {
    return JSON.parse(readFileSync(path, 'utf8'));
  } catch (error) {
    fail(`${label} is invalid JSON: ${error.message}`);
  }
}

function normalizeFile(file, root) {
  const absolute = isAbsolute(file) ? file : resolve(root, file);
  const normalized = relative(root, absolute).split(sep).join('/');
  if (normalized === '..' || normalized.startsWith('../')) {
    fail(`coverage file is outside --root: ${file}`);
  }
  return normalized;
}

function extractSummary(summary, root) {
  const files = {};
  for (const [file, coverage] of Object.entries(summary)) {
    if (file === 'total') continue;
    const normalized = normalizeFile(file, root);
    files[normalized] = {};
    for (const metric of METRICS) {
      const percent = Number(coverage?.[metric]?.pct);
      if (!Number.isFinite(percent) || percent < 0 || percent > 100) {
        fail(`invalid ${metric} percentage for ${normalized}`);
      }
      files[normalized][metric] = percent;
    }
  }
  if (Object.keys(files).length === 0) fail('coverage summary contains no source files');
  return Object.fromEntries(Object.entries(files).sort(([left], [right]) => left.localeCompare(right)));
}

function writeBaseline(path, files) {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `${JSON.stringify({ version: 1, files }, null, 2)}\n`);
  console.log(`Coverage baseline written: ${path}`);
}

function compare(files, baseline, options) {
  if (baseline.version !== 1 || !baseline.files || typeof baseline.files !== 'object') {
    fail('baseline must contain version 1 and a files object');
  }

  const failures = [];
  for (const [file, expected] of Object.entries(baseline.files)) {
    const current = files[file];
    if (!current) {
      if (existsSync(resolve(options.root, file))) failures.push(`${file}: missing from coverage summary`);
      continue;
    }
    for (const metric of METRICS) {
      const floor = Number(expected?.[metric]);
      if (!Number.isFinite(floor)) failures.push(`${file}: invalid baseline ${metric}`);
      else if (current[metric] + options.tolerance < floor) {
        failures.push(`${file}: ${metric} fell from ${floor}% to ${current[metric]}%`);
      }
    }
  }

  for (const [file, current] of Object.entries(files)) {
    if (baseline.files[file]) continue;
    for (const metric of METRICS) {
      if (current[metric] + options.tolerance < options.newFileMin) {
        failures.push(`${file}: new-file ${metric} is ${current[metric]}%, below ${options.newFileMin}%`);
      }
    }
  }

  if (failures.length > 0) fail(`failed:\n  - ${failures.join('\n  - ')}`);
  console.log(`Coverage ratchet passed for ${Object.keys(files).length} files.`);
}

const options = parseArgs(process.argv.slice(2));
const files = extractSummary(readJson(options.summary, 'coverage summary'), options.root);

if (options.writeBaseline) writeBaseline(options.baseline, files);
else compare(files, readJson(options.baseline, 'coverage baseline'), options);
