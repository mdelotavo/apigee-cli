from typing import Dict, Type
from .base import BaseBackup

from .resources.apis import APIsBackup
from .resources.developers import DevelopersBackup

RESOURCE_REGISTRY: Dict[str, Type[BaseBackup]] = {
  "apis": APIsBackup,
  "developers": DevelopersBackup,
}
