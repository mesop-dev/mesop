import {
  Component,
  HostListener,
  provideZoneChangeDetection,
} from '@angular/core';
import {
  DefaultHotReloadWatcher,
  HotReloadWatcher,
} from '../services/hot_reload_watcher';
import {bootstrapApplication} from '@angular/platform-browser';
import {provideAnimations} from '@angular/platform-browser/animations';
import {RouterOutlet, Routes, provideRouter} from '@angular/router';
import {
  DebugErrorDialogService,
  ErrorDialogService,
} from '../services/error_dialog_service';
import {Shell, registerComponentRendererElement} from '../shell/shell';
import {isMac, isChromeOS} from '../utils/platform';
import {Channel} from '../services/channel';
// Keep the following comment to ensure there's a hook for adding TS imports in the downstream sync.
// ADD_TS_IMPORT_HERE

@Component({
  selector: 'mesop-editor',
  template: '<mesop-shell></mesop-shell>',
  standalone: true,
  imports: [Shell],
  providers: [{provide: HotReloadWatcher, useClass: DefaultHotReloadWatcher}],
})
class Editor {
  constructor(
    private readonly channel: Channel,
    private readonly hotReloadWatcher: HotReloadWatcher /* Inject hotReloadWatcher to ensure it's instantiated. */,
  ) {}

  @HostListener('window:keydown', ['$event'])
  handleKeyDown(event: KeyboardEvent) {
    if (this.shouldReload(event)) {
      this.channel.hotReload();
      event.preventDefault();
    }
  }

  /**
   * Determines if the hot reload keyboard shortcut was triggered.
   *
   * Hotkey mappings:
   * - MacOS: cmd + shift + r
   * - ChromeOS: alt + shift + r (to avoid conflict with browser's hard reload)
   * - Other platforms: ctrl + shift + r
   */
  private shouldReload(event: KeyboardEvent): boolean {
    if (event.key !== 'r' || !event.shiftKey) {
      return false;
    }

    if (isMac()) {
      return event.metaKey;
    }

    if (isChromeOS()) {
      return event.altKey;
    }

    return event.ctrlKey;
  }
}

const routes: Routes = [{path: '**', component: Editor}];

@Component({
  selector: 'mesop-editor-app',
  template: '<router-outlet></router-outlet>',
  imports: [RouterOutlet],
  standalone: true,
})
class MesopEditorApp {}

export async function bootstrapApp() {
  const app = await bootstrapApplication(MesopEditorApp, {
    providers: [
      provideAnimations(),
      provideRouter(routes),
      {provide: ErrorDialogService, useClass: DebugErrorDialogService},
      provideZoneChangeDetection(),
    ],
  });
  registerComponentRendererElement(app);
}
