from sqlalchemy import Column, String, Integer, DateTime, ForeignKey,Text,JSON,Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from src.db.database import Base
import enum

class CaseStatus(str,enum.Enum):
  QUEUED = "queued"
  PROCESSING = "processing"
  NEEDS_REVIEW = "needs_review"
  AWAITING_DOCUMENTS= "awaiting_documents"
  APPROVED = "approved"
  REJECTED = "rejected"

class Case(Base):
  __tablename__ = "cases"

  id = Column(String,primary_key=True)
  supplier_name = Column(String,nullable=False)
  status = Column(SQLEnum(CaseStatus),default = CaseStatus.QUEUED,nullable=False)
  created_at = Column(DateTime,default=lambda:datetime.now(timezone.utc))
  updated_at = Column(DateTime,default=lambda:datetime.now(timezone.utc), onupdate=lambda:datetime.now(timezone.utc))

  documents = relationship("Document", back_populates="case")
  findings = relationship("Finding", back_populates="case")
  audit_logs = relationship("AuditLog", back_populates="case")


class Document(Base):
  __tablename__ = "documents"

  id = Column(String, primary_key=True)  # doc_001
  case_id = Column(String, ForeignKey("cases.id"), nullable=False)
  filename = Column(String, nullable=False)
  doc_type = Column(String, nullable=True)
  extracted_data = Column(JSON, nullable=True)  # ExtractedDocument serialized
  created_at = Column(DateTime, default=lambda:datetime.now(timezone.utc))

  case = relationship("Case", back_populates="documents")

class Finding(Base):
  __tablename__ = "findings"

  id = Column(String, primary_key=True)  # finding_id from validation
  case_id = Column(String, ForeignKey("cases.id"), nullable=False)
  field_name = Column(String, nullable=False)
  severity = Column(String, nullable=False)
  message = Column(Text, nullable=False)
  rule_id = Column(String, nullable=False)
  created_at = Column(DateTime, default=lambda:datetime.now(timezone.utc))

  case = relationship("Case", back_populates="findings")

class AuditLog(Base):
  __tablename__ = "audit_logs"

  id = Column(Integer, primary_key=True, autoincrement=True)
  case_id = Column(String, ForeignKey("cases.id"), nullable=False)
  actor = Column(String, nullable=False)  # "system" or user_id
  action = Column(String, nullable=False)  # "extracted", "validated", "human_approved"
  details = Column(JSON, nullable=True)
  created_at = Column(DateTime, default=lambda:datetime.now(timezone.utc))

  case = relationship("Case", back_populates="audit_logs")

class Job(Base):
  __tablename__="jobs"

  id = Column(String,primary_key=True)
  case_id = Column(String,ForeignKey("cases.id"),nullable=False)
  status = Column(String,default="queued")
  error_message = Column(Text,nullable=True)
  created_at = Column(DateTime,default=lambda:datetime.now(timezone.utc))
  updated_at = Column(DateTime,default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc))

  case = relationship("Case")
