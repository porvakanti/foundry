"""Phase 2 storage adapters.

Each module here implements :class:`foundry.repo.AgentRepo` against a real
system. They are interfaces only: every method raises ``NotImplementedError``
with a docstring describing what the integration has to do. Point
:func:`foundry.repo.get_repo` at one of them when it is ready.
"""

from foundry.datastores.azure_pg import AzurePostgresRepo
from foundry.datastores.datasphere import DatasphereRepo
from foundry.datastores.gcp import GCPRepo
from foundry.datastores.sap import SAPRepo

__all__ = ["AzurePostgresRepo", "DatasphereRepo", "GCPRepo", "SAPRepo"]
