import {
  ApplicationRef,
  ChangeDetectionStrategy,
  Component,
  ComponentRef,
  ElementRef,
  EmbeddedViewRef,
  Input,
  Renderer2,
  TemplateRef,
  ViewChild,
  ViewContainerRef,
} from '@angular/core';
import {CommonModule} from '@angular/common';
import {
  ClickEvent,
  Component as ComponentProto,
  RightClickEvent,
  UserEvent,
  WebComponentType,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {BoxType} from 'mesop/mesop/components/box/box_jspb_proto_pb/mesop/components/box/box_pb';
import {
  BaseComponent,
  UserDefinedComponent,
  typeToComponent,
} from './type_to_component';
import {Channel} from '../services/channel';
import {formatStyle} from '../utils/styles';
import {jsonParse} from '../utils/strict_types';
import {MESOP_EVENT_NAME, MesopEvent} from './mesop_event';
import {ErrorDialogService} from '../services/error_dialog_service';

export const COMPONENT_RENDERER_ELEMENT_NAME = 'component-renderer-element';

const WEB_COMPONENT_PREFIX = '<web>';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'component-renderer',
  templateUrl: 'component_renderer.ng.html',
  styleUrl: 'component_renderer.css',
  standalone: true,
  imports: [CommonModule],
})
export class ComponentRenderer {
  @ViewChild('childrenTemplate', {static: true})
  childrenTemplate!: TemplateRef<any>;

  @ViewChild('insertion', {read: ViewContainerRef, static: true})
  insertionRef!: ViewContainerRef;

  @Input() component!: ComponentProto;
  private _boxType: BoxType | undefined;
  private _componentRef!: ComponentRef<BaseComponent>;
  customElement: HTMLElement | undefined;
  projectedViewRef: EmbeddedViewRef<ComponentRenderer> | undefined;
  clickListenerRemover: (() => void) | undefined;
  rightClickListenerRemover: (() => void) | undefined;

  constructor(
    private channel: Channel,
    private renderer: Renderer2,
    private applicationRef: ApplicationRef,
    private elementRef: ElementRef,
    private errorDialogService: ErrorDialogService,
  ) {}

  ngOnDestroy() {
    if (this.customElement) {
      this.customElement.removeEventListener(
        MESOP_EVENT_NAME,
        this.dispatchCustomUserEvent,
      );
    }
    if (this.projectedViewRef) {
      this.projectedViewRef.destroy();
    }
    this.clickListenerRemover?.();
  }

  getKey() {
    return this.component.getKey()?.getKey();
  }

  trackByFn(index: any, item: ComponentProto) {
    const key = item.getKey()?.getKey();
    if (key) {
      return key;
    }
    // Include the component type and URL path in the key.
    // This ensures Angular recognizes it as a new child component,
    // preventing errors from passing new properties to old components
    // and also avoiding DOM state accidentally being carried over.
    // The URL path helps distinguish components across different routes.
    const typeName = item.getType()?.getName();
    const urlPath = window.location.pathname;
    return `${index}___${typeName}___${urlPath}`;
  }

  isBoxType() {
    const typeName = this.component.getType()?.getName();
    return typeName?.getCoreModule() && typeName.getFnName() === 'box';
  }

  type() {
    return this.component.getType();
  }

  ngOnInit() {
    if (isRegularComponent(this.component)) {
      this.createComponentRef();
    }
  }

  ngOnChanges() {
    if (this.customElement) {
      // Update the custom element properties and events
      this.updateCustomElement(this.customElement);

      // Efficiently update children
      this.updateCustomElementChildren();
      return;
    }
    if (isRegularComponent(this.component)) {
      this.updateComponentRef();
      return;
    }
    let hasClickHandler = false;
    let hasRightClickHandler = false;
    if (this.isBoxType()) {
      this._boxType = BoxType.deserializeBinary(
        this.component.getType()!.getValue() as unknown as Uint8Array,
      );
      // Used for determinine which component-renderer elements are not boxes.
      this.elementRef.nativeElement.setAttribute('mesop-box', 'true');
      hasClickHandler = Boolean(this._boxType.getOnClickHandlerId());
      hasRightClickHandler = Boolean(this._boxType.getOnRightClickHandlerId());
    }

    if (hasClickHandler) {
      if (!this.clickListenerRemover) {
        this.clickListenerRemover = this.renderer.listen(
          this.elementRef.nativeElement,
          'click',
          this.onClick.bind(this),
        );
      }
    } else {
      this.clickListenerRemover?.();
    }

    if (hasRightClickHandler) {
      if (!this.rightClickListenerRemover) {
        this.rightClickListenerRemover = this.renderer.listen(
          this.elementRef.nativeElement,
          'contextmenu',
          this.onRightClick.bind(this),
        );
      }
    } else {
      this.rightClickListenerRemover?.();
    }

    this.computeStyles();
  }

  updateCustomElement(customElement: HTMLElement) {
    const webComponentType = WebComponentType.deserializeBinary(
      this.component.getType()!.getValue() as unknown as Uint8Array,
    );
    const properties = jsonParse(
      webComponentType.getPropertiesJson()!,
    ) as object;
    for (const key of Object.keys(properties)) {
      const value = (properties as any)[key];
      // We should have checked this in Python, but just in case
      // we will check the property name right before using it.
      checkPropertyNameIsSafe(key);
      (customElement as any)[key] = value;
    }

    const events = jsonParse(webComponentType.getEventsJson()!) as object;
    for (const event of Object.keys(events)) {
      // We should have checked this in Python, but just in case
      // we will check the property name right before using it.
      checkPropertyNameIsSafe(event);
      (customElement as any)[event] = (events as any)[event];
    }
    // Always try to remove the event listener since we will attach the event listener
    // next. If the event listener wasn't already attached, then removeEventListener is
    // effectively a no-op (i.e. it won't throw an error).
    customElement.removeEventListener(
      MESOP_EVENT_NAME,
      this.dispatchCustomUserEvent,
    );
    if (Object.keys(events).length) {
      customElement.addEventListener(
        MESOP_EVENT_NAME,
        this.dispatchCustomUserEvent,
      );
    }
  }

  private updateCustomElementChildren() {
    const existingChildren = Array.from(this.customElement!.children).filter(
      (child) =>
        // tagName is uppercased in HTML.
        // See: https://developer.mozilla.org/docs/Web/API/Element/tagName
        child.tagName === COMPONENT_RENDERER_ELEMENT_NAME.toUpperCase(),
    );
    const newChildren = this.component.getChildrenList();

    // Update or add children
    for (let i = 0; i < newChildren.length; i++) {
      const child = newChildren[i];
      if (i < existingChildren.length) {
        // Update existing child
        (existingChildren[i] as any)['component'] = child;
      } else {
        // Add new child
        const childElement = document.createElement(
          COMPONENT_RENDERER_ELEMENT_NAME,
        );
        (childElement as any)['component'] = child;
        this.customElement!.appendChild(childElement);
      }
    }

    // Remove excess children
    for (let i = newChildren.length; i < existingChildren.length; i++) {
      this.customElement!.removeChild(existingChildren[i]);
    }
  }

  computeStyles() {
    this.elementRef.nativeElement.style = this.getStyle();
    const classes = this.getClasses();
    if (classes) {
      this.elementRef.nativeElement.classList = classes;
    }
  }

  createComponentRef() {
    const typeName = this.component.getType()?.getName()!;
    let options = {};
    if (this.component.getChildrenList().length) {
      this.projectedViewRef = this.childrenTemplate.createEmbeddedView(this);
      // Need to attach view or it doesn't render.
      // ApplicationRef will automatically detach the view
      // when the view ref is destroyed.
      this.applicationRef.attachView(this.projectedViewRef);
      const index = this.component.getType()?.getTypeIndex() ?? 0;
      const projectableNodes = [];
      projectableNodes[index] = this.projectedViewRef.rootNodes;
      options = {
        projectableNodes,
      };
    }
    const componentClass = typeName.getCoreModule()
      ? typeToComponent[typeName.getFnName()!] || UserDefinedComponent // Some core modules rely on UserDefinedComponent
      : UserDefinedComponent;
    if (typeName.getFnName()?.startsWith(WEB_COMPONENT_PREFIX)) {
      const customElementName = typeName
        .getFnName()!
        .slice(WEB_COMPONENT_PREFIX.length);

      // Check if the custom element is already defined
      if (!customElements.get(customElementName)) {
        const error = new Error(
          `Expected web component '${customElementName}' to be registered by the JS module.

Make sure the web component name is spelled the same between Python and JavaScript.`,
        );
        this.errorDialogService.showError(error);
      }

      this.customElement = document.createElement(customElementName);
      this.updateCustomElement(this.customElement);

      for (const child of this.component.getChildrenList()) {
        const childElement = document.createElement(
          COMPONENT_RENDERER_ELEMENT_NAME,
        );
        (childElement as any)['component'] = child;
        this.customElement.appendChild(childElement);
      }

      this.insertionRef.element.nativeElement.parentElement.appendChild(
        this.customElement,
      );
    } else {
      // Need to insert at insertionRef and *not* viewContainerRef, otherwise
      // the component (e.g. <mesop-text> will not be properly nested inside <component-renderer>).
      this._componentRef = this.insertionRef.createComponent(
        componentClass, // If it's an unrecognized type, we assume it's a user-defined / Python custom component
        options,
      );
      this.updateComponentRef();
    }
  }

  dispatchCustomUserEvent = (event: Event) => {
    const mesopEvent = event as MesopEvent<any>;
    const userEvent = new UserEvent();
    userEvent.setStringValue(JSON.stringify(mesopEvent.payload));
    userEvent.setHandlerId(mesopEvent.handlerId);
    userEvent.setKey(this.component.getKey());
    this.channel.dispatch(userEvent);
  };

  updateComponentRef() {
    if (this._componentRef) {
      const instance = this._componentRef.instance;
      instance.type = this.component.getType()!;
      instance.key = this.component.getKey()!;
      instance.style = this.component.getStyle()!;
      instance.ngOnChanges();
    }
  }

  //////////////
  // Box-specific implementation:
  //////////////

  getStyle(): string {
    if (!this._boxType) {
      return '';
    }

    let style = '';

    if (this.component.getStyle()) {
      style += formatStyle(this.component.getStyle()!);
    }
    return style;
  }

  getClasses(): string {
    if (this._boxType) {
      return this._boxType.getClassesList().join(' ');
    }
    return '';
  }

  onClick(event: MouseEvent) {
    if (!this._boxType) {
      return;
    }
    const userEvent = new UserEvent();
    userEvent.setHandlerId(this._boxType.getOnClickHandlerId()!);
    userEvent.setKey(this.component.getKey());
    const click = new ClickEvent();
    populateClickEvent(click, event);
    userEvent.setClick(click);
    this.channel.dispatch(userEvent);
  }

  onRightClick(event: MouseEvent) {
    if (!this._boxType) {
      return;
    }

    // Disable the default contextmenu on right click.
    event.preventDefault();

    const userEvent = new UserEvent();
    userEvent.setHandlerId(this._boxType.getOnRightClickHandlerId()!);
    userEvent.setKey(this.component.getKey());
    const click = new RightClickEvent();
    populateClickEvent(click, event);
    userEvent.setRightClick(click);
    this.channel.dispatch(userEvent);
  }
}

function isRegularComponent(component: ComponentProto) {
  const typeName = component.getType()?.getName()!;
  return (
    component.getType() &&
    !(typeName.getCoreModule() && typeName.getFnName() === 'box')
  );
}

// Note: the logic here should be kept in sync with
// helper.py's check_property_keys_is_safe
export function checkPropertyNameIsSafe(propertyName: string) {
  const normalizedName = propertyName.toLowerCase();
  if (
    ['src', 'srcdoc'].includes(normalizedName) ||
    normalizedName.startsWith('on')
  ) {
    throw new Error(`Unsafe property name '${propertyName}' cannot be used.`);
  }
}

function populateClickEvent(
  click: ClickEvent | RightClickEvent,
  event: MouseEvent,
) {
  click.setIsTarget(event.target === event.currentTarget);
  click.setClientX(event.clientX);
  click.setClientY(event.clientY);
  click.setPageX(event.pageX);
  click.setPageY(event.pageY);
  click.setOffsetX(event.offsetX);
  click.setOffsetY(event.offsetY);
}
