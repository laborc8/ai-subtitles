import { Environment } from './environment.interface';

export const environment: Environment = {
  production: true,
  apiBaseUrl: 'https://ai.olliecourse.com',
  apiKey: 'L4h6hBOAC5eLHpNdAgMBAAE',
  jwplayerKey: 'Ls5giHR2',
  cloudfrontBaseUrl: 'https://d2iujko1ysket6.cloudfront.net/',
  defaultBucket: 'studema',
  defaultTarget: 'videos/PerformiaInt/EHS/EHS_DAY_5/0341_B.qt',
  defaultLanguage: 'en',
  clientId: 'default',
  clients: [
    {
      id: 'knusperstube',
      name: 'Knusperstube',
      bucket: 'nx-studema-vod-source-1ejycowhvlcek',
      cloudfrontBaseUrl: 'https://d2iujko1ysket6.cloudfront.net/',
      defaultTarget: 'videos/knusperstube-3-austria-1a6689b4/glossar/aufbau_eismaschine_teil_3_v01_25042023.mp4',
      defaultLanguage: 'de'
    },
    {
      id: 'otthaus',
      name: 'Ott-Haus',
      bucket: 'nx-studema-vod-source-1ejycowhvlcek',
      cloudfrontBaseUrl: 'https://d2iujko1ysket6.cloudfront.net/',
      defaultTarget: 'videos/OttHaus/Training/001_basics.mp4',
      defaultLanguage: 'de'
    },
    {
      id: 'ollie',
      name: 'Ollie',
      bucket: 'nx-studema-vod-source-1ejycowhvlcek',
      cloudfrontBaseUrl: 'https://d2iujko1ysket6.cloudfront.net/',
      defaultTarget: 'videos/Ollie/Course/001_welcome.mp4',
      defaultLanguage: 'en'
    },
    {
      id: 'studema',
      name: 'Studema',
      bucket: 'nx-studema-vod-source-1ejycowhvlcek',
      cloudfrontBaseUrl: 'https://d2iujko1ysket6.cloudfront.net/',
      defaultTarget: 'videos/Studema/Training/001_intro.mp4',
      defaultLanguage: 'en'
    },
    {
      id: 'performia',
      name: 'Performia',
      bucket: 'studema',
      cloudfrontBaseUrl: 'https://d2cqk28gglxbe.cloudfront.net/',
      defaultTarget: 'videos/PerformiaInt/EHS/EHS_DAY_5/0341_B.qt',
      defaultLanguage: 'en'
    }
  ],
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