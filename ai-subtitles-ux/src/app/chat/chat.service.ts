import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface ChatResponse {
  assistantText: string;
  audioBase64?: string;
  azureAnalysis?: {
    text: string;
    confidence: number;
    pronunciation?: {
      accuracy_score: number;
      fluency_score: number;
      completeness_score: number;
      overall_score: number;
    };
    status: string;
    raw_result?: {
      confidence_json?: string;
      recognized_text?: string;
      result_reason?: string;
      assessment_reason?: string;
      result_properties?: any;
      nbest?: any[];
      display_text?: string;
      lexical?: string;
      itn?: string;
      masked_itn?: string;
      words?: any[];
      pronunciation_assessment_result?: string;
      pronunciation_recognized_text?: string;
      exception?: string;
      exception_type?: string;
    };
  };
  systemPrompt: string;
  timestamp: Date;
}

export interface ChatRequest {
  client: string;
  user_instructions: string;
  audio?: File;
}

export interface TranscriptionResponse {
  text: string;
  confidence?: number;
  language?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = environment.apiBaseUrl + '/api';

  constructor(private http: HttpClient) {}

  // Text-only chat
  sendTextMessage(client: string, userInstructions: string): Observable<ChatResponse> {
    const formData = new FormData();
    formData.append('client', client);
    formData.append('user_instructions', userInstructions);

    return this.http.post<ChatResponse>(`${this.apiUrl}/chat`, formData);
  }

  // Audio-enabled chat
  sendAudioMessage(client: string, userInstructions: string, audioFile: File): Observable<ChatResponse> {
    const formData = new FormData();
    formData.append('client', client);
    formData.append('user_instructions', userInstructions);
    formData.append('audio', audioFile);

    console.log('Sending audio message:', {
      client,
      userInstructions,
      audioFile: {
        name: audioFile.name,
        size: audioFile.size,
        type: audioFile.type
      }
    });

    return this.http.post<ChatResponse>(`${this.apiUrl}/chat`, formData);
  }

  // Transcribe audio
  transcribeAudio(base64Audio: string): Observable<TranscriptionResponse> {
    const payload = {
      audio: base64Audio
    };

    console.log('Sending audio for transcription, size:', base64Audio.length);
    return this.http.post<TranscriptionResponse>(`${this.apiUrl}/transcribe`, payload);
  }

  // Reset chat history
  resetChat(client: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/chat/reset`, { client });
  }

  // Get chat history
  getChatHistory(client: string): Observable<ChatMessage[]> {
    return this.http.get<ChatMessage[]>(`${this.apiUrl}/chat/history?client=${client}`);
  }

  // Play audio from base64 with better error handling
  playAudio(audioBase64: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        console.log('Playing audio, base64 length:', audioBase64.length);
        
        // Create audio element
        const audio = new Audio();
        
        // Set up event listeners
        audio.onloadstart = () => console.log('Audio loading started');
        audio.oncanplay = () => console.log('Audio can play');
        audio.onplay = () => console.log('Audio started playing');
        audio.onended = () => {
          console.log('Audio playback ended');
          resolve();
        };
        audio.onerror = (error) => {
          console.error('Audio playback error:', error);
          reject(new Error('Failed to play audio'));
        };
        
        // Set the audio source
        // Try different formats based on what the backend might return
        const audioFormats = [
          `data:audio/wav;base64,${audioBase64}`,
          `data:audio/mp3;base64,${audioBase64}`,
          `data:audio/mpeg;base64,${audioBase64}`,
          `data:audio/webm;base64,${audioBase64}`
        ];
        
        let currentFormatIndex = 0;
        
        const tryNextFormat = () => {
          if (currentFormatIndex >= audioFormats.length) {
            reject(new Error('No supported audio format found'));
            return;
          }
          
          audio.src = audioFormats[currentFormatIndex];
          console.log('Trying audio format:', audioFormats[currentFormatIndex].split(';')[0]);
          
          audio.onerror = () => {
            console.log('Format failed, trying next...');
            currentFormatIndex++;
            tryNextFormat();
          };
          
          audio.oncanplay = () => {
            console.log('Audio format supported, starting playback');
            audio.play().catch(error => {
              console.error('Error starting playback:', error);
              reject(error);
            });
          };
        };
        
        tryNextFormat();
        
      } catch (error) {
        console.error('Error creating audio element:', error);
        reject(error);
      }
    });
  }

  // Test audio support
  testAudioSupport(): boolean {
    return !!(window.Audio && window.AudioContext);
  }
} 