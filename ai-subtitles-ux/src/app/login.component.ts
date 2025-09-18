import { Component, EventEmitter, Output } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../environments/environment';

@Component({
  selector: 'app-login',
  template: `
    <div class="flex flex-col items-center justify-center min-h-screen">
      <div class="bg-white p-8 rounded shadow max-w-sm w-full">
        <h2 class="text-2xl font-bold mb-4">Login</h2>
        <input class="w-full mb-4 border rounded p-2" [(ngModel)]="email" placeholder="Username">
        <input class="w-full mb-4 border rounded p-2" [(ngModel)]="secret" type="password" placeholder="Password">
        <button class="bg-blue-500 text-white px-4 py-2 rounded w-full" (click)="login()">Login</button>
        <p class="text-red-500 mt-2" *ngIf="error">{{ error }}</p>
      </div>
    </div>
  `
})
export class LoginComponent {
  email = '';
  secret = '';
  error = '';

  @Output() loginSuccess = new EventEmitter();

  constructor(private http: HttpClient) {}

  login() {
    this.error = '';
    this.http.post<any>(environment.apiBaseUrl + '/api/login', {
      username: this.email,
      password: this.secret,
      client_id: environment.clientId
    }).subscribe({
      next: res => {
        if (res.success) {
          this.loginSuccess.emit();
        } else {
          this.error = 'Login failed.';
        }
      },
      error: () => {
        this.error = 'Invalid credentials.';
      }
    });
  }
}
