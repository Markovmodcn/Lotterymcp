export type PythonProgram = {
    id: string;
    label: string;
    scriptRelativePath: string;
    aliases: readonly string[];
};
export type RunCommandOptions = {
    cwd?: string;
    env?: NodeJS.ProcessEnv;
    inheritStdio?: boolean;
};
export type RunCommandResult = {
    code: number;
    stdout: string;
    stderr: string;
};
export type PythonRuntimeDeps = {
    platform: NodeJS.Platform;
    env: NodeJS.ProcessEnv;
    existsSync: (targetPath: string) => boolean;
    mkdir: (targetPath: string, options?: {
        recursive?: boolean;
    }) => Promise<void>;
    readFile: (targetPath: string, encoding: BufferEncoding) => Promise<string>;
    writeFile: (targetPath: string, content: string, encoding: BufferEncoding) => Promise<void>;
    runCommand: (command: string, args: string[], options?: RunCommandOptions) => Promise<RunCommandResult>;
};
export type PythonProgramRunOptions = {
    apiBaseUrl: string;
    token?: string;
    periods: string;
    repoRoot: string;
    pythonEnvDir?: string;
    outputPath?: string;
    onStatus?: (message: string) => void;
};
export type PythonProgramRunResult = {
    exitCode: number;
    pythonPath: string;
    program: PythonProgram;
};
export declare const PYTHON_PROGRAMS: readonly PythonProgram[];
export declare const getDefaultPythonRuntimeDeps: () => PythonRuntimeDeps;
export declare const getPythonProgramById: (value: string) => PythonProgram | undefined;
export declare const getPythonEnvDir: () => string;
export declare const getVenvPythonPath: (pythonEnvDir: string, platform?: NodeJS.Platform) => string;
export declare const getRequirementsStampPath: (pythonEnvDir: string) => string;
export declare const ensurePythonRuntime: (repoRoot: string, pythonEnvDir: string, deps?: PythonRuntimeDeps, onStatus?: (message: string) => void) => Promise<string>;
export declare const runPythonAnalysisProgram: (programId: string, options: PythonProgramRunOptions, deps?: PythonRuntimeDeps) => Promise<PythonProgramRunResult>;
