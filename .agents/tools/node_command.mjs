import { execFile } from 'node:child_process';

// Node REPL fallback only; normal command tools remain the normal route.
// A result describes a process, never a verified artifact or a stopped process tree.
const errorRecord = error => error === null ? null : {
  ...Object.fromEntries(Object.getOwnPropertyNames(error).map(key => [key, error[key]])),
  name: error.name,
  message: error.message,
};

/** Run one executable without a shell or retries; preserve unknown exit codes.
 * cwd and timeoutMs are explicit. env, when supplied, is the child's full env.
 * A deadline requests SIGTERM on the direct child and waits for execFile's
 * completion callback. A child/descendant holding pipes open may prevent a
 * response: no response is never success. killed means a kill request succeeded,
 * not proof of termination. stdout/stderr are UTF-8, bounded by maxBuffer each.
 * A thrown validation/launch error or any result error remains a failure.
 */
export function runCommand(file, args, { cwd, timeoutMs, maxBuffer = 1024 * 1024, env } = {}) {
  if (typeof cwd !== 'string' || cwd.length === 0) throw new TypeError('cwd is required');
  if (!Number.isInteger(timeoutMs) || timeoutMs <= 0 || timeoutMs > 2147483647) {
    throw new RangeError('timeoutMs must be a positive 32-bit timer duration');
  }
  if (!Number.isSafeInteger(maxBuffer) || maxBuffer <= 0) {
    throw new RangeError('maxBuffer must be a positive safe integer');
  }
  return new Promise(resolve => {
    let child;
    let timer;
    let exitCode = null;
    let signal = null;
    let timedOut = false;
    let terminationError = null;
    const finish = (error, stdout, stderr) => {
      clearTimeout(timer);
      resolve({
        processSuccess: error === null && terminationError === null &&
          exitCode === 0 && signal === null && !timedOut,
        exitCode,
        signal,
        timedOut,
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
        exitCode = code;
        signal = exitSignal;
      });
      // Own the deadline flag: a null error.code or a killed flag alone cannot
      // identify a timeout (maxBuffer and external termination can also kill).
      timer = setTimeout(() => {
        timedOut = true;
        try { child.kill('SIGTERM'); }
        catch (error) { terminationError = error; }
      }, timeoutMs);
    } catch (error) {
      finish(error, '', '');
    }
  });
}
