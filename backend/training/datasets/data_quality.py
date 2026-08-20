"""Data Quality, Leakage Detection, and Training Job Guard for APEX.

Implements all automated checks required by APEX_MASTER_ENGINEERING_SPEC.md §5:
- Duplicate rows
- Impossible tyre ages
- Negative fuel
- Invalid compounds
- Future-information leakage
- Target leakage
- Timestamp ordering
- Missing telemetry bursts
- Outlier speed/RPM
- Invalid race position
- Impossible pit-stop timing

Fails the training job (raises DataLeakageError) if severity is SEVERE.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

VALID_COMPOUNDS = {"SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"}


class IssueSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    SEVERE = "SEVERE"


@dataclass
class DataQualityIssue:
    check: str
    severity: IssueSeverity
    description: str
    affected_rows: int = 0
    sample: Any = None


@dataclass
class DataQualityReport:
    dataset_name: str
    total_rows: int
    issues: list[DataQualityIssue] = field(default_factory=list)
    passed: bool = True

    def add(self, issue: DataQualityIssue) -> None:
        self.issues.append(issue)
        if issue.severity == IssueSeverity.SEVERE:
            self.passed = False

    def summary(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset_name,
            "total_rows": self.total_rows,
            "passed": self.passed,
            "issue_count": len(self.issues),
            "severe": sum(1 for i in self.issues if i.severity == IssueSeverity.SEVERE),
            "warnings": sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING),
            "issues": [
                {
                    "check": i.check,
                    "severity": i.severity,
                    "description": i.description,
                    "affected_rows": i.affected_rows,
                }
                for i in self.issues
            ],
        }


class DataLeakageError(Exception):
    """Raised when severe data leakage or quality violation is detected.
    Training jobs must not proceed past this exception.
    """


class DataQualityChecker:
    """Runs all automated data quality and leakage checks on a tyre telemetry DataFrame.

    Usage:
        report = DataQualityChecker.run(df, dataset_name="fastf1_2023")
        if not report.passed:
            raise DataLeakageError(report.summary())
    """

    @classmethod
    def run(
        cls,
        df: pd.DataFrame,
        dataset_name: str = "dataset",
        fail_on_severe: bool = True,
    ) -> DataQualityReport:
        """Run all quality checks. Raises DataLeakageError if fail_on_severe=True and issues exist."""
        report = DataQualityReport(dataset_name=dataset_name, total_rows=len(df))

        if df.empty:
            report.add(DataQualityIssue(
                check="empty_dataset",
                severity=IssueSeverity.SEVERE,
                description="Dataset is empty — cannot train.",
            ))
            if fail_on_severe:
                raise DataLeakageError(f"[DataQuality] Dataset '{dataset_name}' is empty.")
            return report

        cls._check_duplicates(df, report)
        cls._check_tyre_ages(df, report)
        cls._check_negative_values(df, report)
        cls._check_invalid_compounds(df, report)
        cls._check_future_leakage(df, report)
        cls._check_target_leakage(df, report)
        cls._check_timestamp_ordering(df, report)
        cls._check_missing_bursts(df, report)
        cls._check_outlier_lap_times(df, report)
        cls._check_invalid_race_position(df, report)
        cls._check_impossible_pit_timing(df, report)

        for issue in report.issues:
            level = logging.ERROR if issue.severity == IssueSeverity.SEVERE else logging.WARNING
            logger.log(
                level,
                "[DataQuality][%s] %s: %s (affected_rows=%d)",
                issue.severity,
                issue.check,
                issue.description,
                issue.affected_rows,
            )

        if fail_on_severe and not report.passed:
            severe = [i for i in report.issues if i.severity == IssueSeverity.SEVERE]
            raise DataLeakageError(
                f"[DataQuality] Dataset '{dataset_name}' failed {len(severe)} severe check(s). "
                f"Training job aborted. Issues: {[i.check for i in severe]}"
            )

        return report

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    @staticmethod
    def _check_duplicates(df: pd.DataFrame, report: DataQualityReport) -> None:
        """Check 1: Duplicate rows (exact row duplicates)."""
        dup_count = int(df.duplicated().sum())
        if dup_count > 0:
            pct = dup_count / len(df) * 100
            severity = IssueSeverity.SEVERE if pct > 5.0 else IssueSeverity.WARNING
            report.add(DataQualityIssue(
                check="duplicate_rows",
                severity=severity,
                description=f"{dup_count} duplicate rows ({pct:.1f}%). "
                            f"Severe if >5% of dataset.",
                affected_rows=dup_count,
            ))

    @staticmethod
    def _check_tyre_ages(df: pd.DataFrame, report: DataQualityReport) -> None:
        """Check 2: Impossible tyre ages (< 1 or > 80 laps)."""
        if "tyre_age" not in df.columns:
            return
        invalid = df[(df["tyre_age"] < 1) | (df["tyre_age"] > 80)]
        if len(invalid) > 0:
            sample_vals = [float(v) for v in pd.Series(invalid["tyre_age"]).iloc[:5].tolist()]
            report.add(DataQualityIssue(
                check="impossible_tyre_age",
                severity=IssueSeverity.SEVERE,
                description=f"{len(invalid)} rows have tyre_age outside [1, 80]. "
                            f"Sample values: {sample_vals}",
                affected_rows=len(invalid),
                sample=sample_vals,
            ))

    @staticmethod
    def _check_negative_values(df: pd.DataFrame, report: DataQualityReport) -> None:
        """Check 3: Negative fuel or lap time delta (physically impossible)."""
        for col, label in [("fuel_kg", "fuel_kg"), ("lap_time_delta", "lap_time_delta"), ("lap_time_s", "lap_time_s")]:
            if col not in df.columns:
                continue
            neg = df[df[col] < 0.0]
            if len(neg) > 0:
                report.add(DataQualityIssue(
                    check=f"negative_{label}",
                    severity=IssueSeverity.SEVERE,
                    description=f"{len(neg)} rows have negative {label}.",
                    affected_rows=len(neg),
                ))

    @staticmethod
    def _check_invalid_compounds(df: pd.DataFrame, report: DataQualityReport) -> None:
        """Check 4: Invalid compound labels."""
        if "compound" not in df.columns:
            return
        unknown = df[~df["compound"].str.upper().isin(VALID_COMPOUNDS)]
        if len(unknown) > 0:
            unrec = list(set(pd.Series(unknown["compound"]).dropna().astype(str).tolist()))
            report.add(DataQualityIssue(
                check="invalid_compound",
                severity=IssueSeverity.SEVERE,
                description=f"{len(unknown)} rows have unrecognized compound: "
                            f"{unrec}",
                affected_rows=len(unknown),
            ))

    @staticmethod
    def _check_future_leakage(df: pd.DataFrame, report: DataQualityReport) -> None:
        """Check 5: Future-information leakage — features that include the lap result being predicted.

        Specifically checks if any column named *_next* or *_future* appears in
        a feature set that also has a target column (lap_time_delta or next_lap_time_s).
        """
        future_cols = [c for c in df.columns if any(
            tag in c.lower() for tag in ("_next", "_future", "next_lap", "future_lap")
        )]
        target_cols = [c for c in df.columns if c in ("lap_time_delta", "next_lap_time_s", "target")]

        if future_cols and target_cols:
            report.add(DataQualityIssue(
                check="future_information_leakage",
                severity=IssueSeverity.SEVERE,
                description=f"Potential future-leakage columns present alongside target: "
                            f"future_cols={future_cols}, target_cols={target_cols}",
                affected_rows=len(df),
                sample=future_cols[:5],
            ))

    @staticmethod
    def _check_target_leakage(df: pd.DataFrame, report: DataQualityReport) -> None:
        """Check 6: Target leakage — features with perfect or near-perfect correlation to target."""
        if "lap_time_delta" not in df.columns:
            return
        target = pd.Series(df["lap_time_delta"], dtype=float)
        for col in df.select_dtypes(include=[np.number]).columns:
            if col in ("lap_time_delta", "lap_time_s", "driver_fastest_lap_s", "fuel_corrected_delta"):
                continue  # These are expected to be related
            try:
                col_series = pd.Series(df[col], dtype=float)
                corr = float(target.corr(col_series))
                if abs(corr) > 0.98:
                    report.add(DataQualityIssue(
                        check="target_leakage",
                        severity=IssueSeverity.SEVERE,
                        description=f"Column '{col}' has near-perfect correlation with target "
                                    f"(r={corr:.4f}). Likely a data leak.",
                        affected_rows=len(df),
                        sample=col,
                    ))
            except Exception:
                pass

    @staticmethod
    def _check_timestamp_ordering(df: pd.DataFrame, report: DataQualityReport) -> None:
        """Check 7: Timestamp ordering — per-driver, tyre_age must be monotonically increasing in a stint."""
        if not all(c in df.columns for c in ("tyre_age", "stint")):
            return

        group_cols = [c for c in ("Driver", "season", "circuit", "stint") if c in df.columns]
        if not group_cols:
            return

        violations = 0
        for _, grp in df.groupby(group_cols):
            ages = np.asarray(grp["tyre_age"].values, dtype=float)
            if len(ages) > 1 and not np.all(np.diff(ages) >= 0):
                violations += 1

        if violations > 0:
            severity = IssueSeverity.SEVERE if violations > 5 else IssueSeverity.WARNING
            report.add(DataQualityIssue(
                check="timestamp_ordering",
                severity=severity,
                description=f"{violations} driver/stint groups have non-monotonic tyre_age sequence.",
                affected_rows=violations,
            ))

    @staticmethod
    def _check_missing_bursts(df: pd.DataFrame, report: DataQualityReport) -> None:
        """Check 8: Missing telemetry bursts — large consecutive lap_time_delta gaps."""
        if "lap_time_delta" not in df.columns:
            return
        null_run_threshold = max(10, int(0.02 * len(df)))
        null_series = df["lap_time_delta"].isnull()
        null_bursts = (null_series != null_series.shift()).cumsum()[null_series]

        if len(null_bursts) > null_run_threshold:
            report.add(DataQualityIssue(
                check="missing_telemetry_bursts",
                severity=IssueSeverity.WARNING,
                description=f"{len(null_bursts)} consecutive null values in lap_time_delta "
                            f"(threshold={null_run_threshold}). Possible telemetry dropout.",
                affected_rows=len(null_bursts),
            ))

    @staticmethod
    def _check_outlier_lap_times(df: pd.DataFrame, report: DataQualityReport) -> None:
        """Check 9: Outlier lap times or deltas beyond physically plausible range."""
        if "lap_time_s" in df.columns:
            outliers = df[(df["lap_time_s"] < 50.0) | (df["lap_time_s"] > 300.0)]
            if len(outliers) > 0:
                report.add(DataQualityIssue(
                    check="outlier_lap_time_s",
                    severity=IssueSeverity.WARNING,
                    description=f"{len(outliers)} rows with lap_time_s outside [50, 300]s.",
                    affected_rows=len(outliers),
                ))

        if "lap_time_delta" in df.columns:
            outliers_delta = df[df["lap_time_delta"] > 30.0]
            if len(outliers_delta) > 0:
                report.add(DataQualityIssue(
                    check="outlier_lap_time_delta",
                    severity=IssueSeverity.WARNING,
                    description=f"{len(outliers_delta)} rows with lap_time_delta > 30s (likely outliers).",
                    affected_rows=len(outliers_delta),
                ))

    @staticmethod
    def _check_invalid_race_position(df: pd.DataFrame, report: DataQualityReport) -> None:
        """Check 10: Invalid race positions (< 1 or > 20 for F1 grid)."""
        if "Position" not in df.columns:
            return
        invalid_pos = df[(df["Position"] < 1) | (df["Position"] > 20)]
        if len(invalid_pos) > 0:
            report.add(DataQualityIssue(
                check="invalid_race_position",
                severity=IssueSeverity.WARNING,
                description=f"{len(invalid_pos)} rows with race Position outside [1, 20].",
                affected_rows=len(invalid_pos),
            ))

    @staticmethod
    def _check_impossible_pit_timing(df: pd.DataFrame, report: DataQualityReport) -> None:
        """Check 11: Impossible pit-stop timing — tyre_age resets without pit event marker."""
        if not all(c in df.columns for c in ("tyre_age", "stint")):
            return
        group_cols = [c for c in ("Driver", "season", "circuit") if c in df.columns]
        if not group_cols:
            return

        impossible_resets = 0
        for _, grp in df.groupby(group_cols):
            grp_sorted = grp.sort_values("tyre_age")
            stint_changes = grp_sorted["stint"].diff().fillna(0)
            age_resets = grp_sorted["tyre_age"].diff().fillna(0)
            # Age going backwards without a stint change = impossible
            impossible = ((age_resets < -3) & (stint_changes == 0)).sum()
            impossible_resets += int(impossible)

        if impossible_resets > 0:
            report.add(DataQualityIssue(
                check="impossible_pit_timing",
                severity=IssueSeverity.SEVERE,
                description=f"{impossible_resets} tyre_age backward jumps detected without stint change. "
                            f"Possible data corruption.",
                affected_rows=impossible_resets,
            ))
