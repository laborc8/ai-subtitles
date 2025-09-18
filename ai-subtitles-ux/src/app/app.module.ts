import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { RouterModule, Routes } from '@angular/router';

import { AppComponent } from './app.component';
import { LoginComponent } from './login.component';
import { TranscriptGenComponent } from './transcript-gen/transcript-gen.component';
import { TranscribeComponent } from './transcribe/transcribe.component';
import { ChatComponent } from './chat/chat.component';
import { NavbarComponent } from './navbar/navbar.component';
import { InteractivePlayerComponent } from './studema-interactive-player/interactive-player.component';

const routes: Routes = [
  { path: '', redirectTo: '/transcribe', pathMatch: 'full' },
  { path: 'transcribe', component: TranscribeComponent },
  { path: 'chat', component: ChatComponent }
];

@NgModule({
  declarations: [
    AppComponent, 
    LoginComponent, 
    TranscribeComponent,
    ChatComponent,
    NavbarComponent
  ],
  imports: [
    BrowserModule, 
    FormsModule, 
    HttpClientModule, 
    RouterModule.forRoot(routes),
    TranscriptGenComponent, 
    InteractivePlayerComponent
  ],
  bootstrap: [AppComponent]
})
export class AppModule {}
