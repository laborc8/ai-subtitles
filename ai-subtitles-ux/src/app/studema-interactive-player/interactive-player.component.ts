import {
  Component, Input, Output, EventEmitter, ViewEncapsulation, NgZone, OnInit
} from '@angular/core';
import { OnChanges, SimpleChanges } from '@angular/core';
import { ElementRef } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { Renderer2 } from '@angular/core';
import { environment } from '../../environments/environment';

declare const jwplayer: any;

interface SubtitleApiResponse {
  subtitles: SubtitleTrack[];
  hls_url: string;
  dash_url: string;
  preview_url: string;
}

interface SubtitleTrack {
  file: string;
  label: string;
  lang: string;
}

interface SubtitleEntry {
  index: number;
  start: string;
  end: string;
  text: string;
  startSeconds: number;
}

@Component({
  selector: 'app-studema-interactive-player',
  standalone: true,
  templateUrl: './interactive-player.component.html',
  styleUrls: ['./interactive-player.component.css'],
  imports: [CommonModule, FormsModule],
  encapsulation: ViewEncapsulation.None,
})
export class InteractivePlayerComponent implements OnChanges {
  @Input() videoKey!: string;
  @Input() advancedEncoding: string = "false";
  @Input() defaultLanguage: string = environment.defaultLanguage;
  @Input() clientId: string = environment.clientId;

  @Input() courseId!: string;
  @Input() studentCourseId!: string;
  @Input() studentCourseStepId!: string;
  @Input() courseStepId!: string;
  @Input() companyId!: string;
  @Input() personId!: string;

  @Output() doneClicked = new EventEmitter<any>();

  subtitleTracks: SubtitleTrack[] = [];
  subtitlesByLang: { [lang: string]: SubtitleEntry[] } = {};
  selectedLang: string = environment.defaultLanguage;
  showOriginal = false;

  transcriptText: string = '';
  activeSubtitleIndex = -1;
  searchTerm = '';
  private searchDebounceTimer: any = null;

  hlsUrl: string = '';
  dashUrl: string = '';
  previewUrl: string = '';

  jwplayerKey = environment.jwplayerKey;
  jwplayerLoaded = false;
  private jwPlayerReady: Promise<void>;
  private playerInitialized = false;


  constructor(
    private http: HttpClient,
    private zone: NgZone,
    private sanitizer: DomSanitizer,
    private elRef: ElementRef,
  private renderer: Renderer2

  ) {
    this.jwPlayerReady = new Promise<void>((resolve) => {
      const script = document.createElement('script');
      script.src = `https://cdn.jwplayer.com/libraries/${this.jwplayerKey}.js`;
      script.onload = () => {
        (window as any).jwplayer = jwplayer;
        resolve();
      };
      document.body.appendChild(script);
    });
  }



  ngOnInit() {
    this.selectedLang = this.defaultLanguage || 'en';

    document.addEventListener('copy', this.onCopy);

  }

  ngOnDestroy() {
    document.removeEventListener('copy', this.onCopy);
  }


  ngAfterViewInit() {
    console.log("after view init");



    //this.waitForJWPlayerAndInit();

  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['videoKey'] && changes['videoKey'].currentValue) {
      this.jwPlayerReady.then(() => {
        this.loadVideoData();
      });
    }

    if (changes['defaultLanguage']) {
      this.selectedLang = this.defaultLanguage;
    }

    if (changes['clientId']) {
      // Reload video data if client changes
      if (this.videoKey) {
        this.jwPlayerReady.then(() => {
          this.loadVideoData();
        });
      }
    }
  }

  onCopy = (event: ClipboardEvent) => {
    const selection = window.getSelection();
    if (!selection) return;

    const target = (event.target as HTMLElement) || document.activeElement;

    // Allow copying from explicitly allowed elements
    if (target?.closest('.allow-copy')) {
      return;
    }

    event.preventDefault();
    event.clipboardData?.setData('text/plain', 'Copying transcript content is not allowed.');
  };



  loadVideoData() {
    // Fetch from API, set up player, etc.
    const apiBase = environment.apiBaseUrl;
    const apiKey = environment.apiKey;

    const queryParams = new URLSearchParams({
      video_key: this.videoKey,
      advanced: this.advancedEncoding === 'true' ? 'true' : 'false',
      client_id: this.clientId
    });

    this.http.get<SubtitleApiResponse>(
      `${apiBase}/api/subtitles?${queryParams.toString()}`,
      {
        headers: { 'X-API-Key': apiKey }
      }
    ).subscribe({
      next: (res) => {
        this.subtitleTracks = res.subtitles.map(t => ({
          ...t,
          file: t.file.startsWith('http') ? t.file : `${apiBase}${t.file}`
        }));
        this.hlsUrl = res.hls_url.startsWith('http') ? res.hls_url : `${apiBase}${res.hls_url}`;
        this.dashUrl = res.dash_url.startsWith('http') ? res.dash_url : `${apiBase}${res.dash_url}`;
        this.previewUrl = res.preview_url.startsWith('http') ? res.preview_url : `${apiBase}${res.preview_url}`;

        this.initJWPlayer();

        for (const track of res.subtitles) {
          const trackUrl = track.file.startsWith('http') ? track.file : `${apiBase}${track.file}`;
          this.loadSubtitles(track.lang, trackUrl, apiKey);
        }
      },
      error: err => {
        console.error('Failed to fetch subtitle and video info:', err);
      }
    });
  }


  loadSubtitles(lang: string, url: string, apiKey: string) {
    this.http.get(url, {
      headers: { 'X-API-Key': apiKey },
      responseType: 'text'
    }).subscribe({
      next: srt => {
        const parsed = this.parseSrt(srt).map(s => ({ ...s, lang }));
        this.subtitlesByLang[lang] = parsed;

        if (!this.subtitlesByLang[this.selectedLang]) {
          this.selectedLang = lang;
        }

        if (lang === this.selectedLang) {
          this.transcriptText = srt;
        }
      },
      error: err => {
        console.warn(`Failed to load subtitles for ${lang}:`, err);
      }
    });
  }



  initJWPlayer() {
    if (this.playerInitialized) return;
  this.playerInitialized = true;

    try {
      const apiBase = environment.apiBaseUrl;

      const player = jwplayer('video-player').setup({
        sources: [
          { file: this.hlsUrl, type: 'hls' },
          { file: this.dashUrl, type: 'dash' }
        ],
        image: this.previewUrl,
        tracks: this.subtitleTracks.map(t => ({
          file: t.file.startsWith('http') ? t.file : `${apiBase}${t.file}`,
          label: t.label,
          kind: 'captions',
          default: t.lang === this.selectedLang
        })),
        width: '100%',
        aspectratio: '16:9',
        autostart: false
      });

      player.setCurrentCaptions(1);
      player.on('captionsChanged', (event: any) => {
        const selected = player.getCaptionsList()?.[event.track];
        const lang = this.subtitleTracks.find(t => t.label === selected?.label)?.lang;
        if (lang) this.selectedLang = lang;
      });

      player.on('time', (e: any) => {
        const subs = this.subtitlesByLang[this.selectedLang] || [];
        const index = subs.findIndex((s, i) => {
          const next = subs[i + 1];
          return e.position >= s.startSeconds && (!next || e.position < next.startSeconds);
        });
        this.activeSubtitleIndex = index;
      });
    } catch (err) {
      console.error('JWPlayer setup failed:', err);
    }
  }

  seekTo(seconds: number) {
    const player = jwplayer('video-player');
    player?.seek(seconds);
    player?.play(true);
  }

  setSpeed(rate: number) {
    jwplayer('video-player')?.setPlaybackRate(rate);
  }

  emitDone() {
    this.doneClicked.emit({
      courseId: this.courseId,
      studentCourseId: this.studentCourseId,
      studentCourseStepId: this.studentCourseStepId,
      courseStepId: this.courseStepId,
      companyId: this.companyId,
      personId: this.personId
    });
  }

  parseSrt(srt: string): SubtitleEntry[] {
    const lines = srt.replace(/\r\n|\r/g, '\n').split('\n');
    const entries: SubtitleEntry[] = [];
    let buffer: string[] = [];
    let index = 0;

    for (const line of lines) {
      if (line.trim() === '') {
        if (buffer.length) {
          const timeLine = buffer.find(l => l.includes('-->'));
          const [start, end] = timeLine?.split(' --> ') || [];
          const textLines = buffer.filter(l => !l.includes('-->') && isNaN(Number(l)));
          if (start && end) {
            entries.push({
              index: index++,
              start,
              end,
              text: textLines.join('\n'),
              startSeconds: this.parseTimeToSeconds(start)
            });
          }
          buffer = [];
        }
      } else buffer.push(line);
    }

    return entries;
  }

  parseTimeToSeconds(t: string): number {
    const [h, m, rest] = t.split(':');
    const [s, ms] = rest.split(/[,\.]/);
    return +h * 3600 + +m * 60 + +s + +ms / 1000;
  }

  onSearchChange() {
    clearTimeout(this.searchDebounceTimer);
    this.searchDebounceTimer = setTimeout(() => {
      // Trigger view update
    }, 200);
  }

  highlightSearch(text: string, term: string): SafeHtml {
    if (!term || term.length < 2) return text;
    const regex = new RegExp(`(${term})`, 'gi');
    const highlighted = text.replace(regex, `<span style="background-color: yellow;">$1</span>`);
    return this.sanitizer.bypassSecurityTrustHtml(highlighted);
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
}
