import { Component, OnInit, ViewChild, ElementRef, ChangeDetectorRef } from '@angular/core';
import { ChatService, ChatMessage, ChatResponse, TranscriptionResponse } from './chat.service';

// Speech Recognition API types
interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
}

interface SpeechRecognitionEvent {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionErrorEvent {
  error: string;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

// Extended ChatMessage interface to include audio
interface ExtendedChatMessage extends ChatMessage {
  audioFile?: File;
  audioUrl?: string;
}

@Component({
  selector: 'app-chat',
  template: `
    <div class="p-6 max-w-6xl mx-auto">
      <div class="bg-white rounded-lg shadow-md">
        <!-- Header -->
        <div class="border-b p-4">
          <div class="flex justify-between items-center">
            <h2 class="text-xl font-semibold">AI Chat Assistant</h2>
            <div class="flex space-x-2">
              <select 
                [(ngModel)]="selectedClient" 
                class="border rounded px-3 py-1 text-sm"
                (change)="onClientChange()">
                <option value="default">Default Client</option>
                <option value="studema">Studema</option>
                <option value="performia">Performia</option>
              </select>
              <button 
                (click)="resetChat()"
                class="bg-gray-500 text-white px-3 py-1 rounded text-sm hover:bg-gray-600">
                Reset Chat
              </button>
            </div>
          </div>
        </div>

        <!-- Debug Info -->
        <div *ngIf="debugInfo" class="bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-yellow-800">Debug Info</h3>
              <div class="mt-2 text-sm text-yellow-700">
                <p><strong>Audio Support:</strong> {{ audioSupported ? 'Yes' : 'No' }}</p>
                <p><strong>MediaRecorder Support:</strong> {{ mediaRecorderSupported ? 'Yes' : 'No' }}</p>
                <p><strong>Speech Recognition Support:</strong> {{ speechRecognitionSupported ? 'Yes' : 'No' }}</p>
                <p><strong>Recording Status:</strong> {{ isRecording ? 'Recording' : 'Not Recording' }}</p>
                <p><strong>Listening Status:</strong> {{ isListening ? 'Listening' : 'Not Listening' }}</p>
                <p><strong>Audio File:</strong> {{ audioFile ? audioFile.name + ' (' + audioFile.size + ' bytes)' : 'None' }}</p>
                <p><strong>Error:</strong> {{ lastError || 'None' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Chat Messages -->
        <div class="h-96 overflow-y-auto p-4 space-y-4" #chatContainer>
          <div *ngFor="let message of (chatHistory || [])" class="flex">
            <div 
              [ngClass]="message.role === 'user' ? 'ml-auto bg-blue-100' : 'mr-auto bg-gray-100'"
              class="max-w-xs lg:max-w-md p-3 rounded-lg">
              <div class="text-sm text-gray-600 mb-1">
                {{ message.role === 'user' ? 'You' : 'Assistant' }} - 
                {{ message.timestamp | date:'short' }}
              </div>
              <div class="text-sm">{{ message.content }}</div>
              
              <!-- Audio playback for user messages -->
              <div *ngIf="message.audioFile || message.audioUrl" class="mt-2">
                <button 
                  (click)="playMessageAudio(message)"
                  class="bg-blue-500 text-white px-2 py-1 rounded text-xs hover:bg-blue-600">
                  🔊 Play Audio
                </button>
              </div>
            </div>
          </div>
          
          <!-- Loading indicator -->
          <div *ngIf="isLoading" class="flex justify-center">
            <div class="bg-gray-100 p-3 rounded-lg">
              <div class="flex items-center space-x-2">
                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span class="text-sm text-gray-600">Processing...</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Input Area -->
        <div class="border-t p-4">
          <div class="flex space-x-2 mb-2">
            <button 
              (click)="toggleRecording()"
              [ngClass]="isRecording ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'"
              class="text-white px-3 py-2 rounded text-sm"
              [disabled]="!audioSupported">
              {{ isRecording ? '🛑 Stop Recording' : '🎤 Start Recording' }}
            </button>
            <div *ngIf="isRecording" class="flex items-center text-red-600">
              <div class="animate-pulse">🔴 Recording & Listening...</div>
            </div>
            <div *ngIf="isLoading && audioFile" class="flex items-center text-blue-600">
              <div class="animate-pulse">⏳ Auto-uploading message...</div>
            </div>
            <button 
              (click)="toggleDebug()"
              class="bg-gray-400 text-white px-3 py-2 rounded text-sm hover:bg-gray-500">
              🐛 Debug
            </button>
          </div>

          <!-- Audio File Info -->
          <div *ngIf="audioFile" class="mb-2 p-3 bg-green-50 border border-green-300 rounded-lg">
            <div class="flex items-center justify-between">
              <div class="text-sm text-green-800">
                <div class="font-medium">🎵 Audio Ready for Upload</div>
                <div class="text-xs text-green-600">{{ audioFile.name }} ({{ audioFile.size }} bytes)</div>
                <div *ngIf="userMessage.trim()" class="text-xs text-green-600 mt-1">
                  📝 Text: "{{ userMessage }}"
                </div>
              </div>
              <div class="flex space-x-2">
                <button 
                  (click)="playRecordedAudio()"
                  class="bg-blue-500 text-white px-2 py-1 rounded text-xs hover:bg-blue-600">
                  🔊 Play
                </button>
                <button 
                  (click)="clearAudioFile()"
                  class="bg-red-500 text-white px-2 py-1 rounded text-xs hover:bg-red-600">
                  ✕ Clear
                </button>
              </div>
            </div>
            <div *ngIf="isLoading" class="mt-2 text-xs text-green-600">
              ⏳ Auto-uploading message...
            </div>
          </div>

          <div class="flex space-x-2">
            <input 
              type="text" 
              placeholder="Type your message..." 
              class="flex-1 border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              [(ngModel)]="userMessage"
              (keyup.enter)="sendMessage()"
              [disabled]="isLoading || isRecording">
            
            <button 
              (click)="sendMessage()"
              [disabled]="isLoading || isRecording || (!userMessage.trim() && !audioFile)"
              class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed">
              {{ isLoading && audioFile ? '⏳ Auto-uploading...' : 'Send' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Response Details -->
      <div *ngIf="lastResponse" class="mt-6 bg-white rounded-lg shadow-md p-4">
        <h3 class="text-lg font-semibold mb-3">Last Response Details</h3>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <!-- System Prompt -->
          <div class="bg-gray-50 p-3 rounded">
            <h4 class="font-medium text-gray-700 mb-2">System Prompt</h4>
            <p class="text-sm text-gray-600">{{ lastResponse.systemPrompt }}</p>
          </div>

          <!-- Azure Analysis -->
          <div *ngIf="lastResponse.azureAnalysis" class="bg-gray-50 p-3 rounded">
            <h4 class="font-medium text-gray-700 mb-2">Speech Analysis</h4>
            <div class="text-sm space-y-1">
              <div><strong>Text:</strong> {{ lastResponse.azureAnalysis.text || 'No text' }}</div>
              <div><strong>Confidence:</strong> {{ (lastResponse.azureAnalysis.confidence || 0).toFixed(1) }}%</div>
              <div><strong>Status:</strong> {{ lastResponse.azureAnalysis.status || 'Unknown' }}</div>
              <div *ngIf="lastResponse.azureAnalysis.pronunciation">
                <strong>Pronunciation Scores:</strong>
                <div class="ml-2 text-xs">
                  <div>Accuracy: {{ lastResponse.azureAnalysis.pronunciation.accuracy_score }}</div>
                  <div>Fluency: {{ lastResponse.azureAnalysis.pronunciation.fluency_score }}</div>
                  <div>Completeness: {{ lastResponse.azureAnalysis.pronunciation.completeness_score }}</div>
                  <div>Overall: {{ lastResponse.azureAnalysis.pronunciation.overall_score }}</div>
                </div>
              </div>
              
              <!-- Raw Result (for debugging) -->
              <div *ngIf="lastResponse.azureAnalysis.raw_result" class="mt-3 pt-3 border-t border-gray-300">
                <details class="text-xs">
                  <summary class="cursor-pointer text-gray-600 hover:text-gray-800">
                    🔍 Raw Azure Result (Debug)
                  </summary>
                  <div class="mt-2 p-2 bg-gray-100 rounded text-xs font-mono overflow-x-auto">
                    <div class="mb-2">
                      <strong>Recognized Text:</strong> {{ lastResponse.azureAnalysis.raw_result.recognized_text || 'None' }}
                    </div>
                    <div class="mb-2">
                      <strong>Result Reason:</strong> {{ lastResponse.azureAnalysis.raw_result.result_reason || 'None' }}
                    </div>
                    <div class="mb-2" *ngIf="lastResponse.azureAnalysis.raw_result.pronunciation_assessment_result">
                      <strong>Pronunciation Assessment Result:</strong> {{ lastResponse.azureAnalysis.raw_result.pronunciation_assessment_result }}
                    </div>
                    <div class="mb-2" *ngIf="lastResponse.azureAnalysis.raw_result.display_text">
                      <strong>Display Text:</strong> {{ lastResponse.azureAnalysis.raw_result.display_text }}
                    </div>
                    <div class="mb-2" *ngIf="lastResponse.azureAnalysis.raw_result.lexical">
                      <strong>Lexical:</strong> {{ lastResponse.azureAnalysis.raw_result.lexical }}
                    </div>
                    <div class="mb-2" *ngIf="lastResponse.azureAnalysis.raw_result.itn">
                      <strong>ITN:</strong> {{ lastResponse.azureAnalysis.raw_result.itn }}
                    </div>
                    <div class="mb-2" *ngIf="lastResponse.azureAnalysis.raw_result.masked_itn">
                      <strong>Masked ITN:</strong> {{ lastResponse.azureAnalysis.raw_result.masked_itn }}
                    </div>
                    <div class="mb-2" *ngIf="lastResponse.azureAnalysis.raw_result.pronunciation_recognized_text">
                      <strong>Pronunciation Recognized Text:</strong> {{ lastResponse.azureAnalysis.raw_result.pronunciation_recognized_text }}
                    </div>
                    <div class="mb-2" *ngIf="lastResponse.azureAnalysis.raw_result.words">
                      <strong>Words:</strong>
                      <pre class="mt-1 text-xs">{{ lastResponse.azureAnalysis.raw_result.words | json }}</pre>
                    </div>
                    <div class="mb-2" *ngIf="lastResponse.azureAnalysis.raw_result.nbest">
                      <strong>NBest:</strong>
                      <pre class="mt-1 text-xs">{{ lastResponse.azureAnalysis.raw_result.nbest | json }}</pre>
                    </div>
                    <div class="mb-2">
                      <strong>Confidence JSON:</strong>
                      <pre class="mt-1 text-xs">{{ lastResponse.azureAnalysis.raw_result.confidence_json || 'None' }}</pre>
                    </div>
                    <div *ngIf="lastResponse.azureAnalysis.raw_result.result_properties">
                      <strong>Result Properties:</strong>
                      <pre class="mt-1 text-xs">{{ lastResponse.azureAnalysis.raw_result.result_properties | json }}</pre>
                    </div>
                  </div>
                </details>
              </div>
            </div>
          </div>
        </div>

        <!-- Audio Player -->
        <div *ngIf="lastResponse.audioBase64" class="mt-4">
          <h4 class="font-medium text-gray-700 mb-2">Audio Response</h4>
          <button 
            (click)="playResponseAudio()"
            class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
            🔊 Play Response
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .animate-spin {
      animation: spin 1s linear infinite;
    }
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
  `]
})
export class ChatComponent implements OnInit {
  @ViewChild('chatContainer') chatContainer!: ElementRef;

  chatHistory: ExtendedChatMessage[] = [];
  userMessage = '';
  selectedClient = 'default';
  isLoading = false;
  audioMode = false;
  isRecording = false;
  audioFile: File | null = null;
  mediaRecorder: MediaRecorder | null = null;
  audioChunks: Blob[] = [];
  lastResponse: ChatResponse | null = null;
  transcribedText = '';
  isTranscribing = false;
  
  // Debug properties
  debugInfo = false;
  audioSupported = false;
  mediaRecorderSupported = false;
  lastError = '';
  speechRecognitionSupported = false;
  isListening = false;
  speechRecognition: any = null;
  userMessageAlreadyAdded = false;

  constructor(private chatService: ChatService, private changeDetectorRef: ChangeDetectorRef) {
    console.log('ChatComponent constructor called');
  }

  ngOnInit() {
    console.log('ChatComponent ngOnInit called');
    this.loadChatHistory();
    this.checkAudioSupport();
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  checkAudioSupport() {
    // Check if getUserMedia is supported
    this.audioSupported = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    
    // Check if MediaRecorder is supported
    this.mediaRecorderSupported = !!window.MediaRecorder;
    
    // Check if Speech Recognition is supported
    this.speechRecognitionSupported = !!(window.SpeechRecognition || (window as any).webkitSpeechRecognition);
    
    // Initialize Speech Recognition
    if (this.speechRecognitionSupported) {
      this.speechRecognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
      this.speechRecognition.continuous = false;
      this.speechRecognition.interimResults = true;
      this.speechRecognition.lang = 'en-US';
      
      this.speechRecognition.onresult = (event: SpeechRecognitionEvent) => {
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
        
        // Update the input field with the transcribed text
        this.userMessage = finalTranscript || interimTranscript;
      };
      
      this.speechRecognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.error('Speech recognition error:', event.error);
        this.isListening = false;
        this.lastError = 'Speech recognition error: ' + event.error;
      };
      
      this.speechRecognition.onend = () => {
        this.isListening = false;
        console.log('Speech recognition ended');
      };
    }
    
    console.log('Audio support check:', {
      audioSupported: this.audioSupported,
      mediaRecorderSupported: this.mediaRecorderSupported,
      speechRecognitionSupported: this.speechRecognitionSupported
    });
  }

  toggleDebug() {
    this.debugInfo = !this.debugInfo;
  }

  clearAudioFile() {
    this.audioFile = null;
    this.lastError = '';
  }

  onClientChange() {
    this.loadChatHistory();
  }

  loadChatHistory() {
    console.log('Loading chat history for client:', this.selectedClient);
    this.chatService.getChatHistory(this.selectedClient).subscribe({
      next: (history) => {
        console.log('Chat history response:', history);
        // Ensure history is always an array
        if (Array.isArray(history)) {
          this.chatHistory = history;
        } else if (history && typeof history === 'object') {
          console.warn('Backend returned object instead of array:', history);
          this.chatHistory = [];
        } else {
          console.warn('Backend returned unexpected data type:', typeof history, history);
          this.chatHistory = [];
        }
        console.log('Final chatHistory:', this.chatHistory);
      },
      error: (error) => {
        console.error('Error loading chat history:', error);
        this.lastError = 'Failed to load chat history: ' + error.message;
        // Ensure chatHistory is always an array even on error
        this.chatHistory = [];
      }
    });
  }

  sendMessage() {
    if (this.isLoading) return;

    const message = this.userMessage.trim();
    
    if (!message && !this.audioFile) return;

    this.isLoading = true;
    this.lastError = '';

    // Only add user message to chat if it wasn't already added during auto-upload
    if (message && !this.userMessageAlreadyAdded) {
      this.addMessageToChat('user', message, this.audioFile);
    }

    // Reset the flag for next time
    this.userMessageAlreadyAdded = false;

    // Send to backend
    const request = this.audioFile 
      ? this.chatService.sendAudioMessage(this.selectedClient, message, this.audioFile)
      : this.chatService.sendTextMessage(this.selectedClient, message);

    request.subscribe({
      next: (response) => {
        console.log('=== CHAT RESPONSE ===');
        console.log('Full response:', response);
        console.log('Azure analysis:', response.azureAnalysis);
        if (response.azureAnalysis) {
          console.log('Confidence:', response.azureAnalysis.confidence, 'Type:', typeof response.azureAnalysis.confidence);
          console.log('Pronunciation:', response.azureAnalysis.pronunciation);
        }
        console.log('=== END CHAT RESPONSE ===');
        
        this.lastResponse = response;
        this.addMessageToChat('assistant', response.assistantText);
        this.audioFile = null;
        this.isLoading = false;
        
        // Force change detection to update UI
        this.changeDetectorRef.detectChanges();
        
        // Scroll to bottom after UI update
        setTimeout(() => {
          this.scrollToBottom();
        }, 100);
      },
      error: (error) => {
        console.error('Error sending message:', error);
        this.lastError = 'Failed to send message: ' + error.message;
        this.addMessageToChat('assistant', 'Sorry, there was an error processing your request.');
        this.audioFile = null;
        this.isLoading = false;
        
        // Force change detection to update UI
        this.changeDetectorRef.detectChanges();
      }
    });

    this.userMessage = '';
  }

  addMessageToChat(role: 'user' | 'assistant', content: string, audioFile?: File | null) {
    const message: ExtendedChatMessage = {
      role,
      content,
      timestamp: new Date(),
      audioFile: audioFile || undefined
    };
    this.chatHistory.push(message);
    
    // Force change detection to update UI immediately
    this.changeDetectorRef.detectChanges();
    
    // Scroll to bottom after adding message
    setTimeout(() => {
      this.scrollToBottom();
    }, 50);
  }

  resetChat() {
    this.chatService.resetChat(this.selectedClient).subscribe({
      next: () => {
        this.chatHistory = [];
        this.lastResponse = null;
        this.lastError = '';
      },
      error: (error) => {
        console.error('Error resetting chat:', error);
        this.lastError = 'Failed to reset chat: ' + error.message;
      }
    });
  }

  toggleRecording() {
    console.log('=== TOGGLE RECORDING ===');
    console.log('toggleRecording called, current isRecording:', this.isRecording);
    
    if (this.isRecording) {
      this.stopRecording();
    } else {
      this.startRecording();
    }
  }

  async startRecording() {
    try {
      this.lastError = '';
      console.log('=== START RECORDING & SPEECH RECOGNITION ===');
      console.log('Audio supported:', this.audioSupported);
      console.log('MediaRecorder supported:', this.mediaRecorderSupported);
      console.log('Speech Recognition supported:', this.speechRecognitionSupported);
      
      if (!this.audioSupported) {
        throw new Error('Audio API not supported in this browser');
      }
      
      if (!this.mediaRecorderSupported) {
        throw new Error('MediaRecorder API not supported in this browser');
      }
      
      console.log('Requesting microphone access...');
      
      // Request microphone access with fallback options
      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            sampleRate: 44100
          } 
        });
      } catch (streamError) {
        console.log('Failed with advanced audio options, trying basic audio...');
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      }
      
      console.log('Microphone access granted successfully');
      console.log('Stream tracks:', stream.getTracks().map(t => t.kind));
      
      // Create MediaRecorder with proper MIME type
      let mimeType = 'audio/webm';
      if (!MediaRecorder.isTypeSupported('audio/webm')) {
        if (MediaRecorder.isTypeSupported('audio/mp4')) {
          mimeType = 'audio/mp4';
        } else if (MediaRecorder.isTypeSupported('audio/wav')) {
          mimeType = 'audio/wav';
        } else {
          mimeType = ''; // Let browser choose
        }
      }
      
      console.log('Using MIME type:', mimeType);
      
      // Create MediaRecorder
      this.mediaRecorder = mimeType 
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);
      
      this.audioChunks = [];
      this.isRecording = true;
      console.log('MediaRecorder created, isRecording set to:', this.isRecording);

      this.mediaRecorder.ondataavailable = (event) => {
        console.log('Data available event:', event.data.size, 'bytes');
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
          console.log('Added chunk, total chunks:', this.audioChunks.length);
        }
      };

      this.mediaRecorder.onstart = () => {
        console.log('MediaRecorder onstart event fired');
        console.log('Recording state:', this.mediaRecorder?.state);
      };

      this.mediaRecorder.onstop = () => {
        console.log('MediaRecorder onstop event fired');
        console.log('Total chunks collected:', this.audioChunks.length);
        
        if (this.audioChunks.length > 0) {
          const audioBlob = new Blob(this.audioChunks, { type: mimeType || 'audio/webm' });
          this.audioFile = new File([audioBlob], `recording.${mimeType.split('/')[1] || 'webm'}`, { 
            type: mimeType || 'audio/webm' 
          });
          console.log('Audio file created successfully:', this.audioFile.name, this.audioFile.size, 'bytes');
          
          // Auto-send the message if we have text or audio
          if (this.userMessage.trim() || this.audioFile) {
            console.log('Auto-sending message with audio and text:', this.userMessage);
            
            // Immediately add user message to chat for instant feedback
            if (this.userMessage.trim()) {
              this.addMessageToChat('user', this.userMessage, this.audioFile);
              this.userMessageAlreadyAdded = true;
            } else if (this.audioFile) {
              this.addMessageToChat('user', '[Audio Message]', this.audioFile);
              this.userMessageAlreadyAdded = true;
            }
            
            setTimeout(() => {
              this.sendMessage();
            }, 500); // Small delay to ensure UI updates
          }
        } else {
          console.error('No audio chunks collected!');
          this.lastError = 'No audio data recorded - please try again';
        }
        
        // Clean up stream
        stream.getTracks().forEach((track: MediaStreamTrack) => {
          console.log('Stopping track:', track.kind);
          track.stop();
        });
      };

      this.mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error event:', event);
        this.lastError = 'Recording error occurred - check console for details';
        this.isRecording = false;
      };

      // Start recording
      console.log('Starting MediaRecorder...');
      this.mediaRecorder.start(1000); // 1 second timeslice
      console.log('MediaRecorder started, state:', this.mediaRecorder.state);
      
      // Start speech recognition if supported
      if (this.speechRecognitionSupported && this.speechRecognition) {
        console.log('Starting speech recognition...');
        this.speechRecognition.start();
        this.isListening = true;
        console.log('Speech recognition started');
      }
      
      console.log('=== END START RECORDING & SPEECH RECOGNITION ===');
      
    } catch (error) {
      console.error('=== RECORDING ERROR ===');
      console.error('Error starting recording:', error);
      console.error('Error name:', (error as Error).name);
      console.error('Error message:', (error as Error).message);
      console.error('Error stack:', (error as Error).stack);
      
      this.lastError = 'Failed to start recording: ' + (error as Error).message;
      this.isRecording = false;
      this.isListening = false;
      
      console.error('=== END RECORDING ERROR ===');
    }
  }

  stopRecording() {
    console.log('=== STOP RECORDING ===');
    
    // Stop MediaRecorder
    if (this.mediaRecorder && this.isRecording) {
      console.log('Stopping MediaRecorder...');
      this.mediaRecorder.stop();
      this.isRecording = false;
    }
    
    // Stop speech recognition
    if (this.speechRecognitionSupported && this.speechRecognition && this.isListening) {
      console.log('Stopping speech recognition...');
      this.speechRecognition.stop();
      this.isListening = false;
    }
    
    console.log('=== END STOP RECORDING ===');
  }

  playResponseAudio() {
    if (this.lastResponse?.audioBase64) {
      this.chatService.playAudio(this.lastResponse.audioBase64)
        .then(() => {
          console.log('Audio played successfully');
        })
        .catch(error => {
          console.error('Error playing audio:', error);
          this.lastError = 'Failed to play audio: ' + error.message;
        });
    }
  }

  scrollToBottom() {
    try {
      this.chatContainer.nativeElement.scrollTop = this.chatContainer.nativeElement.scrollHeight;
    } catch (err) {}
  }

  // Transcribe audio using browser's Speech Recognition API
  async transcribeAudio() {
    if (!this.audioFile) return;
    
    this.isTranscribing = true;
    this.lastError = '';
    
    try {
      console.log('Starting audio transcription...');
      
      // Convert audio file to base64 for sending to backend
      const base64Audio = await this.fileToBase64(this.audioFile);
      
      // Send to backend for transcription
      this.chatService.transcribeAudio(base64Audio).subscribe({
        next: (response: TranscriptionResponse) => {
          console.log('Transcription response:', response);
          this.transcribedText = response.text || 'No text transcribed';
          this.isTranscribing = false;
        },
        error: (error: any) => {
          console.error('Transcription error:', error);
          this.lastError = 'Failed to transcribe audio: ' + error.message;
          this.isTranscribing = false;
        }
      });
      
    } catch (error) {
      console.error('Error in transcribeAudio:', error);
      this.lastError = 'Failed to transcribe audio: ' + (error as Error).message;
      this.isTranscribing = false;
    }
  }

  // Play audio from chat message
  playMessageAudio(message: ExtendedChatMessage) {
    if (message.audioFile) {
      const audioUrl = URL.createObjectURL(message.audioFile);
      const audio = new Audio(audioUrl);
      audio.play().catch(error => {
        console.error('Error playing message audio:', error);
        this.lastError = 'Failed to play audio: ' + error.message;
      });
    } else if (message.audioUrl) {
      const audio = new Audio(message.audioUrl);
      audio.play().catch(error => {
        console.error('Error playing message audio:', error);
        this.lastError = 'Failed to play audio: ' + error.message;
      });
    }
  }

  // Convert file to base64
  private fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const result = reader.result as string;
        // Remove the data URL prefix (e.g., "data:audio/wav;base64,")
        const base64 = result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = error => reject(error);
    });
  }

  playRecordedAudio() {
    if (this.audioFile) {
      const audioUrl = URL.createObjectURL(this.audioFile);
      const audio = new Audio(audioUrl);
      audio.play().catch(error => {
        console.error('Error playing recorded audio:', error);
        this.lastError = 'Failed to play recorded audio: ' + error.message;
      });
    }
  }

  toggleAudioMode() {
    console.log('=== TOGGLE AUDIO MODE ===');
    console.log('toggleAudioMode called, current audioMode:', this.audioMode);
    
    this.audioMode = !this.audioMode;
    console.log('audioMode changed to:', this.audioMode);
    
    if (this.audioMode) {
      console.log('Starting recording...');
      this.startRecording();
    } else {
      console.log('Stopping recording...');
      this.stopRecording();
    }
  }
} 