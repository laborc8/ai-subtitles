# Environment Configuration

This directory contains environment-specific configuration files for the WhisperUi application.

## Files

- `environment.interface.ts` - TypeScript interface defining the environment structure
- `environment.ts` - Development environment configuration (default)
- `environment.prod.ts` - Production environment configuration

## Configuration Properties

| Property | Type | Description |
|----------|------|-------------|
| `production` | boolean | Flag indicating if running in production mode |
| `apiBaseUrl` | string | Base URL for the API endpoints |
| `apiKey` | string | API key for authentication |
| `jwplayerKey` | string | JWPlayer license key |
| `cloudfrontBaseUrl` | string | CloudFront CDN base URL |
| `defaultBucket` | string | Default S3 bucket name |
| `defaultTarget` | string | Default video target path |
| `defaultLanguage` | string | Default language code |
| `clientId` | string | Client identifier for multi-client support |
| `clients` | array | Array of client configurations |
| `supportedLanguages` | array | Array of supported languages with selection state |

## Multi-Client Support

The application supports multiple clients with different configurations. Each client can have:
- Different CloudFront base URLs
- Different API keys
- Different default buckets and targets
- Different default languages

### Available Clients

| Client Name | Client ID | Bucket | CloudFront URL | Default Language |
|-------------|-----------|--------|----------------|------------------|
| Knusperstube | `knusperstube` | `knusperstube-videos` | `https://knusperstube.cloudfront.net/` | German |
| Ott-Haus | `otthaus` | `otthaus-videos` | `https://otthaus.cloudfront.net/` | German |
| Ollie | `ollie` | `ollie-videos` | `https://ollie.cloudfront.net/` | English |
| Studema | `studema` | `studema12` | `https://d2iujko1ysket6.cloudfront.net/` | English |
| Performia | `performia` | `studema` | `https://d2iujko1ysket6.cloudfront.net/` | English |

### Client Selection

Users can select a client from a dropdown in the transcription form. When a client is selected:
- The bucket is automatically set based on the client configuration
- The default target path is updated
- The default language is set
- The CloudFront base URL is updated
- The `client_id` is sent with API requests

## Usage

### In Components

Import the environment configuration in your components:

```typescript
import { environment } from '../environments/environment';

// Use environment variables
const apiUrl = environment.apiBaseUrl;
const apiKey = environment.apiKey;
const clientId = environment.clientId;

// Get client configuration
const selectedClient = environment.clients.find(client => client.id === 'performia');
const bucket = selectedClient?.bucket;
```

### Client Selection in Template

```html
<select [(ngModel)]="selectedClientId" (ngModelChange)="onClientChange()">
  <option value="">-- Select a client --</option>
  <option *ngFor="let client of environment.clients" [value]="client.id">
    {{ client.name }}
  </option>
</select>
```

### Interactive Player Usage

```html
<app-studema-interactive-player
  videoKey="videos/PerformiaInt/EHS/EHS_DAY_5/0341_B.qt"
  clientId="performia"
  advancedEncoding="false"
  defaultLanguage="en">
</app-studema-interactive-player>
```

## Build Commands

- **Development**: `npm run build:dev` or `ng build --configuration development`
- **Production**: `npm run build:prod` or `ng build --configuration production`
- **Serve Development**: `npm start` or `ng serve`
- **Serve Production**: `npm run start:prod` or `ng serve --configuration production`

## Environment Switching

The Angular CLI automatically switches environment files based on the build configuration:

- Development builds use `environment.ts`
- Production builds use `environment.prod.ts` (via file replacement in angular.json)

## Adding New Environment Variables

1. Add the property to `environment.interface.ts`
2. Add the property to both `environment.ts` and `environment.prod.ts`
3. Use the property in your components via the environment import

## Adding New Clients

1. Add the client configuration to the `clients` array in both environment files:

```typescript
{
  id: 'newclient',
  name: 'New Client',
  bucket: 'newclient-videos',
  cloudfrontBaseUrl: 'https://newclient.cloudfront.net/',
  defaultTarget: 'videos/NewClient/Introduction/001_intro.mp4',
  defaultLanguage: 'en'
}
```

2. The client will automatically appear in the dropdown selection
3. All API requests will include the selected `client_id` 