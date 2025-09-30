from dataclasses import dataclass

import mesop as me

CARD_WIDTH = "320px"


@dataclass
class Resource:
  title: str
  description: str
  github_url: str
  github_username: str
  img_url: str
  app_url: str | None = None


@dataclass
class Section:
  name: str
  resources: list[Resource]
  icon: str


SECTIONS = [
  Section(
    name="Featured",
    icon="star",
    resources=[
      Resource(
        title="GenMedia Creative Studio",
        description="Showcases creative exploration with Google Cloud's generative media services - Veo, Lyria, Imagen, Chirp 3, and Gemini Image Generation (nano-banana).",
        img_url="https://github.com/user-attachments/assets/61977f3c-dbb6-4002-b8c0-77d57aa03cce",
        github_url="https://github.com/GoogleCloudPlatform/vertex-ai-creative-studio",
        github_username="GoogleCloudPlatform",
      ),
      Resource(
        title="Mesop Duo Chat",
        description="Chat with multiple models at once.",
        github_url="https://github.com/wwwillchen/mesop-duo-chat",
        github_username="wwwillchen",
        app_url="https://huggingface.co/spaces/wwwillchen/mesop-duo-chat",
        img_url="https://github.com/user-attachments/assets/107afb9c-f08c-4f27-bd00-e122415c069e",
      ),
      Resource(
        title="Mesop Prompt Tuner",
        description="Prompt tuning app heavily inspired by Anthropic Console Workbench.",
        app_url="https://huggingface.co/spaces/richard-to/mesop-prompt-tuner",
        img_url="https://github.com/user-attachments/assets/2ec6cbfb-c28b-4f60-98f9-34bfca1f6938",
        github_url="https://github.com/richard-to/mesop-prompt-tuner",
        github_username="richard-to",
      ),
    ],
  ),
  Section(
    name="Apps",
    icon="computer",
    resources=[
      Resource(
        title="Mesop Arena",
        description="Rate generated images head-to-head. Includes ELO leaderboard and voting history.",
        img_url="https://raw.githubusercontent.com/ghchinoy/mesop-arena/refs/heads/main/assets/arena_view.png",
        github_url="https://github.com/ghchinoy/mesop-arena",
        github_username="ghchinoy",
      ),
      Resource(
        title="Custom AI Jira Agent",
        description="Mesop with Django, LangChain Agents, CO-STAR & CoT prompting combined with the Jira API to better automate Jira.",
        img_url="https://github.com/user-attachments/assets/20ab297d-a4d0-4825-b5e6-3e79dc205405",
        github_url="https://github.com/lewisExternal/Custom-AI-Jira-Agent",
        github_username="lewisExternal",
      ),
      Resource(
        title="Multimodal Embeddings Retail Search",
        description="Using multimodal embeddings to search retail product images and titles.",
        img_url="https://github.com/user-attachments/assets/ece910c7-5c2c-4d27-ab6a-0febc7affb12",
        github_url="https://github.com/mandieq/retail_embeddings",
        github_username="mandieq",
      ),
      Resource(
        title="Mesop Jeopardy Live",
        description="Jeopardy using Gemini Multimodal Live API (audio/text).",
        app_url="https://huggingface.co/spaces/richard-to/mesop-jeopardy-live",
        img_url="https://github.com/user-attachments/assets/97d704e1-6df6-4a05-8a77-8e91363295fa",
        github_url="https://github.com/richard-to/mesop-jeopardy-live",
        github_username="richard-to",
      ),
      Resource(
        title="Mesop App Maker",
        description="Generate apps with Mesop using LLMs.",
        app_url="https://huggingface.co/spaces/richard-to/mesop-app-maker",
        img_url="https://github.com/user-attachments/assets/1a826d44-c87b-4c79-aeaf-29bc8da3b1c0",
        github_url="https://github.com/richard-to/mesop-app-maker",
        github_username="richard-to",
      ),
      Resource(
        title="Mesop Jeopardy",
        description="Jeopardy using Mesop + Gemini 1.5 (text only)",
        app_url="https://huggingface.co/spaces/richard-to/mesop-jeopardy",
        img_url="https://github.com/richard-to/mesop-jeopardy/assets/539889/bc27447d-129f-47ae-b0b1-8f5c546762ed",
        github_url="https://github.com/richard-to/mesop-jeopardy",
        github_username="richard-to",
      ),
    ],
  ),
  Section(
    name="Web components",
    icon="code_blocks",
    resources=[
      Resource(
        title="Mesop Markmap",
        description="Mesop web component for the Markmap library.",
        img_url="https://github.com/user-attachments/assets/6aa40ca3-d98a-42b2-adea-3f49b134445d",
        github_url="https://github.com/lianggecm/mesop_markmap",
        app_url="https://colab.research.google.com/drive/17gXlsXPDeo6hcFl1oOyrZ58FTozviN45?usp=sharing",
        github_username="lianggecm",
      ),
    ],
  ),
  Section(
    name="Notebooks",
    icon="description",
    resources=[
      Resource(
        title="Mesop Getting Started Colab",
        description="Get started with Mesop in Colab.",
        img_url="https://github.com/user-attachments/assets/37efbe69-ac97-4d26-8fda-d1b7b2b4976a",
        github_url="https://github.com/mesop-dev/mesop/blob/main/notebooks/mesop_colab_getting_started.ipynb",
        app_url="https://colab.research.google.com/github/mesop-dev/mesop/blob/main/notebooks/mesop_colab_getting_started.ipynb",
        github_username="google",
      ),
      Resource(
        title="Gemma with Mesop Notebook",
        description="Use Gemma with Mesop in Colab.",
        img_url="https://github.com/user-attachments/assets/a52ebf01-7f24-469b-9ad9-b271fdb19e37",
        github_url="https://github.com/google-gemini/gemma-cookbook/blob/main/Gemma/%5BGemma_2%5DUsing_with_Mesop.ipynb",
        app_url="https://colab.research.google.com/github/google-gemini/gemma-cookbook/blob/main/Gemma/%5BGemma_2%5DUsing_with_Mesop.ipynb",
        github_username="google-gemini",
      ),
      Resource(
        title="PaliGemma with Mesop Notebook",
        description="Use PaliGemma with Mesop in Colab.",
        img_url="https://github.com/user-attachments/assets/8cb456a1-f7be-4187-9a3f-f6b48bde73e9",
        github_url="https://github.com/google-gemini/gemma-cookbook/blob/main/PaliGemma/%5BPaliGemma_1%5DUsing_with_Mesop.ipynb",
        app_url="https://colab.research.google.com/github/google-gemini/gemma-cookbook/blob/main/PaliGemma/%5BPaliGemma_1%5DUsing_with_Mesop.ipynb",
        github_username="google-gemini",
      ),
    ],
  ),
]


def scroll_to_section(e: me.ClickEvent):
  me.scroll_into_view(key="section-" + e.key)
  me.state(State).sidenav_menu_open = False


def toggle_theme(e: me.ClickEvent):
  if me.theme_brightness() == "light":
    me.set_theme_mode("dark")
  else:
    me.set_theme_mode("light")


def on_load(e: me.LoadEvent):
  me.set_theme_mode("system")


@me.stateclass
class State:
  sidenav_menu_open: bool


def toggle_menu_button(e: me.ClickEvent):
  s = me.state(State)
  s.sidenav_menu_open = not s.sidenav_menu_open


def is_mobile():
  return me.viewport_size().width < 640


@me.page(
  title="Mesop Showcase",
  on_load=on_load,
  security_policy=me.SecurityPolicy(
    allowed_iframe_parents=["https://huggingface.co"],
  ),
)
def page():
  with me.box(style=me.Style(display="flex", height="100%")):
    if is_mobile():
      with me.content_button(
        type="icon",
        style=me.Style(top=6, left=8, position="absolute", z_index=9),
        on_click=toggle_menu_button,
      ):
        me.icon("menu")
      with me.sidenav(
        opened=me.state(State).sidenav_menu_open,
        style=me.Style(
          background=me.theme_var("surface-container-low"),
        ),
      ):
        sidenav()
    else:
      sidenav()
    with me.box(
      style=me.Style(
        background=me.theme_var("surface-container-low"),
        display="flex",
        flex_direction="column",
        flex_grow=1,
      )
    ):
      with me.box(
        style=me.Style(
          height=240,
          width="100%",
          padding=me.Padding.all(16),
          display="flex",
          align_items="center",
        ),
      ):
        me.text(
          "Mesop Showcase",
          style=me.Style(
            color=me.theme_var("on-background"),
            font_size=22,
            font_weight=500,
            letter_spacing="0.8px",
            padding=me.Padding(left=36) if is_mobile() else None,
          ),
        )

        with me.content_button(
          type="icon",
          style=me.Style(position="absolute", right=4, top=8),
          on_click=toggle_theme,
        ):
          me.icon(
            "light_mode" if me.theme_brightness() == "dark" else "dark_mode"
          )
      with me.box(
        style=me.Style(
          background=me.theme_var("background"),
          flex_grow=1,
          padding=me.Padding(
            left=32,
            right=32,
            bottom=64,
          ),
          border_radius=16,
          overflow_y="auto",
        )
      ):
        for section in SECTIONS:
          me.text(
            section.name,
            style=me.Style(
              font_size=18,
              font_weight=500,
              padding=me.Padding(top=32, bottom=16),
            ),
            key="section-" + section.name,
          )
          with me.box(
            style=me.Style(
              display="grid",
              grid_template_columns=f"repeat(auto-fit, minmax({CARD_WIDTH}, 1fr))",
              gap=24,
              margin=me.Margin(
                bottom=24,
              ),
            )
          ):
            for resource in section.resources:
              card(resource)
        with me.box(
          on_click=lambda e: me.navigate(
            "https://github.com/mesop-dev/mesop/issues/new/choose"
          ),
          style=me.Style(
            cursor="pointer",
            max_width=300,
            background=me.theme_var("surface-container-lowest"),
            box_shadow="0 2px 4px rgba(0, 0, 0, 0.1)",
            # margin=me.Margin.symmetric(horizontal="auto"),
            display="flex",
            justify_content="center",
            align_items="center",
            border_radius=16,
            height=120,
          ),
        ):
          me.icon(
            "add_circle",
            style=me.Style(
              color=me.theme_var("primary"),
              font_size=24,
              margin=me.Margin(right=4, top=2),
            ),
          )
          me.link(
            text="Submit your showcase",
            url="https://github.com/mesop-dev/mesop/issues/new/choose",
            style=me.Style(
              font_size=24,
              color=me.theme_var("on-background"),
              text_decoration="none",
            ),
          )


def sidenav():
  with me.box(
    style=me.Style(
      width=216,
      height="100%",
      background=me.theme_var("surface-container-low"),
      padding=me.Padding.all(16),
    )
  ):
    with me.box(
      style=me.Style(
        display="flex", flex_direction="column", margin=me.Margin(top=48)
      )
    ):
      with me.content_button(
        type="icon",
        on_click=lambda e: me.navigate("https://mesop-dev.github.io/mesop/"),
      ):
        with me.box(
          style=me.Style(display="flex", align_items="center", gap=12)
        ):
          me.icon("home")
          me.text(
            "Home",
            style=me.Style(
              font_size=16,
              margin=me.Margin(bottom=4),
            ),
          )
      with me.content_button(
        type="icon",
        on_click=lambda e: me.navigate(
          "https://mesop-dev.github.io/mesop/demo/"
        ),
      ):
        with me.box(
          style=me.Style(
            display="flex",
            align_items="center",
            gap=8,
          )
        ):
          me.icon("gallery_thumbnail")
          me.text(
            "Demos",
            style=me.Style(
              font_size=16,
              margin=me.Margin(bottom=6, left=4),
            ),
          )
    with me.box(
      style=me.Style(
        padding=me.Padding(top=24),
        display="flex",
        flex_direction="column",
        gap=8,
      ),
    ):
      me.text(
        "Categories",
        style=me.Style(
          font_weight=500,
          letter_spacing="0.4px",
          padding=me.Padding(left=12),
        ),
      )
      for section in SECTIONS:
        with me.box(
          style=me.Style(
            display="flex",
            align_items="center",
            cursor="pointer",
          ),
          on_click=scroll_to_section,
          key=section.name,
        ):
          with me.content_button(type="icon"):
            me.icon(section.icon)
          me.text(section.name)
      with me.box(
        style=me.Style(
          display="flex",
          align_items="center",
          cursor="pointer",
          padding=me.Padding(top=16),
        ),
        on_click=lambda e: me.navigate(
          "https://github.com/mesop-dev/mesop/issues/new/choose"
        ),
      ):
        with me.content_button(type="icon"):
          me.icon("add_circle")
        me.text("Submit your showcase")


def card(resource: Resource):
  with me.box(
    style=me.Style(
      display="flex",
      flex_direction="column",
      gap=12,
      box_shadow="0 2px 4px rgba(0, 0, 0, 0.1)",
      border_radius=16,
      min_width=CARD_WIDTH,
      max_width=480,
      background=me.theme_var("surface-container-lowest"),
    )
  ):
    me.box(
      style=me.Style(
        background=f"url('{resource.img_url}') center/cover no-repeat",
        cursor="pointer",
        height=200,
        width="100%",
        border_radius=16,
        margin=me.Margin(bottom=8),
      ),
      key=resource.app_url or resource.github_url,
      on_click=lambda e: me.navigate(e.key),
    )
    with me.box(
      style=me.Style(
        padding=me.Padding(left=16),
        display="flex",
        flex_direction="column",
        gap=8,
      )
    ):
      me.text(resource.title, style=me.Style(font_weight="bold"))
      with me.box(
        style=me.Style(
          display="flex",
          flex_direction="row",
          align_items="center",
          gap=8,
          cursor="pointer",
        ),
        key="https://github.com/" + resource.github_username,
        on_click=lambda e: me.navigate(e.key),
      ):
        me.image(
          src="https://avatars.githubusercontent.com/"
          + resource.github_username,
          style=me.Style(height=32, width=32, border_radius=16),
        )
        me.text(
          resource.github_username,
          style=me.Style(
            letter_spacing="0.2px",
          ),
        )
      me.text(resource.description, style=me.Style(height=65, font_size=15))
    with me.box(
      style=me.Style(
        display="flex",
        justify_content="space-between",
        padding=me.Padding(left=8, right=8, bottom=8),
      )
    ):
      if resource.github_url:
        me.button(
          "Open repo",
          on_click=lambda e: me.navigate(e.key),
          key=resource.github_url,
        )
      if resource.app_url:
        me.button(
          "Open app",
          on_click=lambda e: me.navigate(e.key),
          key=resource.app_url,
        )
