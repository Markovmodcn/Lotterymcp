export type NbcpConfig = {
    apiBaseUrl: string;
    token: string;
    defaultPeriods: string;
};
export declare const DEFAULT_API_BASE_URL = "https://www.neuxsbot.com";
export declare const DEFAULT_PERIODS = "100";
export declare const CONFIG_DIRNAME = ".neuxsbot";
export declare const CONFIG_FILENAME = "cp.config.json";
export declare const getConfigPath: () => string;
export declare const loadLocalConfig: () => Promise<Partial<NbcpConfig>>;
export declare const resolveConfig: () => Promise<Partial<NbcpConfig>>;
export declare const saveLocalConfig: (config: NbcpConfig) => Promise<void>;
export declare const validateConfig: (config: Partial<NbcpConfig>) => string[];
export declare const maskToken: (token: string) => string;
export declare const renderMcpConfigSnippet: (config: NbcpConfig) => string;
