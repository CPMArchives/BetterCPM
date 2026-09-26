# Engineering Specification 156: Stage 7 Extension Dependency Erratum

## Purpose

This bounded documentation erratum corrects an overstatement in the Stage 7
retained implementation contract. It does not reopen Stages 3 through 8, change
BCPX v1 or BRSX v2, add a dependency manager, or alter the implemented
transactional reconstruction path.

## Source audit

BCPX v1 carries identity, ABI requirements, layout, lifecycle entries,
relocations, exported commands and integrity information. It contains no
declarative dependency, conflict or relative-order records.

BRSX v2 metadata version 1 defines exactly three record types: intercepted
numeric BDOS services, callable-service advertisements and runtime-pointer
slots. Unknown metadata-v1 record types reject. It likewise contains no general
module relationship records.

The production prospective-profile path validates the frozen carrier facts,
complete memory layout, reconstruction classes, relocation and pointer
metadata, callable advertisements, duplicate callable-service identities,
available carrier inputs and explicit profile order. It cannot construct or
validate a relationship graph which neither carrier represents.

No retained 1.0 extension declares a hard module dependency, conflict or
relative-order rule. `P2DOS.RSX` uses TIME as a soft runtime service: it remains
valid without a provider, resolves TIME on every request and reports the
documented claimed-failure result while TIME is unavailable.

## Corrected 1.0 contract

BetterCP/M 1.0 preserves explicit CPX and RSX profile order but defines no
general declarative module-dependency, conflict or relative-order metadata.
BCPX v1 and BRSX v2 carry no such relationships.

Every configuration change remains transactional. The implementation constructs
and validates the complete prospective configuration according to every
invariant represented by the applicable carrier and subsystem contracts and
publishes only after validation succeeds. Failure leaves the previously
published configuration authoritative. Duplicate callable-service providers
remain a defined rejection, and component-specific unload rules such as FDF's
managed logical-binding detachment remain unchanged.

Runtime use of another resident service does not by itself constitute a module
dependency. A consumer may remain installed while a provider is absent when its
service contract defines unavailable behavior.

## Deferred relationship work

A later carrier or metadata revision may define dependency identifiers and
targets, version constraints, installation capability requirements, conflicts,
relative-order declarations, graph and cycle validation, and cross-CPX/RSX
semantics. None of those semantics is frozen by this erratum, and no minor
release is assigned. Design begins only when a concrete approved component
demonstrates the requirement.

## Disposition

This is a specification correction rather than a runtime defect. The existing
1.0 implementation program gains no dependency subsystem, carrier revision or
graph validator. Explicit profile order, transactional validation and rollback,
callable-service uniqueness, runtime discovery and component-specific safety
rules remain release requirements.
