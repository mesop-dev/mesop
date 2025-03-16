from dataclasses import dataclass, field

@dataclass(kw_only=True)
class CORS:
  allowed_origins: list[str] = field(default_factory=list)