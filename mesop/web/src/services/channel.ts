import {Injectable, NgZone} from '@angular/core';
import {
  ServerError,
  States,
  UiRequest,
  UpdateStateEvent,
  UserEvent,
  Component as ComponentProto,
  UiResponse,
  InitRequest,
  Command,
  ChangePrefersColorScheme,
  HotReloadEvent,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {Title} from '@angular/platform-browser';
import {SSE} from '../utils/sse';
import {prefixBasePath} from '../utils/base_path';
import {applyComponentDiff, applyStateDiff} from '../utils/diff';
import {getViewportSize} from '../utils/viewport_size';
import {ThemeService} from './theme_service';
import {getQueryParams} from '../utils/query_params';
import {ExperimentService} from './experiment_service';

const STREAM_END = '<stream_end>';

// Pick 500ms as the minimum duration before showing a progress/busy indicator
// for the channel.
// See: https://github.com/mesop-dev/mesop/issues/365
const WAIT_TIMEOUT_MS = 500;

interface InitParams {
  zone: NgZone;
  onRender: (
    rootComponent: ComponentProto,
    jsModules: readonly string[],
  ) => void;
  onError: (error: ServerError) => void;
  onCommand: (command: Command) => Promise<void>;
}

interface QueuedMessage {
  request: UiRequest;
  response: UiResponse;
}

export enum ChannelStatus {
  OPEN = 'OPEN',
  CLOSED = 'CLOSED',
}

@Injectable({
  providedIn: 'root',
})
export class Channel {
  private _isHotReloading = false;
  private isWaiting = false;
  private isWaitingTimeout: number | undefined;
  private eventSource!: SSE;
  private webSocket: WebSocket | undefined;
  private wsReconnectAttempts = 0;
  private wsMaxReconnectAttempts = 3;
  private initParams!: InitParams;
  private states: States = new States();
  private stateToken = '';
  private rootComponent?: ComponentProto;
  private status!: ChannelStatus;
  private queuedEvents: (() => void)[] = [];
  private hotReloadBackoffCounter = 0;
  private hotReloadCounter = 0;
  private commandQueue: Command[] = [];
  private commandQueuePromise: Promise<void> | undefined;

  // Client-side state
  private overridedTitle = '';

  private messageQueue: QueuedMessage[] = [];

  private processingMessageDeferred: {
    promise: Promise<void>;
    resolve: () => void;
    reject: (reason?: any) => void;
  } | null = null;

  constructor(
    private title: Title,
    private themeService: ThemeService,
    private experimentService: ExperimentService,
  ) {
    this.themeService.setOnChangePrefersColorScheme(() => {
      const userEvent = new UserEvent();
      userEvent.setChangePrefersColorScheme(new ChangePrefersColorScheme());
      this.dispatch(userEvent);
    });
  }

  getStatus(): ChannelStatus {
    return this.status;
  }

  isHotReloading(): boolean {
    return this._isHotReloading;
  }

  /**
   * Return true if the channel has been doing work
   * triggered by a user that's been taking a while.
   */
  isBusy(): boolean {
    if (this.experimentService.websocketsEnabled) {
      // When WebSockets are enabled, we disable the busy indicator
      // because it's possible for the server to push new data
      // at any point. Apps should use their own loading indicators
      // instead.
      return false;
    }
    return this.isWaiting && !this.isHotReloading();
  }

  getRootComponent(): ComponentProto | undefined {
    return this.rootComponent;
  }

  init(initParams: InitParams, request: UiRequest) {
    console.debug('sending UI request', request);

    if (this.experimentService.websocketsEnabled) {
      this.initWebSocket(initParams, request);
    } else {
      this.initSSE(initParams, request);
    }
  }

  private initSSE(initParams: InitParams, request: UiRequest) {
    this.eventSource = new SSE(prefixBasePath('/__ui__'), {
      payload: generatePayloadString(request),
    });
    this.status = ChannelStatus.OPEN;
    this.isWaitingTimeout = setTimeout(() => {
      this.isWaiting = true;
    }, WAIT_TIMEOUT_MS);

    const {zone, onRender, onError, onCommand} = initParams;
    this.initParams = initParams;

    this.eventSource.addEventListener('message', (e) => {
      // Looks like Angular has a bug where it's not intercepting EventSource onmessage.
      zone.run(async () => {
        const data = (e as any).data;
        if (data === STREAM_END) {
          this.eventSource.close();
          this.status = ChannelStatus.CLOSED;
          clearTimeout(this.isWaitingTimeout);
          this.isWaiting = false;
          this._isHotReloading = false;
          await this.processMessageQueue();
          this.dequeueEvent();
          return;
        }

        const array = toUint8Array(atob(data));
        const uiResponse = UiResponse.deserializeBinary(array);
        console.debug('Server event (SSE): ', uiResponse.toObject());
        this.queueMessage(request, uiResponse);
      });
    });
  }

  private initWebSocket(initParams: InitParams, request: UiRequest) {
    if (this.webSocket?.readyState === WebSocket.OPEN) {
      this.status = ChannelStatus.OPEN;
      const payload = generatePayloadString(request);
      this.webSocket.send(payload);
      return;
    }

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}${prefixBasePath(
      '/__ui__',
    )}`;

    this.webSocket = new WebSocket(wsUrl);
    this.status = ChannelStatus.OPEN;
    this.isWaitingTimeout = setTimeout(() => {
      this.isWaiting = true;
    }, WAIT_TIMEOUT_MS);

    const {zone} = initParams;
    this.initParams = initParams;

    this.webSocket.onopen = () => {
      // Send the initial UiRequest upon connection
      const payload = generatePayloadString(request);
      this.webSocket!.send(payload);
      this.wsReconnectAttempts = 0;
    };

    this.webSocket.onmessage = (event) => {
      zone.run(async () => {
        const prefix = 'data: ';
        const payloadData = (
          event.data.slice(prefix.length) as string
        ).trimEnd();

        if (payloadData === STREAM_END) {
          this._isHotReloading = false;
          this.status = ChannelStatus.CLOSED;
          await this.processMessageQueue();
          this.dequeueEvent();
          return;
        }

        const array = toUint8Array(atob(payloadData));
        const uiResponse = UiResponse.deserializeBinary(array);
        console.debug('Server event (WebSocket): ', uiResponse.toObject());
        this.queueMessage(request, uiResponse);
      });
    };

    this.webSocket.onerror = (error) => {
      zone.run(() => {
        console.error('WebSocket error:', error);
        this.status = ChannelStatus.CLOSED;
      });
    };

    this.webSocket.onclose = (event) => {
      zone.run(() => {
        console.error('WebSocket closed:', event.reason);
        this.status = ChannelStatus.CLOSED;

        // Attempt to reconnect if we haven't exceeded max attempts
        if (this.wsReconnectAttempts < this.wsMaxReconnectAttempts) {
          this.wsReconnectAttempts++;
          const backoffDelay = Math.min(
            1000 * 2 ** this.wsReconnectAttempts,
            5000,
          );
          setTimeout(() => {
            // Create a new initial request object when reconnecting the websocket.
            //
            // This is to ensure that we get the latest viewport / theme settings / query params
            // on refresh for the user.
            //
            // This is only a temporary fix. Ideally, when the websocket reconnects, it should
            // retain the existing state and continue from there.
            const refreshRequest = new UiRequest();
            const initRequest = new InitRequest();
            initRequest.setViewportSize(getViewportSize());
            initRequest.setThemeSettings(this.themeService.getThemeSettings());
            initRequest.setQueryParamsList(getQueryParams());
            refreshRequest.setInit(initRequest);
            this.initWebSocket(initParams, refreshRequest);
          }, backoffDelay);
        }
      });
    };
  }

  private async handleUiResponse(
    request: UiRequest,
    uiResponse: UiResponse,
    initParams: InitParams,
  ) {
    const {onRender, onError, onCommand} = initParams;
    switch (uiResponse.getTypeCase()) {
      case UiResponse.TypeCase.UPDATE_STATE_EVENT: {
        this.stateToken = uiResponse.getUpdateStateEvent()!.getStateToken()!;
        switch (uiResponse.getUpdateStateEvent()!.getTypeCase()) {
          case UpdateStateEvent.TypeCase.FULL_STATES: {
            this.states = uiResponse.getUpdateStateEvent()!.getFullStates()!;
            break;
          }
          case UpdateStateEvent.TypeCase.DIFF_STATES: {
            const states = uiResponse.getUpdateStateEvent()!.getDiffStates()!;

            const numDiffStates = states.getStatesList().length;
            const numStates = this.states.getStatesList().length;

            if (numDiffStates !== numStates) {
              throw Error(
                `Number of diffs (${numDiffStates}) doesn't equal the number of states (${numStates}))`,
              );
            }

            // `this.states` should be populated at this point since the first update
            // from the server should be the full state.
            for (let i = 0; i < numDiffStates; ++i) {
              const state = applyStateDiff(
                this.states.getStatesList()[i].getData() as string,
                states.getStatesList()[i].getData() as string,
              );
              this.states.getStatesList()[i].setData(state);
            }
            break;
          }
          case UpdateStateEvent.TypeCase.TYPE_NOT_SET:
            throw new Error('No state event data set');
        }
        break;
      }
      case UiResponse.TypeCase.RENDER: {
        const rootComponent = uiResponse.getRender()!.getRootComponent()!;
        const componentDiff = uiResponse.getRender()!.getComponentDiff()!;

        this.commandQueue.push(...uiResponse.getRender()!.getCommandsList());
        await this.processCommandQueue(onCommand);

        const title = this.overridedTitle || uiResponse.getRender()!.getTitle();
        if (title) {
          this.title.setTitle(title);
        }

        if (componentDiff !== undefined && this.rootComponent !== undefined) {
          // Angular does not update the UI if we apply the diff on the root
          // component instance which is why we create copy of the root component
          // first.
          const rootComponentToUpdate = ComponentProto.deserializeBinary(
            this.rootComponent.serializeBinary(),
          );
          applyComponentDiff(rootComponentToUpdate, componentDiff);
          this.rootComponent = rootComponentToUpdate;
        } else {
          this.rootComponent = rootComponent;
        }

        onRender(
          this.rootComponent,
          uiResponse.getRender()!.getJsModulesList(),
        );
        break;
      }
      case UiResponse.TypeCase.ERROR:
        if (
          uiResponse.getError()?.getException() ===
          'Token not found in state session backend.'
        ) {
          this.queuedEvents.unshift(() => {
            console.warn(
              'Token not found in state session backend. Retrying user event.',
            );
            request.getUserEvent()!.clearStateToken();
            request.getUserEvent()!.setStates(this.states);
            this.init(this.initParams, request);
          });
        } else {
          onError(uiResponse.getError()!);
          console.error('error', uiResponse.getError());
        }
        break;
      case UiResponse.TypeCase.TYPE_NOT_SET:
        throw new Error(`Unhandled case for server event: ${uiResponse}`);
    }
  }

  private async processCommandQueue(
    onCommand: (command: Command) => Promise<void>,
  ) {
    if (this.commandQueuePromise) {
      return this.commandQueuePromise;
    }
    let resolveHandle!: () => void;
    this.commandQueuePromise = new Promise((resolve) => {
      resolveHandle = resolve;
    });
    try {
      while (this.commandQueue.length > 0) {
        const command = this.commandQueue.shift()!;
        await onCommand(command);
      }
    } finally {
      this.commandQueuePromise = undefined;
      resolveHandle();
    }
  }

  private queueMessage(request: UiRequest, response: UiResponse) {
    // We want to process only one message pair at a time, otherwise
    // you can get race conditions like this:
    // https://github.com/mesop-dev/mesop/issues/1231
    this.messageQueue.push({
      request,
      response,
    });
    this.processMessageQueue();
  }

  private async processMessageQueue() {
    if (this.processingMessageDeferred) {
      return this.processingMessageDeferred.promise;
    }

    this.processingMessageDeferred = createDeferred();

    while (this.messageQueue.length > 0) {
      const queuedMessage = this.messageQueue.shift()!;
      try {
        await this.handleUiResponse(
          queuedMessage.request,
          queuedMessage.response,
          this.initParams,
        );
      } catch (error) {
        console.error('Error handling UI response:', error);
      }
    }

    // All queued messages processed; resolve the promise and clear it.
    this.processingMessageDeferred.resolve();
    this.processingMessageDeferred = null;
  }

  dispatch(userEvent: UserEvent) {
    // Every user event should have an event handler,
    // except for the ones below:
    if (
      !userEvent.getHandlerId() &&
      !userEvent.getNavigation() &&
      !userEvent.getResize() &&
      !userEvent.getChangePrefersColorScheme()
    ) {
      // This is a no-op user event, so we don't send it.
      return;
    }
    const initUserEvent = () => {
      if (this.stateToken) {
        userEvent.setStateToken(this.stateToken);
      } else {
        userEvent.setStates(this.states);
      }
      // Make sure we compute these properties right before the user
      // event is dispatched, otherwise this can cause a weird
      // race condition.
      userEvent.setViewportSize(getViewportSize());
      userEvent.setThemeSettings(this.themeService.getThemeSettings());
      userEvent.setQueryParamsList(getQueryParams());

      const request = new UiRequest();
      request.setUserEvent(userEvent);
      this.init(this.initParams, request);
    };

    if (this.status === ChannelStatus.CLOSED) {
      initUserEvent();
    } else {
      this.queuedEvents.push(initUserEvent);
      if (this.experimentService.websocketsEnabled) {
        // We will wait a bit to see if the server will respond with a new state.
        // This addresses common use cases where a user may
        // type in a text input and then click a button and
        // they would expect the updated text input state to be
        // included in the click button event.
        setTimeout(() => {
          const initUserEventIndex = this.queuedEvents.findIndex(
            (event) => event === initUserEvent,
          );
          // The initUserEvent may have already been removed off the queue
          // if the response came back from the server already.
          if (initUserEventIndex !== -1) {
            const initUserEvent = this.queuedEvents.splice(
              initUserEventIndex,
              1,
            )[0];
            initUserEvent();
          }
        }, 500);
      }
    }
  }

  private dequeueEvent() {
    if (this.queuedEvents.length) {
      const queuedEvent = this.queuedEvents.shift()!;
      queuedEvent();
    }
  }

  checkForHotReload() {
    const pollHotReloadEndpoint = async () => {
      try {
        const response = await fetch(
          prefixBasePath(`/__hot-reload__?counter=${this.hotReloadCounter}`),
        );
        if (response.status === 200) {
          const text = await response.text();
          this.hotReloadCounter = Number(text);
          this.hotReload();
          this.hotReloadBackoffCounter = 0;
          // Use void to explicitly not await to avoid downstream sync issue.
          void pollHotReloadEndpoint();
        } else {
          throw new Error(`Server responded with status: ${response.status}`);
        }
      } catch (error) {
        console.error('Hot reload polling error:', error);
        setTimeout(pollHotReloadEndpoint, this.calculateExponentialBackoff());
      }
    };

    pollHotReloadEndpoint();
  }

  private calculateExponentialBackoff(): number {
    const delay = 2 ** this.hotReloadBackoffCounter * 100;
    this.hotReloadBackoffCounter++;
    return delay;
  }

  resetOverridedTitle() {
    this.overridedTitle = '';
  }

  setOverridedTitle(newTitle: string) {
    this.overridedTitle = newTitle;
  }

  hotReload() {
    // Only hot reload if there's no request in-flight.
    // Most likely the in-flight request will receive the updated UI.
    // In the unlikely chance it doesn't, we will wait for the next
    // hot reload trigger which is not ideal but acceptable.
    if (this.getStatus() === ChannelStatus.OPEN) {
      return;
    }
    this._isHotReloading = true;
    const request = new UiRequest();
    const userEvent = new UserEvent();
    userEvent.setStates(this.states);
    userEvent.setHotReload(new HotReloadEvent());
    userEvent.setViewportSize(getViewportSize());
    userEvent.setThemeSettings(this.themeService.getThemeSettings());
    userEvent.setQueryParamsList(getQueryParams());
    request.setUserEvent(userEvent);
    this.init(this.initParams, request);
  }
}

function createDeferred<T = void>(): {
  promise: Promise<T>;
  resolve: (value: T | PromiseLike<T>) => void;
  reject: (reason?: any) => void;
} {
  let resolve: (value: T | PromiseLike<T>) => void = () => {};
  let reject: (reason?: any) => void = () => {};
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return {promise, resolve, reject};
}

function generatePayloadString(request: UiRequest): string {
  let path = window.location.pathname;
  const base = (window as any).__MESOP_BASE_URL_PATH__ as string | undefined;
  if (base && path.startsWith(base)) {
    path = path.slice(base.length) || '/';
  }
  request.setPath(path);
  const array = request.serializeBinary();
  const byteString = btoa(fromUint8Array(array))
    // Make this URL-safe:
    .replace(/\+/g, '-')
    .replace(/\//g, '_');
  return byteString;
}

function fromUint8Array(array: Uint8Array): string {
  // Chunk this to avoid RangeError: Maximum call stack size exceeded
  let result = '';
  const chunkSize = 16384; // This size can be adjusted

  for (let i = 0; i < array.length; i += chunkSize) {
    const chunk = array.subarray(i, i + chunkSize);
    result += String.fromCodePoint(...(chunk as unknown as number[]));
  }

  return result;
}

function toUint8Array(byteString: string): Uint8Array {
  const byteArray = new Uint8Array(byteString.length);
  for (let i = 0; i < byteString.length; i++) {
    byteArray[i] = byteString.charCodeAt(i);
  }
  return byteArray;
}
