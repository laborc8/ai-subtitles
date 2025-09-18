import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  template: `
    <div class="min-h-screen bg-gray-100">
      <!-- Show navbar only when logged in -->
      <app-navbar *ngIf="loggedIn"></app-navbar>
      
      <!-- Login page -->
      <app-login *ngIf="!loggedIn" (loginSuccess)="loggedIn = true"></app-login>
      
      <!-- Main content with routing -->
      <main *ngIf="loggedIn" class="pt-0">
        <router-outlet></router-outlet>
      </main>
    </div>

    <!--
    <app-studema-interactive-player
      videoKey="videos/PerformiaInt/EHS/EHS_DAY_5/0341_B.qt"
      advancedEncoding="false"
      clientId="performia"
      courseId="123"
      studentCourseId="456"
      studentCourseStepId="789"
      courseStepId="101"
      companyId="202"
      personId="303"
      defaultLanguage="en">
    </app-studema-interactive-player>
    -->
  `
})
export class AppComponent {
  loggedIn = false;
}
