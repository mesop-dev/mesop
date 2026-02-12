import {
  afterRenderEffect,
  ApplicationRef,
  ChangeDetectionStrategy,
  Component,
  ErrorHandler,
  HostListener,
  NgZone,
  provideZoneChangeDetection,
  Renderer2,
  signal,
} from '@angular/core';
import {Router, RouterOutlet, Routes, provideRouter} from '@angular/router';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {
  ServerError,
  Component as ComponentProto,
  UserEvent,
  NavigationEvent,
  ResizeEvent,
  UiRequest,
  InitRequest,
  QueryParam,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {CommonModule} from '@angular/common';
import {
  COMPONENT_RENDERER_ELEMENT_NAME,
  ComponentRenderer,
} from '../component_renderer/component_renderer';
import {Channel} from '../services/channel';
import {provideAnimations} from '@angular/platform-browser/animations';
import {bootstrapApplication} from '@angular/platform-browser';
import {MatIconModule, MatIconRegistry} from '@angular/material/icon';
import {MatSidenavModule} from '@angular/material/sidenav';
import {ServerErrorBoxDialogComponent} from '../error/error_box';
import {GlobalErrorHandlerService} from '../services/global_error_handler';
import {getViewportSize} from '../utils/viewport_size';
import {createCustomElement} from '@angular/elements';
import {Subject} from 'rxjs';
import {debounceTime} from 'rxjs/operators';
import {ThemeService} from '../services/theme_service';
import {getQueryParams} from '../utils/query_params';
import {
  ErrorDialogService,
  ProdErrorDialogService,
} from '../services/error_dialog_service';
import {MatDialog} from '@angular/material/dialog';
import {ExperimentService} from '../services/experiment_service';
// Keep the following comment to ensure there's a hook for adding TS imports in the downstream sync.
// ADD_TS_IMPORT_HERE

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-shell',
  templateUrl: 'shell.ng.html',
  standalone: true,
  imports: [
    CommonModule,
    ComponentRenderer,
    MatProgressBarModule,
    MatIconModule,
    MatSidenavModule,
  ],
  providers: [{provide: ErrorHandler, useClass: GlobalErrorHandlerService}],
  styleUrl: 'shell.css',
})
export class Shell {
  rootComponent!: ComponentProto;
  private resizeSubject = new Subject<void>();

  private commandScrollKey = signal('');

  constructor(
    private zone: NgZone,
    private renderer: Renderer2,
    private channel: Channel,
    iconRegistry: MatIconRegistry,
    private router: Router,
    errorHandler: ErrorHandler,
    private themeService: ThemeService,
    private dialog: MatDialog,
    private experimentService: ExperimentService,
  ) {
    iconRegistry.setDefaultFontSetClass('material-symbols-rounded');
    (errorHandler as GlobalErrorHandlerService).setOnError((error) => {
      const errorProto = new ServerError();
      errorProto.setException(`JS Error: ${error.toString()}`);
      this.openServerErrorDialog(errorProto);
    });
    this.resizeSubject
      .pipe(debounceTime(500))
      .subscribe(() => this.onResizeDebounced());

    afterRenderEffect(() => this.maybeExecuteScrollCommand());
  }

  ngOnInit() {
    const request = new UiRequest();
    const initRequest = new InitRequest();
    initRequest.setViewportSize(getViewportSize());
    initRequest.setThemeSettings(this.themeService.getThemeSettings());
    initRequest.setQueryParamsList(getQueryParams());
    request.setInit(initRequest);
    this.channel.init(
      {
        zone: this.zone,
        onRender: async (rootComponent, jsModules) => {
          // Import all JS modules concurrently
          await Promise.all(
            jsModules.map((modulePath) => {
              if (this.experimentService.webComponentsCacheKey) {
                modulePath += `?v=${this.experimentService.webComponentsCacheKey}`;
              }
              return import(modulePath).then(() =>
                console.debug(`Successfully imported JS module: ${modulePath}`),
              );
            }),
          ).then(() => {
            console.debug('All JS modules imported');
          });
          this.rootComponent = rootComponent;
        },
        onCommand: async (command) => {
          if (command.hasNavigate()) {
            const url = command.getNavigate()!.getUrl()!;
            const openInNewTab = command.getNavigate()!.getOpenInNewTab();

            if (openInNewTab) {
              // When opening in a new tab, we need to handle both absolute and root-relative URLs
              // Only http/https URLs are allowed; document-relative URLs are not supported.
              let absoluteUrl = url;
              if (!url.startsWith('http://') && !url.startsWith('https://')) {
                // Reject non-root-relative URLs (e.g., "javascript:", "data:", or other schemes)
                if (!url.startsWith('/')) {
                  console.warn(
                    'Refusing to open potentially unsafe URL in a new tab:',
                    url,
                  );
                  return;
                }
                if (url.startsWith('/')) {
                  // Convert root-relative URL to absolute URL
                  absoluteUrl = window.location.origin + url;
                } else {
                  // For non-http(s), non-root-relative URLs, use the URL as-is
                  absoluteUrl = url;
                }
              }
              // Final safety check: only allow http/https absolute URLs
              if (
                !absoluteUrl.startsWith('http://') &&
                !absoluteUrl.startsWith('https://')
              ) {
                console.warn(
                  'Refusing to open non-http(s) URL in a new tab:',
                  absoluteUrl,
                );
                return;
              }
              window.open(absoluteUrl, '_blank', 'noopener,noreferrer');
              // Return immediately to prevent any other navigation logic from executing
              return;
            }
            if (url.startsWith('http://') || url.startsWith('https://')) {
              window.location.href = url;
            } else {
              await this.router.navigateByUrl(command.getNavigate()!.getUrl()!);
              this.channel.resetOverridedTitle();
            }
          } else if (command.hasScrollIntoView()) {
            // Store the scroll key so we can defer execution of scroll command until
            // after everything is fully rendered. This helps avoid race conditions
            // with the scroll behavior.
            this.commandScrollKey.set(
              command.getScrollIntoView()!.getKey() || '',
            );
          } else if (command.hasSetPageTitle()) {
            this.channel.setOverridedTitle(
              command.getSetPageTitle()!.getTitle() || '',
            );
          } else if (command.hasFocusComponent()) {
            // Focus on component
            const key = command.getFocusComponent()!.getKey();
            const targetElements = document.querySelectorAll(
              `[data-key="${key}"]`,
            );
            if (!targetElements.length) {
              console.error(
                `Could not focus on component with key ${key} because no component found`,
              );
              return;
            }
            if (targetElements.length > 1) {
              console.warn(
                'Found multiple components',
                targetElements,
                'to potentially focus on for key',
                key,
                '. This is probably a bug and you should use a unique key identifier.',
              );
            }
            const matchingElements = targetElements[0].nextElementSibling
              ?.querySelectorAll(`
                a[href]:not([tabindex='-1']),
                area[href]:not([tabindex='-1']),
                input:not([disabled]):not([tabindex='-1']):not([type='file']),
                select:not([disabled]):not([tabindex='-1']),
                textarea:not([disabled]):not([tabindex='-1']),
                button:not([disabled]):not([tabindex='-1']),
                iframe:not([tabindex='-1']),
                [tabindex]:not([tabindex='-1']),
                [contentEditable=true]:not([tabindex='-1'])
              `);
            if (
              matchingElements &&
              typeof matchingElements[0] === 'object' &&
              'focus' in matchingElements[0]
            ) {
              (
                matchingElements[0] as {
                  focus: () => void;
                }
              ).focus();
            } else {
              console.warn(
                `Component with key ${key} does not have a focus method.`,
              );
            }
          } else if (command.hasSetThemeMode()) {
            const themeMode = command.getSetThemeMode();
            if (themeMode?.getThemeMode() == null) {
              throw new Error('Theme mode undefined in setThemeMode command');
            }
            this.themeService.setThemeMode(themeMode);
          } else if (command.hasSetThemeDensity()) {
            const setThemeDensity = command.getSetThemeDensity()!;
            const density = setThemeDensity.getDensity();
            if (density == null) {
              throw new Error('Density undefined in setThemeDensity command');
            }
            this.themeService.setDensity(density);
          } else if (command.hasUpdateQueryParam()) {
            updateUrlFromQueryParam(
              command.getUpdateQueryParam()!.getQueryParam()!,
            );
          } else {
            throw new Error(
              `Unhandled command: ${command.getCommandCase().toString()}`,
            );
          }
        },
        onError: (error) => {
          this.openServerErrorDialog(error);
        },
      },
      request,
    );
  }

  openServerErrorDialog(error: ServerError) {
    this.dialog.closeAll();
    this.dialog.open(ServerErrorBoxDialogComponent, {
      width: 'min(90vw, max(60vw, 600px))',
      data: {error: error},
      autoFocus: 'dialog',
    });
  }

  /** Listen to browser navigation events (go back/forward). */
  @HostListener('window:popstate', ['$event'])
  onPopState(event: Event) {
    const userEvent = new UserEvent();
    userEvent.setNavigation(new NavigationEvent());
    this.channel.dispatch(userEvent);
  }

  showChannelProgressIndicator(): boolean {
    return this.channel.isBusy();
  }

  @HostListener('window:resize')
  onResize(event: Event) {
    this.resizeSubject.next();
  }

  onResizeDebounced() {
    const userEvent = new UserEvent();
    userEvent.setResize(new ResizeEvent());
    this.channel.dispatch(userEvent);
  }

  // Executes the scroll command if a key has been specified.
  maybeExecuteScrollCommand() {
    if (this.commandScrollKey()) {
      const scrollKey = this.commandScrollKey();
      this.commandScrollKey.set('');
      const targetElements = document.querySelectorAll(
        `[data-key="${scrollKey}"]`,
      );
      if (!targetElements.length) {
        console.error(
          `Could not scroll to component with key ${scrollKey} because no component found`,
        );
        return;
      }
      if (targetElements.length > 1) {
        console.warn(
          'Found multiple components',
          targetElements,
          'to potentially scroll to for key',
          scrollKey,
          '. This is probably a bug and you should use a unique key identifier.',
        );
      }
      targetElements[0].parentElement!.scrollIntoView({
        behavior: 'smooth',
      });
    }
  }
}

const routes: Routes = [{path: '**', component: Shell}];

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-app',
  template: '<router-outlet></router-outlet>',
  imports: [RouterOutlet],
  standalone: true,
})
class MesopApp {}

export async function bootstrapApp() {
  const app = await bootstrapApplication(MesopApp, {
    providers: [
      provideZoneChangeDetection(),
      provideAnimations(),
      provideRouter(routes),
      {provide: ErrorDialogService, useClass: ProdErrorDialogService},
    ],
  });
  registerComponentRendererElement(app);
}

export function registerComponentRendererElement(app: ApplicationRef) {
  const ComponentRendererElement = createCustomElement(ComponentRenderer, {
    injector: app.injector,
  });
  customElements.define(
    COMPONENT_RENDERER_ELEMENT_NAME,
    ComponentRendererElement,
  );
}

function updateUrlFromQueryParam(queryParam: QueryParam) {
  const key = queryParam.getKey()!;
  const values = queryParam.getValuesList();
  const url = new URL(window.location.href);
  url.searchParams.delete(key);

  for (const value of values) {
    url.searchParams.append(key, value);
  }

  window.history.replaceState({}, '', url.toString());
}
