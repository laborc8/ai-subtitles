import { enableProdMode, Injector } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';
import { createCustomElement } from '@angular/elements';
import { InteractivePlayerComponent } from './interactive-player.component';
import { HttpClientModule } from '@angular/common/http';
import { NgModule, DoBootstrap } from '@angular/core';

enableProdMode();

@NgModule({
  imports: [BrowserModule, HttpClientModule],
})
class AppModule implements DoBootstrap {
  constructor(private injector: Injector) {}

  ngDoBootstrap() {
    const el = createCustomElement(InteractivePlayerComponent, {
      injector: this.injector,
    });
    customElements.define('widget-studema-interactive-player', el);
  }
}

platformBrowserDynamic()
  .bootstrapModule(AppModule)
  .catch((err) => console.error(err));
