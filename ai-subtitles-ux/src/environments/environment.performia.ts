import { Environment } from './environment.interface';

export const environment: Environment = {
  production: true,
  apiBaseUrl: 'https://ai.olliecourse.com',
  apiKey: 'L4h6hBOAC5eLHpNdAgMBAAE',
  jwplayerKey: 'Ls5giHR2',
  cloudfrontBaseUrl: 'https://performia.cloudfront.net/',
  defaultBucket: 'performia-videos',
  defaultTarget: 'videos/PerformiaInt/EHS/EHS_DAY_5/0341_B.qt',
  defaultLanguage: 'en',
  clientId: 'performia',
  supportedLanguages: [
    { code: 'en', label: 'English', selected: true },
    { code: 'de', label: 'German', selected: false },
    { code: 'es', label: 'Spanish', selected: false },
    { code: 'hu', label: 'Hungarian', selected: false },
    { code: 'cs', label: 'Czech', selected: false },
    { code: 'sv', label: 'Swedish', selected: false },
    { code: 'ru', label: 'Russian', selected: false },
    { code: 'zh', label: 'Chinese', selected: false },
    { code: 'ja', label: 'Japanese', selected: false },
    { code: 'he', label: 'Hebrew', selected: false },
    { code: 'ro', label: 'Romanian', selected: false },
    { code: 'fr', label: 'French', selected: false }
  ]
}; 