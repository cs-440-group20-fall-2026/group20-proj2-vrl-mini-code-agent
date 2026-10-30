# Environment Context (Strategy 1)

## Scope
- Scope: `strategy_1/` and its subdirectories; paths are relative to it. 
- Reference Codebase: `server/src/main/java/com/tco/` for API requests and calculation logic.

## Request & Parameter Specifications (`DistancesRequest`)
- **Core Parameters:** Requires `places` and a positive, finite `earthRadius`.
- **Formula Rules:** 
  - If `formula` is omitted (`null`), it defaults locally to `"vincenty"` while keeping `this.formula` null to prevent JSON serialization leaks.
  - Explicit empty strings or whitespace (`""`) throw an HTTP 400 `BadRequestException`.
  - Supported formula whitelist: `"vincenty"`, `"haversine"`, `"cosine"`, `"law of cosines"`. Any other input throws an `IllegalArgumentException`.

## Build & Execution
- **Compile:** `mvn compile`
- **Test:** `mvn test`
- **Validation Standard:** Ensure all request-level updates maintain strict input validation and appropriate HTTP error mapping before pushing to feature branches or merging into `main`.
