import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { execFileSync, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { readSources } from './read_source.mjs';

const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'forseti-read-source-'));
const source = path.join(directory, 'source.md');
const body = '# Root\r\nintro\r\n## One\r\nfirst\r\n### Child\r\nnested\r\n## Two\r\nsecond\r\n';
await fs.writeFile(source, body);
const read = async (requests, options) => JSON.parse(await readSources(requests, options));

test('small full source is exact, including CRLF', async () => {
  const result = await read([{ path: source }]);
  assert.equal(result.status, 'read');
  assert.equal(result.sources[0].text, body);
});
test('heading includes children but not next peer', async () => {
  const result = await read([{ path: source, heading: 'One' }]);
  assert.equal(result.sources[0].text, '## One\r\nfirst\r\n### Child\r\nnested\r\n');
  assert.equal(result.sources[0].from, 3);
  assert.equal(result.sources[0].to, 6);
});
test('line selection is explicit and exact', async () => {
  const result = await read([{ path: source, from: 7, to: 8 }]);
  assert.equal(result.sources[0].text, '## Two\r\nsecond\r\n');
});
test('combined budget rejects bodies that fit individually', async () => {
  const large = path.join(directory, 'large.md');
  await fs.writeFile(large, '# Large\n' + 'PRIVATE_BODY'.repeat(400));
  assert.equal((await read([{ path: large }])).status, 'read');
  const output = await readSources([{ path: large }, { path: large }]);
  assert.equal(JSON.parse(output).status, 'not_read');
  assert.equal(JSON.parse(output).reason, 'output_budget_exceeded');
  assert.ok(!output.includes('PRIVATE_BODY'));
  assert.ok(Buffer.byteLength(output) <= 8192);
});
test('UTF-8 and JSON escaping count against output budget', async () => {
  const unicode = path.join(directory, 'unicode.md');
  await fs.writeFile(unicode, '界'.repeat(700));
  const output = await readSources([{ path: unicode }], { maxOutputBytes: 1024 });
  assert.equal(JSON.parse(output).status, 'not_read');
  assert.ok(Buffer.byteLength(output) <= 1024);
});
test('navigation is bounded and omitted headings are explicit', async () => {
  const many = path.join(directory, 'many.md');
  await fs.writeFile(many, Array.from({ length: 100 }, (_, i) => '## Heading ' + i + '\n' + 'x'.repeat(100)).join('\n'));
  const output = await readSources([{ path: many }], { maxOutputBytes: 1024 });
  const result = JSON.parse(output);
  assert.equal(result.status, 'not_read');
  assert.ok(result.sources[0].headings_omitted > 0);
  assert.equal(result.sources[0].heading_count, 100);
  assert.equal(result.sources[0].next_heading_line, result.sources[0].headings.length * 2 + 1);
  assert.ok(Buffer.byteLength(output) <= 1024);
});
test('code-fence headings cannot terminate selected sections', async () => {
  const fenced = path.join(directory, 'fenced.md');
  const fence = String.fromCharCode(96).repeat(3);
  const content = '# Root\n## One\n' + fence + 'md\n## False\n' + fence + '\nkept\n## Two\nend';
  await fs.writeFile(fenced, content);
  const result = await read([{ path: fenced, heading: 'One' }]);
  assert.ok(result.sources[0].text.includes('## False'));
  assert.ok(result.sources[0].text.endsWith('kept\n'));
});
test('missing and ambiguous headings do not count as reads', async () => {
  assert.equal((await read([{ path: source, heading: 'Absent' }])).status, 'not_read');
  const duplicate = path.join(directory, 'duplicate.md');
  await fs.writeFile(duplicate, '## Same\none\n## Same\ntwo');
  const result = await read([{ path: duplicate, heading: 'Same' }]);
  assert.equal(result.status, 'not_read');
  assert.match(result.sources[0].error, /Ambiguous/);
});
test('read error never emits other successful source bodies', async () => {
  const result = await readSources([{ path: source }, { path: path.join(directory, 'missing') }]);
  assert.equal(JSON.parse(result).status, 'not_read');
  assert.ok(!result.includes('first'));
});
test('invalid ranges and conflicting selectors fail visibly', async () => {
  for (const request of [{ path: source, from: 0, to: 3 }, { path: source, from: 1, to: 99 },
    { path: source, heading: 'One', from: 3, to: 6 }]) {
    assert.equal((await read([request])).status, 'not_read');
  }
});
test('invalid budgets and request lists are rejected', async () => {
  await assert.rejects(readSources([{ path: source }], { maxOutputBytes: 1 }));
  await assert.rejects(readSources([]));
});
test('CLI returns a complete read or a nonzero not-read result', () => {
  const cli = fileURLToPath(new URL('./read_source.mjs', import.meta.url));
  const good = execFileSync(process.execPath, [cli, '--file', source, '--heading', 'One'], { encoding: 'utf8' });
  assert.equal(JSON.parse(good).status, 'read');
  const bad = spawnSync(process.execPath, [cli, '--file', source, '--heading', 'Missing'], { encoding: 'utf8' });
  assert.equal(bad.status, 2);
  assert.equal(JSON.parse(bad.stdout).status, 'not_read');
});

test('library import works when the host hides the process global', () => {
  const moduleURL = new URL('./read_source.mjs', import.meta.url).href;
  const script = 'globalThis.process = undefined; await import(' + JSON.stringify(moduleURL) + '); console.log("imported")';
  const result = execFileSync(process.execPath, ['--input-type=module', '-e', script], { encoding: 'utf8' });
  assert.equal(result.trim(), 'imported');
});


test('navigation retains every heading when all fit, including late intelligence rules', async () => {
  const many = path.join(directory, 'complete-navigation.md');
  await fs.writeFile(many, Array.from({ length: 26 }, (_, i) => '## Rule ' + i + '\n' + 'x'.repeat(400)).join('\n'));
  const output = await readSources([{ path: many }]);
  const result = JSON.parse(output);
  assert.equal(result.status, 'not_read');
  assert.equal(result.sources[0].headings.length, 26);
  assert.equal(result.sources[0].headings_omitted, 0);
  assert.equal(result.sources[0].headings.at(-1).title, 'Rule 25');
  assert.ok(Buffer.byteLength(output) <= 8192);
  const selected = await read([{ path: many, heading: result.sources[0].headings.at(-1).title }]);
  assert.equal(selected.status, 'read');
  assert.ok(selected.sources[0].text.startsWith('## Rule 25\n'));
});

test.after(async () => {
  for (const name of await fs.readdir(directory)) await fs.unlink(path.join(directory, name));
  await fs.rmdir(directory);
});
