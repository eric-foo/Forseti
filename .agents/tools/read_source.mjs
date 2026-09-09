import fs from 'node:fs/promises';
import { pathToFileURL } from 'node:url';

export const DEFAULT_OUTPUT_BYTES = 8192;
const bytes = value => Buffer.byteLength(value, 'utf8');
const encode = value => JSON.stringify(value);

// Headings inside fenced examples are content, not navigation targets.
function headings(lines) {
  const found = [];
  let fence = null;
  lines.forEach((line, index) => {
    const marker = line.match(/^ {0,3}([\x60~]{3,})/);
    if (marker && /^([\x60]+|[~]+)$/.test(marker[1])) {
      if (!fence) fence = marker[1];
      else if (marker[1][0] === fence[0] && marker[1].length >= fence.length &&
               line.slice(marker[0].length).trim() === '') fence = null;
      return;
    }
    if (fence) return;
    const match = line.match(/^ {0,3}(#{1,6})\s+(.+?)\s*\r?$/);
    if (match) found.push({ line: index + 1, level: match[1].length,
      title: match[2].replace(/\s+#+\s*$/, '') });
  });
  return found;
}

export async function readSources(requests, { maxOutputBytes = DEFAULT_OUTPUT_BYTES } = {}) {
  if (!Number.isInteger(maxOutputBytes) || maxOutputBytes < 1024 || maxOutputBytes > 32768)
    throw new Error('maxOutputBytes must be an integer from 1024 to 32768');
  if (!Array.isArray(requests) || !requests.length || requests.length > 16)
    throw new Error('Supply between 1 and 16 source requests');
  const selected = [];
  const navigation = [];
  for (const request of requests) {
    if (!request || typeof request.path !== 'string' || !request.path)
      throw new Error('Each request needs a path');
    const nav = { path: request.path, status: 'not_read' };
    navigation.push(nav);
    try {
      const text = await fs.readFile(request.path, 'utf8');
      const lines = text.match(/[^\n]*\n|[^\n]+$/g) || [];
      const outline = headings(lines.map(line => line.replace(/\n$/, '')));
      Object.assign(nav, { file_bytes: bytes(text), total_lines: lines.length, from: 1, to: lines.length,
        headings: outline });
      let from = 1;
      let to = lines.length;
      if (request.heading !== undefined) {
        if (request.from !== undefined || request.to !== undefined)
          throw new Error('Choose a heading or a line range, not both');
        const matches = outline.filter(h => h.title === request.heading);
        if (matches.length !== 1)
          throw new Error(matches.length ? 'Ambiguous heading; select exact lines' : 'Heading not found');
        const match = matches[0];
        from = match.line;
        to = (outline.find(h => h.line > from && h.level <= match.level)?.line || lines.length + 1) - 1;
      } else if (request.from !== undefined || request.to !== undefined) {
        from = request.from;
        to = request.to;
        if (!Number.isInteger(from) || !Number.isInteger(to) || from < 1 || to < from || to > lines.length)
          throw new Error('Supply an existing inclusive from/to line range');
      }
      const body = lines.slice(from - 1, to).join('');
      Object.assign(nav, { selected_bytes: bytes(body), from, to,
        headings: outline.filter(h => h.line >= from && h.line <= to) });
      selected.push({ path: request.path, from, to, text: body });
    } catch (error) {
      nav.error = error.code || error.message;
    }
  }
  const result = encode({ status: 'read', sources: selected });
  if (!navigation.some(n => n.error) && bytes(result) <= maxOutputBytes) return result;

  // Never emit a partial body, including when several individually small reads
  // would overflow the combined result. Navigation is not evidence consumption.
  const fallback = { status: 'not_read', reason: navigation.some(n => n.error)
    ? 'request_error' : 'output_budget_exceeded', max_output_bytes: maxOutputBytes,
    requested_output_bytes: bytes(result),
    next: 'Select a heading or from/to lines. Continue omitted navigation with from: next_heading_line and to: this source’s to. No source bodies emitted.',
    sources: navigation };
  for (const nav of navigation) {
    nav.heading_count = nav.headings?.length || 0;
    nav.headings = nav.headings || [];
    nav.headings_omitted = nav.heading_count - nav.headings.length;
  }
  while (bytes(encode(fallback)) > maxOutputBytes && navigation.some(n => n.headings.length)) {
    const nav = navigation.reduce((a, b) => a.headings.length >= b.headings.length ? a : b);
    nav.next_heading_line = nav.headings.pop().line;
    nav.headings_omitted++;
  }
  // A complete heading list must not carry omission guidance; replacing the
  // message with a shorter one cannot breach the budget the loop just met.
  if (!navigation.some(n => n.headings_omitted)) fallback.next =
    'Select an exact heading or inclusive from/to lines; source bodies were not emitted.';
  if (bytes(encode(fallback)) > maxOutputBytes) return encode({ status: 'not_read',
    reason: fallback.reason, max_output_bytes: maxOutputBytes,
    requested_output_bytes: fallback.requested_output_bytes,
    next: 'Navigation exceeds budget; request fewer sources or shorter paths. No source bodies emitted.' });
  return encode(fallback);
}

async function main(args) {
  const requests = [];
  let maxOutputBytes = DEFAULT_OUTPUT_BYTES;
  for (let i = 0; i < args.length; i++) {
    const flag = args[i];
    const value = args[++i];
    if (value === undefined) throw new Error('Every option requires a value');
    if (flag === '--file') requests.push({ path: value });
    else if (flag === '--max-output-bytes') maxOutputBytes = Number(value);
    else if (['--heading', '--from', '--to'].includes(flag) && requests.length) {
      requests.at(-1)[flag.slice(2)] = flag === '--heading' ? value : Number(value);
    } else throw new Error('Use --file PATH [--heading TITLE | --from N --to N] [--max-output-bytes N]');
  }
  const output = await readSources(requests, { maxOutputBytes });
  process.stdout.write(output);
  if (JSON.parse(output).status !== 'read') process.exitCode = 2;
}
if (typeof process !== 'undefined' && process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main(process.argv.slice(2)).catch(() => {
    process.stdout.write(encode({ status: 'not_read', reason: 'invalid_arguments',
      next: 'Use --file PATH [--heading TITLE | --from N --to N] [--max-output-bytes N]. Budget: 1024..32768 bytes.' }));
    process.exitCode = 2;
  });
}
