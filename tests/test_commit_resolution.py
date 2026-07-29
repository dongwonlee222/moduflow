#!/usr/bin/env python3
"""Shared commit-to-issue resolver (issue 095, stream A).

Covers the spec's regression table: trailer-only, branch-only, mixed,
merge-subject with the branch deleted, detached HEAD, unmatched commits, and
the batching constraint that converge must not fan out per commit.
"""
import importlib
import re
import sys
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import commit_resolution as cr  # noqa: E402
import commit_resolution_shapes as shapes  # noqa: E402
from git_repo_builder import GitRepo  # noqa: E402

ISSUE = "095-commit-issue-resolution-parity"
OTHER = "094-risk-based-security-and-quality-review-gate"

FAILURE_INVARIANT_TESTS = {
    "FH-001": (
        "tests.test_commit_resolution.CommitDirectionTruthTests."
        "test_bare_and_indexed_resolution_match_declared_truth",
        "tests.test_commit_resolution_differential.CommitDirectionTests."
        "test_bare_and_full_result_resolution_use_same_policy",
        "tests.test_commit_resolution_differential.GroundTruthTests."
        "test_trailer_disagrees_with_branch",
        "tests.test_commit_resolution.FailureInvariantMutationTests."
        "test_fh001_composite_detects_broken_issue_to_commits",
        "tests.test_commit_resolution.FailureInvariantMutationTests."
        "test_fh001_composite_detects_same_wrong_commit_issue",
    ),
    "FH-002": (
        "tests.test_commit_graph.TopicDeltaTests."
        "test_base_history_is_not_topic_work"
    ),
    "FH-003": (
        "tests.test_commit_graph.TopicDeltaTests."
        "test_published_no_ff_topic_recovers_pre_publication_fork"
    ),
    "FH-004": (
        "tests.test_commit_resolution.MergeClaimInvariantTests."
        "test_subject_token_order_does_not_change_content"
    ),
    "FH-005": (
        "tests.test_commit_graph.TopicDeltaTests."
        "test_stacked_issue_excludes_inner_content"
    ),
    "FH-006": (
        "tests.test_commit_graph.ForkPointInvariantTests."
        "test_advancing_trunk_does_not_change_fork_point"
    ),
    "FH-007": (
        "tests.test_commit_resolution.SourcePrecedenceInvariantTests."
        "test_complete_precedence_chain",
        "tests.test_commit_resolution_differential.CommitDirectionTests."
        "test_bare_and_full_result_resolution_use_same_policy",
        "tests.test_commit_resolution.FailureInvariantMutationTests."
        "test_fh007_composite_detects_branch_first_precedence",
    ),
    "FH-008": (
        "tests.test_commit_resolution_differential.CommitDirectionTests."
        "test_bare_and_full_result_resolution_use_same_policy"
    ),
    "FH-009": (
        "tests.test_commit_resolution.TestHistoricalIssueRegistry."
        "test_issue_on_another_checkout_is_registered"
    ),
    "FH-010": (
        "tests.test_commit_graph.SnapshotTests."
        "test_merge_base_distinguishes_no_base_from_failure"
    ),
    "FH-011": (
        "tests.test_commit_graph.ForkPointInvariantTests."
        "test_disconnected_ref_does_not_change_connected_topic"
    ),
    "FH-012": (
        "tests.test_commit_graph.ForkPointInvariantTests."
        "test_same_tail_slash_ref_stays_a_distinct_equivalent_base_ref"
    ),
    "FH-013": (
        "tests.test_commit_graph.ForkPointInvariantTests."
        "test_incomparable_maximal_forks_are_scoped_to_topic"
    ),
    "FH-014": (
        "tests.test_commit_resolution.DiagnosticProjectionTests."
        "test_ref_inventory_failure_is_structured_and_fails_closed",
        "tests.test_commit_resolution_parity.SharedOwnershipTests."
        "test_live_resolution_has_no_global_base_election_or_origin_head_probe",
    ),
    "FH-015": (
        "tests.test_commit_resolution.MergeClaimInvariantTests."
        "test_deleted_refs_keep_boundary_but_not_unproven_content"
    ),
    "FH-016": (
        "tests.test_commit_resolution.MergeClaimInvariantTests."
        "test_two_parent_multi_name_subject_does_not_relabel_side"
    ),
    "FH-017": (
        "tests.test_commit_graph.ForkPointInvariantTests."
        "test_advancing_trunk_does_not_change_fork_point"
    ),
    "FH-018": (
        "tests.test_linkage_check.FindUnlinkedBehaviorCommitsTests."
        "test_out_of_range_ambiguity_does_not_fail_release_linkage"
    ),
    "FH-019": (
        "tests.test_commit_graph.SnapshotTests."
        "test_loads_log_and_refs_once",
        "tests.test_commit_resolution.DiagnosticProjectionTests."
        "test_build_result_separates_fatal_errors_from_diagnostics",
        "tests.test_commit_resolution.DiagnosticProjectionTests."
        "test_ref_inventory_failure_is_structured_and_fails_closed",
        "tests.test_commit_graph.SnapshotTests."
        "test_merge_base_distinguishes_no_base_from_failure",
        "tests.test_commit_graph.SnapshotTests."
        "test_terminated_ancestry_query_is_a_failure",
        "tests.test_commit_resolution.TestGraphQueryFailures."
        "test_branch_membership_rejects_a_terminated_merge_base_query",
        "tests.test_commit_resolution.TestGraphQueryFailures."
        "test_rev_list_failure_surfaces_and_does_not_attribute",
        "tests.test_commit_graph.SnapshotTests."
        "test_merge_base_rejects_empty_or_multitoken_success_output",
        "tests.test_commit_resolution.TestRangeProjection."
        "test_range_projection_rejects_multi_token_success_output",
        "tests.test_commit_resolution_differential.CommitDirectionTests."
        "test_bare_and_full_result_resolution_use_same_policy",
    ),
    "FH-020": (
        "tests.test_commit_resolution_differential.DeclarationCoverageTests."
        "test_declared_trailer_disagrees_with_branch",
        "tests.test_commit_resolution_differential.GroundTruthTests."
        "test_trailer_disagrees_with_branch",
        "tests.test_commit_resolution_differential.DeclarationSanityTests."
        "test_some_shape_declares_real_work",
        "tests.test_commit_resolution_differential.DeclarationSanityTests."
        "test_no_reference_oracle_remains",
        "tests.test_commit_resolution.MergeClaimInvariantTests."
        "test_subject_token_order_does_not_change_content",
    ),
    "FH-021": (
        "tests.test_linkage_check.ResolveIssueForCommitTests."
        "test_trailer_resolution"
    ),
    "FH-022": (
        "tests.test_commit_graph.SnapshotTests."
        "test_merge_base_rejects_empty_or_multitoken_success_output"
    ),
    "FH-023": (
        "tests.test_commit_graph.ForkPointInvariantTests."
        "test_snapshot_ref_movement_uses_captured_object_ids"
    ),
    "FH-024": (
        "tests.test_commit_graph.ForkPointInvariantTests."
        "test_criss_cross_best_bases_fail_closed_as_ambiguous"
    ),
    "FH-025": (
        "tests.test_commit_graph.ForkPointInvariantTests."
        "test_newer_comparable_candidate_is_the_unique_maximal_fork"
    ),
    "FH-026": (
        "tests.test_commit_resolution.ProcessGateInvariantTests."
        "test_t08_audit_evidence_records_terminal_exit_and_summary",
        "tests.test_commit_resolution.FailureInvariantMutationTests."
        "test_fh026_current_audit_block_removal_is_detected",
    ),
    "FH-027": (
        "tests.test_linkage_check.ResolveIssueForCommitTests."
        "test_trailer_resolution",
        "tests.test_linkage_check.ResolveIssueForCommitTests."
        "test_branch_resolution",
        "tests.test_linkage_check.ResolveIssueForCommitTests."
        "test_snapshot_failure_surfaces_structured_fatal_error",
        "tests.test_linkage_check.ResolveIssueForCommitTests."
        "test_trailer_beats_branch_on_conflict",
    ),
    "FH-028": (
        "tests.test_commit_graph.TopicDeltaTests."
        "test_cached_topology_failure_reaches_membership_on_every_build"
    ),
    "FH-029": (
        "tests.test_commit_graph.TopicDeltaTests."
        "test_publication_recovery_ignores_unrelated_history_for_command_count"
    ),
    "FH-030": (
        "tests.test_commit_resolution_parity.SharedOwnershipTests."
        "test_live_resolution_has_no_global_base_election_or_origin_head_probe"
    ),
    "FH-031": (
        "tests.test_commit_resolution.TestRangeProjection."
        "test_live_range_projects_only_target_topic"
    ),
    "FH-032": (
        "tests.test_commit_resolution.DiagnosticProjectionTests."
        "test_compatibility_errors_dedupe_in_first_seen_order",
        "tests.test_commit_resolution.DiagnosticProjectionTests."
        "test_octopus_duplicate_diagnostics_have_one_compatibility_error",
        "tests.test_commit_resolution.DiagnosticProjectionTests."
        "test_multi_name_duplicate_diagnostics_have_one_compatibility_error",
    ),
    "FH-033": (
        "tests.test_commit_resolution.FailureInvariantMutationTests."
        "test_fh001_composite_detects_broken_issue_to_commits",
        "tests.test_commit_resolution.FailureInvariantMutationTests."
        "test_fh001_composite_detects_same_wrong_commit_issue",
        "tests.test_commit_resolution.FailureInvariantMutationTests."
        "test_fh007_composite_detects_branch_first_precedence",
        "tests.test_commit_resolution.FailureInvariantMutationTests."
        "test_fh026_current_audit_block_removal_is_detected",
        "tests.test_commit_resolution.FailureInvariantMutationTests."
        "test_fh033_required_manifest_detects_removed_fh001_commit_truth",
    ),
    "FH-034": (
        "tests.test_commit_resolution.FailureEvidenceInvariantTests."
        "test_fh026_preserves_historical_regression_state",
        "tests.test_commit_resolution.FailureEvidenceInvariantTests."
        "test_fh033_records_first_remediation_commit_and_qualified_evidence",
        "tests.test_commit_resolution.FailureEvidenceInvariantTests."
        "test_fh034_record_declares_append_only_remediation_contract",
        "tests.test_commit_resolution.FailureEvidenceInvariantTests."
        "test_fh036_record_names_qualified_manifest_acceptance",
    ),
    "FH-035": (
        "tests.test_commit_resolution.ProcessGateInvariantTests."
        "test_t08_audit_evidence_records_terminal_exit_and_summary",
        "tests.test_commit_resolution.FailureEvidenceInvariantTests."
        "test_fh034_record_declares_append_only_remediation_contract",
        "tests.test_commit_resolution.FailureInvariantMutationTests."
        "test_fh026_current_audit_block_removal_is_detected",
    ),
    "FH-036": (
        "tests.test_commit_resolution.FailureInvariantMutationTests."
        "test_fh036_every_declared_component_deletion_is_detected",
        "tests.test_commit_resolution.FailureEvidenceInvariantTests."
        "test_fh036_record_names_qualified_manifest_acceptance",
    ),
    "FH-037": (
        "tests.test_commit_resolution.FailureInvariantMutationTests."
        "test_fh037_named_loader_uses_explicit_owner_module_globals",
        "tests.test_commit_resolution.FailureEvidenceInvariantTests."
        "test_fh037_record_names_qualified_module_identity_evidence",
    ),
    "FH-038": (
        "tests.test_commit_resolution.TestDetachedHead."
        "test_trailer_resolves_and_branch_gap_is_reported",
        "tests.test_commit_resolution.TestDetachedHead."
        "test_untrailed_detached_commit_reports_branch_limitation",
        "tests.test_commit_resolution.TestDetachedHead."
        "test_attached_unrelated_commit_has_no_detached_limitation",
        "tests.test_commit_resolution.TestDetachedHead."
        "test_detached_limitation_has_bare_indexed_parity",
    ),
    "FH-039": (
        "tests.test_commit_graph.HeadStateBoundaryTests."
        "test_symbolic_ref_rc1_is_detached_and_reads_valid_head_sha",
        "tests.test_commit_graph.HeadStateBoundaryTests."
        "test_symbolic_ref_failure_and_termination_are_fatal",
        "tests.test_commit_graph.HeadStateBoundaryTests."
        "test_symbolic_ref_malformed_success_fails_closed",
        "tests.test_commit_graph.HeadStateBoundaryTests."
        "test_detached_head_sha_failure_and_termination_are_fatal",
        "tests.test_commit_graph.HeadStateBoundaryTests."
        "test_detached_head_sha_malformed_success_fails_closed",
        "tests.test_commit_resolution.HeadStateBoundaryProjectionTests."
        "test_symbolic_ref_failure_projects_fatal_without_detached_diagnostic",
        "tests.test_commit_resolution.HeadStateBoundaryProjectionTests."
        "test_detached_sha_failure_projects_fatal_without_detached_diagnostic",
        "tests.test_commit_resolution.TestDetachedHead."
        "test_trailer_resolves_and_branch_gap_is_reported",
    ),
    "FH-040": (
        "tests.test_commit_graph.ForkPointInvariantTests."
        "test_incomparable_non_topic_side_ref_is_attribution_neutral",
        "tests.test_commit_resolution.FailureInvariantMutationTests."
        "test_fh040_composite_detects_removed_side_ref_provenance",
    ),
}

REQUIRED_FAILURE_COMPONENTS = {}
REQUIRED_FAILURE_COMPONENTS.update({
    "FH-001": frozenset(
        {
            "tests.test_commit_resolution.CommitDirectionTruthTests."
            "test_bare_and_indexed_resolution_match_declared_truth",
            "tests.test_commit_resolution_differential.CommitDirectionTests."
            "test_bare_and_full_result_resolution_use_same_policy",
            "tests.test_commit_resolution_differential.GroundTruthTests."
            "test_trailer_disagrees_with_branch",
            "tests.test_commit_resolution.FailureInvariantMutationTests."
            "test_fh001_composite_detects_broken_issue_to_commits",
            "tests.test_commit_resolution.FailureInvariantMutationTests."
            "test_fh001_composite_detects_same_wrong_commit_issue",
        }
    ),
    "FH-007": frozenset(
        {
            "tests.test_commit_resolution.SourcePrecedenceInvariantTests."
            "test_complete_precedence_chain",
            "tests.test_commit_resolution_differential.CommitDirectionTests."
            "test_bare_and_full_result_resolution_use_same_policy",
            "tests.test_commit_resolution.FailureInvariantMutationTests."
            "test_fh007_composite_detects_branch_first_precedence",
        }
    ),
    "FH-014": frozenset(
        {
            "tests.test_commit_resolution.DiagnosticProjectionTests."
            "test_ref_inventory_failure_is_structured_and_fails_closed",
            "tests.test_commit_resolution_parity.SharedOwnershipTests."
            "test_live_resolution_has_no_global_base_election_or_origin_head_probe",
        }
    ),
    "FH-019": frozenset(
        {
            "tests.test_commit_graph.SnapshotTests.test_loads_log_and_refs_once",
            "tests.test_commit_resolution.DiagnosticProjectionTests."
            "test_build_result_separates_fatal_errors_from_diagnostics",
            "tests.test_commit_resolution.DiagnosticProjectionTests."
            "test_ref_inventory_failure_is_structured_and_fails_closed",
            "tests.test_commit_graph.SnapshotTests."
            "test_merge_base_distinguishes_no_base_from_failure",
            "tests.test_commit_graph.SnapshotTests."
            "test_terminated_ancestry_query_is_a_failure",
            "tests.test_commit_resolution.TestGraphQueryFailures."
            "test_branch_membership_rejects_a_terminated_merge_base_query",
            "tests.test_commit_resolution.TestGraphQueryFailures."
            "test_rev_list_failure_surfaces_and_does_not_attribute",
            "tests.test_commit_graph.SnapshotTests."
            "test_merge_base_rejects_empty_or_multitoken_success_output",
            "tests.test_commit_resolution.TestRangeProjection."
            "test_range_projection_rejects_multi_token_success_output",
            "tests.test_commit_resolution_differential.CommitDirectionTests."
            "test_bare_and_full_result_resolution_use_same_policy",
        }
    ),
    "FH-020": frozenset(
        {
            "tests.test_commit_resolution_differential.DeclarationCoverageTests."
            "test_declared_trailer_disagrees_with_branch",
            "tests.test_commit_resolution_differential.GroundTruthTests."
            "test_trailer_disagrees_with_branch",
            "tests.test_commit_resolution_differential.DeclarationSanityTests."
            "test_some_shape_declares_real_work",
            "tests.test_commit_resolution_differential.DeclarationSanityTests."
            "test_no_reference_oracle_remains",
            "tests.test_commit_resolution.MergeClaimInvariantTests."
            "test_subject_token_order_does_not_change_content",
        }
    ),
    "FH-026": frozenset(
        {
            "tests.test_commit_resolution.ProcessGateInvariantTests."
            "test_t08_audit_evidence_records_terminal_exit_and_summary",
            "tests.test_commit_resolution.FailureInvariantMutationTests."
            "test_fh026_current_audit_block_removal_is_detected",
        }
    ),
    "FH-027": frozenset(
        {
            "tests.test_linkage_check.ResolveIssueForCommitTests."
            "test_trailer_resolution",
            "tests.test_linkage_check.ResolveIssueForCommitTests."
            "test_branch_resolution",
            "tests.test_linkage_check.ResolveIssueForCommitTests."
            "test_snapshot_failure_surfaces_structured_fatal_error",
            "tests.test_linkage_check.ResolveIssueForCommitTests."
            "test_trailer_beats_branch_on_conflict",
        }
    ),
    "FH-032": frozenset(
        {
            "tests.test_commit_resolution.DiagnosticProjectionTests."
            "test_compatibility_errors_dedupe_in_first_seen_order",
            "tests.test_commit_resolution.DiagnosticProjectionTests."
            "test_octopus_duplicate_diagnostics_have_one_compatibility_error",
            "tests.test_commit_resolution.DiagnosticProjectionTests."
            "test_multi_name_duplicate_diagnostics_have_one_compatibility_error",
        }
    ),
    "FH-033": frozenset(
        {
            "tests.test_commit_resolution.FailureInvariantMutationTests."
            "test_fh001_composite_detects_broken_issue_to_commits",
            "tests.test_commit_resolution.FailureInvariantMutationTests."
            "test_fh001_composite_detects_same_wrong_commit_issue",
            "tests.test_commit_resolution.FailureInvariantMutationTests."
            "test_fh007_composite_detects_branch_first_precedence",
            "tests.test_commit_resolution.FailureInvariantMutationTests."
            "test_fh026_current_audit_block_removal_is_detected",
            "tests.test_commit_resolution.FailureInvariantMutationTests."
            "test_fh033_required_manifest_detects_removed_fh001_commit_truth",
        }
    ),
    "FH-034": frozenset(
        {
            "tests.test_commit_resolution.FailureEvidenceInvariantTests."
            "test_fh026_preserves_historical_regression_state",
            "tests.test_commit_resolution.FailureEvidenceInvariantTests."
            "test_fh033_records_first_remediation_commit_and_qualified_evidence",
            "tests.test_commit_resolution.FailureEvidenceInvariantTests."
            "test_fh034_record_declares_append_only_remediation_contract",
            "tests.test_commit_resolution.FailureEvidenceInvariantTests."
            "test_fh036_record_names_qualified_manifest_acceptance",
        }
    ),
    "FH-002": frozenset(
        {
            "tests.test_commit_graph.TopicDeltaTests."
            "test_base_history_is_not_topic_work",
        }
    ),
    "FH-003": frozenset(
        {
            "tests.test_commit_graph.TopicDeltaTests."
            "test_published_no_ff_topic_recovers_pre_publication_fork",
        }
    ),
    "FH-004": frozenset(
        {
            "tests.test_commit_resolution.MergeClaimInvariantTests."
            "test_subject_token_order_does_not_change_content",
        }
    ),
    "FH-005": frozenset(
        {
            "tests.test_commit_graph.TopicDeltaTests."
            "test_stacked_issue_excludes_inner_content",
        }
    ),
    "FH-006": frozenset(
        {
            "tests.test_commit_graph.ForkPointInvariantTests."
            "test_advancing_trunk_does_not_change_fork_point",
        }
    ),
    "FH-008": frozenset(
        {
            "tests.test_commit_resolution_differential.CommitDirectionTests."
            "test_bare_and_full_result_resolution_use_same_policy",
        }
    ),
    "FH-009": frozenset(
        {
            "tests.test_commit_resolution.TestHistoricalIssueRegistry."
            "test_issue_on_another_checkout_is_registered",
        }
    ),
    "FH-010": frozenset(
        {
            "tests.test_commit_graph.SnapshotTests."
            "test_merge_base_distinguishes_no_base_from_failure",
        }
    ),
    "FH-011": frozenset(
        {
            "tests.test_commit_graph.ForkPointInvariantTests."
            "test_disconnected_ref_does_not_change_connected_topic",
        }
    ),
    "FH-012": frozenset(
        {
            "tests.test_commit_graph.ForkPointInvariantTests."
            "test_same_tail_slash_ref_stays_a_distinct_equivalent_base_ref",
        }
    ),
    "FH-013": frozenset(
        {
            "tests.test_commit_graph.ForkPointInvariantTests."
            "test_incomparable_maximal_forks_are_scoped_to_topic",
        }
    ),
    "FH-015": frozenset(
        {
            "tests.test_commit_resolution.MergeClaimInvariantTests."
            "test_deleted_refs_keep_boundary_but_not_unproven_content",
        }
    ),
    "FH-016": frozenset(
        {
            "tests.test_commit_resolution.MergeClaimInvariantTests."
            "test_two_parent_multi_name_subject_does_not_relabel_side",
        }
    ),
    "FH-017": frozenset(
        {
            "tests.test_commit_graph.ForkPointInvariantTests."
            "test_advancing_trunk_does_not_change_fork_point",
        }
    ),
    "FH-018": frozenset(
        {
            "tests.test_linkage_check.FindUnlinkedBehaviorCommitsTests."
            "test_out_of_range_ambiguity_does_not_fail_release_linkage",
        }
    ),
    "FH-021": frozenset(
        {
            "tests.test_linkage_check.ResolveIssueForCommitTests."
            "test_trailer_resolution",
        }
    ),
    "FH-022": frozenset(
        {
            "tests.test_commit_graph.SnapshotTests."
            "test_merge_base_rejects_empty_or_multitoken_success_output",
        }
    ),
    "FH-023": frozenset(
        {
            "tests.test_commit_graph.ForkPointInvariantTests."
            "test_snapshot_ref_movement_uses_captured_object_ids",
        }
    ),
    "FH-024": frozenset(
        {
            "tests.test_commit_graph.ForkPointInvariantTests."
            "test_criss_cross_best_bases_fail_closed_as_ambiguous",
        }
    ),
    "FH-025": frozenset(
        {
            "tests.test_commit_graph.ForkPointInvariantTests."
            "test_newer_comparable_candidate_is_the_unique_maximal_fork",
        }
    ),
    "FH-028": frozenset(
        {
            "tests.test_commit_graph.TopicDeltaTests."
            "test_cached_topology_failure_reaches_membership_on_every_build",
        }
    ),
    "FH-029": frozenset(
        {
            "tests.test_commit_graph.TopicDeltaTests."
            "test_publication_recovery_ignores_unrelated_history_for_command_count",
        }
    ),
    "FH-030": frozenset(
        {
            "tests.test_commit_resolution_parity.SharedOwnershipTests."
            "test_live_resolution_has_no_global_base_election_or_origin_head_probe",
        }
    ),
    "FH-031": frozenset(
        {
            "tests.test_commit_resolution.TestRangeProjection."
            "test_live_range_projects_only_target_topic",
        }
    ),
    "FH-035": frozenset(
        {
            "tests.test_commit_resolution.ProcessGateInvariantTests."
            "test_t08_audit_evidence_records_terminal_exit_and_summary",
            "tests.test_commit_resolution.FailureEvidenceInvariantTests."
            "test_fh034_record_declares_append_only_remediation_contract",
            "tests.test_commit_resolution.FailureInvariantMutationTests."
            "test_fh026_current_audit_block_removal_is_detected",
        }
    ),
    "FH-036": frozenset(
        {
            "tests.test_commit_resolution.FailureInvariantMutationTests."
            "test_fh036_every_declared_component_deletion_is_detected",
            "tests.test_commit_resolution.FailureEvidenceInvariantTests."
            "test_fh036_record_names_qualified_manifest_acceptance",
        }
    ),
    "FH-037": frozenset(
        {
            "tests.test_commit_resolution.FailureInvariantMutationTests."
            "test_fh037_named_loader_uses_explicit_owner_module_globals",
            "tests.test_commit_resolution.FailureEvidenceInvariantTests."
            "test_fh037_record_names_qualified_module_identity_evidence",
        }
    ),
    "FH-038": frozenset(
        {
            "tests.test_commit_resolution.TestDetachedHead."
            "test_trailer_resolves_and_branch_gap_is_reported",
            "tests.test_commit_resolution.TestDetachedHead."
            "test_untrailed_detached_commit_reports_branch_limitation",
            "tests.test_commit_resolution.TestDetachedHead."
            "test_attached_unrelated_commit_has_no_detached_limitation",
            "tests.test_commit_resolution.TestDetachedHead."
            "test_detached_limitation_has_bare_indexed_parity",
        }
    ),
    "FH-039": frozenset(
        {
            "tests.test_commit_graph.HeadStateBoundaryTests."
            "test_symbolic_ref_rc1_is_detached_and_reads_valid_head_sha",
            "tests.test_commit_graph.HeadStateBoundaryTests."
            "test_symbolic_ref_failure_and_termination_are_fatal",
            "tests.test_commit_graph.HeadStateBoundaryTests."
            "test_symbolic_ref_malformed_success_fails_closed",
            "tests.test_commit_graph.HeadStateBoundaryTests."
            "test_detached_head_sha_failure_and_termination_are_fatal",
            "tests.test_commit_graph.HeadStateBoundaryTests."
            "test_detached_head_sha_malformed_success_fails_closed",
            "tests.test_commit_resolution.HeadStateBoundaryProjectionTests."
            "test_symbolic_ref_failure_projects_fatal_without_detached_diagnostic",
            "tests.test_commit_resolution.HeadStateBoundaryProjectionTests."
            "test_detached_sha_failure_projects_fatal_without_detached_diagnostic",
            "tests.test_commit_resolution.TestDetachedHead."
            "test_trailer_resolves_and_branch_gap_is_reported",
        }
    ),
    "FH-040": frozenset(
        {
            "tests.test_commit_graph.ForkPointInvariantTests."
            "test_incomparable_non_topic_side_ref_is_attribution_neutral",
            "tests.test_commit_resolution.FailureInvariantMutationTests."
            "test_fh040_composite_detects_removed_side_ref_provenance",
        }
    ),
})


def _failure_corpus():
    return Path(
        "specs/095-commit-issue-resolution-parity/failure-history.md"
    ).read_text(encoding="utf-8")


def _mapped_test_names(mapped):
    return (mapped,) if isinstance(mapped, str) else tuple(mapped)


def _run_named_tests(names, *, owner_module=None):
    if owner_module is None:
        owner_module = sys.modules[__name__]
    owner_prefix = "tests.test_commit_resolution."
    suite = unittest.TestSuite()
    for name in names:
        if name.startswith(owner_prefix):
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromName(
                    name.removeprefix(owner_prefix),
                    owner_module,
                )
            )
        else:
            suite.addTests(unittest.defaultTestLoader.loadTestsFromName(name))
    result = unittest.TestResult()
    suite.run(result)
    return result


def _test_result_details(result):
    problems = [
        f"{test.id()}: {traceback.splitlines()[-1]}"
        for test, traceback in result.failures + result.errors
    ]
    problems.extend(f"{test.id()}: skipped: {reason}" for test, reason in result.skipped)
    return "\n".join(problems)


def _required_component_gaps(mapping):
    gaps = {}
    for failure_id, required in REQUIRED_FAILURE_COMPONENTS.items():
        actual = set(_mapped_test_names(mapping.get(failure_id, ())))
        missing = sorted(required - actual)
        if missing:
            gaps[failure_id] = missing
    return gaps


def resolve_shape(name):
    """Resolve a fixture shape by stable subject instead of repository SHA."""
    with GitRepo(**shapes.REPO_KWARGS.get(name, {})) as repo:
        shapes.ALL_SHAPES[name](repo)
        built = cr.build_attribution(repo.runner, repo.path)
        content_owners = {}
        declared_content_owners = {}
        boundary_issues = set()
        for sha, record in built["records"].items():
            actual = frozenset((built["attribution"].get(sha) or {}).keys())
            if len(record["parents"]) < 2:
                content_owners[record["subject"]] = actual
                declared_content_owners[record["subject"]] = repo.truth[sha]
            else:
                boundary_issues.update(actual)
        return {
            "content_owners": content_owners,
            "declared_content_owners": declared_content_owners,
            "boundary_issues": boundary_issues,
            "diagnostics": built["diagnostics"],
        }


class SourcePrecedenceInvariantTests(unittest.TestCase):
    def test_complete_precedence_chain(self):
        """FH-007: trailer > branch > merge-subject, through one finalizer."""
        records = {"sha": {"parents": []}}

        def claim(issue_id, source):
            return {
                "issue_id": issue_id,
                "source": source,
                "kind": "content",
            }

        trailer = claim(shapes.ALPHA, "trailer")
        branch = claim(shapes.BETA, "branch")
        merge_subject = claim(shapes.GAMMA, "merge-subject")

        self.assertEqual(
            cr.SOURCE_PRECEDENCE,
            ("trailer", "branch", "merge-subject"),
        )
        self.assertEqual(
            cr.finalize_claims(
                records,
                {"sha": [merge_subject, branch, trailer]},
            ),
            {"sha": {shapes.ALPHA: "trailer"}},
        )
        self.assertEqual(
            cr.finalize_claims(records, {"sha": [merge_subject, branch]}),
            {"sha": {shapes.BETA: "branch"}},
        )
        self.assertEqual(
            cr.finalize_claims(records, {"sha": [merge_subject]}),
            {"sha": {shapes.GAMMA: "merge-subject"}},
        )


class CommitDirectionTruthTests(unittest.TestCase):
    def test_bare_and_indexed_resolution_match_declared_truth(self):
        """FH-001: both commit directions must match literal fixture truth."""
        with GitRepo() as repo:
            shapes.trailer_disagrees_with_branch(repo)
            conflict = next(
                sha
                for sha, expected in repo.truth.items()
                if expected == frozenset({shapes.BETA})
            )
            expected_issue = next(iter(repo.truth[conflict]))
            built = cr.build_attribution(
                repo.runner,
                repo.path,
                target_shas={conflict},
            )
            bare = cr.resolve_issue_for_commit(
                repo.runner,
                repo.path,
                conflict,
            )
            indexed = cr.resolve_issue_for_commit(
                repo.runner,
                repo.path,
                conflict,
                attribution=built,
            )

        for label, result in (("bare", bare), ("indexed", indexed)):
            with self.subTest(call_shape=label):
                self.assertEqual(result["issue_id"], expected_issue)
                self.assertEqual(result["source"], "trailer")


class FailureEvidenceInvariantTests(unittest.TestCase):
    def _failure_section(self, failure_id, next_heading):
        return _failure_corpus().split(
            f"### {failure_id}", 1
        )[1].split(next_heading, 1)[0]

    def test_fh026_preserves_historical_regression_state(self):
        """FH-034: reopening FH-026 cannot erase its captured prior state."""
        section = self._failure_section("FH-026", "### FH-027")

        self.assertIn(
            "**Historical state (preserved)**: regression captured.",
            section,
        )
        self.assertEqual(section.count("- **Status**:"), 1)

    def test_fh033_records_first_remediation_commit_and_qualified_evidence(self):
        """FH-034: FH-033 names the exact prior fix and executable proof."""
        section = self._failure_section("FH-033", "### FH-034")

        self.assertIn("`04bae8d`", section)
        self.assertIn("`910a19c`", section)
        self.assertIn(
            "`CommitDirectionTruthTests."
            "test_bare_and_indexed_resolution_match_declared_truth`",
            section,
        )
        self.assertIn(
            "`FailureInvariantMutationTests."
            "test_fh033_required_manifest_detects_removed_fh001_commit_truth`",
            section,
        )
        self.assertEqual(section.count("- **Status**:"), 1)

    def test_fh034_record_declares_append_only_remediation_contract(self):
        """FH-034: the corpus declares preservation plus exact fix evidence."""
        section = self._failure_section(
            "FH-034",
            "### FH-035",
        )

        self.assertIn("preserves prior status text as history", section)
        self.assertIn("exact fixing commit", section)
        self.assertIn("qualified executable test evidence", section)
        self.assertIn("`910a19c`", section)
        self.assertIn(
            "`FailureEvidenceInvariantTests."
            "test_fh026_preserves_historical_regression_state`",
            section,
        )
        self.assertIn(
            "`FailureEvidenceInvariantTests."
            "test_fh033_records_first_remediation_commit_and_qualified_evidence`",
            section,
        )
        self.assertIn(
            "terminal exit 0: 350 tests passed in 223.391 seconds",
            section,
        )
        self.assertEqual(section.count("- **Status**:"), 1)

    def test_fh036_record_names_qualified_manifest_acceptance(self):
        """FH-034/FH-036: manifest evidence names its executable proof."""
        section = self._failure_section(
            "FH-036",
            "### FH-037",
        )

        self.assertIn("`d9cdb2d`", section)
        self.assertIn(
            "`FailureInvariantMutationTests."
            "test_fh036_every_declared_component_deletion_is_detected`",
            section,
        )
        self.assertIn(
            "`FailureHistoryTraceabilityTests."
            "test_required_mapping_components_are_present`",
            section,
        )
        self.assertEqual(section.count("- **Status**:"), 1)

    def test_fh037_record_names_qualified_module_identity_evidence(self):
        """FH-037: the corpus names the exact fix, proof, and full gate."""
        section = self._failure_section(
            "FH-037",
            "### FH-038",
        )

        self.assertIn("`5d1509a`", section)
        self.assertIn(
            "`tests.test_commit_resolution.FailureInvariantMutationTests."
            "test_fh037_named_loader_uses_explicit_owner_module_globals`",
            section,
        )
        self.assertIn("`python3 -m unittest discover -s tests`", section)
        self.assertIn(
            "final terminal exit 0: 1018 tests passed in 289.178 seconds",
            section,
        )
        self.assertEqual(section.count("- **Status**:"), 1)


class ProcessGateInvariantTests(unittest.TestCase):
    def test_t08_audit_evidence_records_terminal_exit_and_summary(self):
        """FH-026: the current T08 block must contain terminal gate evidence."""
        section = _failure_corpus().split(
            "### FH-026", 1
        )[1].split("### FH-027", 1)[0]
        marker = "- **T08 I3 terminal evidence**:"

        self.assertEqual(section.count(marker), 1)
        evidence = section.split(marker, 1)[1].split("\n- **", 1)[0]
        self.assertRegex(evidence, r"six\s+Issue\s+095\s+suites")
        self.assertRegex(
            evidence,
            r"terminal\s+exit\s+0:\s+\d+\s+tests\s+passed\s+in\s+"
            r"\d+(?:\.\d+)?\s+seconds",
        )


class FailureInvariantMutationTests(unittest.TestCase):
    def test_fh037_named_loader_uses_explicit_owner_module_globals(self):
        """FH-037: nested tests execute against their supplied owner module."""
        owner = types.ModuleType("discovered_test_commit_resolution")
        owner.sentinel = "mutated"

        class ProbeTests(unittest.TestCase):
            def test_reads_owner_module_globals(self):
                self.assertEqual(owner.sentinel, "original")

        owner.ProbeTests = ProbeTests
        result = _run_named_tests(
            (
                "tests.test_commit_resolution.ProbeTests."
                "test_reads_owner_module_globals",
            ),
            owner_module=owner,
        )

        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.failures), 1)
        self.assertFalse(result.wasSuccessful())

    def test_fh040_composite_detects_removed_side_ref_provenance(self):
        """FH-040: disabling provenance filtering turns the invariant red."""
        original = cr.commit_graph._unproven_side_ref_forks
        try:
            cr.commit_graph._unproven_side_ref_forks = (
                lambda *args, **kwargs: (set(), [])
            )
            result = _run_named_tests(
                (
                    "tests.test_commit_graph.ForkPointInvariantTests."
                    "test_incomparable_non_topic_side_ref_is_attribution_neutral",
                )
            )
        finally:
            cr.commit_graph._unproven_side_ref_forks = original

        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.failures), 1)
        self.assertFalse(result.wasSuccessful())

    def test_fh001_composite_detects_broken_issue_to_commits(self):
        """FH-033: FH-001 fails when issue-to-commits returns no ownership."""
        differential = importlib.import_module(
            "tests.test_commit_resolution_differential"
        )
        original = differential.cr.resolve_commits_for_issue
        try:
            differential.cr.resolve_commits_for_issue = (
                lambda *args, **kwargs: {"commits": []}
            )
            result = _run_named_tests(
                (
                    "tests.test_commit_resolution_differential.GroundTruthTests."
                    "test_trailer_disagrees_with_branch",
                )
            )
        finally:
            differential.cr.resolve_commits_for_issue = original

        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.failures), 1)
        self.assertFalse(result.wasSuccessful())

    def test_fh001_composite_detects_same_wrong_commit_issue(self):
        """FH-033: FH-001 rejects matching bare/indexed wrong ownership."""
        original = cr.resolve_issue_for_commit
        try:
            cr.resolve_issue_for_commit = lambda *args, **kwargs: {
                "sha": args[2],
                "issue_id": shapes.ALPHA,
                "source": "branch",
                "fatal_errors": [],
                "diagnostics": [],
                "degraded": [],
                "errors": [],
            }
            result = _run_named_tests(
                (
                    "tests.test_commit_resolution.CommitDirectionTruthTests."
                    "test_bare_and_indexed_resolution_match_declared_truth",
                )
            )
        finally:
            cr.resolve_issue_for_commit = original

        self.assertEqual(result.errors, [])
        self.assertEqual(
            len(result.failures),
            2,
            "both bare and indexed truth assertions must reject the same wrong issue",
        )
        self.assertFalse(result.wasSuccessful())

    def test_fh007_composite_detects_branch_first_precedence(self):
        """FH-033: FH-007 fails under branch > trailer precedence."""
        original = cr.SOURCE_PRECEDENCE
        try:
            cr.SOURCE_PRECEDENCE = ("branch", "trailer", "merge-subject")
            result = _run_named_tests(
                (
                    "tests.test_commit_resolution.SourcePrecedenceInvariantTests."
                    "test_complete_precedence_chain",
                )
            )
        finally:
            cr.SOURCE_PRECEDENCE = original

        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.failures), 1)
        self.assertFalse(result.wasSuccessful())

    def test_fh026_current_audit_block_removal_is_detected(self):
        """FH-033: FH-026 fails when the current T08 evidence is removed."""
        corpus = _failure_corpus()
        mutated = re.sub(
            r"\n- \*\*T08 I3 terminal evidence\*\*:.*?(?=\n- \*\*)",
            "",
            corpus,
            count=1,
            flags=re.DOTALL,
        )
        self.assertNotEqual(mutated, corpus)

        original = globals()["_failure_corpus"]
        try:
            globals()["_failure_corpus"] = lambda: mutated
            result = _run_named_tests(
                (
                    "tests.test_commit_resolution.ProcessGateInvariantTests."
                    "test_t08_audit_evidence_records_terminal_exit_and_summary",
                )
            )
        finally:
            globals()["_failure_corpus"] = original

        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.failures), 1)
        self.assertFalse(result.wasSuccessful())

    def test_fh033_required_manifest_detects_removed_fh001_commit_truth(self):
        """FH-033: deleting a required FH-001 component turns the audit red."""
        required = (
            "tests.test_commit_resolution.CommitDirectionTruthTests."
            "test_bare_and_indexed_resolution_match_declared_truth"
        )
        mutated = dict(FAILURE_INVARIANT_TESTS)
        mutated["FH-001"] = tuple(
            name
            for name in _mapped_test_names(mutated["FH-001"])
            if name != required
        )
        self.assertNotIn(required, mutated["FH-001"])

        original = globals()["FAILURE_INVARIANT_TESTS"]
        try:
            globals()["FAILURE_INVARIANT_TESTS"] = mutated
            result = _run_named_tests(
                (
                    "tests.test_commit_resolution.FailureHistoryTraceabilityTests."
                    "test_required_mapping_components_are_present",
                )
            )
        finally:
            globals()["FAILURE_INVARIANT_TESTS"] = original

        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.failures), 1)
        self.assertFalse(result.wasSuccessful())

    def test_fh036_every_declared_component_deletion_is_detected(self):
        """FH-036: every canonical component is independent and mandatory."""
        source = Path(__file__).read_text(encoding="utf-8")
        manifest_source = source.split(
            "REQUIRED_FAILURE_COMPONENTS =", 1
        )[1].split("\n\ndef _failure_corpus", 1)[0]
        self.assertNotIn(
            "FAILURE_INVARIANT_TESTS",
            manifest_source,
            "the canonical manifest must not be derived from the mutable map",
        )

        for failure_id, required in REQUIRED_FAILURE_COMPONENTS.items():
            for component in required:
                with self.subTest(
                    failure_id=failure_id,
                    removed=component,
                ):
                    mutated = dict(FAILURE_INVARIANT_TESTS)
                    mutated[failure_id] = tuple(
                        name
                        for name in _mapped_test_names(mutated[failure_id])
                        if name != component
                    )
                    self.assertEqual(
                        _required_component_gaps(mutated),
                        {failure_id: [component]},
                    )


class FailureHistoryTraceabilityTests(unittest.TestCase):
    def test_every_open_or_redesign_failure_has_a_test_reference(self):
        corpus = _failure_corpus()
        tests = "\n".join(
            path.read_text(encoding="utf-8")
            for path in Path("tests").glob("test_commit*.py")
        ) + Path("tests/test_linkage_check.py").read_text(
            encoding="utf-8"
        ) + Path("tests/test_project_converge.py").read_text(
            encoding="utf-8"
        )
        required = re.findall(
            r"\|\s*(FH-\d{3})\s*\|.*\|\s*(?:open|superseded by redesign)\s*\|",
            corpus,
        )
        missing = [failure_id for failure_id in required if failure_id not in tests]
        self.assertEqual(missing, [])

    def test_every_failure_record_maps_to_executable_invariant_tests(self):
        failure_ids = set(
            re.findall(r"^### (FH-\d{3})\b", _failure_corpus(), re.MULTILINE)
        )

        self.assertEqual(set(FAILURE_INVARIANT_TESTS), failure_ids)
        test_names = []
        for failure_id, mapped in FAILURE_INVARIANT_TESTS.items():
            names = _mapped_test_names(mapped)
            with self.subTest(failure_id=failure_id):
                self.assertTrue(names)
                self.assertEqual(len(names), len(set(names)))
            test_names.extend(names)

        unique_test_names = tuple(dict.fromkeys(test_names))
        result = _run_named_tests(unique_test_names)
        self.assertEqual(result.testsRun, len(unique_test_names))
        self.assertTrue(result.wasSuccessful(), _test_result_details(result))
        self.assertEqual(result.skipped, [])

    def test_required_mapping_components_are_present(self):
        """FH-033: canonical components cannot disappear from a nonempty map."""
        self.assertEqual(
            set(REQUIRED_FAILURE_COMPONENTS),
            set(FAILURE_INVARIANT_TESTS),
        )
        self.assertEqual(
            {
                failure_id: frozenset(_mapped_test_names(mapped))
                for failure_id, mapped in FAILURE_INVARIANT_TESTS.items()
            },
            REQUIRED_FAILURE_COMPONENTS,
        )
        self.assertEqual(_required_component_gaps(FAILURE_INVARIANT_TESTS), {})


class DiagnosticProjectionTests(unittest.TestCase):
    def test_unrelated_issue_diagnostic_is_not_an_error(self):
        """FH-018: issue-scoped callers see only intersecting diagnostics."""
        diagnostics = [
            {
                "code": "ambiguous-topic-fork",
                "message": "alpha",
                "issue_id": shapes.ALPHA,
            },
            {
                "code": "ambiguous-topic-fork",
                "message": "beta",
                "issue_id": shapes.BETA,
            },
        ]

        projected = cr.project_diagnostics(
            diagnostics,
            target_issue_ids={shapes.BETA},
        )

        self.assertEqual(
            [diagnostic["issue_id"] for diagnostic in projected],
            [shapes.BETA],
        )

    def test_snapshot_failure_is_never_filtered(self):
        """FH-010: compatibility errors always retain fatal Git failures."""
        result = cr.compatibility_errors(["git log failed"], [])

        self.assertEqual(result, ["git log failed"])

    def test_merge_diagnostic_does_not_mark_base_ref_unavailable(self):
        """Merge ownership ambiguity is independent of base-ref availability."""
        degraded = cr._project_degraded(
            [],
            [
                {
                    "code": "merge-side-unresolved",
                    "message": "merge side is ambiguous",
                    "issue_id": shapes.ALPHA,
                }
            ],
        )

        self.assertEqual(degraded, ["merge-side-unresolved"])

    def test_topic_fork_diagnostic_marks_base_ref_unavailable(self):
        """Topic fork ambiguity means branch-base evidence is unavailable."""
        degraded = cr._project_degraded(
            [],
            [
                {
                    "code": "ambiguous-topic-fork",
                    "message": "topic fork is ambiguous",
                    "issue_id": shapes.ALPHA,
                }
            ],
        )

        self.assertEqual(
            degraded,
            [cr.DEGRADED_BRANCH_UNAVAILABLE, "ambiguous-topic-fork"],
        )

    def test_compatibility_errors_dedupe_in_first_seen_order(self):
        """FH-032: flat compatibility errors are stable and non-repeating."""
        diagnostics = [
            {"code": "one", "message": "shared"},
            {"code": "two", "message": "diagnostic"},
            {"code": "three", "message": "diagnostic"},
        ]

        result = cr.compatibility_errors(
            ["fatal", "shared", "fatal"],
            diagnostics,
        )

        self.assertEqual(result, ["fatal", "shared", "diagnostic"])

    def test_build_result_separates_fatal_errors_from_diagnostics(self):
        """FH-010: snapshot failure is structured and survives empty scope."""
        with GitRepo() as repo:
            def failing(args, cwd=None):
                if args[:2] == ["git", "log"]:
                    return type(
                        "Result",
                        (),
                        {
                            "returncode": 128,
                            "stdout": "",
                            "stderr": "fatal: snapshot unavailable",
                        },
                    )()
                return repo.runner(args, cwd)

            built = cr.build_attribution(
                failing,
                repo.path,
                target_shas=set(),
                target_issue_ids=set(),
            )

        self.assertEqual(built["fatal_errors"], built["errors"])
        self.assertTrue(built["fatal_errors"])
        self.assertEqual(built["diagnostics"], [])

    def test_ref_inventory_failure_is_structured_and_fails_closed(self):
        """FH-014: default-ref inventory failure is observable, not fallback."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            work = repo.commit("feat: branch work")
            calls = []

            def failing(args, cwd=None):
                calls.append(tuple(args))
                if args[:2] == ["git", "for-each-ref"]:
                    return type(
                        "Result",
                        (),
                        {
                            "returncode": 128,
                            "stdout": "",
                            "stderr": "fatal: ref inventory unavailable",
                        },
                    )()
                return repo.runner(args, cwd)

            built = cr.build_attribution(failing, repo.path)

        self.assertNotIn(work, built["attribution"])
        self.assertTrue(
            any("for-each-ref" in error for error in built["fatal_errors"])
        )
        self.assertEqual(built["errors"], built["fatal_errors"])
        self.assertEqual(built["diagnostics"], [])
        self.assertFalse(
            any(call[:2] == ("git", "symbolic-ref") for call in calls),
            "a failed immutable ref inventory must not trigger a named fallback",
        )

    def test_unrelated_graph_ambiguity_does_not_degrade_requested_issue(self):
        """FH-007/FH-008/FH-009/FH-018: project errors and degradation once."""
        with GitRepo() as repo:
            shapes.ambiguous_same_tail_remotes(repo)

            built = cr.build_attribution(
                repo.runner,
                repo.path,
                target_issue_ids={shapes.BETA},
            )

        self.assertEqual(built["fatal_errors"], [])
        self.assertEqual(built["diagnostics"], [])
        self.assertEqual(built["degraded"], [])
        self.assertEqual(built["errors"], [])

    def test_prebuilt_whole_result_reprojects_to_requested_issue(self):
        """FH-018: reused indexes cannot leak another issue's diagnostics."""
        with GitRepo() as repo:
            shapes.ambiguous_same_tail_remotes(repo)
            whole = cr.build_attribution(repo.runner, repo.path)
            calls_after_build = repo.call_count

            result = cr.resolve_commits_for_issue(
                repo.runner,
                repo.path,
                shapes.BETA,
                index=whole,
                target_issue_ids={shapes.BETA},
            )

            self.assertTrue(whole["diagnostics"])
            self.assertEqual(
                repo.call_count,
                calls_after_build,
                "index reuse must not rebuild",
            )

        self.assertEqual(result["fatal_errors"], [])
        self.assertEqual(result["diagnostics"], [])
        self.assertEqual(result["degraded"], [])
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["coverage"]["base_ref_available"])

    def test_attribution_only_issue_index_is_rejected_without_rebuild(self):
        """A partial legacy index cannot safely synthesize commit metadata."""
        calls = []

        def runner(args, cwd=None):
            calls.append(args)
            raise AssertionError("partial index must not trigger Git")

        with self.assertRaisesRegex(TypeError, "full attribution result"):
            cr.resolve_commits_for_issue(
                runner,
                Path("."),
                shapes.BETA,
                index={"sha": {shapes.BETA: "branch"}},
                target_issue_ids={shapes.BETA},
            )

        self.assertEqual(calls, [])

    def _assert_duplicate_diagnostics_have_one_compatibility_error(self, shape):
        with GitRepo(**shapes.REPO_KWARGS.get(shape, {})) as repo:
            shapes.ALL_SHAPES[shape](repo)
            built = cr.build_attribution(repo.runner, repo.path)

        messages = [item["message"] for item in built["diagnostics"]]
        self.assertGreater(
            len(messages),
            len(set(messages)),
            f"{shape} must exercise multiple structured copies",
        )
        self.assertEqual(built["errors"], list(dict.fromkeys(messages)))

    def test_octopus_duplicate_diagnostics_have_one_compatibility_error(self):
        """FH-032: octopus SHA/issue diagnostics retain one flat message."""
        self._assert_duplicate_diagnostics_have_one_compatibility_error(
            "octopus_mapping_ambiguous"
        )

    def test_multi_name_duplicate_diagnostics_have_one_compatibility_error(self):
        """FH-032: multi-name SHA/issue diagnostics retain one flat message."""
        self._assert_duplicate_diagnostics_have_one_compatibility_error(
            "two_parent_multi_name_ambiguous"
        )

    def test_partial_duplicate_diagnostics_have_one_compatibility_error(self):
        """FH-032: partial ambiguity keeps structure without flat repetition."""
        self._assert_duplicate_diagnostics_have_one_compatibility_error(
            "stacked_partial_ambiguity_conventional_merge"
        )


class MergeClaimInvariantTests(unittest.TestCase):
    def test_subject_token_order_does_not_change_content(self):
        """FH-004: subject token order is not parent-side evidence."""
        normal = resolve_shape("octopus_merge")
        reversed_order = resolve_shape("octopus_subject_order_reversed")
        self.assertEqual(
            normal["content_owners"],
            reversed_order["content_owners"],
        )

    def test_octopus_parent_order_does_not_change_shared_content(self):
        """FH-005: mapped overlap is resolved by topic, not parent order."""
        beta_first = resolve_shape("octopus_shared_ancestor_b_before_a")
        alpha_first = resolve_shape("octopus_shared_ancestor_a_before_b")
        self.assertEqual(
            beta_first["content_owners"],
            alpha_first["content_owners"],
        )
        self.assertEqual(
            beta_first["content_owners"],
            beta_first["declared_content_owners"],
        )

    def test_partial_unresolved_octopus_keeps_mapped_partition(self):
        """FH-005: one unresolved side cannot disable mapped-side partition."""
        beta_first = resolve_shape("octopus_partial_unresolved_b_before_a")
        alpha_first = resolve_shape("octopus_partial_unresolved_a_before_b")
        self.assertEqual(
            beta_first["content_owners"],
            alpha_first["content_owners"],
        )
        self.assertEqual(
            beta_first["content_owners"],
            beta_first["declared_content_owners"],
        )
        self.assertEqual(
            beta_first["content_owners"]["feat: unresolved gamma work"],
            frozenset(),
        )
        self.assertTrue(
            any(
                diagnostic["code"] == "merge-side-unresolved"
                and diagnostic.get("issue_id") == shapes.GAMMA
                for diagnostic in beta_first["diagnostics"]
            )
        )

    def test_partial_topic_ambiguity_is_scoped_to_its_interval(self):
        """FH-005: unique stacked intervals survive a same-tip ambiguity."""
        result = resolve_shape("stacked_partial_ambiguity_conventional_merge")
        self.assertEqual(
            result["content_owners"]["feat: unique alpha interval"],
            frozenset({shapes.ALPHA}),
        )
        self.assertEqual(
            result["content_owners"]["feat: ambiguous beta gamma interval"],
            frozenset(),
        )
        self.assertEqual(
            result["content_owners"]["feat: unique delta interval"],
            frozenset({shapes.DELTA}),
        )
        for issue_id in (shapes.BETA, shapes.GAMMA):
            self.assertTrue(
                any(
                    diagnostic["code"] == "merge-side-unresolved"
                    and diagnostic.get("issue_id") == issue_id
                    for diagnostic in result["diagnostics"]
                )
            )

    def test_deleted_refs_keep_boundary_but_not_unproven_content(self):
        """FH-015: deleted refs retain boundaries and expose unresolved sides."""
        result = resolve_shape("octopus_mapping_ambiguous")
        self.assertEqual(
            result["boundary_issues"],
            {shapes.ALPHA, shapes.BETA},
        )
        self.assertTrue(
            any(
                diagnostic["code"] == "merge-side-unresolved"
                for diagnostic in result["diagnostics"]
            )
        )

    def test_two_parent_multi_name_subject_does_not_relabel_side(self):
        """FH-016: a multi-name subject cannot relabel content."""
        result = resolve_shape("two_parent_multi_name_ambiguous")
        self.assertEqual(
            result["content_owners"],
            result["declared_content_owners"],
        )


class FinalizeClaimOrderTests(unittest.TestCase):
    def setUp(self):
        self.records = {
            "work": {
                "parents": [],
            },
        }

    def test_unresolved_branch_before_outer_content_blocks_guess(self):
        """FH-016: inner unresolved evidence is a same-source barrier."""
        candidates = {
            "work": [
                {
                    "issue_id": shapes.ALPHA,
                    "source": "branch",
                    "kind": "unresolved",
                },
                {
                    "issue_id": shapes.GAMMA,
                    "source": "branch",
                    "kind": "content",
                },
            ],
        }
        self.assertEqual(
            cr.finalize_claims(self.records, candidates),
            {},
        )

    def test_mapped_content_before_unresolved_sibling_survives(self):
        """FH-016: earlier graph-corroborated content remains authoritative."""
        candidates = {
            "work": [
                {
                    "issue_id": shapes.ALPHA,
                    "source": "branch",
                    "kind": "content",
                },
                {
                    "issue_id": shapes.BETA,
                    "source": "branch",
                    "kind": "unresolved",
                },
            ],
        }
        self.assertEqual(
            cr.finalize_claims(self.records, candidates),
            {"work": {shapes.ALPHA: "branch"}},
        )

    def test_trailer_resolves_across_earlier_branch_barrier(self):
        """FH-016: stronger trailer evidence can resolve blocked branch data."""
        candidates = {
            "work": [
                {
                    "issue_id": shapes.ALPHA,
                    "source": "branch",
                    "kind": "unresolved",
                },
                {
                    "issue_id": shapes.GAMMA,
                    "source": "branch",
                    "kind": "content",
                },
                {
                    "issue_id": shapes.BETA,
                    "source": "trailer",
                    "kind": "content",
                },
            ],
        }
        self.assertEqual(
            cr.finalize_claims(self.records, candidates),
            {"work": {shapes.BETA: "trailer"}},
        )


class TestTrailerResolution(unittest.TestCase):
    def test_trailer_commit_resolves(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            sha = repo.commit("feat: something", issue=ISSUE)
            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertEqual(out["issue_id"], ISSUE)
            self.assertEqual(out["source"], "trailer")
            self.assertEqual(out["errors"], [])

    def test_commit_without_trailer_or_branch_is_unresolved(self):
        with GitRepo() as repo:
            sha = repo.commit("chore: unrelated")
            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertIsNone(out["issue_id"])
            self.assertIsNone(out["source"])


class TestBranchResolution(unittest.TestCase):
    def test_branch_only_commit_resolves(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            sha = repo.commit("feat: no trailer here")
            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertEqual(out["issue_id"], ISSUE)
            self.assertEqual(out["source"], "branch")

    def test_trailer_wins_over_branch(self):
        """Precedence rule: trailer > branch (Global Constraint 2)."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(OTHER)
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{OTHER}")
            sha = repo.commit("feat: trailer disagrees with branch", issue=ISSUE)
            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertEqual(out["issue_id"], ISSUE)
            self.assertEqual(out["source"], "trailer")


class TestMergeSubjectResolution(unittest.TestCase):
    def test_merge_subject_resolves_after_branch_deleted(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            repo.commit("feat: work")
            repo.checkout("main")
            repo.merge(name, message=f"Merge branch 'codex/{ISSUE}'")
            repo.delete_branch(name)
            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            sources = {c["source"] for c in out["commits"]}
            self.assertIn("merge-subject", sources)


class TestOverCollection(unittest.TestCase):
    """Branch containment is not branch authorship.

    A branch cut from main has all of main as ancestors, so plain
    `git rev-list <branch>` attributes the entire base history to the issue.
    Measured on issue 093 while building this module: 279 collected against 52
    actually contributed. This test fixes the boundary."""

    def test_base_history_is_not_attributed_to_the_branch(self):
        with GitRepo() as repo:
            base_one = repo.commit("chore: base one")
            base_two = repo.commit("chore: base two")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            mine = repo.commit("feat: branch work")
            repo.checkout("main")
            repo.merge(name, message=f"Merge branch 'codex/{ISSUE}'")

            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            shas = {c["sha"] for c in out["commits"]}

            self.assertIn(mine, shas, "the branch's own commit must be collected")
            self.assertNotIn(base_one, shas, "base history predates the branch")
            self.assertNotIn(base_two, shas, "base history predates the branch")

    def test_merged_branch_contribution_survives_branch_deletion(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            mine = repo.commit("feat: no trailer, branch only")
            repo.checkout("main")
            repo.merge(name, message=f"Merge branch 'codex/{ISSUE}'")
            repo.delete_branch(name)

            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            shas = {c["sha"] for c in out["commits"]}
            self.assertIn(
                mine,
                shas,
                "merge topology must still attribute the commit once the branch is gone",
            )


class TestIssueToCommits(unittest.TestCase):
    def test_collects_trailer_and_branch_commits(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            with_trailer = repo.commit("feat: a", issue=ISSUE)
            without_trailer = repo.commit("feat: b")
            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            shas = {c["sha"] for c in out["commits"]}
            self.assertIn(with_trailer, shas)
            self.assertIn(
                without_trailer,
                shas,
                "branch-only commit must be collected — this is the issue 095 defect",
            )

    def test_unmatched_count_is_reported(self):
        with GitRepo() as repo:
            repo.commit("chore: unrelated one")
            repo.commit("chore: unrelated two")
            repo.add_issue_file(ISSUE)
            repo.commit("feat: mine", issue=ISSUE)
            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            self.assertEqual(len(out["commits"]), 1)
            self.assertEqual(out["repo_unmatched_count"], 3)
            self.assertEqual(out["repo_examined_count"], 4)
            self.assertEqual(out["errors"], [], "unmatched is descriptive, not an error")

    def test_each_commit_carries_its_source(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            repo.commit("feat: a", issue=ISSUE)
            repo.commit("feat: b")
            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            for entry in out["commits"]:
                self.assertIn(entry["source"], cr.SOURCE_PRECEDENCE)


class HeadStateBoundaryProjectionTests(unittest.TestCase):
    def _assert_fatal_projection(self, out, expected_fragment):
        self.assertIsNone(out["issue_id"])
        self.assertIsNone(out["source"])
        self.assertTrue(out["fatal_errors"])
        self.assertIn(expected_fragment, out["fatal_errors"][0])
        self.assertEqual(out["diagnostics"], [])
        self.assertEqual(out["degraded"], [cr.DEGRADED_BRANCH_UNAVAILABLE])
        self.assertEqual(out["errors"], out["fatal_errors"])
        self.assertFalse(
            any(
                "detached-head-branch-unavailable"
                in diagnostic.get("code", "")
                for diagnostic in out["diagnostics"]
            )
        )

    def test_symbolic_ref_failure_projects_fatal_without_detached_diagnostic(self):
        """FH-039: HEAD-ref failure reaches the public commit wrapper."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            sha = repo.commit("feat: trailer work", issue=ISSUE)

            def failing(args, cwd=None):
                if tuple(args) == tuple(cr.HEAD_REF_ARGS):
                    return type(
                        "Result",
                        (),
                        {
                            "returncode": -9,
                            "stdout": "",
                            "stderr": "terminated",
                        },
                    )()
                return repo.runner(args, cwd)

            out = cr.resolve_issue_for_commit(failing, repo.path, sha)

        self._assert_fatal_projection(out, "terminated by signal 9")

    def test_detached_sha_failure_projects_fatal_without_detached_diagnostic(self):
        """FH-039: detached SHA failure reaches the public commit wrapper."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            sha = repo.commit("feat: trailer work", issue=ISSUE)
            repo.detach()

            def failing(args, cwd=None):
                if tuple(args) == tuple(cr.HEAD_SHA_ARGS):
                    return type(
                        "Result",
                        (),
                        {
                            "returncode": 128,
                            "stdout": "",
                            "stderr": "fatal: cannot resolve HEAD",
                        },
                    )()
                return repo.runner(args, cwd)

            out = cr.resolve_issue_for_commit(failing, repo.path, sha)

        self._assert_fatal_projection(out, "cannot resolve HEAD")


class TestDetachedHead(unittest.TestCase):
    @staticmethod
    def _expected_limitation(sha):
        return {
            "code": "detached-head-branch-unavailable",
            "message": (
                f"commit {sha} is checked out at detached HEAD; "
                "branch attribution is unavailable"
            ),
            "sha": sha,
        }

    def _assert_detached_limitation(self, out, sha):
        expected = self._expected_limitation(sha)
        self.assertEqual(out["fatal_errors"], [])
        self.assertEqual(out["diagnostics"], [expected])
        self.assertEqual(
            out["degraded"],
            [
                cr.DEGRADED_BRANCH_UNAVAILABLE,
                "detached-head-branch-unavailable",
            ],
        )
        self.assertEqual(out["errors"], [expected["message"]])

    def test_trailer_resolves_and_branch_gap_is_reported(self):
        """FH-038: intrinsic trailer truth survives a detached checkout."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            sha = repo.commit("feat: work", issue=ISSUE)
            repo.detach()
            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertEqual(out["issue_id"], ISSUE)
            self.assertEqual(out["source"], "trailer")
            self._assert_detached_limitation(out, sha)

    def test_untrailed_detached_commit_reports_branch_limitation(self):
        """FH-038: detached unmatched is not silently ordinary unmatched."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.detach()
            sha = repo.commit("feat: detached work without trailer")

            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)

        self.assertIsNone(out["issue_id"])
        self.assertIsNone(out["source"])
        self._assert_detached_limitation(out, sha)

    def test_attached_unrelated_commit_has_no_detached_limitation(self):
        """FH-038: ordinary attached unmatched history is not degraded."""
        with GitRepo() as repo:
            sha = repo.commit("chore: unrelated")
            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)

        self.assertIsNone(out["issue_id"])
        self.assertEqual(out["fatal_errors"], [])
        self.assertEqual(out["diagnostics"], [])
        self.assertEqual(out["degraded"], [])
        self.assertEqual(out["errors"], [])

    def test_detached_limitation_has_bare_indexed_parity(self):
        """FH-038: both public commit call shapes project one index signal."""
        with GitRepo() as repo:
            base = repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.detach()
            sha = repo.commit("feat: detached work without trailer")
            built = cr.build_attribution(repo.runner, repo.path)
            calls_after_build = repo.call_count

            indexed = cr.resolve_issue_for_commit(
                repo.runner,
                repo.path,
                sha,
                attribution=built,
            )
            self.assertEqual(
                repo.call_count,
                calls_after_build,
                "a supplied index must not add a per-commit Git probe",
            )
            indexed_base = cr.resolve_issue_for_commit(
                repo.runner,
                repo.path,
                base,
                attribution=built,
            )
            bare = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)

        self.assertEqual(indexed, bare)
        self._assert_detached_limitation(indexed, sha)
        self.assertEqual(
            indexed_base["diagnostics"],
            [],
            "a whole index must scope the detached limitation to HEAD",
        )
        self.assertEqual(indexed_base["degraded"], [])
        self.assertEqual(indexed_base["errors"], [])

    def test_commit_orphaned_by_branch_deletion_resolves_to_nothing(self):
        """A known limitation, asserted rather than hidden.

        Delete the only branch holding a commit and it becomes unreachable
        from every ref, so `--all` does not see it and no source can attribute
        it. It resolves to `None`, indistinguishable from a commit that
        genuinely belongs to no issue.

        `degraded` is deliberately empty here. The flag means branch evidence
        could not be consulted; here there is no evidence left to consult,
        which is a different thing. The previous version of this test asserted
        `branch-unavailable` and passed with its own `detach()` removed — it
        never checked what its name claimed."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            sha = repo.commit("feat: no trailer")
            repo.checkout("main")
            repo.delete_branch(name)

            index = cr.build_attribution(repo.runner, repo.path)
            self.assertNotIn(sha, index["records"], "an orphaned commit is unreachable")

            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertIsNone(out["issue_id"])
            self.assertEqual(out["degraded"], [])

    def test_a_trailer_survives_branch_deletion(self):
        """The reason the trailer outranks branch evidence: it is intrinsic to
        the commit and does not depend on a ref still existing."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            sha = repo.commit("feat: with trailer", issue=ISSUE)
            repo.checkout("main")
            repo.merge(name, message=f"Merge branch 'codex/{ISSUE}'")
            repo.delete_branch(name)

            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertEqual(out["issue_id"], ISSUE)
            self.assertEqual(out["source"], "trailer")


class TestBatching(unittest.TestCase):
    """Global Constraint 4: git calls must not scale with history length."""

    def _calls_for_history(self, commit_count):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            for index in range(commit_count):
                repo.commit(f"feat: step {index}")
            repo.call_count = 0
            cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            return repo.call_count

    def test_call_count_independent_of_history_length(self):
        small = self._calls_for_history(3)
        large = self._calls_for_history(30)
        self.assertEqual(
            small,
            large,
            f"git calls grew with history: {small} for 3 commits, {large} for 30",
        )

    def test_membership_is_built_once(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            for index in range(5):
                repo.commit(f"feat: step {index}")
            membership = cr.build_branch_membership(repo.runner, repo.path)
            self.assertTrue(membership["membership"])
            head = repo.head()
            self.assertIn(head, membership["membership"])
            self.assertTrue(
                any(
                    name.endswith(f"codex/{ISSUE}")
                    for name in membership["membership"][head]
                )
            )


class TestParity(unittest.TestCase):
    """Both query directions must agree — the check that stops the two
    consumers drifting apart again."""

    def test_directions_agree_on_mixed_history(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            repo.commit("feat: a", issue=ISSUE)
            repo.commit("feat: b")
            repo.commit("feat: c", issue=ISSUE)

            self._assert_directions_agree(repo)

    def test_directions_agree_on_merged_history(self):
        """The asymmetry this pins: while stream A was being built, only the
        issue->commits direction consulted merge topology, so a merged branch
        commit resolved from one direction and not the other. On 30 real
        commits that disagreed 13 times."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            merged = repo.commit("feat: no trailer, branch only")
            repo.checkout("main")
            repo.merge(name, message=f"Merge branch 'codex/{ISSUE}'")
            repo.delete_branch(name)

            index = cr.build_attribution(repo.runner, repo.path)
            per_commit = cr.resolve_issue_for_commit(
                repo.runner, repo.path, merged, attribution=index["attribution"]
            )
            self.assertEqual(
                per_commit["issue_id"],
                ISSUE,
                "a merged branch commit must resolve from the commit direction too",
            )
            self._assert_directions_agree(repo)

    def _assert_directions_agree(self, repo):
        index = cr.build_attribution(repo.runner, repo.path)
        from_issue = {
            c["sha"]
            for c in cr.resolve_commits_for_issue(
                repo.runner, repo.path, ISSUE, index=index
            )["commits"]
        }
        from_commits = set()
        for sha in repo.log_shas():
            out = cr.resolve_issue_for_commit(
                repo.runner, repo.path, sha, attribution=index["attribution"]
            )
            if out["issue_id"] == ISSUE:
                from_commits.add(sha)

        self.assertEqual(
            from_issue,
            from_commits,
            "issue→commits and commit→issue resolved different sets",
        )


class TestRegressionMatrix(unittest.TestCase):
    """The remaining rows of the spec's regression table (issue 095, task D1).

    Streams A and B covered the rows they needed as they went; these fill the
    rest so the table is a coverage contract rather than a wish list."""

    def test_trailer_survives_rebase_style_rewrite(self):
        """A trailer is intrinsic to the commit, so it outlives history edits
        that branch and merge evidence do not."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            repo.commit("feat: with trailer", issue=ISSUE)
            repo.checkout("main")
            repo.merge(name, message=f"Merge branch 'codex/{ISSUE}'")
            repo.delete_branch(name)

            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            sources = {c["source"] for c in out["commits"]}
            self.assertIn("trailer", sources)

    def test_two_issues_in_one_history_do_not_bleed(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.add_issue_file(OTHER)
            mine = repo.commit("feat: mine", issue=ISSUE)
            theirs = repo.commit("feat: theirs", issue=OTHER)

            mine_out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            theirs_out = cr.resolve_commits_for_issue(repo.runner, repo.path, OTHER)

            self.assertEqual([c["sha"] for c in mine_out["commits"]], [mine])
            self.assertEqual([c["sha"] for c in theirs_out["commits"]], [theirs])

    def test_branch_suffix_resolves_to_the_issue_not_the_suffix(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}-engine")
            mine = repo.commit("feat: suffixed branch")
            repo.checkout("main")
            repo.merge(name, message=f"Merge branch 'codex/{ISSUE}-engine'")

            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            self.assertIn(mine, {c["sha"] for c in out["commits"]})

    def test_unknown_issue_id_resolves_nothing_without_error(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.commit("feat: mine", issue=ISSUE)

            out = cr.resolve_commits_for_issue(
                repo.runner, repo.path, "999-does-not-exist"
            )
            self.assertEqual(out["commits"], [])
            self.assertEqual(out["errors"], [])
            self.assertEqual(out["repo_unmatched_count"], 2)

    def test_empty_repository_is_not_an_error(self):
        with GitRepo() as repo:
            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            self.assertEqual(out["commits"], [])
            self.assertEqual(out["repo_examined_count"], 0)

    def test_git_failure_is_reported_not_swallowed(self):
        with GitRepo() as repo:
            repo.commit("chore: base")

            def failing(args, cwd=None):
                if args[:2] == ["git", "log"]:
                    class Result:
                        returncode = 128
                        stdout = ""
                        stderr = "fatal: bad revision"

                    return Result()
                return repo.runner(args, cwd)

            out = cr.resolve_commits_for_issue(failing, repo.path, ISSUE)
            self.assertEqual(out["commits"], [])
            self.assertTrue(out["errors"])
            self.assertIn("bad revision", out["errors"][0])


class TestRemoteTrackingRefs(unittest.TestCase):
    """Issue 095 review, finding 1 and 3.

    Every branch in a real repository exists twice: `codex/X` and
    `origin/codex/X`. The first implementation excluded only the exact branch
    name from its rev-list, so the counterpart re-included the branch and it
    excluded itself — `build_branch_membership` returned an empty map against
    this repository while passing 33 tests, because no fixture had a remote."""

    def test_live_branch_with_remote_counterpart_still_resolves(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            mine = repo.commit("feat: unmerged branch work")
            repo.publish(name)
            repo.checkout("main")

            built = cr.build_branch_membership(repo.runner, repo.path)
            self.assertIn(
                mine,
                built["membership"],
                "a branch that also exists as a remote ref must not exclude itself",
            )

            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            self.assertIn(mine, {c["sha"] for c in out["commits"]})

    def test_remote_only_branch_resolves(self):
        """The 092 shape: work pushed to a branch this checkout has no local
        copy of."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            mine = repo.commit("feat: remote-only work")
            repo.publish(name)
            repo.checkout("main")
            repo.delete_branch(name)

            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            self.assertIn(
                mine,
                {c["sha"] for c in out["commits"]},
                "unmerged work on a remote branch is the case this issue exists for",
            )

    def test_base_history_still_excluded_with_a_remote(self):
        """Fixing self-exclusion must not reopen the over-collection defect."""
        with GitRepo() as repo:
            base = repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            repo.commit("feat: branch work")
            repo.publish(name)
            repo.checkout("main")

            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            self.assertNotIn(base, {c["sha"] for c in out["commits"]})


class TestNoPerCommitProbe(unittest.TestCase):
    """Issue 095 review, finding 2: the degraded probe reintroduced the
    per-commit fan-out that task A2 removed."""

    def test_resolving_unmatched_commits_issues_no_branch_contains(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            for index in range(5):
                repo.commit(f"chore: unrelated {index}")

            index = cr.build_attribution(repo.runner, repo.path)
            repo.call_count = 0
            calls_before = len(repo.call_log)
            for sha in repo.log_shas():
                cr.resolve_issue_for_commit(
                    repo.runner, repo.path, sha, attribution=index["attribution"]
                )
            issued = repo.call_log[calls_before:]
            contains = [c for c in issued if c[:3] == ["git", "branch", "--contains"]]
            self.assertEqual(
                contains, [], "no per-commit branch probe may return (GC4)"
            )

    def test_supplied_index_answers_without_asking_git(self):
        """F12: the index already holds every source, trailer included. Asking
        git again per commit was measured at 65 redundant `git show -s` calls,
        1.7s, on a 65-commit range."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            for index_n in range(4):
                repo.commit(f"feat: step {index_n}", issue=ISSUE)

            index = cr.build_attribution(repo.runner, repo.path)
            attributed = [s for s in repo.log_shas() if s in index["attribution"]]
            self.assertTrue(attributed, "fixture should attribute something")

            before = len(repo.call_log)
            for sha in attributed:
                cr.resolve_issue_for_commit(
                    repo.runner, repo.path, sha, attribution=index["attribution"]
                )
            issued = repo.call_log[before:]
            self.assertEqual(
                issued, [], f"an attributed commit must answer from the index: {issued}"
            )

            # A commit absent from a supplied legacy index remains unresolved
            # without asking Git. The mapping is authoritative but cannot
            # carry the structured errors/degradation of a whole build result.


class TestUnregisteredIssueIds(unittest.TestCase):
    """Naming a branch is not the same as having an issue.

    `issue_id_from_branch` used to return the branch tail when no registered
    issue matched, so a behavior commit on `codex/999-not-a-real-issue`
    satisfied the linkage gate — `ok: True, unlinked: 0` — while linking to
    nothing that exists. Found by the commit-direction oracle, which enumerates
    registered issues and so could not see the phantom id."""

    def test_branch_naming_an_unregistered_issue_resolves_to_nothing(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch("codex/999-not-a-real-issue")
            sha = repo.commit("feat: work under a phantom issue")

            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertIsNone(out["issue_id"])

    def test_linkage_gate_flags_a_phantom_branch(self):
        from scripts import linkage_check

        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            base = repo.head()
            repo.branch("codex/999-not-a-real-issue")
            (repo.path / "scripts").mkdir(exist_ok=True)
            repo.commit("feat: behavior change", filename="scripts/thing.py")

            out = linkage_check.find_unlinked_behavior_commits(
                repo.runner, repo.path, base, repo.head()
            )
            self.assertFalse(out["ok"], "a phantom issue id must not pass the gate")
            self.assertEqual(len(out["unlinked"]), 1)

    def test_registered_issue_still_resolves(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            sha = repo.commit("feat: real work")

            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertEqual(out["issue_id"], ISSUE)

    def test_empty_registry_rejects_an_unknown_branch(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.branch("codex/321-no-issues-tracked")
            sha = repo.commit("feat: work")

            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertIsNone(out["issue_id"])

    def test_empty_registry_rejects_an_unknown_trailer(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            sha = repo.commit(
                "feat: work",
                issue="321-no-issues-tracked",
            )

            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertIsNone(out["issue_id"])

    def test_empty_registry_rejects_an_unknown_merge_subject(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            name = repo.branch("codex/321-no-issues-tracked")
            work = repo.commit("feat: work")
            repo.checkout("main")
            merge = repo.merge(
                name,
                message="Merge branch 'codex/321-no-issues-tracked'",
            )

            index = cr.build_attribution(repo.runner, repo.path)
            self.assertNotIn(work, index["attribution"])
            self.assertNotIn(merge, index["attribution"])


class TestHistoricalIssueRegistry(unittest.TestCase):
    def test_issue_on_another_checkout_is_registered(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.branch("registry")
            repo.add_issue_file(ISSUE)
            repo.checkout("main")
            self.assertFalse((repo.path / "issues" / f"{ISSUE}.md").exists())

            errors = []
            self.assertIn(ISSUE, cr.known_issue_ids(repo.runner, repo.path, errors))
            self.assertEqual(errors, [])

    def test_deleted_issue_file_remains_registered_from_history(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo._git("rm", f"issues/{ISSUE}.md")
            repo._git("commit", "-q", "-m", f"chore: archive {ISSUE}")

            errors = []
            self.assertIn(ISSUE, cr.known_issue_ids(repo.runner, repo.path, errors))
            self.assertEqual(errors, [])

    def test_empty_repository_has_a_valid_empty_registry(self):
        with GitRepo() as repo:
            errors = []
            self.assertEqual(cr.known_issue_ids(repo.runner, repo.path, errors), [])
            self.assertEqual(errors, [])

    def test_registry_ids_are_sorted_and_deduplicated(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(OTHER)
            repo.add_issue_file(ISSUE)
            issue_path = repo.path / "issues" / f"{OTHER}.md"
            issue_path.write_text("# Updated issue\n")
            repo._git("add", str(issue_path))
            repo._git("commit", "-q", "-m", f"docs: update {OTHER}")

            errors = []
            self.assertEqual(
                cr.known_issue_ids(repo.runner, repo.path, errors),
                [OTHER, ISSUE],
            )
            self.assertEqual(errors, [])


class TestGraphQueryFailures(unittest.TestCase):
    ORIGIN_HEAD_ARGS = [
        "git",
        "symbolic-ref",
        "--quiet",
        "--short",
        "refs/remotes/origin/HEAD",
    ]

    @staticmethod
    def _failed_result(message, returncode=128):
        class Result:
            stdout = ""
            stderr = message

        Result.returncode = returncode
        return Result()

    def _repo_with_live_issue_branch(self):
        repo = GitRepo()
        repo.commit("chore: base")
        repo.add_issue_file(ISSUE)
        repo.branch(f"codex/{ISSUE}")
        work = repo.commit("feat: branch work")
        repo.checkout("main")
        return repo, work

    def test_rev_list_failure_surfaces_and_does_not_attribute(self):
        repo, work = self._repo_with_live_issue_branch()
        try:
            def failing(args, cwd=None):
                if args[:2] == ["git", "rev-list"]:
                    return self._failed_result("fatal: graph unavailable")
                return repo.runner(args, cwd)

            index = cr.build_attribution(failing, repo.path)

            self.assertNotIn(work, index["attribution"])
            self.assertIn(cr.DEGRADED_BRANCH_UNAVAILABLE, index["degraded"])
            self.assertTrue(
                any("rev-list" in error and "graph unavailable" in error
                    for error in index["errors"])
            )
        finally:
            repo.__exit__()

    def test_merge_base_failure_surfaces_and_does_not_attribute(self):
        repo, work = self._repo_with_live_issue_branch()
        try:
            def failing(args, cwd=None):
                if args[:3] == ["git", "merge-base", "--all"]:
                    return self._failed_result("fatal: corrupt commit graph")
                return repo.runner(args, cwd)

            index = cr.build_attribution(failing, repo.path)

            self.assertNotIn(work, index["attribution"])
            self.assertIn(cr.DEGRADED_BRANCH_UNAVAILABLE, index["degraded"])
            self.assertTrue(
                any("merge-base" in error and "corrupt commit graph" in error
                    for error in index["errors"])
            )
        finally:
            repo.__exit__()

    def test_merge_base_fatal_blocks_trailer_in_build_whole_and_bare(self):
        """FH-010: no ownership escapes a fatal live graph query."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            work = repo.commit(
                "feat: branch work with trailer",
                issue=ISSUE,
            )
            repo.checkout("main")

            def failing(args, cwd=None):
                if args[:3] == ["git", "merge-base", "--all"]:
                    return self._failed_result("fatal: graph unavailable")
                return repo.runner(args, cwd)

            built = cr.build_attribution(
                failing,
                repo.path,
                target_shas={work},
            )
            whole = cr.resolve_issue_for_commit(
                failing,
                repo.path,
                work,
                attribution=built,
            )
            bare = cr.resolve_issue_for_commit(
                failing,
                repo.path,
                work,
            )

        self.assertTrue(built["fatal_errors"])
        self.assertEqual(built["attribution"], {})
        for result in (whole, bare):
            self.assertIsNone(result["issue_id"])
            self.assertTrue(result["fatal_errors"])
            self.assertEqual(result["fatal_errors"], result["errors"])

    def test_registry_fatal_blocks_trailer_ownership(self):
        """FH-010: issue registry failure also fails closed after snapshot."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            work = repo.commit("feat: work with trailer", issue=ISSUE)

            def failing(args, cwd=None):
                if tuple(args) == cr.ISSUE_HISTORY_ARGS:
                    return self._failed_result("fatal: registry unavailable")
                return repo.runner(args, cwd)

            built = cr.build_attribution(
                failing,
                repo.path,
                target_shas={work},
            )
            resolved = cr.resolve_issue_for_commit(
                failing,
                repo.path,
                work,
                attribution=built,
            )

        self.assertTrue(built["fatal_errors"])
        self.assertEqual(built["attribution"], {})
        self.assertIsNone(resolved["issue_id"])
        self.assertEqual(resolved["fatal_errors"], built["fatal_errors"])

    def test_topic_delta_rejects_a_terminated_merge_base_query(self):
        repo, work = self._repo_with_live_issue_branch()
        try:
            def terminated(args, cwd=None):
                if args[:3] == ["git", "merge-base", "--all"]:
                    return self._failed_result(
                        "terminated by signal",
                        returncode=-15,
                    )
                return repo.runner(args, cwd)

            index = cr.build_attribution(terminated, repo.path)

            self.assertNotIn(work, index["attribution"])
            self.assertIn(cr.DEGRADED_BRANCH_UNAVAILABLE, index["degraded"])
            self.assertTrue(
                any("merge-base" in error and "terminated by signal" in error
                    for error in index["errors"])
            )
        finally:
            repo.__exit__()

    def test_live_membership_does_not_call_origin_head(self):
        repo, work = self._repo_with_live_issue_branch()
        try:
            calls = []

            def terminated(args, cwd=None):
                calls.append(args)
                return repo.runner(args, cwd)

            index = cr.build_attribution(terminated, repo.path)

            self.assertNotIn(self.ORIGIN_HEAD_ARGS, calls)
            self.assertIn(work, index["attribution"])
            self.assertEqual(index["errors"], [])
            self.assertEqual(index["degraded"], [])
        finally:
            repo.__exit__()

    def test_live_membership_does_not_need_origin_head_fallback(self):
        repo, work = self._repo_with_live_issue_branch()
        try:
            calls = []

            def missing(args, cwd=None):
                calls.append(args)
                return repo.runner(args, cwd)

            index = cr.build_attribution(missing, repo.path)

            self.assertNotIn(self.ORIGIN_HEAD_ARGS, calls)
            self.assertIn(work, index["attribution"])
            self.assertEqual(index["errors"], [])
            self.assertEqual(index["degraded"], [])
        finally:
            repo.__exit__()

    def test_branch_membership_rejects_a_terminated_merge_base_query(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.add_issue_file(OTHER)
            repo.branch(f"codex/{ISSUE}")
            issue_work = repo.commit("feat: issue work")
            repo.checkout("main")
            repo.branch(f"codex/{OTHER}")
            other_work = repo.commit("feat: other work")
            repo.checkout("main")

            def terminated(args, cwd=None):
                if args[:3] == ["git", "merge-base", "--all"]:
                    return self._failed_result(
                        "terminated by signal",
                        returncode=-15,
                    )
                return repo.runner(args, cwd)

            built = cr.build_branch_membership(terminated, repo.path)

            self.assertNotIn(issue_work, built["membership"])
            self.assertNotIn(other_work, built["membership"])
            self.assertIn(cr.DEGRADED_BRANCH_UNAVAILABLE, built["degraded"])
            self.assertTrue(
                any("merge-base" in error and "terminated by signal" in error
                    for error in built["errors"])
            )

    def test_merge_base_rc_one_means_not_ancestor_not_error(self):
        repo, _ = self._repo_with_live_issue_branch()
        try:
            def not_ancestor(args, cwd=None):
                if args[:3] == ["git", "merge-base", "--is-ancestor"]:
                    return type(
                        "Result",
                        (),
                        {"returncode": 1, "stdout": "", "stderr": ""},
                    )()
                return repo.runner(args, cwd)

            index = cr.build_attribution(not_ancestor, repo.path)

            self.assertFalse(
                any("merge-base" in error for error in index["errors"])
            )
        finally:
            repo.__exit__()


class TestDegradedMeaning(unittest.TestCase):
    """F3: the flag must mean branch evidence could not be consulted, not
    that the repository's refs happen to be arranged a certain way.

    It used to fire whenever no issue-shaped branch existed — true of most
    healthy repositories, where every merged branch still resolves through
    merge topology — and stayed silent in cases where attribution really was
    impossible."""

    def test_healthy_repo_with_issue_branches_is_not_degraded(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            repo.commit("feat: work")
            repo.checkout("main")
            self.assertEqual(cr.build_attribution(repo.runner, repo.path)["degraded"], [])

    def test_healthy_repo_without_issue_branches_is_not_degraded(self):
        """Nothing was unavailable — there are simply no issue branches."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.commit("feat: work", issue=ISSUE)
            self.assertEqual(cr.build_attribution(repo.runner, repo.path)["degraded"], [])

    def test_issue_branch_with_no_base_is_degraded(self):
        """Evidence exists and cannot be read: the case the flag is for."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            repo.commit("feat: work")
            repo._git("branch", "-q", "-D", "main")

            self.assertIn(
                cr.DEGRADED_BRANCH_UNAVAILABLE,
                cr.build_attribution(repo.runner, repo.path)["degraded"],
            )

    def test_detached_commits_reach_the_index(self):
        """FH-038: detached commits stay visible and report their limitation."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            repo.commit("feat: on branch")
            repo.checkout("main")
            repo.detach()
            detached = repo.commit("feat: detached work")

            index = cr.build_attribution(repo.runner, repo.path)
            self.assertIn(detached, index["records"])
            self.assertEqual(index["fatal_errors"], [])
            self.assertEqual(
                index["diagnostics"],
                [
                    {
                        "code": "detached-head-branch-unavailable",
                        "message": (
                            f"commit {detached} is checked out at detached "
                            "HEAD; branch attribution is unavailable"
                        ),
                        "sha": detached,
                    }
                ],
            )
            self.assertEqual(
                index["degraded"],
                [
                    cr.DEGRADED_BRANCH_UNAVAILABLE,
                    "detached-head-branch-unavailable",
                ],
            )


class TestRangeProjection(unittest.TestCase):
    def _malformed_range_result(self, output):
        repo = GitRepo()
        repo.commit("chore: base")
        repo.add_issue_file(ISSUE)
        repo.branch(f"codex/{ISSUE}")
        work = repo.commit("feat: issue")
        range_text = f"{work}^..{work}"
        range_args = ["git", "log", "--format=%H", range_text]

        def malformed(args, cwd=None):
            if args == range_args:
                return type(
                    "Result", (),
                    {"returncode": 0, "stdout": output, "stderr": ""},
                )()
            return repo.runner(args, cwd)

        return repo, cr.resolve_commits_for_issue(
            malformed, repo.path, ISSUE, rev_range=range_text
        )

    def test_live_range_projects_only_target_topic(self):
        """FH-031: full topology resolves a range without truncating graph data."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.add_issue_file(OTHER)
            alpha = repo.branch(f"codex/{ISSUE}")
            a_work = repo.commit("feat: alpha")
            repo.checkout("main")
            beta = repo.branch(f"codex/{OTHER}")
            b_work = repo.commit("feat: beta")

            result = cr.resolve_commits_for_issue(
                repo.runner, repo.path, OTHER, rev_range=f"{a_work}..{b_work}"
            )

            self.assertEqual({item["sha"] for item in result["commits"]}, {b_work})
            self.assertEqual(result["errors"], [])

    def test_empty_normal_range_is_an_empty_success(self):
        """FH-031: HEAD..HEAD is valid and distinct from malformed rc=0 output."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            index = cr.build_attribution(repo.runner, repo.path, rev_range="HEAD..HEAD")
            self.assertEqual(index["order"], [])
            self.assertEqual(index["attribution"], {})
            self.assertEqual(index["unmatched"], [])
            self.assertEqual(index["errors"], [])

    def test_graph_empty_range_with_distinct_ref_names_is_an_empty_success(self):
        """FH-031: rc=0 empty range is valid even when endpoint text differs."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo._git("branch", "range-left", "HEAD")
            repo._git("branch", "range-right", "HEAD")
            index = cr.build_attribution(
                repo.runner, repo.path, rev_range="range-left..range-right"
            )
            self.assertEqual(index["order"], [])
            self.assertEqual(index["attribution"], {})
            self.assertEqual(index["unmatched"], [])
            self.assertEqual(index["errors"], [])

    def test_range_projects_the_public_attribution_map_not_only_order(self):
        """FH-031: full topology remains internal; public attribution is ranged."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.add_issue_file(OTHER)
            repo.branch(f"codex/{ISSUE}")
            a_work = repo.commit("feat: alpha", issue=ISSUE)
            repo.checkout("main")
            repo.branch(f"codex/{OTHER}")
            b_work = repo.commit("feat: beta", issue=OTHER)
            index = cr.build_attribution(repo.runner, repo.path, rev_range=f"{a_work}..{b_work}")
            self.assertEqual(index["order"], [b_work])
            self.assertEqual(set(index["attribution"]), {b_work})
            self.assertNotIn(a_work, index["attribution"])

    def test_range_projection_failure_returns_no_full_topology_attribution(self):
        """FH-031: a failed range query never falls back to the --all index."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            work = repo.commit("feat: issue")
            range_args = ["git", "log", "--format=%H", f"{work}^..{work}"]

            def failing(args, cwd=None):
                if args == range_args:
                    return TestGraphQueryFailures._failed_result("range unavailable")
                return repo.runner(args, cwd)

            result = cr.resolve_commits_for_issue(failing, repo.path, ISSUE, rev_range=f"{work}^..{work}")
            self.assertEqual(result["commits"], [])
            self.assertTrue(any("range unavailable" in error for error in result["errors"]))

    def test_terminated_range_projection_returns_no_attribution(self):
        """FH-031: a signal-terminated range query is observable and closed."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            work = repo.commit("feat: issue")
            range_args = ["git", "log", "--format=%H", f"{work}^..{work}"]

            def terminated(args, cwd=None):
                if args == range_args:
                    return TestGraphQueryFailures._failed_result("", returncode=-15)
                return repo.runner(args, cwd)

            result = cr.resolve_commits_for_issue(terminated, repo.path, ISSUE, rev_range=f"{work}^..{work}")
            self.assertEqual(result["commits"], [])
            self.assertTrue(any("exit code -15" in error for error in result["errors"]))

    def test_range_projection_rejects_multi_token_success_output(self):
        """FH-022/FH-031: a successful range response must be one SHA per line."""
        repo, result = self._malformed_range_result("not-a-snapshot-sha extra\n")
        try:
            self.assertEqual(result["commits"], [])
            self.assertTrue(any("range" in error and "malformed" in error for error in result["errors"]))
        finally:
            repo.__exit__()

    def test_range_projection_rejects_unknown_success_output(self):
        """FH-022/FH-031: an unknown SHA in rc=0 range output is fatal."""
        for output in ("not-a-snapshot-sha\n",):
            with self.subTest(output=output):
                repo, result = self._malformed_range_result(output)
                try:
                    self.assertEqual(result["commits"], [])
                    self.assertTrue(any("range" in error and "malformed" in error for error in result["errors"]))
                finally:
                    repo.__exit__()


if __name__ == "__main__":
    unittest.main()
