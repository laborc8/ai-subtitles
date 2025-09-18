export interface ClientConfig {
  id: string;
  name: string;
  bucket: string;
  cloudfrontBaseUrl: string;
  defaultTarget: string;
  defaultLanguage: string;
}

export interface Environment {
  production: boolean;
  apiBaseUrl: string;
  apiKey: string;
  jwplayerKey: string;
  cloudfrontBaseUrl: string;
  defaultBucket: string;
  defaultTarget: string;
  defaultLanguage: string;
  clientId: string;
  clients: ClientConfig[];
  supportedLanguages: Array<{
    code: string;
    label: string;
    selected: boolean;
  }>;
} 