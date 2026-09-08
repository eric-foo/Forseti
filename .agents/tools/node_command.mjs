import { execFile } from 'node:child_process';

// Node REPL fallback only; normal command tools remain the normal route.
// A result describes a process, never a verified artifact or a stopped process tree.
const errorRecord = error => error === null ? null : {
  ...Object.fromEntries(Object.getOwnPropertyNames(error).map(key => [key, error[key]])),
  name: error.name,
  message: error.message,
};

/** Start once, inspect at review checkpoints, and consume the same result.
 * cwd is required. timeoutMs is an optional explicit hard deadline, never an
 * expected-duration checkpoint. env, when supplied, is the child's full env.
 * inspect() reports observation only, not health or process success. terminate()
 * requests SIGTERM once on the direct child; it never retries the command.
 * A deadline or explicit stop detaches our pipe read ends. A direct child that
 * outlives SIGTERM can still hold the result open; no response is never success.
 * Output after termination is requested is not collected. killed means a kill
 * request succeeded, not proof of termination or descendant shutdown.
 * stdout/stderr are UTF-8, bounded by maxBuffer each. Inspection reports counts
 * of decoded characters without accumulating another copy of the output.
 */
export function startCommand(file, args, { cwd, timeoutMs, maxBuffer = 1024 * 1024, env } = {}) {
  if (typeof cwd !== 'string' || cwd.length === 0) throw new TypeError('cwd is required');
  if (timeoutMs !== undefined &&
      (!Number.isInteger(timeoutMs) || timeoutMs <= 0 || timeoutMs > 2147483647)) {
    throw new RangeError('timeoutMs must be a positive 32-bit hard deadline when supplied');
  }
  if (!Number.isSafeInteger(maxBuffer) || maxBuffer <= 0) {
    throw new RangeError('maxBuffer must be a positive safe integer');
  }
  const started = performance.now();
  let child;
  let timer;
  let exitCode = null;
  let signal = null;
  let exitObserved = false;
  let completed = false;
  let timedOut = false;
  let interrupted = false;
  let terminationError = null;
  let stdoutChars = 0;
  let stderrChars = 0;
  let lastOutputElapsedMs = null;
  let finishedElapsedMs;
  const terminate = (deadline = false) => {
    if (completed || timedOut || interrupted) return;
    clearTimeout(timer);
    timedOut = deadline;
    interrupted = !deadline;
    try { child?.kill('SIGTERM'); }
    catch (error) { terminationError = error; }
    // execFile completes on stream close; inherited pipes must not strand it.
    child?.stdout?.destroy();
    child?.stderr?.destroy();
  };
  const result = new Promise(resolve => {
    const finish = (error, stdout, stderr) => {
      clearTimeout(timer);
      completed = true;
      finishedElapsedMs = performance.now() - started;
      resolve({
        processSuccess: error === null && terminationError === null &&
          exitCode === 0 && signal === null && !timedOut && !interrupted,
        exitCode,
        signal,
        timedOut,
        interrupted,
        killed: child?.killed ?? false,
        outputTruncated: error?.code === 'ERR_CHILD_PROCESS_STDIO_MAXBUFFER',
        error: errorRecord(error),
        terminationError: errorRecord(terminationError),
        stdout,
        stderr,
      });
    };
    try {
      child = execFile(file, args, { cwd, env, encoding: 'utf8', maxBuffer, shell: false }, finish);
      child.once('exit', (code, exitSignal) => {
        exitObserved = true;
        exitCode = code;
        signal = exitSignal;
      });
      child.stdout?.on('data', chunk => {
        stdoutChars += chunk.length;
        lastOutputElapsedMs = performance.now() - started;
      });
      child.stderr?.on('data', chunk => {
        stderrChars += chunk.length;
        lastOutputElapsedMs = performance.now() - started;
      });
      if (timeoutMs !== undefined) timer = setTimeout(() => terminate(true), timeoutMs);
    } catch (error) {
      finish(error, '', '');
    }
  });
  return {
    result,
    inspect: () => ({
      state: completed ? 'completed' : exitObserved ? 'awaiting_output_close' : 'running',
      pid: child?.pid ?? null,
      elapsedMs: finishedElapsedMs ?? performance.now() - started,
      exitCode, signal, timedOut, interrupted,
      stdoutChars, stderrChars, lastOutputElapsedMs,
    }),
    terminate: () => terminate(false),
  };
}

// Awaiting convenience for bounded work. It exposes no inspect or terminate
// handle, so no review checkpoint can replace a deadline here and timeoutMs
// stays required; use startCommand across REPL calls to inspect without one.
export function runCommand(file, args, options) {
  if (options?.timeoutMs === undefined) {
    throw new RangeError('timeoutMs is required by runCommand; use startCommand to inspect work without a hard deadline');
  }
  return startCommand(file, args, options).result;
}
