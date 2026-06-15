# rad-planner 4.0 + rad-session 5.0 — Coordinated Upgrade Plan (Machine-Readable)

**Date drafted:** 2026-05-14
**Status:** draft
**Human-readable companion:** `2026-05-14-rad-planner-rad-session-upgrade-plan-human.md`

The plan below is YAML-structured for parsing. Field names use snake_case. Every milestone has `conversation_points`, `action_points`, and `exit_criteria` where applicable. Dependencies are explicit. Risks and out-of-scope items are enumerated.

```yaml
plan:
  id: rad-planner-4.0-rad-session-5.0-upgrade
  date_drafted: 2026-05-14
  status: draft
  version: 0.1
  human_companion: 2026-05-14-rad-planner-rad-session-upgrade-plan-human.md

agent_scope:
  v1_primary_scopes:
    - claude_only          # CLAUDE.md canonical, no AGENTS.md
    - codex_only           # AGENTS.md canonical, no CLAUDE.md
    - claude_and_codex     # AGENTS.md canonical, CLAUDE.md as @AGENTS.md shim
  v1_supported_via_agents_md_portability:
    - gemini_cli
    - opencode
    - cursor
    - windsurf
    - antigravity
  v1_out_of_scope:
    - dedicated_GEMINI_md_shim
    - other_vendor_specific_shims_beyond_CLAUDE_md
    - migration_tooling_v3_to_v4
    - migration_tooling_v4_to_v5
  roadmap_v4.1_v5.1:
    - GEMINI_md_if_demand_surfaces
    - OPENCODE_md_if_demand_surfaces
  readme_requirement: explicit_multi_agent_acknowledgment_required

teaching_model:
  plan_skill_teaches: always_unconditional_regardless_of_mode
  wrapup_skill_teaches: mode_gated
  mode_preference_location: .rad/profile  # tentative; pending Phase 0 lock
  default_mode: mentor
  mode_options:
    - mentor    # explanation + draft entry on every candidate decision
    - dev       # quick skip/handle list with no explanation
  graduation_policy: user_driven_only_no_auto_graduation

phases:

  - id: phase-0
    title: Lock the design (pre-work)
    type: conversation-and-spec
    dependencies: []
    duration_estimate_days: [2, 3]
    duration_timeboxed_max_days: 5

    conversation_points:
      - adopt_research_doc_structure_canonical_yes_or_refine
      - file_ownership_matrix_planner_vs_session_vs_human_owned
      - mode_preference_location_dot_rad_profile_vs_operating_manual_frontmatter
      - entry_point_detection_heuristics_signals_per_entry_point
      - status_md_schema_field_by_field_with_evidence_sources

    action_points:
      - write_doc_conventions_md_replaces_existing_file_conventions_md
      - write_cross_plugin_contracts_md
      - write_entry_point_routing_md
      - write_status_md_schema_md

    exit_criteria:
      - all_four_spec_docs_locked_via_user_review
      - no_open_spec_blockers_for_implementation

  - id: phase-1
    title: Build rad-planner 4.0
    type: build
    dependencies: [phase-0]
    duration_estimate_weeks: [2, 3]
    target_version: 4.0.0
    current_version: 3.0.0

    milestones:

      - id: M0
        title: Pre-flight discovery
        conversation_points:
          - where_does_project_live: [cwd, named_path, doesnt_exist_create_at_path]
          - which_agents: [claude, codex, both, not_sure_yet]
          - whats_already_here: [CLAUDE_md, AGENTS_md, docs_dir, claude_init_residue, codex_init_residue]
          - which_entry_point: [greenfield, improvement, pivot, plan_boost, drift_check]
        action_points:
          - implement_discovery_prompt_sequence
          - implement_existing_state_detection_heuristics
          - implement_entry_point_routing_logic
          - implement_project_directory_validation
        exit_criteria:
          - discovery_output_deterministic_across_fixtures
          - no_writes_before_discovery_completes
          - existing_init_residue_detected_correctly

      - id: M1-M5
        title: Five-phase conversation
        sub_milestones:
          - id: M1
            title: Constitution_and_Frame
            outputs: [operating_manual_content_draft]
            writes_to: [CLAUDE_md_or_AGENTS_md_conditional]
          - id: M2
            title: Goal_Backward_Scope
            method: GSD_scaffold_what_must_be_TRUE_EXIST_CRITICAL
            outputs: [vision_md_non_goals_draft, current_md_objective_draft, open_questions, risks]
          - id: M3
            title: Sequence_with_Size_Discipline
            constraint: milestones_2_to_3_tasks_50_percent_context_target
            outputs: [current_md_milestones_draft, optional_roadmap_md_draft_if_multiple_milestones]
          - id: M4
            title: Quality_Gates
            outputs: [current_md_validation_commands, current_md_stop_conditions, notes_for_next_session]
          - id: M5
            title: Doc_Set_Recommendation
            outputs: [doc_set_with_project_specific_rationale, complexity_routing_decision]
            complexity_routing_options: [lite, standard, full]
        conversation_points:
          - phases_teach_unconditionally_always_teaches_mode
          - phase_outputs_reviewed_before_next_phase
          - user_can_revise_prior_phase_outputs_anytime
        action_points:
          - draft_phase_by_phase_agent_prompts
          - implement_phase_routing
          - implement_phase_output_validation
          - implement_always_teaches_explanations
          - implement_complexity_routing_in_phase_5
        exit_criteria:
          - all_five_phases_produce_valid_drafts
          - user_approves_final_plan_before_M6

      - id: M6
        title: Doc creation (executes plan's M0)
        conversation_points:
          - confirm_approved_doc_set
          - preserve_existing_init_residue
        action_points:
          - write_operating_manual_CLAUDE_md_and_or_AGENTS_md
          - write_strategic_docs:
              - vision_md
              - architecture_md
              - planning_current_md
              - status_md_scaffold
              - decisions_README_md
          - optional_writes_if_recommended:
              - roadmap_md
              - settings_json
              - hook_scaffolding
          - write_dot_rad_profile_with_mode_preference
        exit_criteria:
          - all_approved_files_exist_in_project_directory
          - no_existing_user_content_overwritten
          - validators_pass_on_emitted_docs

      - id: M7
        title: Validators
        action_points:
          - reshape_plan_lint_py_for_new_doc_set
          - add_status_validator_py_freshness_checks
          - add_doc_redundancy_py_cross_doc_duplicate_detection
          - add_doc_contradiction_py_cross_doc_disagreement_detection
        exit_criteria:
          - all_validators_have_unit_tests
          - validators_run_cleanly_on_fixture_outputs

      - id: M8
        title: End-to-end validation
        action_points:
          - fixture_project_per_entry_point: 4_fixtures
          - claude_only_fixture
          - codex_only_fixture
          - dual_agent_fixture
          - mentor_mode_fixture
          - dev_mode_fixture
          - token_budget_observation_per_phase
        exit_criteria:
          - all_fixtures_pass
          - token_budgets_within_target_no_phase_exceeds_5k_before_user_value

      - id: M9
        title: Release
        action_points:
          - update_SKILL_md_for_plan
          - update_plugin_json_3_0_0_to_4_0_0_with_human_readable_description
          - update_marketplace_catalog_blurb
          - update_README_may_2026_callout
        exit_criteria:
          - plugin_validator_agent_passes_clean
          - marketplace_json_valid

  - id: phase-2
    title: Build rad-session 5.0
    type: build
    dependencies: [phase-1]
    duration_estimate_weeks: [1.5, 2]
    target_version: 5.0.0
    current_version: 4.0.0

    milestones:

      - id: M1
        title: /init rebuild
        conversation_points:
          - project_directory_and_agent_scope_same_as_planner_pre_flight
          - existing_init_residue_detection_claude_and_codex
          - confirm_strategic_doc_creation_deferred_to_rad_planner_plan
        action_points:
          - implement_detection_and_enrichment_logic
          - implement_conditional_operating_manual_creation: [claude, codex, both]
          - implement_status_md_scaffolding
          - implement_settings_json_defaults_if_claude_in_scope
          - implement_gap_recommendation_messaging
        exit_criteria:
          - existing_init_content_preserved
          - operating_manual_created_appropriately_for_scope
          - no_strategic_doc_creation_by_init

      - id: M2
        title: /startup rebuild
        action_points:
          - implement_priority_read_sequence: [operating_manual, status_md, current_md, refs]
          - implement_freshness_verification_status_md_mtime_vs_git_activity
          - implement_resume_context_surfacing
          - measure_execution_time_target_under_5_seconds_wall_clock
        exit_criteria:
          - startup_completes_in_target_time
          - resume_context_coherent_across_fixtures

      - id: M3
        title: /wrapup rebuild
        action_points:
          - implement_evidence_based_reality_assessment: [git_diff, test_output, plan_task_completions]
          - implement_status_md_write_from_evidence_not_chat
          - implement_candidate_decision_detection: [mechanical_triggers, soft_model_reasoning]
          - implement_mode_aware_surfacing: [mentor_teaching_with_drafts, dev_quick_list]
          - implement_cross_doc_redundancy_check_via_doc_redundancy_py
          - implement_cross_doc_contradiction_check_via_doc_contradiction_py
          - implement_milestone_archive_logic_current_to_planning_archive
          - bound_work_to_avoid_10_minute_spirals
        exit_criteria:
          - wrapup_writes_status_from_evidence_not_chat
          - candidate_decisions_surface_with_mode_appropriate_format
          - cross_doc_checks_complete_in_bounded_time

      - id: M4
        title: Operating manual flavor adaptation
        action_points:
          - implement_detection_heuristic_for_non_standard_manual_names
          - implement_adaptive_reading_regardless_of_filename
          - dont_impose_canonical_naming_on_existing_projects
        exit_criteria:
          - non_standard_project_layouts_work
          - no_imposing_of_canonical_naming

      - id: M5
        title: End-to-end validation
        action_points:
          - full_lifecycle_fixture_init_plan_startup_wrapup_startup_wrapup
          - non_standard_layout_fixture
          - mentor_and_dev_mode_fixtures
          - single_and_dual_agent_fixtures
        exit_criteria:
          - all_fixtures_pass

      - id: M6
        title: Release
        action_points:
          - update_SKILL_md_for_init_startup_wrapup_checkpoint
          - update_plugin_json_4_0_0_to_5_0_0
          - update_marketplace_catalog_blurb
        exit_criteria:
          - plugin_validator_passes_clean

  - id: phase-3
    title: Release and distribution
    type: release
    dependencies: [phase-2]
    duration_estimate_weeks: 1
    action_points:
      - coordinated_marketplace_bump_1_5_0_to_1_6_0
      - submit_both_plugins_to_anthropic_marketplace
      - README_updates_explaining_multi_agent_reality_and_upgrade_path
      - light_adoption_tracking_setup
    exit_criteria:
      - marketplace_submission_accepted
      - README_accurate
      - upgrade_path_documented

out_of_scope:
  v1_explicit:
    - GEMINI_md_dedicated_shim
    - OPENCODE_md_dedicated_shim
    - other_vendor_specific_shims_beyond_CLAUDE_md
    - migration_tooling_v3_to_v4
    - migration_tooling_v4_to_v5
    - external_LLM_cross_review_flag
    - PreToolUse_re_read_hook
    - skills_generation_by_planner
    - AGENTS_md_nested_hierarchy
    - GUI_or_terminal_UI
  roadmap_v4.1_v5.1_if_demand:
    - GEMINI_md_if_demand_surfaces
    - OPENCODE_md_if_demand_surfaces
    - external_LLM_cross_review_optional_flag
    - PreToolUse_re_read_hook
    - skill_recommendation_in_phase_5

honest_risks:
  - id: spec_lock_overrun
    description: Edge cases keep surfacing in conversation
    severity: medium
    mitigation: timebox_5_days_max_document_remaining_assumptions
  - id: detection_false_positives_or_negatives
    description: Existing-state detection misreads init residue
    severity: high
    mitigation: dry_run_mode_fixture_testing_conservative_default_when_in_doubt_ask
  - id: token_cost_spiral
    description: GSD-style 4_to_1_orchestration_overhead
    severity: medium
    mitigation: per_phase_budgets_validation_observation_mechanical_validators_preferred
  - id: distribution_blocked
    description: Marketplace gatekeeping delays or rejects submission
    severity: medium
    mitigation: README_and_metadata_quality_from_day_one_submit_early_in_phase_3
  - id: five_phase_too_long_for_small_projects
    description: User fatigue before reaching Phase 5
    severity: medium
    mitigation: lite_flag_short_circuits_to_3_phase_mode_auto_detect_bail_signals

success_criteria:
  - both_plugin_validators_pass_clean
  - end_to_end_fixture_pass_all_entry_points_both_scopes_both_modes
  - token_budgets_within_target
  - marketplace_submission_accepted
  - README_accurately_describes_multi_agent_reality
  - this_plan_marked_shipped_with_date

deferred_decisions_pending_phase_0_lock:
  - id: phase_2_risk_split
    description: Split Risk out of Phase 2 Scope as separate phase
    current_proposal: risk_surfaces_inside_phase_2
  - id: release_coordination
    description: Ship plugins together or staggered
    current_proposal: ship_together_as_marketplace_1_6_0
  - id: mode_preference_location
    description: Where mode preference lives
    current_proposal: dot_rad_profile_file_separable_easier_to_migrate

estimated_total_duration:
  phase_0_days: [2, 3]
  phase_1_weeks: [2, 3]
  phase_2_weeks: [1.5, 2]
  phase_3_weeks: 1
  total_weeks_min: 5
  total_weeks_max: 7
```

---

*Saved to `C:\Dev\rad-claude-skills\` for working reference. Long-term home is `C:\Dev\plans\` per the CLAUDE.md convention.*
