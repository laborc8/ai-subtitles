import { Component, NgZone } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { environment } from '../../environments/environment';

declare const jwplayer: any;

interface SubtitleEntry {
  index: number;
  start: string;
  end: string;
  text: string;
  startSeconds: number;
  lang?: string;
}


@Component({
  standalone: true,
  selector: 'app-transcript-gen',
  templateUrl: './transcript-gen.component.html',
  styleUrls: ['./transcript-gen.component.css'],
  imports: [CommonModule, FormsModule]
})
export class TranscriptGenComponent {
  environment = environment;
  selectedClientId: string = '';
  
  bucket = '';
  target = '';
  prompt_lang = 'en';
  enable_translation = false;
  override = false;  // Default to false

  upload = false;
  upload_bucket = '';
  upload_prefix = '';
  advancedEncoding = true;

  logs: string[] = [];

  videoUrl: string = '';
  jwplayerLoaded = false;

  previewUrl: string = '';
  subtitleTracks: any[] = [];
  subtitlesByLang: { [lang: string]: SubtitleEntry[] } = {};
  transcriptText: string = '';

  selectedLang = 'en';
  showOriginal = false;

  searchTerm = '';
  activeSubtitleIndex = -1;
  private searchDebounceTimer: any = null;

  supportedLanguages = environment.supportedLanguages;

  // Set these appropriately
  cloudfrontBaseUrl = environment.cloudfrontBaseUrl;
  jwplayerKey = environment.jwplayerKey;

  isLoading = false;

  constructor(private http: HttpClient, private zone: NgZone) {
    const script = document.createElement('script');
    script.src = 'https://cdn.jwplayer.com/libraries/' + this.jwplayerKey + '.js';

    script.onload = () => {
      console.log('JWPlayer script loaded.');
      (window as any).jwplayer = jwplayer; // ensure global assignment if needed
      this.jwplayerLoaded = true;
    };

    document.body.appendChild(script);
  }

  getSelectedClient() {
    return this.environment.clients.find(client => client.id === this.selectedClientId);
  }

  onClientChange() {
    const selectedClient = this.getSelectedClient();
    if (selectedClient) {
      this.bucket = selectedClient.bucket;
      this.target = selectedClient.defaultTarget;
      this.prompt_lang = selectedClient.defaultLanguage;
      this.cloudfrontBaseUrl = selectedClient.cloudfrontBaseUrl;
    }
  }

  pingServer() {
    this.logs.push('Pinging server...');
    this.http.get<any>(environment.apiBaseUrl + '/api/ping').subscribe({
      next: (res) => this.logs.push(`Ping response: ${JSON.stringify(res)}`),
      error: (err) => this.logs.push('Ping failed: ' + (err.message || 'Server unreachable'))
    });
  }

  startTranscription() {
    if (!this.selectedClientId) {
      this.logs.push('Please select a client first.');
      return;
    }

    this.logs = [
      `Preparing transcription for: ${this.target}`,
      `Client: ${this.getSelectedClient()?.name}`,
      `Bucket: ${this.bucket}`,
      'Sending request to backend...'
    ];

    this.videoUrl = '';
    this.previewUrl = '';
    this.subtitleTracks = [];
    this.subtitlesByLang = {};
    this.transcriptText = '';
    this.activeSubtitleIndex = -1;
    this.isLoading = true;


    const payload: any = {
      bucket: this.bucket,
      target: this.target,
      prompt_lang: this.prompt_lang,
      enable_translation: true,
      upload: this.upload,
      advanced_encoding: this.advancedEncoding,
      override: this.override,  // Add override to payload
      client_id: this.selectedClientId  // Use selected client ID
    };

    if (this.upload) {
      payload.upload_bucket = this.upload_bucket;
      payload.upload_prefix = this.upload_prefix;
    }

    payload.languages = this.supportedLanguages
      .filter(l => l.selected)
      .map(l => l.code);

    if (payload.languages.length === 0) {
      payload.languages = ['en']; // fallback
    }

    this.http.post<any>(environment.apiBaseUrl + '/api/transcribe', payload).subscribe({
      next: (result) => {
        this.logs.push('--- DONE ---');
        this.logs.push(JSON.stringify(result, null, 2));

		/*
        //const subtitleKey = this.upload ? `${fileBase}.srt` : `api/storage/${fileBase}/${fileBase}.srt`;
        //const transcriptKey = this.upload ? `${fileBase}.txt` : `api/storage/${fileBase}/${fileBase}.txt`;

        const fileBase = this.target.split('/').pop()?.replace('.mp4', '') || 'output';
        const videoKey = this.target;

        console.log("---");

        if (this.upload) {
          // Construct all URLs from CloudFront when uploaded
          this.subtitleUrl = this.cloudfrontBaseUrl + this.upload_prefix + '/' + fileBase + '.srt';
          this.previewUrl = this.cloudfrontBaseUrl + this.upload_prefix + '/' + fileBase + '_01.png';
          this.videoUrl = this.cloudfrontBaseUrl + this.upload_prefix + '/hls/master.m3u8';
          const dashUrl = this.cloudfrontBaseUrl + this.upload_prefix + '/dash/stream.mpd';
          const transcriptPath = this.cloudfrontBaseUrl + this.upload_prefix + '/' + fileBase + '.txt';

          this.initJWPlayerWithSources(this.videoUrl, dashUrl, this.subtitleUrl, this.previewUrl);
          this.getTranscriptFromUrl(transcriptPath, false);  // false = don't prepend host
        } else {
          // Use backend URLs
          this.subtitleUrl = environment.apiBaseUrl + result[0].subtitle_url;
          this.previewUrl = result[0].preview_url;
          this.videoUrl = result[0].hls_url;
          const dashUrl = result[0].dash_url;

          this.initJWPlayerWithSources(this.videoUrl, dashUrl, this.subtitleUrl, this.previewUrl);
          this.getTranscriptFromUrl(result[0].transcript_url, true);  // true = prepend host
        }
        */
		const fileBase = this.target.split('/').pop()?.replace('.mp4', '') || 'output';
        this.previewUrl = result[0].preview_url;
        this.videoUrl = result[0].hls_url;

        this.subtitleTracks = [];

        for (const lang of this.supportedLanguages) {
          let url = result[0][`subtitle_url_${lang.code}`];

          // fallback for English
          if (lang.code === 'en' && !url && result[0].subtitle_url) {
            url = result[0].subtitle_url;
          }

          if (url) {
            const fullUrl = environment.apiBaseUrl + url;
            this.subtitleTracks.push({
              file: fullUrl,
              label: lang.label,
              kind: 'captions',
              default: lang.code === 'en'
            });
            this.loadSubtitlesForLang(lang.code, fullUrl);
          }
        }

        console.log('Subtitle languages loaded:', Object.keys(this.subtitlesByLang));
        console.log('Selected language:', this.selectedLang);

        const waitForJwPlayer = () => {
          if (this.jwplayerLoaded && typeof jwplayer === 'function') {
            this.initJWPlayerWithTracks();
          } else {
            setTimeout(waitForJwPlayer, 100); // retry every 100ms
          }
        };
        waitForJwPlayer();
        this.isLoading = false;
      },
      error: (err) => {
        this.logs.push('Error: ' + (err?.error?.message || err.message || err));

        this.isLoading = false;
      }
    });
  }

  loadSubtitlesForLang(lang: string, url: string) {
    this.http.get(url, {
      headers: {
        'X-API-Key': environment.apiKey
      },
      responseType: 'text'  // Moved inside the same object
    }).subscribe({
      next: (srt) => {
        const parsed = this.parseSrt(srt).map(s => ({ ...s, lang }));
        this.subtitlesByLang[lang] = parsed;

        console.log(`Loaded ${parsed.length} subtitles for ${lang}:`, parsed);

        if (!this.subtitlesByLang[this.selectedLang]) {
          console.warn(`No transcript found for ${this.selectedLang}`);
          this.selectedLang = lang;
        }

        if (lang === this.selectedLang) {
          this.transcriptText = srt;
        }
      },
      error: () => this.logs.push(`Failed to load transcript for ${lang}.`)
    });
  }




  initJWPlayerWithTracks() {
    setTimeout(() => {
      console.log("jwplayer loaded");
      const player = jwplayer('video-player').setup({
        image: this.previewUrl,
        playlist: [{
          image: this.previewUrl,
          sources: [
            { file: this.videoUrl }
          ],
          tracks: this.subtitleTracks
        }],
        width: "100%",
        aspectratio: "16:9",
        autostart: true,
        dash: "shaka"
      });

      jwplayer('video-player').setCurrentCaptions(1); // Default to English
      console.log('Tracks loaded into JWPlayer:', jwplayer('video-player').getCaptionsList());

      // Handle subtitle language switching
      player.on('captionsChanged', (event: any) => {
        console.log("captionsChange");

        const captionTracks = player.getCaptionsList();
        const selectedTrack = captionTracks?.[event.track]; // event.track is the index
        const selectedLabel = selectedTrack?.label?.toLowerCase();

        if (selectedLabel) {
          const matchingLang = this.supportedLanguages.find(lang => lang.label.toLowerCase() === selectedLabel);
          if (matchingLang) {
            this.selectedLang = matchingLang.code;
          }
        }

      });


      // Track active subtitle
      player.on('time', (e: any) => {
              const currentTime = e.position;
              const subs = this.subtitlesByLang[this.selectedLang] || [];
              const activeIndex = subs.findIndex((s, i) => {
                const next = subs[i + 1];
                return currentTime >= s.startSeconds && (!next || currentTime < next.startSeconds);
              });
              this.activeSubtitleIndex = activeIndex;
              //this.scrollActiveSubtitleIntoView();
            });
          }, 500);
        }


  /*
  seekTo(seconds: number) {
    jwplayer('video-player').seek(seconds);
  }
  */

  seekTo(seconds: number) {
    console.log('Seeking to:', seconds);
    const playerInstance = jwplayer('video-player');
    if (playerInstance && typeof playerInstance.seek === 'function') {
      playerInstance.seek(seconds);
      playerInstance.play(true); // ensure playback resumes if paused
    }
  }

  scrollActiveSubtitleIntoView() {
    const el = document.getElementById('subtitle-' + this.activeSubtitleIndex);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  onSearchChange() {
    clearTimeout(this.searchDebounceTimer);
    this.searchDebounceTimer = setTimeout(() => {
      // force change detection or re-parse if needed
    }, 200);
  }

  highlightSearch(text: string, term: string): string {
    if (!text) return '';
    if (!term || term.length < 2) return text;
    const regex = new RegExp(`(${term})`, 'gi');
    return text.replace(regex, `<span class="bg-yellow-200">$1</span>`);
  }

/*
  getTranscriptFromUrl(url: string, prependHost: boolean = true) {
    const fullUrl = prependHost ? environment.apiBaseUrl + url : url;
    this.http.get(fullUrl, { responseType: 'text' }).subscribe({
      next: (srtText) => {
        this.transcriptText = srtText;
        this.parsedSubtitles = this.parseSrt(srtText);
      },
      error: () => {
        this.logs.push('Failed to load transcript.');
        this.transcriptText = '';
        this.parsedSubtitles = [];
      }
    });
  }


  getSignedVideoUrl(s3Key: string) {
    this.http.post<any>(environment.apiBaseUrl + '/api/sign-url', { 
      key: s3Key,
      client_id: environment.clientId
    }).subscribe({
      next: (res) => {
        this.videoUrl = res?.signed_url;
        this.initJWPlayer();
      },
      error: (err) => {
        this.logs.push('Failed to get signed video URL');
      }
    });
  }

  getTranscript(url: string) {
    this.http.get(environment.apiBaseUrl + url, { responseType: 'text' }).subscribe({
      next: (srtText) => {
        this.parsedSubtitles = this.parseSrt(srtText);
      },
      error: () => this.logs.push('Failed to load transcript.')
    });
  }
*/
parseSrt(srtText: string): SubtitleEntry[] {
  if (!srtText) return [];

  // Normalize line endings and remove WEBVTT header
  const lines = srtText
    .replace(/\r\n|\r/g, '\n')
    .replace(/^WEBVTT.*\n+/i, '')
    .split('\n');

  const subtitles: SubtitleEntry[] = [];
  let index = 1;
  let buffer: string[] = [];

  for (const line of lines) {
    if (line.trim() === '') {
      if (buffer.length) {
        let timeLine = '';
        let textLines: string[] = [];

        if (buffer[0].includes('-->')) {
          timeLine = buffer[0];
          textLines = buffer.slice(1);
        } else if (buffer[1]?.includes('-->')) {
          timeLine = buffer[1];
          textLines = buffer.slice(2);
        } else {
          console.warn('Skipping invalid block (no --> found):', buffer);
          buffer = [];
          continue;
        }

        const [start, end] = timeLine.split(' --> ');
        const text = textLines.join('\n').trim();

        if (start && end) {
          subtitles.push({
            index,
            start: start.trim(),
            end: end.trim(),
            text,
            startSeconds: this.parseTimeToSeconds(start.trim())
          });
          index++;
        }
      }
      buffer = [];
    } else {
      buffer.push(line);
    }
  }

  return subtitles;
}



parseTimeToSeconds(timeStr: string): number {
  const [hh, mm, ssMs] = timeStr.split(':');
  const [ss, ms] = ssMs.includes(',') ? ssMs.split(',') : ssMs.split('.');
  return parseInt(hh) * 3600 + parseInt(mm) * 60 + parseInt(ss) + parseInt(ms) / 1000;
}

shouldInsertTimeBreak(index: number): boolean {
  const subs = this.subtitlesByLang[this.selectedLang] || [];
  const current = subs[index];
  const prev = subs[index - 1];
  return !prev || Math.floor(current.startSeconds / 900) !== Math.floor(prev.startSeconds / 900);
}


formatTimeBlock(seconds: number): string {
  const total = Math.floor(seconds);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const mm = m.toString().padStart(2, '0');
  const hh = h > 0 ? `${h}:` : '';
  return `${hh}${mm}:00`;
}

getGroupedSubtitles(lang: string): SubtitleEntry[][] {
  const subs = this.subtitlesByLang[lang] || [];
  const groups: SubtitleEntry[][] = [];
  for (let i = 0; i < subs.length; i += 5) {
    groups.push(subs.slice(i, i + 5));
  }
  return groups;
}

isGroupActive(group: { startSeconds: number }): boolean {
  const current = this.activeSubtitleIndex;
  const subs = this.subtitlesByLang[this.selectedLang] || [];

  const groupStart = group.startSeconds;
  const groupEnd = groupStart + 20; // rough range (~20s chunk)

  if (current < 0 || !subs[current]) return false;

  const currentTime = subs[current].startSeconds;
  return currentTime >= groupStart && currentTime < groupEnd;
}


}
