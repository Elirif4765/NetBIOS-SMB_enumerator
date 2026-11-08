from database import Base
from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column


class Scans(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_batch: Mapped[str]
    interface: Mapped[str]
    subnet: Mapped[str]
    elapsed_seconds: Mapped[int]
    hosts_found: Mapped[int | None]
    hosts: Mapped[list["Hosts"]] = relationship(back_populates="scan", cascade="all, delete-orphan")

class Hosts(Base):
    __tablename__ = "host_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"))
    ip: Mapped[str]
    port_139: Mapped[str]
    port_445: Mapped[str]
    hostnames: Mapped[list[str]] = mapped_column(JSON)
    workgroups: Mapped[list[str]] = mapped_column(JSON)
    shares: Mapped[list[str] | None] = mapped_column(JSON)
    risk_status: Mapped[str]
    scan: Mapped["Scans"] = relationship(back_populates="hosts")