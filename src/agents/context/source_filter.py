"""
Source filtering data structures.
"""

from dataclasses import dataclass, field


@dataclass
class SourceFilterData:
    """Container for flagged sources."""

    flagged_sources: list[str] = field(default_factory=list)

    def add_flagged_source(self, domain: str) -> None:
        if domain and domain not in self.flagged_sources:
            self.flagged_sources.append(domain)

    def add_flagged_sources(self, domains: list[str]) -> None:
        for domain in domains:
            self.add_flagged_source(domain)

    @property
    def search_filter(self) -> str:
        """Get DuckDuckGo filter string."""

        return " ".join([f"-site:{domain}" for domain in self.flagged_sources])
