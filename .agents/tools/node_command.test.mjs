import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mkdtemp, readFile, rmdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { runCommand, startCommand } from './node_command.mjs';
import { setTimeout as delay } from 'node:timers/promises';

const options = { cwd: process.cwd(), timeoutMs: 5000 };
const runNode = (source, overrides = {}) =>
  runCommand(process.execPath, ['-e', source], { ...options, ...overrides });

test('successful exit preserves both output streams', async () => {
  const result = await runNode('process.stdout.write("hello"); process.stderr.write("diagnostic")');
  assert.equal(result.processSuccess, true);
  assert.equal(result.exitCode, 0);
  assert.equal(result.error, null);
  assert.equal(result.signal, null);
  assert.equal(result.timedOut, false);
  assert.equal(result.outputTruncated, false);
  assert.equal(result.stdout, 'hello');
  assert.equal(result.stderr, 'diagnostic');
});

test('nonzero exit retains native error and output', async () => {
  const result = await runNode('process.stdout.write("partial"); process.stderr.write("bad"); process.exitCode = 7');
  assert.equal(result.processSuccess, false);
  assert.equal(result.exitCode, 7);
  assert.equal(result.error.code, 7);
  assert.equal(result.error.name, 'Error');
  assert.match(result.error.message, /Command failed/);
  assert.ok(result.error.stack);
  assert.equal(result.stdout, 'partial');
  assert.equal(result.stderr, 'bad');
});

test('launch failure has no observed exit and retains ENOENT details', async () => {
  const result = await runCommand(join(process.cwd(), 'missing-executable-node-command-test'), [], options);
  assert.equal(result.processSuccess, false);
  assert.equal(result.exitCode, null);
  assert.equal(result.error.code, 'ENOENT');
  assert.ok(result.error.syscall);
  assert.ok(result.error.path);
  assert.equal(result.signal, null);
  assert.equal(result.timedOut, false);
});

test('synchronous launch rejection remains structured failure', async () => {
  const result = await runCommand(null, [], options);
  assert.equal(result.processSuccess, false);
  assert.equal(result.exitCode, null);
  assert.equal(result.error.code, 'ERR_INVALID_ARG_TYPE');
});

test('timeout with null exit is failure, with partial output preserved', async () => {
  const result = await runNode('process.stdout.write("started"); setInterval(() => {}, 1000)', { timeoutMs: 1000 });
  assert.equal(result.processSuccess, false);
  assert.equal(result.exitCode, null);
  assert.equal(result.error.code, null);
  assert.equal(result.signal, 'SIGTERM');
  assert.equal(result.error.signal, 'SIGTERM');
  assert.equal(result.killed, true);
  assert.equal(result.timedOut, true);
  assert.equal(result.outputTruncated, false);
  assert.equal(result.stdout, 'started');
});

test('self-termination is failure without being mislabeled timeout', async () => {
  const result = await runNode('process.stdout.write("started"); process.kill(process.pid, "SIGTERM")');
  assert.equal(result.processSuccess, false);
  // Windows TerminateProcess reports exit 1; POSIX reports the signal.
  assert.equal(result.exitCode, process.platform === 'win32' ? 1 : null);
  assert.equal(result.signal, process.platform === 'win32' ? null : 'SIGTERM');
  assert.equal(result.timedOut, false);
  assert.equal(result.stdout, 'started');
});

test('a deadline followed by graceful exit zero is still not success', {
  skip: process.platform === 'win32' ? 'Windows does not deliver catchable SIGTERM' : false,
}, async () => {
  const result = await runNode('process.on("SIGTERM", () => process.exit(0)); setInterval(() => {}, 1000)', { timeoutMs: 1000 });
  assert.equal(result.exitCode, 0);
  assert.equal(result.timedOut, true);
  assert.equal(result.processSuccess, false);
});

test('a descendant holding the pipes cannot strand the call past the deadline', async () => {
  // The direct child hands its stdout/stderr to a detached grandchild and exits
  // zero at once, so only the deadline can release the call.
  const source = 'require("node:child_process")' +
    '.spawn(process.execPath, ["-e", "setTimeout(() => {}, 10000)"], { detached: true, stdio: ["ignore", 1, 2] })' +
    '.unref(); process.stdout.write("parent-exited")';
  const started = Date.now();
  const result = await runNode(source, { timeoutMs: 1000 });
  const elapsed = Date.now() - started;
  assert.equal(result.processSuccess, false);
  assert.equal(result.timedOut, true);
  assert.equal(result.stdout, 'parent-exited');
  assert.ok(elapsed < 6000, 'deadline did not release the call: ' + elapsed + 'ms');
});

for (const stream of ['stdout', 'stderr']) {
  test(stream + ' buffer overflow preserves truncation and fails', async () => {
    const result = await runNode('process.' + stream + '.write("x".repeat(65536))', { maxBuffer: 128 });
    assert.equal(result.processSuccess, false);
    assert.equal(result.error.code, 'ERR_CHILD_PROCESS_STDIO_MAXBUFFER');
    assert.equal(result.outputTruncated, true);
    assert.equal(result.timedOut, false);
    assert.equal(result[stream], 'x'.repeat(128));
  });
}

test('exit zero cannot verify an expected artifact', async t => {
  const directory = await mkdtemp(join(tmpdir(), 'forseti-node-artifact-test-'));
  t.after(() => rmdir(directory));
  const result = await runNode('process.stdout.write("claimed saved")');
  assert.equal(result.processSuccess, true);
  assert.equal(result.stdout, 'claimed saved');
  await assert.rejects(readFile(join(directory, 'expected.txt')), { code: 'ENOENT' });
});

test('invalid budgets fail before launch', () => {
  assert.throws(() => runCommand(process.execPath, [], { cwd: process.cwd(), timeoutMs: 0 }), /timeoutMs/);
  assert.throws(() => runCommand(process.execPath, [], { timeoutMs: 1000 }), /cwd/);
  assert.throws(() => runNode('', { maxBuffer: 0 }), /maxBuffer/);
});

test('an awaited run keeps its required deadline; only an inspectable start may omit one', async () => {
  // runCommand returns no handle, so an omitted deadline is an unbounded,
  // unstoppable await rather than a checkpointed one. Fail before launch.
  assert.throws(() => runCommand(process.execPath, [], { cwd: process.cwd() }), /timeoutMs/);
  const command = startCommand(process.execPath, ['-e', ''], { cwd: process.cwd() });
  assert.equal(command.inspect().timedOut, false);
  command.terminate();
  await command.result;
});


test('healthy work survives review checkpoints with one process and no hard deadline', async t => {
  const command = startCommand(process.execPath, ['-e',
    'const tick = setInterval(() => process.stdout.write("."), 100); setTimeout(() => { clearInterval(tick); process.stdout.write("done"); }, 1400)'],
    { cwd: process.cwd() });
  t.after(() => command.terminate());
  const first = command.inspect();
  await delay(500); // expected-duration checkpoint, not a kill timer
  const checkpoint = command.inspect();
  assert.equal(checkpoint.pid, first.pid);
  assert.equal(checkpoint.state, 'running');
  assert.equal(checkpoint.timedOut, false);
  assert.equal(checkpoint.interrupted, false);
  assert.equal('processSuccess' in checkpoint, false);
  assert.ok(checkpoint.stdoutChars > 0);
  assert.ok(checkpoint.lastOutputElapsedMs > 0);
  const result = await command.result;
  assert.equal(result.processSuccess, true);
  assert.equal(result.timedOut, false);
  assert.match(result.stdout, /^\.+done$/);
  assert.equal(command.inspect().state, 'completed');
  command.terminate(); // completed results cannot be relabeled by a late stop
  assert.equal(command.inspect().interrupted, false);
});

test('a quiet checkpoint is not a deadline or a failure verdict', async t => {
  const command = startCommand(process.execPath, ['-e', 'setTimeout(() => {}, 900)'], { cwd: process.cwd() });
  t.after(() => command.terminate());
  await delay(300);
  assert.equal(command.inspect().state, 'running');
  assert.equal(command.inspect().stdoutChars, 0);
  assert.equal(command.inspect().lastOutputElapsedMs, null);
  assert.equal((await command.result).processSuccess, true);
});

test('explicit stop is interruption, not timeout, and never success', async t => {
  const command = startCommand(process.execPath, ['-e', 'setInterval(() => {}, 1000)'], { cwd: process.cwd(), timeoutMs: 5000 });
  t.after(() => command.terminate());
  await delay(100);
  command.terminate();
  command.terminate(); // same stop decision, no restart or repeated signal
  const result = await command.result;
  assert.equal(result.processSuccess, false);
  assert.equal(result.interrupted, true);
  assert.equal(result.timedOut, false);
  assert.equal(result.exitCode, null);
  assert.equal(result.signal, 'SIGTERM');
  assert.equal(command.inspect().state, 'completed');
});
