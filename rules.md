# Global Android Coding Standards & Preferences

> **Rule Inheritance & Fallback Directive**:
  Every project-specific rule file (`GEMINI.md` or `AGENTS.md` in project roots) must reference and extend this global configuration (`C:\Users\Or Dvir\.gemini\rules.md`). If this global file is ever unreachable, missing, or the path changed, the agent MUST proactively alert the user immediately so the link can be restored.

> **Non-Disruptive Guardrail for Existing Codebases**:
  If an existing project or file does not currently conform to these rules, **DO NOT automatically or unilaterally refactor it**. Focus strictly on the user's immediate request to avoid noise and unexpected breakages. You may *suggest* modernization/alignment, but execution must be explicitly requested or permitted by the user.

> **Agent Communication & Behavior Standards**:
  - **Clarify, Don't Assume**: If a request is ambiguous, ask targeted follow-up questions before acting. Never guess intent.
  - **Code Over Memory**: Inspect actual project files rather than relying on memory, unless the context is very recent and unlikely to have changed.
  - **Concise & Plain Language**: Speak plainly and to the point. No fluff, no over-explaining. The user will ask if they need more detail.
  - **Token & Rate Limit Optimization**: Keep responses compact and token-efficient for free-tier quotas.
  - **All Output Is a Draft**: Treat every code change as a first draft for user review. Nothing is final or shipped until the user explicitly approves it.
  - **Stop on Errors**: If you encounter an error, limitation, or unexpected result, **stop and report it**. Do not silently guess a workaround.
  - **Git Tracking**: Global rules (`rules.md`) and skills are tracked in the `agents-config` Git repo. For changes: create a branch, commit, open a PR, and **stop**. Never merge — only the user may approve and merge PRs. Project-specific rules are tracked in the respective project repository.
  - **Incremental Task Execution (applies to all coding tasks, all projects)**:
    - Break large tasks into small, cohesive **units of change** — each forming a logical, reviewable chunk.
    - After completing each unit, pause for user review and approval before continuing.
    - Only push approved changes to the remote. Ask the user whether to push now or combine with the next unit.
    - If a unit is still too large, break it down further into smaller intervals that make logical sense.
    - This prevents: overloading the user with massive reviews, leaving work half-done if tokens run out, and large unreviewed diffs.

---


## 1. Package Naming & Build Type Conventions
- **Base Package Name**: `com.hotmail.or_dvir.<app_name>` (e.g. `com.hotmail.or_dvir.myapp`).
- **Debug Build Type Convention**:
  Always configure the `debug` build type with suffixes so debug and release apps can exist side-by-side on the same device:
  - Kotlin DSL (`build.gradle.kts`):
    ```kotlin
    buildTypes {
        debug {
            isDebuggable = true
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-DEBUG"
        }
    }
    ```
  - Groovy DSL (`build.gradle`):
    ```groovy
    buildTypes {
        debug {
            debuggable true
            applicationIdSuffix '.debug'
            versionNameSuffix '-DEBUG'
        }
    }
    ```

---

## 2. Core Architecture & Tech Stack
- **Language**: 100% Kotlin with structured concurrency (Coroutines & Flow). No RxJava or legacy raw callbacks.
- **UI Framework**: Modern Jetpack Compose with Material Design 3 (`androidx.compose.material3`). Never generate legacy XML layouts, Views, or Support Fragments unless explicitly asked.
- **Architectural Patterns (Pragmatic MVI / MVVM)**:
  - **Screen State & Actions**: Prefer `ScreenState` (data class) + `ScreenAction` (sealed interface) + `onAction(action)` in the ViewModel for unidirectional data flow.
  - **One-Time UI Events**: Dispatch navigation, Snackbars, or toasts via `Channel<UiEvent>` (consumed as a Flow in Compose).
  - **Lifecycle-Aware Collection**: Always collect state Flows in Composables using `collectAsStateWithLifecycle()` (from `androidx.lifecycle.runtime.compose`) rather than raw `collectAsState()`.
  - **Pragmatic State Management (Do Not Overcomplicate)**:
    - Complex/business state: Maintained in ViewModel and exposed via `StateFlow<ScreenState>`.
    - Simple/direct state: `mutableStateOf(...)` can be used directly wherever simpler--either inside ViewModel (e.g. `var searchQuery by mutableStateOf("")`) OR locally inside Composables via `remember { mutableStateOf(...) }` for transient UI flags (e.g., dropdown expansion, dialogs, animations).
  - **Recomposition Stability**: Apply `@Immutable` / `@Stable` annotations to custom UI models when beneficial for preventing unnecessary recomposition passes.
- **Data Layer & Domain**:
  - Repositories manage data sources (Room, Firebase, etc.). Avoid unnecessary single-line UseCases unless business logic is genuinely complex.
  - For large/complex projects, organize by feature modules (e.g. `feature/auth/`); for standard smaller projects, maintain a clean, flat pragmatic structure.
- **Dependency Management & BOMs**:
  - Always use Gradle Version Catalogs (`gradle/libs.versions.toml`). No hardcoded versions in `build.gradle.kts`.
  - Always use Bill of Materials (BOM) platform dependencies whenever available (e.g. `firebase-bom`, `compose-bom`).
- **Firebase & Environment Separation**:
  - Default to Firebase (Auth, Firestore, Cloud Storage, etc.) using modern Kotlin Firebase SDKs.
  - Always separate Production and Development/Debug Firebase projects via source sets pre-configured in advance:
    - `app/src/debug/google-services.json` (Development / Testing Firebase project)
    - `app/src/release/google-services.json` (Production Firebase project)
- **Error Handling**: Use Kotlin's built-in `Result<T>` by default for repositories unless a custom sealed hierarchy (e.g. `NetworkResult<T>`) is genuinely warranted.
- **Dependency Injection**: Modern Hilt or Koin.

---

## 3. UI Design & System Behavior
- **Edge-to-Edge Layout**:
  - Always call `enableEdgeToEdge()` in `MainActivity`.
  - Always respect `scaffoldLevel innerPadding` / `WindowInsets` so content never gets clipped by the status bar, notch, or gesture navigation bar.
- **Expressive Material 3 Colors & Accents (Avoid Bland UI)**:
  - **Tonal Containers**: Use `surfaceContainer`, `surfaceContainerHigh`, and `surfaceContainerLow` for cards and groups rather than flat gray/white surfaces with plain lines.
  - **Colored Icon Badges**: For settings/preferences rows and lists, wrap icons in tinted rounded badge containers (e.g. `primaryContainer`, `secondaryContainer`, or `tertiaryContainer` with matching icon tints) for high-end visual feel.
  - **Tertiary & Semantic Tokens**: Use `tertiary` for accents and extend `ColorScheme` with semantic status colors (`success`, `warning`, `info`) where beneficial.
- **Generating UI Options**:
  - When the user asks for *"offer UI options for this screen"*, PROACTIVELY present **3 to 4 distinct layout & aesthetic archetypes** (e.g., Card-Grouped, immersive Hero-Header, compact filtered grid, minimalist divided), explaining the UX strengths of each.
- **Theme Selection & Persistence**:
  - Apps should support 3-way theme selection: **System Default**, **Always Light**, and **Always Dark** (managed via Material 3 theming).
  - Persist the selected preference locally using the latest officially recommended method for lightweight key-value storage (e.g. Jetpack DataStore).
- **Preview Strategy**:
  - **Reusable Components**: Combine multiple component states (e.g. Enabled + Disabled, Primary + Secondary, Active + Inactive) inside a single combined preview container wherever possible to prevent preview explosion.
  - **Full Screens**: Provide previews covering all relevant domain states (e.g. Success/Content, Loading, Empty, Error, or any feature-specific user states).
- **State Hoisting**: Keep individual UI components stateless where reasonable by passing state and event lambdas up to the screen-level caller.

---

## 4. Gradle Build & Performance Optimizations
- When initializing or auditing a project, ensure `gradle.properties` enables modern build acceleration:
  ```properties
  org.gradle.caching=true
  org.gradle.parallel=true
  org.gradle.configuration-cache=true
  ```
- Verify builds and tests via `./gradlew assembleDebug` or `./gradlew testDebugUnitTest` upon major changes.
- Use `android layout` or `android screen capture` when debugging live UI on devices/emulators.

---

## 5. Guideline for Creating New Project-Specific `AGENTS.md` Files
 Whenever initializing a new Android project or adding project rules, the agent MUST create a top-level `AGENTS.md` in that project's root folder following this exact structure:

```markdown
# [App Name] - Project Guidelines & Context

> **Inherits Global Standards**: [Global Android Rules](file:///C:/Users/Or%20Dvir/.gemini/rules.md)
> If the file above cannot be read or is unreachable, alert the user immediately.

## 1. Project Identity & Overview
- Package Name: `com.hotmail.or_dvir.<app_name>`
- App Purpose: [Brief description]


## 2. Tech Stack & Data Sources
- Backend / Services: Firebase (Separate Prod & Debug projects)
  - `app/src/debug/google-services.json`
  - `app/src/release/google-services.json`
- Local Storage: [Room DB, DataStore, etc.]
- UI Libraries: Material 3, Compose BoM, etc.



## 3. Key Features & Screens
- [Feature 1 / Screen 1]
- [Feature 2 / Screen 2]
```
